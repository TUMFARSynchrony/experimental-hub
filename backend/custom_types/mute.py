"""Provide the `MuteRequestDict` TypedDict and is_valid_mute_request function.

Use for type hints and static type checking without any overhead during runtime.
"""

from typing import TypeGuard, TypedDict

import custom_types.util as util


class MuteRequestDict(TypedDict):
    """TypedDict for the MUTE request.

    Attributes
    ----------
    participant_id : str
        Participant ID for the requested endpoint.
    mute_video : bool
    mute_audio : bool
    """

    participant_id: str
    mute_video: bool
    mute_audio: bool


def is_valid_mute_request(data) -> TypeGuard[MuteRequestDict]:
    """Check if `data` is a valid custom_types.mute.MuteRequestDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid MuteRequestDict.
    """
    return (
        util.check_valid_typeddict_keys(data, MuteRequestDict)
        and isinstance(data["participant_id"], str)
        and isinstance(data["mute_video"], bool)
        and isinstance(data["mute_audio"], bool)
    )
