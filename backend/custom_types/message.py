"""Provide the `MessageDict` TypedDict and valid `MESSAGE_TYPES`.

Use for type hints and static type checking without any overhead during runtime.
"""

from __future__ import annotations
import logging

from typing import Any, Literal, TypeGuard, TypedDict, get_args

import custom_types.util as util

logger = logging.getLogger("Message")


class MessageDict(TypedDict):
    """TypedDict for api messages.  All messages sent should be a MessageDict.

    The `MessageDict` is used to send and receive messages and identify the contents of
    a message via `type`.  The content of a message can be anything, e.g. an ErrorDict,
    Session Data, ...

    Attributes
    ----------
    type : custom_types.message.MESSAGE_TYPES
        Unique message type identifying the contents.
    data : Any
        Content of the message.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#message
    """

    type: MESSAGE_TYPES
    data: Any


MESSAGE_TYPES = Literal[
    "TEST",
    "SUCCESS",
    "ERROR",
    "SESSION_DESCRIPTION",
    "CONNECTION_PROPOSAL",
    "CONNECTION_OFFER",
    "CONNECTION_ANSWER",
    "SAVE_SESSION",
    "SAVED_SESSION",
    "SESSION_CHANGE",
    "DELETE_SESSION",
    "DELETED_SESSION",
    "GET_SESSION_LIST",
    "SESSION_LIST",
    "CHAT",
    "CREATE_EXPERIMENT",
    "JOIN_EXPERIMENT",
    "LEAVE_EXPERIMENT",
    "START_EXPERIMENT",
    "STOP_EXPERIMENT",
    "EXPERIMENT_CREATED",
    "EXPERIMENT_STARTED",
    "EXPERIMENT_ENDED",
    "ADD_NOTE",
    "KICK_PARTICIPANT",
    "BAN_PARTICIPANT",
    "KICK_NOTIFICATION",
    "BAN_NOTIFICATION",
    "MUTE",
    "SET_FILTERS",
]
"""Possible message types for custom_types.message.MessageDict.

See Also
--------
Data Types Wiki :
    https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#message
"""


def is_valid_messagedict(data: Any) -> TypeGuard[MessageDict]:
    """Check if `data` is a valid MessageDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Does not check the contents of MessageDict.data / non recursive.

    Parameters
    ----------
    data : any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid MessageDict.
    """
    # Check if all required and only required or optional keys exist in data
    if not util.check_valid_typeddict_keys(data, MessageDict):
        return False

    known_type = data["type"] in get_args(MESSAGE_TYPES)
    if not known_type:
        logger.debug(f'Unknown message type: {data["type"]}')

    return known_type
