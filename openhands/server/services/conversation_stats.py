import base64
import pickle
from threading import Lock

from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm_registry import RegistryEvent
from openhands.llm.metrics import Metrics
from openhands.storage.files import FileStore
from openhands.storage.locations import get_conversation_stats_filename


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

        logger.info(f'combined metrics\n\n{total_metrics}')
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
