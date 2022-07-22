"""Provide the `ParticipantDict` TypedDict.

Use for type hints and static type checking without any overhead during runtime.
"""

from typing import TypeGuard, TypedDict

import custom_types.util as util

from custom_types.filters import is_valid_filter_dict
from custom_types.size import SizeDict, is_valid_size
from custom_types.chat_message import ChatMessageDict, is_valid_chatmessage
from custom_types.position import PositionDict, is_valid_position
from custom_types.filters import FilterDict


class ParticipantDict(TypedDict):
    """TypedDict representing an participant.

    Contains sensitive information that should not be send to non-experimenter clients.

    Attributes
    ----------
    id: str, default ""
        Unique id for this participant in a Session.  When creating a new Participant in
        a Session, this field is initially set to an empty string.
    first_name : str
        First name of the participant.
    last_name : str
        Last name of the participant.
    muted_video : bool
        Whether the participants' video is forcefully muted by the experimenter.
    muted_audio : bool
        Whether the participants' audio is forcefully muted by the experimenter.
    audio_filters : list of custom_types.filters.FilterDict
        Active audio filters for this participant.
    audio_filters : list of custom_types.filters.FilterDict
        Active video filters for this participant.
    position : custom_types.position.PositionDict
        Position of the participant's stream on the canvas.
    size : custom_types.size.SizeDict
        Size of the participant's stream on the canvas.
    chat : list of custom_types.chat_log.ChatLogDict
        Chat log between experimenter and participant.
    banned : bool
        Whether this participant is banned from the experiment.

    See Also
    --------
    ParticipantSummaryDict :
        custom_types.participant_summary.ParticipantSummaryDict used to send a summary
        of a participant to the client.
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#Participant
    """

    id: str
    first_name: str
    last_name: str
    muted_video: bool
    muted_audio: bool
    audio_filters: list[FilterDict]
    video_filters: list[FilterDict]
    position: PositionDict
    size: SizeDict
    chat: list[ChatMessageDict]
    banned: bool


def is_valid_participant(data, recursive: bool = True) -> TypeGuard[ParticipantDict]:
    """Check if `data` is a valid ParticipantDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.
    recursive : bool, default True
        If true, filters, chat, position and size will be checked recursively.

    Returns
    -------
    bool
        True if `data` is a valid ParticipantDict.
    """
    if not util.check_valid_typeddict_keys(data, ParticipantDict):
        return False

    # Shallow checks for variables with recursive types
    if (
        not isinstance(data["audio_filters"], list)
        or not isinstance(data["video_filters"], list)
        or not isinstance(data["chat"], list)
        or not isinstance(data["position"], dict)
        or not isinstance(data["size"], dict)
    ):
        return False

    if recursive:
        for filter in data["audio_filters"]:
            if not is_valid_filter_dict(filter):
                return False
        for filter in data["video_filters"]:
            if not is_valid_filter_dict(filter):
                return False
        for message in data["chat"]:
            if not is_valid_chatmessage(message):
                return False
        if not is_valid_size(data["size"]) or not is_valid_position(data["position"]):
            return False

    return (
        isinstance(data["id"], str)
        and isinstance(data["first_name"], str)
        and isinstance(data["last_name"], str)
        and isinstance(data["muted_video"], bool)
        and isinstance(data["muted_audio"], bool)
        and isinstance(data["banned"], bool)
    )
