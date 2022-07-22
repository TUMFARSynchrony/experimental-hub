"""Provide the `Connection` and `SubConnection` classes."""

from __future__ import annotations
from typing import Any, Callable, Coroutine, Tuple
from aiortc import (
    RTCPeerConnection,
    RTCDataChannel,
    RTCSessionDescription,
    MediaStreamTrack,
    RTCRtpSender,
)
from pyee.asyncio import AsyncIOEventEmitter
import shortuuid
import asyncio
import logging
import json

from modules.track_handler import TrackHandler
from modules.exceptions import ErrorDictException
from modules.connection_interface import ConnectionInterface
from modules.connection_state import ConnectionState, parse_connection_state

from custom_types.error import ErrorDict
from custom_types.filters import FilterDict
from modules.filter_api_interface import FilterAPIInterface
from custom_types.message import MessageDict, is_valid_messagedict
from custom_types.participant_summary import ParticipantSummaryDict
from custom_types.connection import (
    RTCSessionDescriptionDict,
    ConnectionProposalDict,
    ConnectionOfferDict,
    ConnectionAnswerDict,
)


class Connection(ConnectionInterface):
    """Connection with a single client using multiple sub-connections.

    Implements modules.connection_interface.ConnectionInterface.

    Extends AsyncIOEventEmitter, providing the following events:
    - `state_change` : modules.connection_state.ConnectionState
        Emitted when the state of this connection changes.

    Notes
    -----
    The sequence should be something like this:

    Receive offer -> create Connection (adds event listeners for tracks, datachannel
    etc.) -> set remote description -> create answer -> set local description -> send
    answer to peer.

    This is not intended as a guide to aiortc / WebRTC, just as a reference when to
    create the Connection instance.

    See Also
    --------
    connection_factory : use to create new Connection and answer for an WebRTC offer.
    """

    _log_name_suffix: str
    _stopped: bool
    _state: ConnectionState
    _main_pc: RTCPeerConnection
    _dc: RTCDataChannel | None
    _message_handler: Callable[[MessageDict], Coroutine[Any, Any, None]]
    _incoming_audio: TrackHandler
    _incoming_video: TrackHandler
    _sub_connections: dict[str, SubConnection]
    _tasks: list[asyncio.Task]

    def __init__(
        self,
        pc: RTCPeerConnection,
        message_handler: Callable[[MessageDict], Coroutine[Any, Any, None]],
        log_name_suffix: str,
        filter_api: FilterAPIInterface,
    ) -> None:
        """Create new Connection based on a aiortc.RTCPeerConnection.

        Add event listeners to `pc`.  Should be donne before the remote description of
        `pc` is set.

        Parameters
        ----------
        pc : aiortc.RTCPeerConnection
            WebRTC peer connection.
        message_handler : function (custom_typed.message.MessageDict) -> None
            Handler for incoming messages over the datachannel.  Incoming messages will
            be parsed and type checked (only top level, not including contents of data).
        log_name_suffix : str
            Suffix for logger.  Format: Connection-<log_name_suffix>.

        See Also
        --------
        connection_factory : use to create new Connection and answer for an WebRTC
            offer.

        Notes
        -----
        Make sure to call `complete_setup` after initialization.
        """
        super().__init__()
        self._logger = logging.getLogger(f"Connection-{log_name_suffix}")
        self._stopped = False
        self._log_name_suffix = log_name_suffix
        self._sub_connections = {}
        self._state = ConnectionState.NEW
        self._main_pc = pc
        self._message_handler = message_handler
        self._incoming_audio = TrackHandler("audio", self, filter_api)
        self._incoming_video = TrackHandler("video", self, filter_api)

        self._dc = None
        self._tasks = []

        # Register event handlers
        pc.add_listener("datachannel", self._on_datachannel)
        pc.add_listener("connectionstatechange", self._on_connection_state_change)
        pc.add_listener("track", self._on_track)

    async def complete_setup(
        self, audio_filters: list[FilterDict], video_filters: list[FilterDict]
    ) -> None:
        """Complete Connection setup.

        Parameters
        ----------
        audio_filters : list of custom_types.filter.FilterDict
            Default audio filters for this connection.
        video_filters : list of custom_types.filter.FilterDict
            Default video filters for this connection.
        """
        await asyncio.gather(
            self._incoming_audio.complete_setup(audio_filters),
            self._incoming_video.complete_setup(video_filters),
        )

    @property
    def incoming_audio(self) -> TrackHandler:
        """Get modules.track_handler.TrackHandler for incoming audio track."""
        return self._incoming_audio

    @property
    def incoming_video(self) -> TrackHandler:
        """Get modules.track_handler.TrackHandler for incoming video track."""
        return self._incoming_video

    def __str__(self) -> str:
        """Get string representation of this Connection."""
        return f"state={self._state}"

    def __repr__(self) -> str:
        """Get representation of this Connection obj."""
        return (
            f"Connection({str(self)}, logger_name=Connection-{self._log_name_suffix})"
        )

    async def stop(self) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        if self._stopped:
            return
        self._stopped = True
        self._logger.debug("Stopping Connection")

        if self._state not in [ConnectionState.CLOSED, ConnectionState.FAILED]:
            self._set_state(ConnectionState.CLOSED)

        # Close all SubConnections
        coros: list[Coroutine] = []
        for sc in self._sub_connections.values():
            coros.append(sc.stop())
        await asyncio.gather(*coros, *self._tasks)

        # Close main connection
        if self._dc is not None:
            self._dc.close()
        if self._incoming_video is not None:
            await self._incoming_video.stop()
        if self._incoming_audio is not None:
            await self._incoming_audio.stop()
        await self._main_pc.close()
        self.remove_all_listeners()

    async def send(self, data: MessageDict | dict) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        if self._dc is None or self._dc.readyState != "open":
            self._logger.warning("Can not send data because datachannel is not open")
            await self._set_failed_state_and_close()
            return
        stringified = json.dumps(data)
        self._logger.debug(f"Sending data: {stringified}")
        self._dc.send(stringified)

    @property
    def state(self) -> ConnectionState:
        # For docstring see ConnectionInterface or hover over function declaration
        return self._state

    async def create_subscriber_proposal(
        self, participant_summary: ParticipantSummaryDict | str | None
    ) -> ConnectionProposalDict:
        # For docstring see ConnectionInterface or hover over function declaration

        subconnection_id = shortuuid.uuid()
        sc = SubConnection(
            subconnection_id,
            self._incoming_video.subscribe(),
            self._incoming_audio.subscribe(),
            participant_summary,
            self._log_name_suffix,
        )
        sc.add_listener("connection_closed", self._handle_closed_subconnection)
        self._sub_connections[subconnection_id] = sc
        return sc.proposal

    async def handle_subscriber_offer(
        self, offer: ConnectionOfferDict
    ) -> ConnectionAnswerDict:
        # For docstring see ConnectionInterface or hover over function declaration
        subconnection_id = offer["id"]
        sc = self._sub_connections.get(subconnection_id)
        if sc is None:
            self._logger.error(f"SubConnection for ID: {subconnection_id} not found.")
            raise ErrorDictException(
                code=0,
                type="UNKNOWN_SUBCONNECTION_ID",
                description=f"Unknown offer ID {subconnection_id}",
            )

        offer_description = RTCSessionDescription(
            offer["offer"]["sdp"], offer["offer"]["type"]
        )
        return await sc.handle_offer(offer_description)

    async def stop_subconnection(self, subconnection_id: str) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        if subconnection_id not in self._sub_connections:
            self._logger.error(
                "Failed to remove subconnection, unknown subconnection_id: "
                f"{subconnection_id}"
            )
            return

        sub_connection = self._sub_connections[subconnection_id]
        await sub_connection.stop()
        return

    async def set_muted(self, video: bool, audio: bool) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        if self._incoming_video is not None:
            self._incoming_video.muted = video
        if self._incoming_audio is not None:
            self._incoming_audio.muted = audio

    async def set_video_filters(self, filters: list[FilterDict]) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        await self._incoming_video.set_filters(filters)

    async def set_audio_filters(self, filters: list[FilterDict]) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        await self._incoming_audio.set_filters(filters)

    async def _handle_closed_subconnection(self, subconnection_id: str) -> None:
        """Remove a closed SubConnection from Connection."""
        self._logger.debug(f"Remove sub connection {subconnection_id}")
        self._sub_connections.pop(subconnection_id)
        self._logger.debug(f"SubConnections after removing: {self._sub_connections}")

    def _on_datachannel(self, channel: RTCDataChannel) -> None:
        """Handle new incoming datachannel.

        Parameters
        ----------
        channel : aiortc.RTCDataChannel
            Incoming data channel.
        """
        self._logger.debug("Received datachannel")
        self._dc = channel
        self._dc.on("message", self._parse_and_handle_message)
        self._dc.on("close", self._handle_datachannel_close)
        self._set_state(ConnectionState.CONNECTED)

    async def _handle_datachannel_close(self) -> None:
        """Handle the `close` event on datachannel."""
        self._logger.debug("Datachannel closed")
        await self._check_if_closed()

    async def _check_if_closed(self) -> None:
        """Check if this Connection is closed and should stop."""
        if (
            self._incoming_audio is not None
            and self._incoming_video is not None
            and self._incoming_audio.readyState == "ended"
            and self._incoming_video.readyState == "ended"
        ):
            self._logger.debug("All incoming tracks are closed -> stop connection")
            await self.stop()

        if self._dc is not None and self._dc.readyState == "closed":
            self._logger.debug("Datachannel closed -> stop connection")
            await self.stop()

    async def _parse_and_handle_message(self, message: Any) -> None:
        """Parse, check and forward incoming datachannel message.

        Checks if message is a valid string containing a
        custom_types.message.MessageDict JSON object.  If contents are invalid, a error
        response is send.

        Parameters
        ----------
        message : Any
            Incoming data channel message.  Ignored if type is not str.
        """
        if not isinstance(message, str):
            return

        try:
            message_dict = json.loads(message)
        except Exception as err:
            self._logger.warning(f"Failed to parse message. Error: {err}")
            # Send error response in following if statement.
            message_dict = None

        # Handle invalid message type
        if not is_valid_messagedict(message_dict):
            self._logger.info(f"Received invalid message.")
            self._logger.debug(f"Invalid message: {message}")
            err = ErrorDict(
                type="INVALID_REQUEST",
                code=400,
                description="Received message is not a valid Message object.",
            )
            response = MessageDict(type="ERROR", data=err)
            await self.send(response)
            return

        # Pass message to message handler in user.
        await self._message_handler(message_dict)

    def _on_connection_state_change(self):
        """Handle connection state change for `_main_pc`."""
        self._logger.debug(
            f"Peer Connection state change: {self._main_pc.connectionState}"
        )
        state = parse_connection_state(self._main_pc.connectionState)
        if state == ConnectionState.CONNECTED and self._dc is None:
            # Connection is established, but dc is not yet open.
            self._logger.debug("Established connection, waiting for datachannel")
            return
        self._set_state(state)

    def _set_state(self, state: ConnectionState):
        """Set connection state and emit `state_change` event."""
        if self._state == state:
            return

        self._logger.debug(f"Connection state is: {state}")
        self._state = state
        self.emit("state_change", state)

    async def _set_failed_state_and_close(self) -> None:
        """Sets the state to `FAILED` and closes the Connection."""
        self._set_state(ConnectionState.FAILED)
        await self.stop()

    def _on_track(self, track: MediaStreamTrack):
        """Synchronous wrapper for `_async_on_track`.

        Creates a new task for to execute `_async_on_track`.

        Parameters
        ----------
        track : aiortc.MediaStreamTrack
            Incoming track.

        Note
        ----
        This function can not be asynchronous, otherwise it will no longer function
        correctly.  See: https://github.com/aiortc/aiortc/issues/578.
        """
        self._logger.debug(f"{track.kind} track received")
        if track.kind == "audio":
            task = asyncio.create_task(self._incoming_audio.set_track(track))
            sender = self._main_pc.addTrack(self._incoming_audio.subscribe())
            self._listen_to_track_close(self._incoming_audio, sender)
        elif track.kind == "video":
            task = asyncio.create_task(self._incoming_video.set_track(track))
            sender = self._main_pc.addTrack(self._incoming_video.subscribe())
            self._listen_to_track_close(self._incoming_video, sender)
        else:
            self._logger.error(f"Unknown track kind {track.kind}. Ignoring track")
            return

        self._tasks.append(task)

        @track.on("ended")
        def _on_ended():
            """Handles tracks ended event."""
            self._logger.debug(f"{track.kind} track ended")

    def _listen_to_track_close(self, track: TrackHandler, sender: RTCRtpSender):
        """Add a handler to the `ended` event on `track` that closes its transceiver.

        Parameters
        ----------
        track : modules.track_handler.TrackHandler
            Track to listen to the `ended` event.
        sender : aiortc.RTCRtpSender
            Sender of the track.  Used to find the correct transceiver.
        """

        @track.on("ended")
        async def _close_transceiver():
            """Find and close the correct transceiver for `sender`."""
            for transceiver in self._main_pc.getTransceivers():
                if transceiver.sender is sender:
                    self._logger.debug("Found transceiver, closing")
                    await transceiver.stop()
                    break
            await self._check_if_closed()


ConnectionInterface.register(Connection)


class SubConnection(AsyncIOEventEmitter):
    """SubConnection used to send additional stream to a client.

    Each SubConnection has a audio and video track -> one stream which they send to the
    client.  For communication it used the datachannel of the parent
    module.connection.Connection.

    Extends AsyncIOEventEmitter, providing the following events:
    - `connection_closed` : str
        Emitted when this SubConnection closes.  Data is the ID of this SubConnection.
    """

    id: str
    _participant_summary: ParticipantSummaryDict | str | None
    _pc: RTCPeerConnection

    _audio_track: MediaStreamTrack
    _video_track: MediaStreamTrack

    _closed: bool
    _logger: logging.Logger

    def __init__(
        self,
        id: str,
        video_track: MediaStreamTrack,
        audio_track: MediaStreamTrack,
        participant_summary: ParticipantSummaryDict | str | None,
        log_name_suffix: str,
    ) -> None:
        """Initialize new SubConnection.

        Parameters
        ----------
        id : str
        video_track : aiortc.MediaStreamTrack
            Video track that will be send in this SubConnection.
        audio_track : aiortc.MediaStreamTrack
            Audio track that will be send in this SubConnection.
        participant_summary : None or custom_types.participant_summary.ParticipantSummaryDict
            Participant summary or ID send to the client with the initial offer.
        """
        super().__init__()
        self._logger = logging.getLogger(f"SubConnection-{log_name_suffix}")
        self.id = id
        self._audio_track = audio_track
        self._video_track = video_track
        self._closed = False
        self._participant_summary = participant_summary

        self._pc = RTCPeerConnection()
        self._pc.addTrack(video_track)
        self._pc.addTrack(audio_track)
        self._pc.on("connectionstatechange", self._on_connection_state_change)

        # Stop SubConnection if one of the tracks ends
        # audio_track.on("ended", self.stop)
        # video_track.on("ended", self.stop)

    @property
    def proposal(self):
        """Get a custom_types.connection.ConnectionProposalDict for this SubConnection.

        See Also
        --------
        Connection Protocol Wiki :
            https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol
        """
        return ConnectionProposalDict(
            id=self.id, participant_summary=self._participant_summary
        )

    async def stop(self) -> None:
        """Stop the SubConnection and its associated tracks.

        Emits a `connection_closed` event with the ID of this SubConnection.  When
        finished, it removes all event listeners from this Connection, as no more events
        will be emitted.
        """
        if self._closed:
            return
        self.emit("connection_closed", self.id)

        self._audio_track.stop()
        self._video_track.stop()

        self._logger.debug("Closing SubConnection")
        self._closed = True
        await self._pc.close()
        self.remove_all_listeners()

    async def handle_offer(self, offer: RTCSessionDescription) -> ConnectionAnswerDict:
        """Handle a `CONNECTION_OFFER` message for this SubConnection.

        Parameters
        ----------
        offer : aiortc.RTCSessionDescription

        Returns
        -------
        custom_types.connection.ConnectionAnswerDict
            Answer that should be send as a response to the offer.

        See Also
        --------
        Connection Protocol Wiki :
            https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol
        """
        await self._pc.setRemoteDescription(offer)

        answer = await self._pc.createAnswer()
        await self._pc.setLocalDescription(answer)  # type: ignore

        answer_dict = RTCSessionDescriptionDict(
            sdp=self._pc.localDescription.sdp, type=self._pc.localDescription.type  # type: ignore
        )
        return ConnectionAnswerDict(id=self.id, answer=answer_dict)

    async def _on_connection_state_change(self):
        """Handle connection state change."""
        self._logger.debug(f"Peer Connection state change: {self._pc.connectionState}")
        if self._pc.connectionState in ["closed", "failed"]:
            await self.stop()


async def connection_factory(
    offer: RTCSessionDescription,
    message_handler: Callable[[MessageDict], Coroutine[Any, Any, None]],
    log_name_suffix: str,
    audio_filters: list[FilterDict],
    video_filters: list[FilterDict],
    filter_api: FilterAPIInterface,
) -> Tuple[RTCSessionDescription, Connection]:
    """Instantiate Connection.

    Parameters
    ----------
    offer : aiortc.RTCSessionDescription
        WebRTC offer for building the connection to the client.
    message_handler : function (message: custom_types.message.MessageDict) -> None
        Message handler for Connection.  Connection will pass parsed MessageDicts to
        this handler.
    log_name_suffix : str
        Suffix for logger used in Connection.  Format: Connection-<log_name_suffix>.
    audio_filters : list of custom_types.filter.FilterDict
        Default audio filters for this connection.
    video_filters : list of custom_types.filter.FilterDict
        Default video filters for this connection.

    Returns
    -------
    tuple with aiortc.RTCSessionDescription, modules.connection.Connection
        WebRTC answer that should be send back to the client and a Connection.
    """
    pc = RTCPeerConnection()
    connection = Connection(pc, message_handler, log_name_suffix, filter_api)
    await connection.complete_setup(audio_filters, video_filters)

    # handle offer
    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)  # type: ignore

    return (pc.localDescription, connection)
