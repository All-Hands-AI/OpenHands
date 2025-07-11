import json
from typing import Callable
from uuid import uuid4

from openhands.core.config.llm_config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics
from openhands.storage.files import FileStore
from openhands.storage.locations import (
    get_conversation_llm_registry_filename,
    get_conversation_registered_llm,
)


class LLMRegistry:
    metrics_id = str(uuid4())
    service_to_llm: dict[str, LLM] = {}
    restored_llm: dict[str, Metrics] = {}

    def __init__(
        self,
        file_store: FileStore,
        conversation_id: str,
        user_id: str | None,
    ):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.file_store = file_store

        self.registry_path = get_conversation_llm_registry_filename(
            self.conversation_id, self.user_id
        )

        # Always attempt to restore registry if it exists
        self.maybe_restore_registry()

    def request_extraneous_completion(
        self, service_id: str, llm_config: LLMConfig, messages: list[dict[str, str]]
    ) -> str:
        if service_id not in self.service_to_llm:
            llm = LLM(config=llm_config, service_id=service_id)
            self.service_to_llm[service_id] = llm

        llm = self.service_to_llm[service_id]
        response = llm.completion(messages=messages)
        return response['choices'][0]['message']['content'].strip()

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

        return total_metrics

    def save_registry(self):
        # Create registry paths and save them
        # Used to reference individual metric dumps
        # This is so that we can instantiate multiple LLM Registry for the same conversation and ensure they stay in sync
        # IMPORTANT: this syncing only works as long as service ids are mutually exclusive between the LLM Registry (no two registry update the same LLM Service)
        loaded_paths: list[str] = json.loads(self.file_store.read(self.registry_path))
        paths = set(loaded_paths)
        for service_id in self.service_to_llm:
            paths.add(service_id)

        self.file_store.write(self.registry_path, json.dumps(list(paths)))

        # This only flushes the services the which are registered with this registry
        for service_id, llm in self.service_to_llm.items():
            registered_llm_path = get_conversation_registered_llm(
                service_id, self.conversation_id, self.user_id
            )
            self.file_store.write(registered_llm_path, json.dumps(llm.metrics))

    def maybe_restore_registry(self):
        if not self.conversation_id:
            return

        loaded_paths: list[str] = json.loads(self.file_store.read(self.registry_path))
        paths = set(loaded_paths)

        for service_id in paths:
            registered_llm_path = get_conversation_registered_llm(
                service_id, self.conversation_id, self.user_id
            )
            serialized_metrics = self.file_store.read(registered_llm_path)
            self.restored_llm[service_id] = json.loads(serialized_metrics)
