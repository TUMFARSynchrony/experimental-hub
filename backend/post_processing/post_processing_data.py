from __future__ import annotations
import logging


class PostProcessingData():
    """Object class for the post processing data of the experiments."""

    _logger: logging.Logger
    _type: str
    _filename: str
    _session_id: str
    _participant_id: str

    def __init__(
        self, type: str, filename: str, session_id: str, participant_id: str
    ) -> None:
        """Initialize new PostProcessingData.

        Parameters
        ----------
        type : str
            The value would be video/audio.
        filename : str
            The filename of the recorded data.
        session_id : str
            Session ID of the recorded data.
        participant_id : str
            Participant ID of the recorded data.
        """
        super().__init__()
        self._logger = logging.getLogger(f"{type.capitalize()}-PostProcessingData")
        self._type = type
        self._filename = filename
        self._session_id = session_id
        self._participant_id = participant_id

    @property
    def type(self) -> str:
        """Get type of PostProcessingData."""
        return self._type

    @property
    def filename(self) -> str:
        """Get filename of PostProcessingData."""
        return self._filename
    
    @property
    def session_id(self) -> str:
        """Get session ID of PostProcessingData."""
        return self._session_id
    
    @property
    def participant_id(self) -> str:
        """Get participant ID of PostProcessingData."""
        return self._participant_id
