"""Provide TrackHandler for handing and distributing tracks."""

import asyncio
import logging
import shortuuid
from typing import Literal
from aiortc.mediastreams import (
    MediaStreamTrack,
    MediaStreamError,
    AudioStreamTrack,
    VideoStreamTrack,
)
from av import VideoFrame, AudioFrame
from aiortc.contrib.media import MediaRelay

from custom_types.filters import FilterDict
from modules.exceptions import ErrorDictException
from filters.rotate import RotationFilter
from filters.edge_outline import EdgeOutlineFilter
from filters.filter import Filter
from filters.mute import MuteVideoFilter, MuteAudioFilter


class TrackHandler(MediaStreamTrack):
    """Handles and distributes an incoming audio track to multiple subscribers."""

    kind = Literal["unknown", "audio", "video"]
    muted: bool

    _track: MediaStreamTrack
    _relay: MediaRelay
    _mute_filter: MuteAudioFilter | MuteVideoFilter
    _filters: dict[str, Filter]
    _logger: logging.Logger
    __lock: asyncio.Lock

    def __init__(
        self,
        kind: Literal["audio", "video"],
        track: MediaStreamTrack | None = None,
        muted: bool = False,
    ) -> None:
        """Initialize new TrackHandler for `track`.

        Parameters
        ----------
        kind : str, "audio" or "video"
            Kind of MediaStreamTrack this handler handles.
        track : aiortc.mediastreams.MediaStreamTrack
            Track this handler should manage and distribute.  None if track is set
            later.
        muted : bool, default False
            Whether this track should be muted.

        Raises
        ------
        ValueError
            If kind is not "audio" or "video".
        """
        super().__init__()
        self._logger = logging.getLogger(f"{kind.capitalize()}TrackHandler")
        self.__lock = asyncio.Lock()
        self.kind = kind
        if track is not None:
            self._track = track
        elif kind == "video":
            self._track = VideoStreamTrack()
        elif kind == "audio":
            self._track = AudioStreamTrack()
        else:
            raise ValueError(
                f'Invalid kind: "{kind}". Accepted values: "audio" or "video"'
            )
        self.muted = muted
        self._relay = MediaRelay()
        self._mute_filter = (
            MuteAudioFilter("0", {}) if kind == "audio" else MuteVideoFilter("0", {})
        )
        self._filters = {}

        # Forward the ended event to this handler.
        self._track.add_listener("ended", self.stop)

    @property
    def track(self):
        """Get source track for this TrackHandler.

        Notes
        -----
        Use `subscribe` to add a subscriber to this track.
        """
        return self._track

    async def set_track(self, value: MediaStreamTrack):
        """Set source track for this TrackHandler.

        Parameters
        ----------
        value : MediaStreamTrack
            New source track for this TrackHandler.  `kind` of value must match the kind
            of this TrackHandler.

        Raises
        ------
        ValueError
            If `kind` of value doesn't match the kind of this TrackHandler.
        """
        if value.kind != self.kind:
            raise ValueError(
                f"Source track for TrackHandler must be of kind: {self.kind}"
            )

        async with self.__lock:
            self._track.remove_listener("ended", self.stop)
            self._track = value
            self._track.add_listener("ended", self.stop)

    def subscribe(self) -> MediaStreamTrack:
        """Subscribe to the track managed by this handler.

        Creates a new proxy which relays the track.  This is required to add multiple
        subscribers to one track.

        Returns
        -------
        aiortc.mediastreams.MediaStreamTrack
            Proxy track for the track this TrackHandler manages.

        Notes
        -----
        If this track needs to be used somewhere, always use subscribe to create an
        proxy!  If this TrackHandler is used directly, the framerate will be divided
        between the new consumer and all existing subscribers.
        """
        return self._relay.subscribe(self, False)

    async def set_filters(self, filter_configs: list[FilterDict]) -> None:
        """TODO document"""
        async with self.__lock:
            self._set_filters(filter_configs)

    def _set_filters(self, filter_configs: list[FilterDict]) -> None:
        """TODO document"""
        updated_ids = [f["id"] for f in filter_configs if f["id"] != ""]
        self._logger.debug(f"Updated filters: {updated_ids}")

        # Check for invalid ids.
        for config in filter_configs:
            if config["id"] != "" and config["id"] not in self._filters:
                raise ErrorDictException(
                    code=404, type="UNKNOWN_FILTER_ID", description="Unknown filter ID."
                )

        new_filters: dict[str, Filter] = {}
        for config in filter_configs:
            # If id is not empty, reuse and update existing filter.
            id = config["id"]
            if id != "":
                new_filters[id] = self._filters[id]
                new_filters[id].set_config(config)
                continue

            # Create a new filter for configs with empty id.
            filter = self._create_filter(config)
            new_filters[filter.id] = filter

        self._filters = new_filters

    def _create_filter(self, filter_config: FilterDict) -> Filter:
        """TODO document"""
        id = filter_config["id"] if filter_config["id"] != "" else shortuuid.uuid()
        type = filter_config["type"]

        match type:
            case "Rotation":
                return RotationFilter(id, filter_config)
            case "EdgeOutline":
                return EdgeOutlineFilter(id, filter_config)
            case _:
                raise ErrorDictException(
                    code=404,
                    type="UNKNOWN_FILTER_TYPE",
                    description=f'Unknown filter type "{type}".',
                )

    async def recv(self) -> AudioFrame | VideoFrame:
        """Receive the next av.AudioFrame from this track.

        Checks if this track is muted and returns silence if so.

        Returns
        -------
        av.AudioFrame or av.VideoFrame
            Next frame from the track this TrackHandler manages.  Return type depends
            on `kind` of this TrackHandler.

        Raises
        ------
        MediaStreamError
            If `self.readyState` is not "live"
        """
        if self.readyState != "live":
            raise MediaStreamError

        frame = await self.track.recv()

        for filter in self._filters.values():
            frame = await filter.process(frame)

        if self.muted:
            muted_frame = await self._mute_filter.process(frame)
            return muted_frame

        return frame