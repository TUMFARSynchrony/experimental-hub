"""Provide the `KickRequestDict` and `KickNotificationDict` TypedDicts.

Use for type hints and static type checking without any overhead during runtime.
"""

from typing import TypeGuard, TypedDict

import custom_types.util as util


class KickRequestDict(TypedDict):
    """TypedDict for `KICK` requests from experimenters.

    Attributes
    ----------
    participant_id : str
        ID of the participant that should be kicked.
    reason : str
        Reason for kicking the participant.
    """

    participant_id: str
    reason: str


class KickNotificationDict(TypedDict):
    """TypedDict for `KICK_NOTIFICATION` messages send to participant.

    Attributes
    ----------
    reason : str
        Reason for kicking the participant.
    """

    reason: str


def is_valid_kickrequest(data) -> TypeGuard[KickRequestDict]:
    """Check if `data` is a valid KickRequestDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid KickRequestDict.
    """
    return (
        util.check_valid_typeddict_keys(data, KickRequestDict)
        and isinstance(data["participant_id"], str)
        and isinstance(data["reason"], str)
    )
