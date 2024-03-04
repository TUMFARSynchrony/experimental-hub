from abc import ABC, abstractmethod
from custom_types import util
from typing import Any, TypeGuard

from chat_filters import ChatFilterDict


class ChatFilter(ABC):
    _config: ChatFilterDict

    def __init__(
        self,
        config: ChatFilterDict,
    ) -> None:
        """Initialize new Chat filter.

        Parameters
        ----------
        config : ChatFilterDict
            Configuration for chat filter.`config["name"]` must match the filter
            implementation.

        """
        self.run_if_muted = False
        self._config = config

    @property
    def config(self) -> ChatFilterDict:
        """Get ChatFilter config."""
        return self._config

    def set_config(self, config: ChatFilterDict) -> None:
        """Update chat filter config.

        Notes
        -----
        Provide a custom implementation for this function in a subclass in case the
        filter should react to config changes.
        """
        self._config = config

    @abstractmethod
    def apply_filter(self, msg: str) -> Any:
        pass

    @staticmethod
    def validate_dict(data) -> TypeGuard[ChatFilterDict]:
        return util.check_valid_typeddict_keys(data, ChatFilterDict)
