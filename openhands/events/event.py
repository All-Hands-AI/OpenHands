from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from openhands.events.tool import ToolCallMetadata
from openhands.llm.metrics import Metrics


class EventSource(str, Enum):
    AGENT = 'agent'
    USER = 'user'
    ENVIRONMENT = 'environment'


class FileEditSource(str, Enum):
    LLM_BASED_EDIT = 'llm_based_edit'
    OH_ACI = 'oh_aci'  # openhands-aci


class FileReadSource(str, Enum):
    OH_ACI = 'oh_aci'  # openhands-aci
    DEFAULT = 'default'


@dataclass
class Event:
    @property
    def message(self) -> str | None:
        if hasattr(self, '_message'):
            return self._message  # type: ignore[attr-defined]
        return ''

    @property
    def id(self) -> int:
        if hasattr(self, '_id'):
            return self._id  # type: ignore[attr-defined]
        return -1

    @property
    def timestamp(self):
        if hasattr(self, '_timestamp') and isinstance(self._timestamp, str):
            return self._timestamp

    @timestamp.setter
    def timestamp(self, value: datetime) -> None:
        if isinstance(value, datetime):
            self._timestamp = value.isoformat()

    @property
    def source(self) -> EventSource | None:
        if hasattr(self, '_source'):
            return self._source  # type: ignore[attr-defined]
        return None

    @property
    def cause(self) -> int | None:
        if hasattr(self, '_cause'):
            return self._cause  # type: ignore[attr-defined]
        return None

    @property
    def timeout(self) -> int | None:
        if hasattr(self, '_timeout'):
            return self._timeout  # type: ignore[attr-defined]
        return None

    @timeout.setter
    def timeout(self, value: int | None) -> None:
        self._timeout = value
        if value is not None and value > 600:
            from openhands.core.logger import openhands_logger as logger

            logger.warning(
                'Timeout greater than 600 seconds may not be supported by '
                'the runtime. Consider setting a lower timeout.'
            )

        # Check if .blocking is an attribute of the event
        if hasattr(self, 'blocking'):
            # .blocking needs to be set to True if .timeout is set
            self.blocking = True

    # optional metadata, LLM call cost of the edit
    @property
    def llm_metrics(self) -> Metrics | None:
        if hasattr(self, '_llm_metrics'):
            return self._llm_metrics  # type: ignore[attr-defined]
        return None

    @llm_metrics.setter
    def llm_metrics(self, value: Metrics) -> None:
        self._llm_metrics = value

    # optional field
    @property
    def tool_call_metadata(self) -> ToolCallMetadata | None:
        if hasattr(self, '_tool_call_metadata'):
            return self._tool_call_metadata  # type: ignore[attr-defined]
        return None

    @tool_call_metadata.setter
    def tool_call_metadata(self, value: ToolCallMetadata) -> None:
        self._tool_call_metadata = value
