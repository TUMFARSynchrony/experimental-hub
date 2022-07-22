"""Provide filter TypedDicts: `SetFiltersRequestDict` and `FilterDict`.

Use for type hints and static type checking without any overhead during runtime.

When more complex filters with custom settings are implemented, they should be added
here.  `is_valid_filter_dict` should then include checks for the additional Filters,
based on FilterDict.
"""

import logging
from typing import Literal, TypeGuard, TypedDict, get_args

import custom_types.util as util

logger = logging.getLogger("Filters")

FILTER_TYPES = Literal[
    "MUTE_AUDIO",
    "MUTE_VIDEO",
    "ROTATION",
    "EDGE_OUTLINE",
    "FILTER_API_TEST",
]
"""Valid filter types."""


class FilterDict(TypedDict):
    """TypedDict for basic filters without extra parameters other than a `type`.

    Attributes
    ----------
    type : str
        filter type (unique identifier / name)
    id : str
        Filter id.  Empty string if adding a new filter.  Read only for client.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#filter
    """

    type: FILTER_TYPES
    id: str


def is_valid_filter_dict(data) -> TypeGuard[FilterDict]:
    """Check if `data` is a valid FilterDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid FilterDict.
    """
    if not util.check_valid_typeddict_keys(data, FilterDict):
        return False

    if data["type"] not in get_args(FILTER_TYPES):
        logging.debug(f'Invalid filter type: "{data["type"]}".')
        return False

    return isinstance(data["type"], str) and isinstance(data["id"], str)


class SetFiltersRequestDict(TypedDict):
    """TypedDict for `SET_FILTERS` requests.

    Attributes
    ----------
    participant_id : str
        Participant ID for the requested endpoint.
    audio_filters : list of custom_types.filters.FilterDict
        Active audio filters for participant with `participant_id`.
    video_filters : list of custom_types.filters.FilterDict
        Active video filters for participant with `participant_id`.
    """

    participant_id: str
    audio_filters: list[FilterDict]
    video_filters: list[FilterDict]


def is_valid_set_filters_request(
    data, recursive: bool = True
) -> TypeGuard[SetFiltersRequestDict]:
    """Check if `data` is a valid custom_types.filters.SetFiltersRequest.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.
    recursive : bool, default True
        If true, filters will be checked recursively.

    Returns
    -------
    bool
        True if `data` is a valid FilterDict.
    """
    if (
        not util.check_valid_typeddict_keys(data, SetFiltersRequestDict)
        or not isinstance(data["audio_filters"], list)
        or not isinstance(data["video_filters"], list)
        or not isinstance(data["participant_id"], str)
    ):
        return False

    if recursive:
        ids = []
        for filter in data["audio_filters"]:
            if filter["id"] in ids:
                logger.debug(f'Duplicate id: "{filter["id"]}" in SetFiltersRequestDict')
                return False
            ids.append(filter["id"])
            if not is_valid_filter_dict(filter):
                return False

        ids = []
        for filter in data["video_filters"]:
            if filter["id"] in ids:
                logger.debug(f'Duplicate id: "{filter["id"]}" in SetFiltersRequestDict')
                return False
            ids.append(filter["id"])
            if not is_valid_filter_dict(filter):
                return False

    return True
