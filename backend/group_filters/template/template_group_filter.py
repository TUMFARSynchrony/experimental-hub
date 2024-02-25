import numpy as np
from av import VideoFrame, AudioFrame
from filters.filter_dict import FilterDict
from group_filters import GroupFilter
from typing import Any
from scipy.interpolate import interp1d


class TemplateGroupFilter(GroupFilter):
    """
    A simple template group filter which applies the followings:
    - takes the mean of each frame on a video track of a participant at the individual
    frame processing step. This part runs in the track handler of the corresponding
    participant.
    - aligns the data collected at the aggregator for 2 participants before the
    aggregation step. This part runs in the corresponding aggregator.
    - takes the standard deviation of aligned data of 2 participants at the
    aggregation step. This part runs in the corresponding aggregator.

    Can be used as a template to copy when creating a new group filter.
    """

    data_len_per_participant = 1  # data required for aggregation
    num_participants_in_aggregation = 2  # number of participants joining in aggregation

    def __init__(self, config: FilterDict, participant_id: str):
        super().__init__(config, participant_id)

    @staticmethod
    def name() -> str:
        # TODO: Change this name to a unique name.
        return "TEMPLATE_GF"

    @staticmethod
    def type() -> str:
        # TODO: change this according to your filter type (SESSION, TEST or NONE)
        return "NONE"

    @staticmethod
    def channel() -> str:
        # TODO: change this according to your filter channel (video, audio, both)
        return "video"

    @staticmethod
    def default_config() -> dict:
        # TODO: change this according to your filter config
        return {
            # example of how a filter config can look like
            # add or delete this
            # This would show that there is a string variable (direction) which can have different
            # values and another int variable (size)
            # in the frontend, we would then have either a dropdown (direction) or input (size)
            # The values can be changed and sent back to the backend
            #
            #
            # "direction": {
            #     "defaultValue": ["clockwise", "anti-clockwise"],
            #     "value": "clockwise",
            #     "requiresOtherFilter": False,
            # },
            # "size": {
            #     "min": 1,
            #     "max": 60,
            #     "step": 1,
            #     "value": 45,
            #     "defaultValue": 45,
            # },
        }

    async def process_individual_frame(
        self, original: VideoFrame | AudioFrame, ndarray: np.ndarray
    ) -> Any:
        # TODO: Change this to implement the individual frame processing step.
        return ndarray.mean()

    @staticmethod
    def align_data(x: list, y: list, base_timeline: list) -> list:
        # TODO: Change this to implement an alignment function.
        # Needs to be implemented as a static method.
        interpolator = interp1d(x, y, kind="nearest", fill_value="extrapolate")
        return list(interpolator(base_timeline))

    @staticmethod
    def aggregate(data: list[list[Any]]) -> Any:
        # TODO: Change this to implement the aggregation step.
        # Needs to be implemented as a static method.
        np_data = np.array(data)
        return np_data.std(axis=0)[0]
