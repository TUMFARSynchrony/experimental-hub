"""Provide the `Participant` class and `participant_factory` factory function.

Notes
-----
Use participant_factory for creating new participants to ensure that they have a valid
hub.connection.Connection.
"""

from __future__ import annotations
import asyncio
import logging
import os
from typing import Any, Coroutine

from filters import filter_utils
from session.data.participant import ParticipantSummaryDict
from session.data.participant import ParticipantDict
from custom_types.chat_message import is_valid_chatmessage
from custom_types.kick import KickNotificationDict
from custom_types.message import MessageDict
from custom_types.success import SuccessDict

import experiment.experiment as _exp
from experiment import ExperimentState
from connection.connection_state import ConnectionState
from hub.exceptions import ErrorDictException
from session.data.participant import ParticipantData
from users.experimenter import User
import hub.hub as _h


class Participant(User):
    """Participant is a type of hub.user.User with participant rights.

    Has access to a different set of API endpoints than other Users.  API endpoints for
    participants are defined here.

    Methods
    -------
    get_summary()
        Get custom_types.participant_summary.ParticipantSummaryDict for this Participant
        .
    kick(reason)
        Kick the Participant.
    ban(reason)
        Ban the Participant.

    See Also
    --------
    participant_factory : Instantiate connection with a new Participant based on WebRTC
        `offer`.  Use factory instead of initiating Participants directly.
    """

    _experiment: _exp.Experiment
    _participant_data: ParticipantData
    _hub: _h.Hub

    def __init__(
        self,
        participant_id: str,
        experiment: _exp.Experiment,
        participant_data: ParticipantData,
        hub: _h.Hub,
    ) -> None:
        """Instantiate new Participant instance.

        Parameters
        ----------
        participant_id : str
            Unique identifier for Participant.  Must exist in experiment.
        experiment : hub.experiment.Experiment
            Experiment the participant is part of.
        participant_data : session.data.participant.ParticipantData
            Participant data this participant represents.

        See Also
        --------
        participant_factory : Instantiate connection with a new Participant based on
            WebRTC `offer`.  Use factory instead of instantiating Participant directly.
        """
        super(Participant, self).__init__(
            participant_id, participant_data.muted_video, participant_data.muted_audio
        )
        self._logger = logging.getLogger(f"Participant-{participant_id}")
        self._participant_data = participant_data
        self._experiment = experiment
        self._hub = hub
        experiment.add_participant(self)
        experiment.on("state", self._handle_state)

        # Add API endpoints
        self.on_message("CHAT", self._handle_chat)
        self.on_message("GET_SESSION", self._handle_get_session)
        # INFO: This is a solution to get filters data for one participant.
        # However, it is currently not working.
        # Please have a look at issue: https://github.com/TUMFARSynchrony/experimental-hub/issues/154
        # self.on_message("GET_FILTERS_DATA", self._handle_get_filters_data)

    def __str__(self) -> str:
        """Get string representation of this participant.

        Currently, returns value of `__repr__`.
        """
        return (
            f"id={self.id}, participant_name={self._participant_data.participant_name},"
            f" experiment={self._experiment.session.id}"
        )

    def __repr__(self) -> str:
        """Get representation of this participant."""
        return f"Participant({str(self)})"

    def get_summary(self) -> ParticipantSummaryDict:
        return self._participant_data.as_summary_dict()

    async def kick(self, reason: str) -> None:
        """Kick the participant.

        Notify the participant about the kick with a `KICK_NOTIFICATION` message and
        disconnect the participant.

        Parameters
        ----------
        reason : str
            Reason for the kick.  Will be sent to the participant in the
            `KICK_NOTIFICATION`.
        """
        kick_notification = KickNotificationDict(reason=reason)
        message = MessageDict(type="KICK_NOTIFICATION", data=kick_notification)
        await self.send(message)

        await self.disconnect()

    async def ban(self, reason: str) -> None:
        """Ban the participant.

        Notify the participant about the ban with a `BAN_NOTIFICATION` message and
        disconnect the participant.

        Parameters
        ----------
        reason : str
            Reason for the kick.  Will be sent to the participant in the
            `BAN_NOTIFICATION`.
        """
        ban_notification = KickNotificationDict(reason=reason)
        message = MessageDict(type="BAN_NOTIFICATION", data=ban_notification)
        await self.send(message)

        await self.disconnect()

    async def _handle_connection_state_change(self, state: ConnectionState) -> None:
        """Handler for connection "state_change" event.

        Implements the abstract `_handle_connection_state_change` function in
        hub.user.User.

        Parameters
        ----------
        state : hub.connection_state.ConnectionState
            New state of the connection this Participant has with the client.
        """
        self._logger.debug(f"Handle state change. State: {state}")
        if state is ConnectionState.CONNECTED:
            self._logger.info(f"Participant connected. {self}")
            coroutines: list[Coroutine] = []
            # Add stream to all experimenters
            for e in self._experiment.experimenters:
                coroutines.append(self.add_subscriber(e))

            # Add stream to all participants and all participants streams to self
            if self._experiment.state == ExperimentState.RUNNING:
                coroutines.append(self._subscribe_and_add_subscribers())
                if self.experiment.session.record:
                    coroutines.append(self.start_recording())
            else:
                # Wait for experiment to start (state = `RUNNING`) before subscribing
                self._subscribe_later()

            await asyncio.gather(*coroutines)

    async def _subscribe_and_add_subscribers(self):
        """Subscribe to all participants in experiment and add them as subscribers."""
        coroutines: list[Coroutine] = []
        for p in self._experiment.participants.values():
            if p is self:
                continue
            coroutines.append(self.add_subscriber(p))
            coroutines.append(p.add_subscriber(self))
        await asyncio.gather(*coroutines)

    def _subscribe_later(self):
        """Wait for experiment state to be running, then subscribe to others.

        Notes
        -----
        Uses event handlers for the connection `state` event and user (self)
        `disconnected` event. The latter is used to remove the connection event handler.
        """

        @self.on("disconnected")
        def _remove_subscribe_callback(_) -> None:
            """Remove listeners from experiment when participant disconnects."""
            try:
                self._experiment.remove_listener("state", _subscribe_callback)
            except KeyError:
                pass

        @self._experiment.on("state")
        async def _subscribe_callback(state: ExperimentState) -> None:
            """If `state` is `RUNNING`, subscribe to all participants in experiment."""
            if state == ExperimentState.RUNNING:
                _remove_subscribe_callback(None)
                participants = self._experiment.participants.values()
                coroutines = [p.add_subscriber(self) for p in participants if p != self]
                await asyncio.gather(*coroutines)
            else:
                return

    async def _handle_state(self, state: Any):
        """Handle state.

        Notes
        -----
        Uses event handlers for the connection `state` event and user (self)
        `disconnected` event. The latter is used to remove the connection event handler.
        """
        if self.experiment.session.record:
            if state == ExperimentState.RUNNING:
                await self.start_recording()
            elif state == ExperimentState.ENDED:
                await self.stop_recording()
            else:
                return

    async def _handle_chat(self, data: Any) -> MessageDict:
        """Handle requests with type `CHAT`.

        Check if data is a valid custom_types.chat_message.ChatMessageDict, target is
        set to "experimenter", author is the ID of this participant and pass the request
        to the experiment.

        Parameters
        ----------
        data : any or custom_types.chat_message.ChatMessageDict
            Message data, can be anything.  Everything other than
            custom_types.chat_message.ChatMessageDict will result in a `ERROR` response.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `CHAT`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.chat_message.ChatMessageDict, target is
            not set to "experimenter" or author is not the ID of this participant.
        """
        if not is_valid_chatmessage(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid ChatMessage.",
            )

        if data["author"] != self.id:
            raise ErrorDictException(
                code=400,
                type="INVALID_REQUEST",
                description="Author of message must be participant ID.",
            )

        await self._experiment.handle_chat_message(data)

        success = SuccessDict(
            type="CHAT", description="Successfully send chat message."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_get_session(self, data: Any) -> MessageDict:
        """Handle requests with type `GET_SESSION`.

        Loads session with given id from session manager.  Responds with type:
        `GET_SESSION`.

        Parameters
        ----------
        _ : any
            Message data.  Ignored / not required.

        Returns
        -------
        custom_types.message.MessageDict with type: `SESSION` and data: custom_types.session.SessionDict.
        """
        session = self._hub.session_manager.get_session(data["session_id"])
        if session is None:
            raise ErrorDictException(
                code=404,
                type="UNKNOWN_SESSION",
                description="No session with the given ID found to update.",
            )
        session_dict = session.asdict()
        return MessageDict(type="SESSION", data=session_dict)

    def get_recording_path(self):
        """Get the recording path for current participant.

        Notes
        -----
        All recordings will be saved in sessions folder by default.
        The format: ./sessions/<session_id>/<participant_id>
        """
        record_directory_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "sessions",
            self.experiment.session.id,
        )
        if not os.path.isdir(record_directory_path):
            os.mkdir(record_directory_path)
        return record_directory_path + "/" + self.id

    def get_participant_data(self) -> ParticipantDict:
        """Get `self._experiment` or raise ErrorDictException if it is None.

        Use to check if this Experimenter is connected to an
        hub.experiment.Experiment.

        Raises
        ------
        ErrorDictException
            If `self._experiment` is None
        """
        if self._participant_data is not None:
            return self._participant_data.asdict()

        raise ErrorDictException(
            code=409, type="INVALID_REQUEST", description="Participant has no data"
        )

    async def _handle_get_filters_data(self, data: Any) -> MessageDict:
        """Handle requests with type `GET_FILTERS_DATA`.

        Check if data is a valid GetFiltersDataRequestDict and return filter data for
        specific participant.

        Parameters
        ----------
        data : any or filters.GetFiltersDataRequestDict
            Message data.  Checks if data is a valid GetFiltersDataRequestDict and raises
            an ErrorDictException if not.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `FILTERS_DATA`, data: dict[str, FiltersDataDict]

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.filters.GetFiltersDataRequestDict.
            Or if values of data are incorrect.
        """
        if not filter_utils.is_valid_get_filters_data_dict(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid GetFiltersData.",
            )

        res = await self.get_filters_data_for_one_participant(data)

        return MessageDict(type="FILTERS_DATA", data=res)
