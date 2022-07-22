"""Provide the `Experimenter` class and `experimenter_factory` factory function.

Notes
-----
Use experimenter_factory for creating new Experimenters to ensure that they have a valid
modules.connection.Connection.
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any, Coroutine
from aiortc import RTCSessionDescription

from custom_types.filters import is_valid_set_filters_request
from custom_types.session import is_valid_session
from custom_types.chat_message import is_valid_chatmessage
from custom_types.kick import is_valid_kickrequest
from custom_types.message import MessageDict
from custom_types.success import SuccessDict
from custom_types.note import is_valid_note
from custom_types.mute import is_valid_mute_request
from custom_types.session_id_request import is_valid_session_id_request


from modules.filter_api import FilterAPI
from modules.connection_state import ConnectionState
from modules.connection import connection_factory
from modules.connection_subprocess import connection_subprocess_factory
from modules.exceptions import ErrorDictException
from modules.user import User
import modules.experiment as _exp
import modules.hub as _h


class Experimenter(User):
    """Experimenter is a type of modules.user.User with experimenter rights.

    Has access to a different set of API endpoints than other Users.  API endpoints for
    experimenters are defined here.

    See Also
    --------
    experimenter_factory : Instantiate connection with a new Experimenter based on
        WebRTC `offer`.  Use factory instead of instantiating Experimenter directly.
    """

    _experiment: _exp.Experiment | None
    _hub: _h.Hub

    def __init__(self, id: str, hub: _h.Hub) -> None:
        """Instantiate new Experimenter instance.

        Parameters
        ----------
        id : str
            Unique identifier for this Experimenter.
        hub : modules.hub.Hub
            Hub this Experimenter is part of.  Used for api calls.

        See Also
        --------
        experimenter_factory : Instantiate connection with a new Experimenter based on
            WebRTC `offer`.  Use factory instead of instantiating Experimenter directly.
        """
        super(Experimenter, self).__init__(id)
        self._logger = logging.getLogger(f"Experimenter-{id}")
        self._hub = hub
        self._experiment = None

        # Add API endpoints
        self.on_message("GET_SESSION_LIST", self._handle_get_session_list)
        self.on_message("SAVE_SESSION", self._handle_save_session)
        self.on_message("DELETE_SESSION", self._handle_delete_session)
        self.on_message("CREATE_EXPERIMENT", self._handle_create_experiment)
        self.on_message("JOIN_EXPERIMENT", self._handle_join_experiment)
        self.on_message("LEAVE_EXPERIMENT", self._handle_leave_experiment)
        self.on_message("START_EXPERIMENT", self._handle_start_experiment)
        self.on_message("STOP_EXPERIMENT", self._handle_stop_experiment)
        self.on_message("ADD_NOTE", self._handle_add_note)
        self.on_message("CHAT", self._handle_chat)
        self.on_message("KICK_PARTICIPANT", self._handle_kick)
        self.on_message("BAN_PARTICIPANT", self._handle_ban)
        self.on_message("MUTE", self._handle_mute)
        self.on_message("SET_FILTERS", self._handle_set_filters)

    def __str__(self) -> str:
        """Get string representation of this experimenter.

        Currently returns value of `__repr__`.
        """
        return f"id={self.id}, experiment={str(self._experiment)}"

    def __repr__(self) -> str:
        """Get representation of this experimenter."""
        return f"Experimenter({str(self)})"

    async def _handle_connection_state_change(self, state: ConnectionState) -> None:
        """Handler for connection "state_change" event.

        Implements the abstract `_handle_connection_state_change` function in
        modules.user.User.

        Parameters
        ----------
        state : modules.connection_state.ConnectionState
            New state of the connection this Experimenter has with the client.
        """
        self._logger.debug(f"Handle state change. State: {state}")
        if state is ConnectionState.CONNECTED:
            self._logger.info(f"Experimenter connected. {str(self)}")
            await self._subscribe_to_participants_streams()

    async def _subscribe_to_participants_streams(self) -> None:
        """Subscribe to all participants in `self._experiment`."""
        if self._experiment is not None:
            coros: list[Coroutine] = []
            for p in self._experiment.participants.values():
                if p is self:
                    continue
                coros.append(p.add_subscriber(self))
            await asyncio.gather(*coros)

    async def _handle_get_session_list(self, _) -> MessageDict:
        """Handle requests with type `GET_SESSION_LIST`.

        Loads all known sessions from session manager.  Responds with type:
        `SESSION_LIST`.

        Parameters
        ----------
        _ : any
            Message data.  Ignored / not required.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SESSION_LIST` and data: list of
            custom_types.session.SessionDict.
        """
        sessions = self._hub.session_manager.get_session_dict_list()
        return MessageDict(type="SESSION_LIST", data=sessions)

    async def _handle_save_session(self, data: Any) -> MessageDict:
        """Handle requests with type `SAVE_SESSION`.

        Checks if received data is a valid SessionDict.  Try to update existing session,
        if `id` in data is not a empty string, otherwise try to create new session.

        As a response, `SAVED_SESSION` is send to the caller.  Additionally,
        `SESSION_CHANGE` is send to all other experimenters connected to the hub.

        Parameters
        ----------
        data : any or custom_types.session.SessionDict
            Message data, can be anything.  Everything other than
            custom_types.session_id_request.SessionIdRequestDict will raise an
            modules.exceptions.ErrorDictException.

        Raises
        ------
        ErrorDictException
            If data is not a valid SessionDict or session id is not known (cannot update
            unknown session).
        """
        # Data check
        if not is_valid_session(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid Session object.",
            )

        sm = self._hub.session_manager
        if data["id"] == "":
            # Create new session
            session = sm.create_session(data)

            # Notify all experimenters about the change
            session_dict = session.asdict()
            message = MessageDict(type="SESSION_CHANGE", data=session_dict)
            await self._hub.send_to_experimenters(message, self)
            return MessageDict(type="SAVED_SESSION", data=session_dict)

        # Update existing session
        session = sm.get_session(data["id"])
        if session is None:
            raise ErrorDictException(
                code=404,
                type="UNKNOWN_SESSION",
                description="No session with the given ID found to update.",
            )

        # Check if session has already started and should not be edited anymore
        if session.start_time != 0:
            raise ErrorDictException(
                code=409,
                type="EXPERIMENT_ALREADY_STARTED",
                description="Cannot edit session, session has already started.",
            )

        # Check if read only parameters where changed
        # Checks for participant IDs are included in session.update()
        if data["creation_time"] != session.creation_time:
            raise ErrorDictException(
                code=409,
                type="INVALID_PARAMETER",
                description=(
                    'Cannot change session "creation_time", field is read only.'
                ),
            )

        if data["start_time"] != session.start_time:
            raise ErrorDictException(
                code=409,
                type="INVALID_PARAMETER",
                description='Cannot change session "start_time", field is read only.',
            )

        if data["end_time"] != session.end_time:
            raise ErrorDictException(
                code=409,
                type="INVALID_PARAMETER",
                description='Cannot change session "end_time", field is read only.',
            )

        session.update(data)

        # Notify all experimenters about the change
        session_dict = session.asdict()
        message = MessageDict(type="SESSION_CHANGE", data=session_dict)
        await self._hub.send_to_experimenters(message, self)

        return MessageDict(type="SAVED_SESSION", data=session_dict)

    async def _handle_delete_session(self, data: Any) -> None:
        """Handle requests with type `DELETE_SESSION`.

        Check if data is a valid custom_types.session_id_request.SessionIdRequestDict.
        If found, delete session with the `session_id` in `data`.

        After deletion, a `DELETED_SESSION` message is send to all experimenters.

        Parameters
        ----------
        data : any or custom_types.session_id_request.SessionIdRequestDict
            Message data, can be anything.  Everything other than
            custom_types.session_id_request.SessionIdRequestDict will raise an
            modules.exceptions.ErrorDictException.

        Raises
        ------
        ErrorDictException
            If data is not a valid dict with an `session_id` str or if `session_id` is
            not known.
        """
        if not is_valid_session_id_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid SessionIdRequest.",
            )

        session_id = data["session_id"]
        # Check if there is an experiment running with this session_id
        if session_id in self._hub.experiments:
            raise ErrorDictException(
                code=400,
                type="EXPERIMENT_RUNNING",
                description="Cannot delete session with running experiment.",
            )

        self._hub.session_manager.delete_session(session_id)

        # Notify all experimenters about the change
        message = MessageDict(type="DELETED_SESSION", data=session_id)
        await self._hub.send_to_experimenters(message)

    async def _handle_create_experiment(self, data: Any) -> MessageDict:
        """Handle requests with type `CREATE_EXPERIMENT`.

        Check if data is a valid custom_types.session_id_request.SessionIdRequestDict.
        If found, try to create a new modules.experiment.Experiment based on the session
        with the `session_id` in `data`.

        Experimenters are notified using a `EXPERIMENT_CREATED` message by the hub.

        Parameters
        ----------
        data : any or custom_types.session_id_request.SessionIdRequestDict
            Message data, can be anything.  Everything other than
            custom_types.session_id_request.SessionIdRequestDict will raise an
            modules.exceptions.ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `JOIN_EXPERIMENT`.

        Raises
        ------
        ErrorDictException
            If data is not a valid dict with an `session_id` str, if `session_id` is not
            known or if there is already an Experiment with `session_id`.
        """
        if not is_valid_session_id_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid SessionIdRequest.",
            )

        self._experiment = await self._hub.create_experiment(data["session_id"])
        self._experiment.add_experimenter(self)

        # Subscribe to participants in experiment
        await self._subscribe_to_participants_streams()

        # Notify caller that he joined the experiment
        success = SuccessDict(
            type="JOIN_EXPERIMENT",
            description="Successfully started and joined experiment.",
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_join_experiment(self, data: Any) -> MessageDict:
        """Handle requests with type `JOIN_EXPERIMENT`.

        Check if data is a valid custom_types.session_id_request.SessionIdRequestDict.
        If found, try to join an existing modules.experiment.Experiment with the
        `session_id` in `data`.

        Parameters
        ----------
        data : any or custom_types.session_id_request.SessionIdRequestDict
            Message data, can be anything.  Everything other than
            custom_types.session_id_request.SessionIdRequestDict will raise an
            modules.exceptions.ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `JOIN_EXPERIMENT`.

        Raises
        ------
        ErrorDictException
            If data is not a valid dict with a `session_id` str or if there is no
            Experiment with `session_id`. Also raises if this experimenter is already
            part of an experiment.
        """
        if not is_valid_session_id_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid SessionIdRequest.",
            )

        if self._experiment is not None:
            raise ErrorDictException(
                code=409,
                type="ALREADY_JOINED_EXPERIMENT",
                description=(
                    "Can not join an experiment while already connected to an "
                    "experiment."
                ),
            )

        experiment = self._hub.experiments.get(data["session_id"])

        if experiment is None:
            raise ErrorDictException(
                code=404,
                type="UNKNOWN_EXPERIMENT",
                description="There is no experiment with the given ID.",
            )

        self._experiment = experiment
        self._experiment.add_experimenter(self)

        # Subscribe to participants in experiment
        await self._subscribe_to_participants_streams()

        success = SuccessDict(
            type="JOIN_EXPERIMENT", description="Successfully joined experiment."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_leave_experiment(self, _) -> MessageDict:
        """Handle requests with type `LEAVE_EXPERIMENT`.

        If part of an experiment, remove self from experiment and set `self._experiment`
        to None.

        Raises
        ------
        ErrorDictException
            If this Experimenter is not connected to an modules.experiment.Experiment.
        """
        experiment = self.get_experiment_or_raise("Failed to leave experiment.")
        experiment.remove_experimenter(self)

        for participant in experiment.participants.values():
            await participant.remove_subscriber(self)

        self._experiment = None

        success = SuccessDict(
            type="LEAVE_EXPERIMENT", description="Successfully left experiment."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_start_experiment(self, _) -> MessageDict:
        """Handle requests with type `START_EXPERIMENT`.

        Parameters
        ----------
        _ : any
            Message data.  Ignored / not required.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `START_EXPERIMENT`.

        Raises
        ------
        ErrorDictException
            If this Experimenter is not connected to an modules.experiment.Experiment or
            the Experiment has already started.
        """
        experiment = self.get_experiment_or_raise("Cannot start experiment.")
        await experiment.start()

        success = SuccessDict(
            type="START_EXPERIMENT", description="Successfully started experiment."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_stop_experiment(self, _) -> MessageDict:
        """Handle requests with type `STOP_EXPERIMENT`.

        Parameters
        ----------
        _ : any
            Message data.  Ignored / not required.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `STOP_EXPERIMENT`.

        Raises
        ------
        ErrorDictException
            If this Experimenter is not connected to an modules.experiment.Experiment or
            the Experiment has already ended.
        """
        experiment = self.get_experiment_or_raise("Cannot stop experiment.")
        await experiment.stop()

        success = SuccessDict(
            type="STOP_EXPERIMENT", description="Successfully stopped experiment."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_add_note(self, data: Any) -> MessageDict:
        """Handle requests with type `ADD_NOTE`.

        Check if data is a valid custom_types.note.NoteDict and adds the note to the
        modules.experiment.Experiment the Experimenter is connected to.

        Parameters
        ----------
        data : any or custom_types.note.NoteDict
            Message data, can be anything.  Everything other than
            custom_types.note.NoteDict will raise an
            modules.exceptions.ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `ADD_NOTE`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.note.NoteDict or if this Experimenter is
            not connected to an modules.experiment.Experiment.
        """
        if not is_valid_note(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid Note.",
            )

        experiment = self.get_experiment_or_raise("Cannot add note.")
        experiment.session.notes.append(data)

        success = SuccessDict(type="ADD_NOTE", description="Successfully added note.")
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_chat(self, data: Any) -> MessageDict:
        """Handle requests with type `CHAT`.

        Check if data is a valid custom_types.chat_message.ChatMessageDict, `target` is
        "experimenter" and pass the request to the experiment.

        Parameters
        ----------
        data : any or custom_types.chat_message.ChatMessageDict
            Message data, can be anything.  Everything other than
            custom_types.chat_message.ChatMessageDict will raise an ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `CHAT`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.chat_message.ChatMessageDict,
            `target` is not "experimenter" or this Experimenter is not connected to an
            modules.experiment.Experiment.
        """
        if not is_valid_chatmessage(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid ChatMessage.",
            )

        if data["author"] != "experimenter":
            raise ErrorDictException(
                code=400,
                type="INVALID_REQUEST",
                description="Author of message must be experimenter.",
            )

        experiment = self.get_experiment_or_raise("Cannot send chat message.")
        await experiment.handle_chat_message(data)

        success = SuccessDict(
            type="CHAT", description="Successfully send chat message."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_kick(self, data: Any) -> MessageDict:
        """Handle requests with type `KICK`.

        Check if data is a valid custom_types.kick.KickRequestDict and pass the request
        to the experiment.

        Parameters
        ----------
        data : any or custom_types.kick.KickRequestDict
            Message data, can be anything.  Everything other than
            custom_types.kick.KickRequestDict will raise an ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `KICK`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.kick.KickRequestDict or if this
            Experimenter is not connected to an modules.experiment.Experiment.
        """
        if not is_valid_kickrequest(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid KickRequest.",
            )

        experiment = self.get_experiment_or_raise("Cannot kick participant.")
        await experiment.kick_participant(data["participant_id"], data["reason"])

        success = SuccessDict(
            type="KICK_PARTICIPANT", description="Successfully kicked participant."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_ban(self, data: Any) -> MessageDict:
        """Handle requests with type `BAN`.

        Check if data is a valid custom_types.kick.KickRequestDict and pass the request
        to the experiment.

        Parameters
        ----------
        data : any or custom_types.kick.KickRequestDict
            Message data, can be anything.  Everything other than
            custom_types.kick.KickRequestDict will raise an ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `BAN`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.kick.KickRequestDict or if this
            Experimenter is not connected to an modules.experiment.Experiment.
        """
        if not is_valid_kickrequest(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid KickRequest.",
            )

        experiment = self.get_experiment_or_raise("Cannot ban participant.")
        await experiment.ban_participant(data["participant_id"], data["reason"])

        success = SuccessDict(
            type="BAN_PARTICIPANT", description="Successfully banned participant."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_mute(self, data: Any) -> MessageDict:
        """Handle requests with type `MUTE`.

        Check if data is a valid custom_types.mute.MuteRequestDict, parse and pass the
        request to the experiment.

        Parameters
        ----------
        data : any or custom_types.mute.MuteRequestDict
            Message data, can be anything.  Everything other than
            custom_types.mute.MuteRequestDict will raise an ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `MUTE`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.mute.MuteRequestDict or if this
            Experimenter is not connected to an modules.experiment.Experiment.
        """
        if not is_valid_mute_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid MuteRequest.",
            )

        experiment = self.get_experiment_or_raise("Failed to mute participant.")
        await experiment.mute_participant(
            data["participant_id"], data["mute_video"], data["mute_audio"]
        )

        success = SuccessDict(
            type="MUTE", description="Successfully changed muted state for participant."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_set_filters(self, data: Any) -> MessageDict:
        """Handle requests with type `SET_FILTERS`.

        Check if data is a valid custom_types.filters.SetFiltersRequestDict.

        Parameters
        ----------
        data : any or custom_types.filters.SetFiltersRequestDict
            Message data.  Checks if data is a valid SetFiltersRequestDict and raises
            an ErrorDictException if not.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `ERROR`, data: custom_types.error.ErrorDict and
            ErrorType type: `NOT_IMPLEMENTED`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.filters.SetFiltersRequestDict.
        """
        if not is_valid_set_filters_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid SetFiltersRequest.",
            )

        participant_id = data["participant_id"]
        video_filters = data["video_filters"]
        audio_filters = data["audio_filters"]
        experiment = self.get_experiment_or_raise("Failed to set filters.")
        coros = []

        if participant_id == "all":
            # Update participant data
            for p_data in experiment.session.participants.values():
                p_data.video_filters = video_filters
                p_data.audio_filters = audio_filters

            # Update connected Participants
            for p in experiment.participants.values():
                coros.append(p.connection.set_video_filters(video_filters))
                coros.append(p.connection.set_audio_filters(audio_filters))

        elif participant_id in experiment.session.participants:
            # Update participant data
            p_data = experiment.session.participants[participant_id]
            p_data.video_filters = video_filters
            p_data.audio_filters = audio_filters

            # Update connected Participant
            p = experiment.participants.get(participant_id)
            if p is not None:
                coros.append(p.connection.set_video_filters(video_filters))
                coros.append(p.connection.set_audio_filters(audio_filters))
        else:
            raise ErrorDictException(
                code=404,
                type="UNKNOWN_PARTICIPANT",
                description=f'Unknown participant ID: "{participant_id}".',
            )
        await asyncio.gather(*coros)

        # Notify Experimenters connected to the hub about the data change
        message = MessageDict(type="SESSION_CHANGE", data=experiment.session.asdict())
        await self._hub.send_to_experimenters(message)

        # Respond with success message
        success = SuccessDict(
            type="SET_FILTERS", description="Successfully changed filters."
        )
        return MessageDict(type="SUCCESS", data=success)


async def experimenter_factory(
    offer: RTCSessionDescription, id: str, hub: _h.Hub
) -> tuple[RTCSessionDescription, Experimenter]:
    """Instantiate connection with a new Experimenter based on WebRTC `offer`.

    Instantiate new modules.experimenter.Experimenter, handle offer using
    modules.connection.connection_factory and set connection for the Experimenter.

    This sequence must be donne for all experimenters.  Instantiating an Experimenter
    directly will likely lead to problems, since it wont have a Connection.

    Parameters
    ----------
    offer : aiortc.RTCSessionDescription
        WebRTC offer for building the connection to the client.
    id : str
        Unique identifier for Experimenter.
    hub : modules.hub.Hub
        Hub the Experimenter will be part of.  Used for api calls.

    Returns
    -------
    tuple with aiortc.RTCSessionDescription, modules.experimenter.Experimenter
        WebRTC answer that should be send back to the client and Experimenter
        representing the client.
    """
    experimenter = Experimenter(id, hub)
    filter_api = FilterAPI(experimenter)
    log_name_suffix = f"E-{id}"

    if hub.config.experimenter_multiprocessing:
        answer, connection = await connection_subprocess_factory(
            offer,
            experimenter.handle_message,
            log_name_suffix,
            hub.config,
            [],
            [],
            filter_api,
        )
    else:
        answer, connection = await connection_factory(
            offer, experimenter.handle_message, log_name_suffix, [], [], filter_api
        )

    experimenter.set_connection(connection)
    return (answer, experimenter)
