from typing import TypedDict


class ChatFilterDict(TypedDict):
    """TypedDict for chat filters with only basic attributes.

    Attributes
    ----------
    id : str
        Filter id.  Empty string if adding a new filter.  Read only for client.
    name : str
        Filter name (unique identifier / name)
    config: dict
        Filter configuration. Contains all variables for the filter


    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#filter
    """

    id: str
    name: str
    config: dict
