import base64
import pickle
from threading import Lock

from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm_registry import RegistryEvent
from openhands.llm.metrics import Metrics
from openhands.storage.files import FileStore
from openhands.storage.locations import (
    get_conversation_stats_filename,
)


class ConversationStats:
    def __init__(
        self,
        file_store: FileStore | None,
        conversation_id: str,
        user_id: str | None,
    ):
        self.metrics_path = get_conversation_stats_filename(conversation_id, user_id)
        self.file_store = file_store
        self.conversation_id = conversation_id
        self.user_id = user_id

        self._save_lock = Lock()

        self.service_to_metrics: dict[str, Metrics] = {}
        self.restored_metrics: dict[str, Metrics] = {}

        # Always attempt to restore registry if it exists
        self.maybe_restore_metrics()

    def save_metrics(self):
        if not self.file_store:
            return

        with self._save_lock:
            pickled = pickle.dumps(self.service_to_metrics)
            serialized_metrics = base64.b64encode(pickled).decode('utf-8')
            self.file_store.write(self.metrics_path, serialized_metrics)
            logger.info(
                'Saved converation stats',
                extra={'conversation_id': self.conversation_id},
            )

    def maybe_restore_metrics(self):
        if not self.file_store or not self.conversation_id:
            return

        try:
            encoded = self.file_store.read(self.metrics_path)
            pickled = base64.b64decode(encoded)
            self.restored_metrics = pickle.loads(pickled)
            logger.info(f'restored metrics: {self.conversation_id}')
        except FileNotFoundError:
            pass

    def get_combined_metrics(self) -> Metrics:
        total_metrics = Metrics()
        for metrics in self.service_to_metrics.values():
            total_metrics.merge(metrics)
        return total_metrics

    def get_metrics_for_service(self, service_id: str) -> Metrics:
        if service_id not in self.service_to_metrics:
            raise Exception(f'LLM service does not exist {service_id}')

        return self.service_to_metrics[service_id]

    def register_llm(self, event: RegistryEvent):
        # Listen for llm creations and track their metrics
        llm = event.llm
        service_id = event.service_id

        if service_id in self.restored_metrics:
            llm.metrics = self.restored_metrics[service_id].copy()
            del self.restored_metrics[service_id]

        self.service_to_metrics[service_id] = llm.metrics

    def merge(self, conversation_stats: 'ConversationStats'):
        """
        Merge two ConversationStats objects.

        - Take all metrics from both `restored_metrics` and `service_to_metrics`
          for each object.
        - If any service_id exists in BOTH objects, raise an error.
        - Combine into a single dict on `self.service_to_metrics` and clear
          `self.restored_metrics`.
        - Save the merged result.
        """
        # All IDs present on self (both active and restored)
        self_ids = set(self.service_to_metrics.keys()) | set(
            self.restored_metrics.keys()
        )

        # All IDs present on the other stats (both active and restored)
        other_ids = set(conversation_stats.service_to_metrics.keys()) | set(
            conversation_stats.restored_metrics.keys()
        )

        # Any overlap between the two services should error out
        dupes = self_ids & other_ids
        if dupes:
            raise ValueError(f'Duplicate service IDs across stats: {sorted(dupes)}')

        # Start from self's current active metrics
        merged: dict[str, Metrics] = dict(self.service_to_metrics)

        # Add any restored metrics from self that aren't in active (flattening into one dict)
        for service_id, m in self.restored_metrics.items():
            merged[service_id] = m

        # Add all of other's active metrics
        for service_id, m in conversation_stats.service_to_metrics.items():
            merged[service_id] = m

        # Add all of other's restored metrics
        for service_id, m in conversation_stats.restored_metrics.items():
            merged[service_id] = m

        # Commit merged view
        self.service_to_metrics = merged
        self.save_metrics()
        logger.info(
            'Merged conversation stats',
            extra={
                'conversation_id': self.conversation_id,
                'merged_count': len(merged),
            },
        )
