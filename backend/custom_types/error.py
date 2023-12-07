"""Provide the `ErrorDict` TypedDict and valid `ERROR_TYPES`.

Use for type hints and static type checking without any overhead during runtime.
"""

from __future__ import annotations

from typing import TypedDict, Literal


class ErrorDict(TypedDict):
    """TypedDict for error api response.

    When an API call fails, an ErrorDict is send as response, informing the client of
    the error.

    Attributes
    ----------
    code : int
        HTTP response status code.
    type : custom_types.error.ERROR_TYPES
        Unique error type.
    description : str
        Error description.  Intended to be displayed to the enduser.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#error
    """

    code: int
    type: ERROR_TYPES
    description: str


ERROR_TYPES = Literal[
    "NOT_IMPLEMENTED",
    "INTERNAL_SERVER_ERROR",
    "INVALID_REQUEST",
    "INVALID_DATATYPE",
    "UNKNOWN_ID",
    "DUPLICATE_ID",
    "UNKNOWN_SESSION",
    "UNKNOWN_EXPERIMENT",
    "UNKNOWN_PARTICIPANT",
    "UNKNOWN_USER",
    "UNKNOWN_SUBCONNECTION_ID",
    "UNKNOWN_FILTER_ID",
    "UNKNOWN_FILTER_TYPE",
    "BANNED_PARTICIPANT",
    "PARTICIPANT_ALREADY_CONNECTED",
    "EXPERIMENT_ALREADY_STARTED",
    "INVALID_PARAMETER",
    "NOT_CONNECTED_TO_EXPERIMENT",
    "EXPERIMENT_RUNNING",
    "ALREADY_JOINED_EXPERIMENT",
    "FILE_NOT_FOUND",
    "FILE_ALREADY_EXISTS",
    "STILL_PROCESSING",
    "POST_PROCESSING_FAILED",
]
"""Possible error types for custom_types.error.ErrorDict.

See Also
--------
Data Types Wiki :
    https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#error
"""
