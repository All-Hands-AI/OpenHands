from __future__ import annotations
from dataclasses import dataclass, field
import os
from types import MappingProxyType
from typing import cast

import docker
from docker.models.containers import Container
import httpx
import socketio

from openhands.controller.agent import Agent
from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import MessageAction
from openhands.events.event_store import EventStore
from openhands.events.nested_event_store import NestedEventStore
from openhands.events.stream import EventStream
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE, ProviderHandler
from openhands.llm.llm import LLM
from openhands.runtime.builder.docker import DockerRuntimeBuilder
from openhands.runtime.impl.docker.containers import stop_all_containers
from openhands.runtime.impl.docker.docker_runtime import DockerRuntime
from openhands.runtime.utils.runtime_build import build_runtime_image
from openhands.server.config.server_config import ServerConfig
from openhands.server.conversation_manager.conversation_manager import ConversationManager
from openhands.server.conversation_manager.standalone_conversation_manager import StandaloneConversationManager
from openhands.server.data_models.agent_loop_info import AgentLoopInfo
from openhands.server.monitoring import MonitoringListener
from openhands.server.session.conversation import Conversation
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.session.session import ROOM_KEY, Session
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.data_models.settings import Settings
from openhands.storage.files import FileStore
from openhands.storage.memory import InMemoryFileStore
from openhands.utils.import_utils import get_impl


#TODO: This works so fundamentally differently than the previous impl it should not extend it.
# Extend ConversationManager as soon as we have all methods
@dataclass
class DockerNestedConversationManager(ConversationManager):
    """Conversation manager where the agent loops exist inside the docker containers."""
    sio: socketio.AsyncServer
    config: AppConfig
    server_config: ServerConfig
    file_store: FileStore
    docker_client: docker.DockerClient = field(default_factory=docker.from_env)
    _conversation_store_class: type[ConversationStore] | None = None

    async def __aenter__(self):
        #return await super().__aenter__()
        pass

    async def __aexit__(self, exc_type, exc_value, traceback):
        #return await super().__aexit__(exc_type, exc_value, traceback)
        pass

    async def attach_to_conversation(
        self, sid: str, user_id: str | None = None
    ) -> Conversation | None:
        # Attaching conversations not suported in this manager - clients should connect directly!
        raise ValueError('unsupported_operation')

    async def detach_from_conversation(self, conversation: Conversation):
        # Attaching conversations not suported in this manager - clients should connect directly!
        raise ValueError('unsupported_operation')

    async def join_conversation(
        self,
        sid: str,
        connection_id: str,
        settings: Settings,
        user_id: str | None,
    ) -> AgentLoopInfo:
        # Attaching conversations not suported in this manager - clients should connect directly!
        raise ValueError('unsupported_operation')

    async def get_running_agent_loops(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> set[str]:
        """
        Get the running agent loops directly from docker.
        """
        names = (container.name for container in self.docker_client.containers.list())
        conversation_ids = {
            name[len('openhands-runtime-'):]
            for name in names
            if name.startswith('openhands-runtime-')
        }
        if filter_to_sids is not None:
            conversation_ids = {
                conversation_id for conversation_id in conversation_ids
                if conversation_id in filter_to_sids
            }
        return conversation_ids

    async def get_connections(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> dict[str, str]:
        results: dict[str, str] = {}
        """
        for container in self.docker_client.containers.list():
            if not container.name.startswith('openhands-runtime-'):
                continue
            conversation_id = container.name[len('openhands-runtime-'):]
            if filter_to_sids is None or conversation_id in filter_to_sids:
                env = container.attrs['Config']['Env']
                container_port = int(next(e[5:] for e in env if e.startswith('port=')))
                api_url = f'{self.config.sandbox.local_runtime_url}:{container_port}'
                async with httpx.AsyncClient() as client:
                    response = await client.get(f'{api_url}/conversations/{conversation_id}')
                    conversation_info = await response.json()
                    conversation_info['num_connections']
        """
        return results

    async def maybe_start_agent_loop(
        self,
        sid: str,
        settings: Settings,
        user_id: str | None,
        initial_user_msg: MessageAction | None = None,
        replay_json: str | None = None,
    ) -> AgentLoopInfo:
        if not await self.is_agent_loop_running(sid):
            await self._start_agent_loop(
                sid, settings, user_id, initial_user_msg, replay_json
            )
        
        nested_url = self._get_nested_url(sid)
        return AgentLoopInfo(
            conversation_id=sid,
            url=nested_url,
            api_key=None,
            event_store=NestedEventStore(
                base_url=nested_url,
                sid=sid,
                user_id=user_id,
            ),
        )

    async def _start_agent_loop(self, sid, settings, user_id, initial_user_msg = None, replay_json = None):
        logger.info(f'starting_agent_loop:{sid}', extra={'session_id': sid})

        response_ids = await self.get_running_agent_loops(user_id)
        if len(response_ids) >= self.config.max_concurrent_conversations:
            logger.info(
                f'too_many_sessions_for:{user_id or ""}',
                extra={'session_id': sid, 'user_id': user_id},
            )
            # Get the conversations sorted (oldest first)
            conversation_store = await self._get_conversation_store(user_id)
            conversations = await conversation_store.get_all_metadata(response_ids)
            conversations.sort(key=_last_updated_at_key, reverse=True)

            while len(conversations) >= self.config.max_concurrent_conversations:
                oldest_conversation_id = conversations.pop().conversation_id
                logger.debug(
                    f'closing_from_too_many_sessions:{user_id or ""}:{oldest_conversation_id}',
                    extra={'session_id': oldest_conversation_id, 'user_id': user_id},
                )
                # Send status message to client and close session.
                status_update_dict = {
                    'status_update': True,
                    'type': 'error',
                    'id': 'AGENT_ERROR$TOO_MANY_CONVERSATIONS',
                    'message': 'Too many conversations at once. If you are still using this one, try reactivating it by prompting the agent to continue',
                }
                await self.sio.emit(
                    'oh_event',
                    status_update_dict,
                    to=ROOM_KEY.format(sid=oldest_conversation_id),
                )
                await self.close_session(oldest_conversation_id)

        # Maybe we just create a runtime here.
        # We also attach runtimes
        """
        if self.runtime_container_image is None:
            config = self.config
            builder = DockerRuntimeBuilder(self.docker_client)
            base_container_image = self.config.sandbox.base_container_image
            if base_container_image is None:
                raise ValueError(
                    'Neither runtime container image nor base container image is set'
                )
            self.runtime_container_image = build_runtime_image(
                base_container_image,
                builder,
                platform=config.sandbox.platform,
                extra_deps=config.sandbox.runtime_extra_deps,
                force_rebuild=config.sandbox.force_rebuild_runtime,
                extra_build_args=config.sandbox.runtime_extra_build_args,
            )
        """

        # I think we need to change the API here. The manager should not need a session
        session = Session(
            sid=sid,
            file_store=self.file_store,
            config=self.config,
            sio=self.sio,
            user_id=user_id,
        )
        agent_cls = settings.agent or self.config.default_agent
        agent_name = agent_cls if agent_cls is not None else 'agent'
        llm = LLM(
            config=self.config.get_llm_config_from_agent(agent_name),
            retry_listener=session._notify_on_llm_retry,
        )
        llm = session._create_llm(agent_cls)
        agent_config = self.config.get_agent_config(agent_cls)
        agent = Agent.get_cls(agent_cls)(llm, agent_config)

        git_provider_tokens = None
        if isinstance(settings, ConversationInitData):
            git_provider_tokens = settings.git_provider_tokens

        provider_handler = ProviderHandler(
            provider_tokens=git_provider_tokens
            or cast(PROVIDER_TOKEN_TYPE, MappingProxyType({}))
        )
        env_vars = await provider_handler.get_env_vars(expose_secrets=True)
        env_vars['CONVERSATION_MANAGER_CLASS'] = 'openhands.server.conversation_manager.standalone_conversation_manager.StandaloneConversationManager'
        env_vars['SERVE_FRONTEND'] = '0'
        env_vars['RUNTIME'] = 'local'

        event_stream = EventStream(sid, self.file_store, user_id)
        runtime = DockerRuntime(
            config=self.config,
            event_stream=event_stream,
            sid=sid,
            plugins=agent.sandbox_plugins,
            headless_mode=False,
            attach_to_existing=False,
            env_vars=env_vars,
            main_module="openhands.server",
        )

        # Hack - disable setting initial env.
        runtime.setup_initial_env = lambda: None  # type:ignore
        
        await runtime.connect()

        # TODO: After we start the nested server, we need to initialize the conversation
        async with httpx.AsyncClient() as client:
            #setup the settings...
            settings_json = settings.model_dump()
            settings_json.pop('git_provider_tokens', None)
            settings_json.pop('custom_secrets', None)
            response = await client.post(f"{runtime.api_url}/api/settings", json=settings_json)

            response = await client.post(f"{runtime.api_url}/api/conversations", json={
                "initial_user_msg": initial_user_msg,
                "image_urls": [],
                "repository": settings.selected_repository,
                #"git_provider": ,
                "selected_branch": settings.selected_repository,
                "initial_user_msg": initial_user_msg,
            })

        return session

    async def send_to_event_stream(self, connection_id: str, data: dict):
        logger.info('DockerNestedConversationManager:send_to_event_stream', extra={
            "connection_id": connection_id,
            "data": data,
        })
        # TODO:
        # Connect to sandbox and send event
        raise ValueError('unsupported_operation')

    async def disconnect_from_session(self, connection_id: str):
        logger.info('DockerNestedConversationManager:disconnect_from_session', extra={
            "connection_id": connection_id,
        })
        # TODO:
        # Disconnect from session
        raise ValueError('unsupported_operation')

    async def close_session(self, sid: str):
        logger.info('DockerNestedConversationManager:close_session', extra={
            "sid": sid,
        })
        stop_all_containers(f'openhands-runtime-{sid}')

    async def get_agent_loop_info(self, user_id = None, filter_to_sids = None):
        results = []
        for container in self.docker_client.containers.list():
            if not container.name.startswith('openhands-runtime-'):
                continue
            conversation_id = container.name[len('openhands-runtime-'):]
            if filter_to_sids is not None and conversation_id not in filter_to_sids:
                continue
            nested_url = self.get_nested_url_for_container(container)
            agent_loop_info = AgentLoopInfo(
                conversation_id=conversation_id,
                url=nested_url,
                api_key=None,
                event_store=NestedEventStore(
                    base_url=nested_url,
                    sid=conversation_id,
                    user_id=user_id,
                ),
            )
            results.append(agent_loop_info)
        return results        


    @classmethod
    def get_instance(
        cls,
        sio: socketio.AsyncServer,
        config: AppConfig,
        file_store: FileStore,
        server_config: ServerConfig,
        monitoring_listener: MonitoringListener,
    ) -> ConversationManager:
        #return DockerNestedConversationManager(
        #    sio,
        #    config,
        #    file_store,
        #    server_config,
        #    monitoring_listener or MonitoringListener(),
        #)
        return DockerNestedConversationManager(
            sio=sio,
            config=config,
            server_config=server_config,
            file_store=file_store,
        )

    async def _get_conversation_store(self, user_id: str | None) -> ConversationStore:
        conversation_store_class = self._conversation_store_class
        if not conversation_store_class:
            self._conversation_store_class = conversation_store_class = get_impl(
                ConversationStore,  # type: ignore
                self.server_config.conversation_store_class,
            )
        store = await conversation_store_class.get_instance(self.config, user_id)
        return store
    
    def _get_nested_url(self, sid: str) -> str:
        container = self.docker_client.containers.get(f"openhands-runtime-{sid}")
        return self.get_nested_url_for_container(container)

    def get_nested_url_for_container(self, container: Container) -> str:
        env = container.attrs['Config']['Env']
        container_port = int(next(e[5:] for e in env if e.startswith('port=')))
        nested_url = f'{self.config.sandbox.local_runtime_url}:{container_port}'
        return nested_url


def _last_updated_at_key(conversation: ConversationMetadata) -> float:
    last_updated_at = conversation.last_updated_at
    if last_updated_at is None:
        return 0.0
    return last_updated_at.timestamp()
