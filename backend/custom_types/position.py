"""Provide the `PositionDict` TypedDict.

Use for type hints and static type checking without any overhead during runtime.
"""

from typing import TypeGuard, TypedDict

import custom_types.util as util


class PositionDict(TypedDict):
    """3D position for a user on a canvas.

    Attributes
    ----------
    x : int or float
        X coordinate.
    y : int or float
        Y coordinate.
    z : int or float
        Z coordinate.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#Participant
    """

    x: int | float
    y: int | float
    z: int | float


def is_valid_position(data) -> TypeGuard[PositionDict]:
    """Check if `data` is a valid PositionDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid PositionDict.
    """
    return (
        util.check_valid_typeddict_keys(data, PositionDict)
        and (isinstance(data["x"], int) or isinstance(data["x"], float))
        and (isinstance(data["y"], int) or isinstance(data["y"], float))
        and (isinstance(data["z"], int) or isinstance(data["z"], float))
    )
