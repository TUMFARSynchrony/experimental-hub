"""Provide messages used internally by the Connection classes in front-/backend.

Use for type hints and static type checking without any overhead during runtime.
"""

from __future__ import annotations
from typing import Any, Literal, TypeGuard, TypedDict, get_args

from custom_types.participant_summary import ParticipantSummaryDict

import custom_types.util as util


class ConnectionProposalDict(TypedDict):
    """TypedDict for sending a `CONNECTION_PROPOSAL` message to the client.

    Attributes
    ----------
    id : str
        Identifier of this proposal.  Must be used in the
        custom_types.connection.ConnectionOfferDict to identify the offer.
    participant_summary : custom_types.participant_summary.ParticipantSummaryDict or None
        Optional summary for the participant the subconnection is connected to.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#ConnectionProposal
    Connection Protocol Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol
    """

    id: str
    participant_summary: ParticipantSummaryDict | str | None


class ConnectionOfferDict(TypedDict):
    """TypedDict for sending a `CONNECTION_OFFER` message to the client.

    Attributes
    ----------
    id : str
        Identifier of this offer.  Must be used in the
        custom_types.connection.ConnectionAnswerDict to identify the answer.
    offer : custom_types.connection.RTCSessionDescriptionDict
        WebRtc offer.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#ConnectionOffer
    Connection Protocol Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol
    """

    id: str
    offer: RTCSessionDescriptionDict


def is_valid_connection_offer_dict(data: Any) -> TypeGuard[ConnectionOfferDict]:
    """Check if `data` is a valid custom_types.connection.ConnectionOfferDict.

    Parameters
    ----------
    data : Any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid custom_types.connection.ConnectionOfferDict.
    """
    # Check if all required and only required or optional keys exist in data
    if not util.check_valid_typeddict_keys(data, ConnectionOfferDict):
        return False

    return isinstance(data["id"], str) and is_valid_rtc_session_description_dict(
        data["offer"]
    )


class RTCSessionDescriptionDict(TypedDict):
    """TypedDict representing a WebRtc session description.

    Attributes
    ----------
    sdp : str
        Session Description Protocol.
    type : custom_types.connection.RTC_SESSION_TYPES
        Type of the session description.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#RTCSessionDescription
    Connection Protocol Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol
    """

    sdp: str
    type: RTC_SESSION_TYPES


RTC_SESSION_TYPES = Literal["offer", "pranswer", "answer", "rollback"]


def is_valid_rtc_session_description_dict(
    data: Any,
) -> TypeGuard[RTCSessionDescriptionDict]:
    """Check if `data` is a valid custom_types.connection.RTCSessionDescriptionDict.

    Parameters
    ----------
    data : Any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid custom_types.connection.RTCSessionDescriptionDict.
    """
    # Check if all required and only required or optional keys exist in data
    if not util.check_valid_typeddict_keys(data, RTCSessionDescriptionDict):
        return False

    return isinstance(data["sdp"], str) and data["type"] in get_args(RTC_SESSION_TYPES)


class ConnectionAnswerDict(TypedDict):
    """TypedDict for the client answer `CONNECTION_ANSWER` to `CONNECTION_OFFER`.

    Attributes
    ----------
    id : str
        Identifier of the original custom_types.connection.ConnectionOfferDict
        / `CONNECTION_OFFER`.
    answer : custom_types.connection.RTCSessionDescriptionDict
        WebRtc answer to the offer send before.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#ConnectionAnswer
    Connection Protocol Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol
    """

    id: str
    answer: RTCSessionDescriptionDict


def is_valid_connection_answer_dict(data: Any) -> TypeGuard[ConnectionAnswerDict]:
    """Check if `data` is a valid custom_types.connection.ConnectionAnswerDict.

    Parameters
    ----------
    data : Any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid custom_types.connection.ConnectionAnswerDict.
    """
    # Check if all required and only required or optional keys exist in data
    if not util.check_valid_typeddict_keys(data, ConnectionAnswerDict):
        return False

    return isinstance(data["id"], str) and is_valid_rtc_session_description_dict(
        data["answer"]
    )
