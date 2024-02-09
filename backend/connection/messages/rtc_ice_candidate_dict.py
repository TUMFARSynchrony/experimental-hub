from typing import TypedDict, Any, TypeGuard

from custom_types import util


class RTCIceCandidateDict(TypedDict):
    """TypedDict representing a WebRtc session description.

    Attributes
    ----------
    candidate : str
        A string containing the candidate-attribute information.
    sdpMid : str
    sdpMLineIndex : int
    usernameFragment : str

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchrony/experimental-hub/wiki/Data-Types#rtcicecandidate
    Connection Protocol Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol
    """

    candidate: str
    sdpMid: str
    sdpMLineIndex: int
    usernameFragment: str


def is_valid_rtc_ice_candidate_dict(
    data: Any,
) -> TypeGuard[RTCIceCandidateDict]:
    """Check if `data` is a valid connection.messages.RTCIceCandidateDict.

    Parameters
    ----------
    data : Any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid connection.messages.RTCIceCandidateDict.
    """
    # Check if all required and only required or optional keys exist in data
    if not util.check_valid_typeddict_keys(data, RTCIceCandidateDict):
        return False

    return isinstance(data["candidate"], str) and \
        isinstance(data["sdpMid"], str) and \
        isinstance(data["sdpMLineIndex"], int) and \
        isinstance(data["usernameFragment"], str | None)
