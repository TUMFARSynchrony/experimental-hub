"""Provide the `SuccessDict` TypedDict.

Use for type hints and static type checking without any overhead during runtime.
"""

from __future__ import annotations

from typing import TypedDict, Literal


class SuccessDict(TypedDict):
    """Response TypedDict to successfull api calls.

    Attributes
    ----------
    type : custom_types.success.SUCCESS_TYPES
        Unique success type, defining what accion was successfully executed.
    description : str
        Description of what action (api call) was successfully executed.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#success
    """

    type: SUCCESS_TYPES
    description: str


SUCCESS_TYPES = Literal[
    "SAVE_SESSION",
    "DELETE_SESSION",
    "JOIN_EXPERIMENT",
    "LEAVE_EXPERIMENT",
    "START_EXPERIMENT",
    "STOP_EXPERIMENT",
    "ADD_NOTE",
    "CHAT",
    "KICK_PARTICIPANT",
    "BAN_PARTICIPANT",
    "MUTE",
    "SET_FILTERS",
    "POST_PROCESSING_VIDEO",
    "SET_GROUP_FILTERS",
]
"""Possible success types for custom_types.success.SuccessDict.

See Also
--------
Data Types Wiki :
    https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#message
"""
