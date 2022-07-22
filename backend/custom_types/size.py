"""Provide the `SizeDict` TypedDict.

Use for type hints and static type checking without any overhead during runtime.
"""

from typing import TypeGuard, TypedDict

import custom_types.util as util


class SizeDict(TypedDict):
    """TypedDict for the size of a users's stream on the canvas.

    Attributes
    ----------
    width : int or float
        Width of the stream.
    height : int or float
        Height of the stream.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#participant
    """

    width: int | float
    height: int | float


def is_valid_size(data) -> TypeGuard[SizeDict]:
    """Check if `data` is a valid SizeDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid SizeDict.
    """
    return (
        util.check_valid_typeddict_keys(data, SizeDict)
        and (isinstance(data["width"], int) or isinstance(data["width"], float))
        and (isinstance(data["height"], int) or isinstance(data["height"], float))
    )
