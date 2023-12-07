from __future__ import annotations
from abc import ABCMeta, abstractmethod
from .post_processing_data import PostProcessingData


class PostProcessingInterface(metaclass=ABCMeta):
    """Abstract interface for post-processing of the experiments.

    Notes
    -----
    Do not instantiate directly, use subclasses / implementations of
    `PostProcessingInterface` instead.

    See Also
    --------
    post_processing.video.producer : Implementation for PostProcessingInterface.
    """

    _recording_list: list[PostProcessingData]

    @abstractmethod
    def execute(self) -> None:
        """Execute the post-processing of the recorded data.

        The implementation would depend on the recorded data type, whether it is
        a video or audio.
        """
        pass

    @property
    def recording_list(self):
        """Get the array of post_processing.PostProcessingData."""
        return self._recording_list
    
    @recording_list.setter
    def recording_list(self, value):
        """Set recording list value."""
        self._recording_list = value