"""Provide the `CanvasElementDict` TypedDict`.

Use for type hints and static type checking without any overhead during runtime.
"""

from typing import Any, TypeGuard, TypedDict

import custom_types.util as util

from session.data.position.position_data import PositionData
from session.data.size.size_data import SizeData
from session.data.position import is_valid_position
from session.data.size import is_valid_size


class CanvasElementDict(TypedDict):
    """TypedDict for sending canvas element between client and server.

    Attributes
    ----------
    id : str
        id of the participant
    participant_name: str
        name of the participant
    size: SizeData
        size information of the video stream inside the canvas
    position: PositionData
        position information of the video stream inside the canvas

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchrony/experimental-hub/wiki/Data-Types#canvaselement
    """

    id: str
    participant_name: str
    size: SizeData
    position: PositionData


def is_valid_canvas_element(data: Any) -> TypeGuard[CanvasElementDict]:
    """Check if `data` is a valid CanvasElementDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid CanvasElementDict.
    """

    if not util.check_valid_typeddict_keys(data, CanvasElementDict):
        return False

    if not isinstance(data["position"], dict) or not isinstance(data["size"], dict):
        return False

    if not is_valid_size(data["size"]) or not is_valid_position(data["position"]):
        return False

    return isinstance(data["id"], str) and isinstance(data["participant_name"], str)
