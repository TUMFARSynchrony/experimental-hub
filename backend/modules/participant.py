"""Provide the `Participant` class and `participant_factory` factory function.

Notes
-----
Use participant_factory for creating new participants to ensure that they have a valid
modules.connection.Connection.
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any, Coroutine
from aiortc import RTCSessionDescription

from custom_types.participant_summary import ParticipantSummaryDict
from custom_types.chat_message import ChatMessageDict, is_valid_chatmessage
from custom_types.kick import KickNotificationDict
from custom_types.message import MessageDict
from custom_types.success import SuccessDict

from modules.config import Config
import modules.experiment as _exp
from modules.filter_api import FilterAPI
from modules.connection_state import ConnectionState
from modules.exceptions import ErrorDictException
from modules.connection import connection_factory
from modules.connection_subprocess import connection_subprocess_factory
from modules.data import ParticipantData
from modules.user import User


class Participant(User):
    """Participant is a type of modules.user.User with participant rights.

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

    def __init__(
        self,
        id: str,
        experiment: _exp.Experiment,
        participant_data: ParticipantData,
    ) -> None:
        """Instantiate new Participant instance.

        Parameters
        ----------
        id : str
            Unique identifier for Participant.  Must exist in experiment.
        experiment : modules.experiment.Experiment
            Experiment the participant is part of.
        participant_data : modules.data.ParticipantData
            Participant data this participant represents.

        See Also
        --------
        participant_factory : Instantiate connection with a new Participant based on
            WebRTC `offer`.  Use factory instead of instantiating Participant directly.
        """
        super(Participant, self).__init__(
            id, participant_data.muted_video, participant_data.muted_audio
        )
        self._logger = logging.getLogger(f"Participant-{id}")
        self._participant_data = participant_data
        self._experiment = experiment
        experiment.add_participant(self)

        # Add API endpoints
        self.on_message("CHAT", self._handle_chat)

    def __str__(self) -> str:
        """Get string representation of this participant.

        Currently returns value of `__repr__`.
        """
        return (
            f"id={self.id}, first_name={self._participant_data.first_name}, last_name="
            f"{self._participant_data.last_name}, experiment="
            f"{self._experiment.session.id}"
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
            Reason for the kick.  Will be send to the participant in the
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
            Reason for the kick.  Will be send to the participant in the
            `BAN_NOTIFICATION`.
        """
        ban_notification = KickNotificationDict(reason=reason)
        message = MessageDict(type="BAN_NOTIFICATION", data=ban_notification)
        await self.send(message)

        await self.disconnect()

    async def _handle_connection_state_change(self, state: ConnectionState) -> None:
        """Handler for connection "state_change" event.

        Implements the abstract `_handle_connection_state_change` function in
        modules.user.User.

        Parameters
        ----------
        state : modules.connection_state.ConnectionState
            New state of the connection this Participant has with the client.
        """
        self._logger.debug(f"Handle state change. State: {state}")
        if state is ConnectionState.CONNECTED:
            self._logger.info(f"Participant connected. {self}")
            coros: list[Coroutine] = []
            # Add stream to all experimenters
            for e in self._experiment.experimenters:
                coros.append(self.add_subscriber(e))

            # Add stream to all participants and all participants streams to self
            for p in self._experiment.participants.values():
                if p is self:
                    continue
                coros.append(self.add_subscriber(p))
                coros.append(p.add_subscriber(self))

            await asyncio.gather(*coros)

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

        if data["target"] != "experimenter":
            raise ErrorDictException(
                code=403,
                type="INVALID_REQUEST",
                description='Participants can only chat with "experimenter".',
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


async def participant_factory(
    offer: RTCSessionDescription,
    id: str,
    experiment: _exp.Experiment,
    participant_data: ParticipantData,
    config: Config,
) -> tuple[RTCSessionDescription, Participant]:
    """Instantiate connection with a new Participant based on WebRTC `offer`.

    Instantiate new modules.participant.Participant, handle offer using
    modules.connection.connection_factory and set connection for the Participant.

    This sequence must be donne for all participants.  Instantiating an Participant
    directly will likely lead to problems, since it wont have a Connection.

    Parameters
    ----------
    offer : aiortc.RTCSessionDescription
        WebRTC offer for building the connection to the client.
    id : str
        Unique identifier for Participant.  Must exist in experiment.
    experiment : modules.experiment.Experiment
        Experiment the participant is part of.
    config : modules.config.Config
        Hub configuration / Config object.

    Returns
    -------
    tuple with aiortc.RTCSessionDescription, modules.participant.Participant
        WebRTC answer that should be send back to the client and Participant
        representing the client.
    """
    participant = Participant(id, experiment, participant_data)
    filter_api = FilterAPI(participant)
    log_name_suffix = f"P-{id}"

    if config.participant_multiprocessing:
        answer, connection = await connection_subprocess_factory(
            offer,
            participant.handle_message,
            log_name_suffix,
            config,
            participant_data.audio_filters,
            participant_data.video_filters,
            filter_api,
        )
    else:
        answer, connection = await connection_factory(
            offer,
            participant.handle_message,
            log_name_suffix,
            participant_data.audio_filters,
            participant_data.video_filters,
            filter_api,
        )

    participant.set_connection(connection)
    return (answer, participant)
