"""Provide the `ChatMessageDict` TypedDict`.

Use for type hints and static type checking without any overhead during runtime.
"""

from typing import Any, TypeGuard, TypedDict

import custom_types.util as util


class ChatMessageDict(TypedDict):
    """TypedDict for sending chat messages between client and server.

    Attributes
    ----------
    message : str
        Message contents.
    time : int
        Time the message was send in milliseconds since January 1, 1970, 00:00:00 (UTC).
    author : str
        Author of the message. Participant ID or "experimenter".
    target : str
        Intended receiver of the message. Participant ID or "experimenter".
        For participant: always "experimenter".
        For experimenter: specific participant ID or "participants" for sending message
        to all participants.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#chatmessage
    """

    message: str
    time: int
    author: str
    target: str


def is_valid_chatmessage(data: Any) -> TypeGuard[ChatMessageDict]:
    """Check if `data` is a valid ChatMessageDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid ChatMessageDict.
    """
    return (
        util.check_valid_typeddict_keys(data, ChatMessageDict)
        and isinstance(data["message"], str)
        and isinstance(data["time"], int)
        and isinstance(data["author"], str)
        and isinstance(data["target"], str)
    )
