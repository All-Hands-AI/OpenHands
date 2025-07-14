import base64
import pickle
from threading import Lock
from typing import Callable
from uuid import uuid4

from openhands.core.config.llm_config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics
from openhands.storage.files import FileStore
from openhands.storage.locations import get_conversation_llm_registry_filename


class LLMRegistry:
    metrics_id = str(uuid4())
    service_to_llm: dict[str, LLM] = {}
    restored_llm: dict[str, Metrics] = {}

    def __init__(
        self,
        file_store: FileStore | None,
        conversation_id: str,
        user_id: str | None,
    ):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.file_store = file_store

        self.registry_path = get_conversation_llm_registry_filename(
            self.conversation_id, self.user_id
        )

        self._save_lock = Lock()

        # Always attempt to restore registry if it exists
        self.maybe_restore_registry()

    def request_extraneous_completion(
        self, service_id: str, llm_config: LLMConfig, messages: list[dict[str, str]]
    ) -> str:
        print('extraneous completion', service_id)
        if service_id not in self.service_to_llm:
            llm = LLM(config=llm_config, service_id=service_id)
            self.service_to_llm[service_id] = llm

        llm = self.service_to_llm[service_id]
        response = llm.completion(messages=messages)

        # We always save the registry after extraneous completions as we cannot predict
        # the next time the registry will be saved
        self.save_registry()
        return response.choices[0].message.content.strip()

    def register_llm(
        self,
        service_id: str,
        config: LLMConfig,
        retry_listener: Callable[[int, int], None] | None = None,
    ):
        logger.info(
            f'[Metrics registry {self.metrics_id}]: Registering service for {service_id}'
        )

        if service_id in self.service_to_llm:
            raise Exception(f'Registering duplicate LLM: {service_id}')

        # We're restoring an existing registry, we should use the existing metrics
        if service_id in self.restored_llm:
            llm = LLM(
                config=config,
                service_id=service_id,
                retry_listener=retry_listener,
                metrics=self.restored_llm[service_id],
            )
            del self.restored_llm[service_id]
        else:
            llm = LLM(
                config=config, service_id=service_id, retry_listener=retry_listener
            )

        self.service_to_llm[service_id] = llm
        return llm

    def request_existing_service(
        self,
        service_id: str,
        config: LLMConfig,
        retry_listener: Callable[[int, int], None] | None = None,
    ):
        if service_id not in self.service_to_llm:
            raise Exception(f'LLM service does not exist {service_id}')
        existing_llm = self.service_to_llm[service_id]

        return LLM(
            config=config,
            service_id=service_id,
            metrics=existing_llm.metrics,
            retry_listener=retry_listener,
        )

    def get_combined_metrics(self) -> Metrics:
        total_metrics = Metrics()
        for llm in self.service_to_llm.values():
            total_metrics.merge(llm.metrics)

        print('total metrics', self.service_to_llm)
        return total_metrics

    def save_registry(self):
        if not self.file_store:
            return

        with self._save_lock:
            metrics: dict[str, Metrics] = {}
            for service_id, llm in self.service_to_llm.items():
                metrics[service_id] = llm.metrics.copy()

            pickled = pickle.dumps(metrics)
            serialized_metrics = base64.b64encode(pickled).decode('utf-8')
            self.file_store.write(self.registry_path, serialized_metrics)

    def maybe_restore_registry(self):
        if not self.file_store or not self.conversation_id:
            return

        try:
            encoded = self.file_store.read(self.registry_path)
            pickled = base64.b64decode(encoded)
            self.restored_llm = pickle.loads(pickled)
        except FileNotFoundError:
            pass
