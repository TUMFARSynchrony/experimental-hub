"""Provide the `PostProcessingRequestDict` TypedDict.

Use for type hints and static type checking without any overhead during runtime.
"""

from typing import TypeGuard, TypedDict

import custom_types.util as util


class PostProcessingDict(TypedDict):
    """TypedDict for post-processing request from experimenters.

    Attributes
    ----------
    session_id : str
        ID of the experiment/session.
    """

    session_id: str


def is_valid_postprocessingrequest(data) -> TypeGuard[PostProcessingDict]:
    """Check if `data` is a valid PostProcessingDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid PostProcessingDict.
    """
    return (
        util.check_valid_typeddict_keys(data, PostProcessingDict)
        and isinstance(data["session_id"], str)
    )
