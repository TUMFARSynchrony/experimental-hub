"""Provide the `NoteDict` TypedDict.

Use for type hints and static type checking without any overhead during runtime.
"""

from typing import TypeGuard, TypedDict

import custom_types.util as util


class NoteDict(TypedDict):
    """TypedDict for notes in custom_types.session.SessionDict.

    Attributes
    ----------
    time : int
        Time the note was saved in milliseconds since January 1, 1970, 00:00:00 (UTC).
    speakers : list of str
        List of Participant IDs for participants speaking when the note was saved.
    content : str
        Text content of the note, written by an experimenter.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#note
    """

    time: int
    speakers: list[str]
    content: str


def is_valid_note(data) -> TypeGuard[NoteDict]:
    """Check if `data` is a valid NoteDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid NoteDict.
    """
    if not util.check_valid_typeddict_keys(data, NoteDict):
        return False

    # Check speakers list
    if not isinstance(data["speakers"], list):
        return False
    for entry in data["speakers"]:
        if not isinstance(entry, str):
            return False

    return isinstance(data["time"], int) and isinstance(data["content"], str)
