import logging

from hub.exceptions import ErrorDictException
from session.data.participant import participant_data_factory
from session.data.session import SessionDict, SessionData
from session.data.session.session_data_functions import (
    has_duplicate_participant_ids,
    _generate_participant_ids,
)


def session_data_factory(session_dict: SessionDict) -> SessionData:
    """Create a SessionData object based on a SessionDict.

    Parameters
    ----------
    session_dict : session.data.session.SessionDict
        Session dictionary with the data for the resulting SessionData

    Returns
    -------
    session.data.session.SessionData
        SessionData based on the data in `session_dict`.

    Raises
    ------
    ValueError
        If `id` in `session_dict` is an empty string.
    ErrorDictException
        If a duplicate participant ID was found.
    """
    if session_dict["id"] == "":
        raise ValueError('Missing "id" in session dict.')
    if session_dict["creation_time"] != 0:
        raise ValueError('"creation_time" must be 0 when creating new SessionData.')

    if has_duplicate_participant_ids(session_dict):
        raise ErrorDictException(
            type="DUPLICATE_ID",
            code=400,
            description="Duplicate participant ID found in session data.",
        )
    _generate_participant_ids(session_dict)
    participants = {}
    for participant_dict in session_dict["participants"]:
        p = participant_data_factory(participant_dict)
        participants[p.id] = p

    return SessionData(
        session_dict["id"],
        session_dict["title"],
        session_dict["date"],
        session_dict["record"],
        session_dict["time_limit"],
        session_dict["description"],
        session_dict["notes"],
        participants,
        session_dict["log"],
    )
