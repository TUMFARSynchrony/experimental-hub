"""Provide messages used internally by the Connection classes in front-/backend.

Use for type hints and static type checking without any overhead during runtime.
"""

from .connection_proposal_dict import ConnectionProposalDict
from .rtc_session_description_dict import (
    RTCSessionDescriptionDict,
    is_valid_rtc_session_description_dict,
)
from .connection_answer_dict import (
    ConnectionAnswerDict,
    is_valid_connection_answer_dict,
)
from .connection_offer_dict import ConnectionOfferDict, is_valid_connection_offer_dict

from .rtc_ice_candidate_dict import RTCIceCandidateDict, is_valid_rtc_ice_candidate_dict
from .add_ice_candidate_dict import AddIceCandidateDict, is_valid_add_ice_candidate_dict
