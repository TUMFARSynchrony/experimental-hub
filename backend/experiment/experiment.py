"""Provide the `Experiment` class."""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING
from pyee.asyncio import AsyncIOEventEmitter

from custom_types.message import MessageDict
from custom_types.chat_message import ChatMessageDict

from hub.util import timestamp
from experiment.experiment_state import ExperimentState
from hub.exceptions import ErrorDictException
from session.data.session import SessionData

from group_filters.group_filter_aggregator import GroupFilterAggregator
from filters.filter_dict import FilterDict
from group_filters import group_filter_aggregator_factory
import asyncio

if TYPE_CHECKING:
    from users import Experimenter, Participant


class Experiment(AsyncIOEventEmitter):
    """Experiment representing a running session.

    Extends AsyncIOEventEmitter, providing the following events:
    - `state` : hub.experiment_state.ExperimentState
        Emitted when the connection state changes.
    """

    _logger: logging.Logger
    _state: ExperimentState
    session: SessionData
    _experimenters: list[Experimenter]
    _participants: dict[str, Participant]
    _audio_group_filter_aggregators: dict[str, GroupFilterAggregator]
    _video_group_filter_aggregators: dict[str, GroupFilterAggregator]

    def __init__(self, session: SessionData):
        """Start a new Experiment.

        Parameters
        ----------
        session : session.data.session.SessionData
            SessionData this experiment is based on. Will modify the session during
            execution.
        """
        super().__init__()
        self._logger = logging.getLogger(f"Experiment-{session.id}")
        self._state = ExperimentState.WAITING
        self.session = session
        self._experimenters = []
        self._participants = {}
        self._logger.info(f"Experiment created: {self}")
        self.session.creation_time = timestamp()
        self._audio_group_filter_aggregators = {}
        self._video_group_filter_aggregators = {}

    def __str__(self) -> str:
        """Get string representation of this Experiment."""
        return f"session={self.session.id}, title={self.session.title}"

    def __repr__(self) -> str:
        """Get representation of this Experiment obj."""
        return f"Experiment({str(self)})"

    @property
    def state(self) -> ExperimentState:
        """State the experiment is in."""
        return self._state

    @property
    def participants(self):
        """Participants currently connected to the Experiment."""
        return self._participants

    @property
    def experimenters(self):
        """Experimenters currently connected to the Experiment."""
        return self._experimenters

    async def start(self):
        """Start the experiment.

        If state is `WAITING`, save the current time in `session.start_time` and set
        state to `RUNNING`.  If state is not `WAITING`, an ErrorDictException is raised.

        Also send a `EXPERIMENT_STARTED` message to all users connected to the
        experiment, if experiment was successfully started.

        Raises
        ------
        ErrorDictException
            If experiment state is not `WAITING`.
        """
        if self._state != ExperimentState.WAITING:
            raise ErrorDictException(
                code=409,
                type="INVALID_REQUEST",
                description="Experiment cant be started, state is not WAITING.",
            )

        self._set_state(ExperimentState.RUNNING)
        time = timestamp()
        self._logger.info(f"Experiment started. Start time: {time}")
        self.session.start_time = time

        # Notify all users
        end_message = MessageDict(type="EXPERIMENT_STARTED", data={"start_time": time})
        await self.send("all", end_message, secure_origin=True)

    async def stop(self):
        """Stop the experiment.

        If state is not already `ENDED`, save the current time in `session.end_time`
        and in `session.start_time`, if not already set, and set state to `ENDED`.

        Raises
        ------
        ErrorDictException
            If experiment state is already `ENDED`.
        """
        if self._state is ExperimentState.ENDED:
            raise ErrorDictException(
                code=409,
                type="INVALID_REQUEST",
                description="Experiment is already stopped.",
            )

        self._set_state(ExperimentState.ENDED)
        time = timestamp()
        self._logger.info(f"Experiment ended. End time: {time}")
        self.session.end_time = time
        if self.session.start_time == 0:
            self.session.start_time = time

        # Notify all users
        end_message = MessageDict(
            type="EXPERIMENT_ENDED",
            data={"end_time": time, "start_time": self.session.start_time},
        )
        await self.send("all", end_message, secure_origin=True)

    async def send(
        self, to: str, data: Any, exclude: str = "", secure_origin: bool = False
    ):
        """Send data to a single or group of users.

        Select the correct target (group) according to the `to` parameter and send the
        given `data` to all targets.

        Parameters
        ----------
        to : str
            Target for the data. Can be a participant ID or one of the following groups:
            - `"all"` send data to all participants and experimenters. `secure_origin`
              must be true for this group to avoid the use of all from a untrusted
              client (only allowed internally).
            - `"participants"` send data to all participants.
            - `"experimenter"` send data to all experimenters.

        data : Any
            Data that will be sent.
        exclude : str, optional
            User ID to exclude from targets, e.g. ID from sender of `data`.
        secure_origin : bool, default False
            If True, `to` = "all" is allowed.  Used to disallow clients using "all".

        Notes
        -----
        broadcast is a separate variable to avoid misbehaving clients sending data to
        everyone.

        Raises
        ------
        ErrorDictException
            If `to` is not "all", "participants", "experimenter" or a known participant
            ID.  Also raised if `to` is set to "all", but `secure_origin` is false.
        """
        # Select target
        targets: list[Experimenter | Participant] = []
        match to:
            case "all":
                if not secure_origin:
                    raise ErrorDictException(
                        400,
                        "INVALID_REQUEST",
                        'Message target "all" is not allowed.',
                    )
                targets.extend(self._participants.values())
                targets.extend(self._experimenters)
            case "participants":
                targets.extend(self._participants.values())
            case "experimenter":
                targets.extend(self._experimenters)
            case _:
                if to in self._participants:
                    targets.append(self._participants[to])
                else:
                    raise ErrorDictException(
                        404,
                        "UNKNOWN_USER",
                        f"Failed to send data to {to}, user not found.",
                    )

        # Send data
        for user in targets:
            if exclude != user.id:
                await user.send(data)

    async def handle_chat_message(self, chat_message: ChatMessageDict):
        """Log and send a chat message to `target` in `chat_message`.

        Parameters
        ----------
        chat_message : custom_types.chat_message.ChatMessageDict
            Chat message that will be send.

        Raises
        ------
        ErrorDictException
            If `target` in `chat_message` is not "participants", "experimenter" or a
            known participant ID.
        """
        # Save message in log of the correct participant(s)
        target = chat_message["target"]
        author = chat_message["author"]
        if target in "participants":
            for p in self.session.participants.values():
                p.chat.append(chat_message)
        else:
            # In this case target or author is assumed to be a single participant
            if target == "experimenter":
                participant = self.session.participants.get(author)
            else:
                participant = self.session.participants.get(target)

            if participant is None:
                raise ErrorDictException(
                    code=404,
                    type="UNKNOWN_USER",
                    description="No participant found for the given ID.",
                )
            participant.chat.append(chat_message)

        # Send message
        msg_dict = MessageDict(type="CHAT", data=chat_message)
        await self.send(chat_message["target"], msg_dict)

    def add_participant(self, participant: Participant):
        """Add participant to experiment.

        Parameters
        ----------
        participant : hub.participant.Participant
            Participant joining the experiment.
        """
        self._participants[participant.id] = participant
        self._logger.debug(
            f"{repr(participant)} joined Experiment. "
            f"Participants connected to experiment: {list(self._participants.values())}"
        )
        participant.add_listener("disconnected", self.remove_participant)

    def remove_participant(self, participant: Participant):
        """Remove a participant from this experiment.

        Parameters
        ----------
        participant : hub.participant.Participant
            Participant leaving the experiment.
        """
        self._participants.pop(participant.id)
        self._logger.debug(
            f"{repr(participant)} left Experiment. "
            f"Participants connected to experiment: {list(self._participants.values())}"
        )

    async def kick_participant(self, participant_id: str, reason: str):
        """Kick a participant from this experiment.

        Notify the participant before disconnecting the connection.

        Parameters
        ----------
        participant_id : str
            ID of the participant that should be kicked.
        reason : str
            Reason for kicking the participant.

        Raises
        ------
        ErrorDictException
            If the `participant_id` is not known.
        """
        participant = self._participants.get(participant_id)
        if participant is None:
            raise ErrorDictException(
                code=404,
                type="UNKNOWN_PARTICIPANT",
                description=(
                    "Failed to kick Participant. Participant with the given ID not "
                    "found."
                ),
            )

        self._logger.debug(f"Kick participant {participant_id}, reason: {reason}")
        await participant.kick(reason)

    async def ban_participant(self, participant_id: str, reason: str):
        """Ban a participant from this experiment.

        Notify the participant before disconnecting the connection.

        Parameters
        ----------
        participant_id : str
            ID of the participant that should be banned.
        reason : str
            Reason for banning the participant.

        Raises
        ------
        ErrorDictException
            If `participant_id` is not known.
        """

        # Save ban in session data
        participant_data = self.session.participants.get(participant_id)
        if participant_data is None:
            raise ErrorDictException(
                code=404,
                type="UNKNOWN_PARTICIPANT",
                description=(
                    "Failed to ban Participant. Participant with the given ID not "
                    "found."
                ),
            )

        self._logger.debug(f"Ban participant {participant_id}, reason: {reason}")

        # Ban Participant, if connected.
        if participant_id in self._participants:
            participant = self._participants[participant_id]
            await participant.ban(reason)

        # Save banned state in session / participant data
        participant_data.banned = True

    async def mute_participant(self, participant_id: str, video: bool, audio: bool):
        """Set the muted state for the participant with `participant_id`.

        Parameters
        ----------
        participant_id : str
            ID of the target participant.
        video : bool
            Whether the participants video should be muted.
        audio : bool
            Whether the participants audio should be muted.
        """
        # Save muted state in session data
        participant_data = self.session.participants.get(participant_id)
        if participant_data is None:
            raise ErrorDictException(
                code=404,
                type="UNKNOWN_PARTICIPANT",
                description=(
                    "Failed to mute participant, requested participantId is not part "
                    "of this experiment."
                ),
            )
        participant_data.muted_audio = audio
        participant_data.muted_video = video

        # Mute participant if participant is already connected
        if participant_id in self._participants:
            await self._participants[participant_id].set_muted(video, audio)

    def add_experimenter(self, experimenter: Experimenter):
        """Add experimenter to experiment.

        Parameters
        ----------
        experimenter : hub.experimenter.Experimenter
            Experimenter joining the experiment.
        """
        self._experimenters.append(experimenter)
        self._logger.info(f"Experimenter ({str(experimenter)}) joined Experiment")
        self._logger.debug(
            f"Experimenters connected to experiment: {self._experimenters}"
        )
        experimenter.add_listener("disconnected", self.remove_experimenter)

    def remove_experimenter(self, experimenter: Experimenter):
        """Remove an experimenter from this experiment.

        Parameters
        ----------
        experimenter : hub.experimenter.Experimenter
            Experimenter leaving the experiment.

        Raises
        ------
        ValueError
            If the given `experimenter` is not part of this experiment.
        """
        self._experimenters.remove(experimenter)
        experimenter.remove_listener("disconnected", self.remove_experimenter)

        self._logger.info(f"Experimenter ({str(experimenter)}) left Experiment")
        self._logger.debug(
            f"Experimenters connected to experiment: {self._experimenters}"
        )

    def _set_state(self, state: ExperimentState) -> None:
        """Change state and emit `state` event.

        Aborts if current state is equal to the new state.

        Parameters
        ----------
        state : hub.experiment_state.ExperimentState
            New experiment state.
        """
        if self._state == state:
            return

        self._state = state
        self.emit("state", self._state)

    async def set_video_group_filter_aggregators(
        self, group_filter_configs: list[FilterDict], ports: list[tuple[int, int]]
    ) -> None:
        old_group_filter_aggregators = self._video_group_filter_aggregators

        self._video_group_filter_aggregators = {}
        coroutines = []
        for config, port_tuple in zip(group_filter_configs, ports):
            filter_id = config["id"]
            # Reuse existing filter for matching id and name.
            if (
                filter_id in old_group_filter_aggregators
                and old_group_filter_aggregators[filter_id]._group_filter.name()
                == config["name"]
            ):
                self._video_group_filter_aggregators[
                    filter_id
                ] = old_group_filter_aggregators[filter_id]

                self._video_group_filter_aggregators[filter_id].delete_data()
            else:
                # Create a new filter for configs with empty id.
                self._video_group_filter_aggregators[filter_id] = (
                    group_filter_aggregator_factory.create_group_filter_aggregator(
                        "video", config, port_tuple
                    )
                )

        # Cleanup old group filter aggregators
        for (
            filter_id,
            old_group_filter_aggregator,
        ) in old_group_filter_aggregators.items():
            if filter_id not in self._video_group_filter_aggregators:
                coroutines.append(old_group_filter_aggregator.cleanup())

        # Run new group filter aggregators
        for (
            new_group_filter_aggregator
        ) in self._video_group_filter_aggregators.values():
            task = asyncio.create_task(new_group_filter_aggregator.run())
            new_group_filter_aggregator.set_task(task)
            coroutines.append(task)

        await asyncio.gather(*coroutines)

    async def set_audio_group_filter_aggregators(
        self, group_filter_configs: list[FilterDict], ports: list[tuple[int, int]]
    ) -> None:
        old_group_filter_aggregators = self._audio_group_filter_aggregators

        self._audio_group_filter_aggregators = {}
        coroutines = []
        for config, port_tuple in zip(group_filter_configs, ports):
            filter_id = config["id"]
            # Reuse existing filter for matching id and name.
            if (
                filter_id in old_group_filter_aggregators
                and old_group_filter_aggregators[filter_id]._group_filter.name()
                == config["name"]
            ):
                self._audio_group_filter_aggregators[
                    filter_id
                ] = old_group_filter_aggregators[filter_id]

                self._audio_group_filter_aggregators[filter_id].delete_data()
            else:
                # Create a new filter for configs with empty id.
                self._audio_group_filter_aggregators[filter_id] = (
                    group_filter_aggregator_factory.create_group_filter_aggregator(
                        "audio", config, port_tuple
                    )
                )

        # Cleanup old group filter aggregators
        for (
            filter_id,
            old_group_filter_aggregator,
        ) in old_group_filter_aggregators.items():
            if filter_id not in self._audio_group_filter_aggregators:
                coroutines.append(old_group_filter_aggregator.cleanup())

        # Run new group filter aggregators
        for (
            new_group_filter_aggregator
        ) in self._audio_group_filter_aggregators.values():
            task = asyncio.create_task(new_group_filter_aggregator.run())
            new_group_filter_aggregator.set_task(task)
            coroutines.append(task)

        await asyncio.gather(*coroutines)
