from abc import ABC
import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from time import time
from typing import Callable
from uuid import UUID

from fastapi import Depends
import httpx
from openhands.agent_server.models import ConversationInfo, SendMessageRequest, StartConversationRequest, StoredConversation, ConversationPage
from openhands.sdk.conversation.state import AgentExecutionStatus
from openhands.sdk.llm import LLM
from openhands.tools.preset.default import get_default_agent
from pydantic import Field, TypeAdapter

from openhands.app_server.conversation.sandboxed_conversation_info_service import SandboxedConversationInfoService
from openhands.app_server.conversation.conversation_models import SandboxedConversation, SandboxedConversationInfo, SandboxedConversationPage, StartSandboxedConversationRequest
from openhands.app_server.dependency import get_dependency_resolver, get_httpx_client
from openhands.app_server.errors import SandboxError
from openhands.app_server.sandbox.sandbox_models import AGENT_SERVER, SandboxInfo, SandboxStatus
from openhands.app_server.sandbox.sandbox_service import SandboxService
from openhands.app_server.conversation.sandboxed_conversation_service import SandboxedConversationService, SandboxedConversationServiceResolver
from openhands.app_server.user.user_service import UserService

_conversation_info_type_adapter = TypeAdapter(list[ConversationInfo | None])


@dataclass
class LiveStatusSandboxedConversationService(SandboxedConversationService):
    """SandboxedConversationService which combines live status info with stored data.
    """
    user_service: UserService
    sandboxed_conversation_info_service: SandboxedConversationInfoService
    sandbox_service: SandboxService
    sandbox_startup_timeout: int
    sandbox_startup_poll_frequency: int
    httpx_client: httpx.AsyncClient

    async def search_sandboxed_conversations(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
        page_id: str | None = None,
        limit: int = 20,
    ) -> SandboxedConversationPage:
        """Search for sandboxed conversations."""
        page = await self.sandboxed_conversation_info_service.search_sandboxed_conversation_info(
            title__contains=title__contains,
            created_at__gte=created_at__gte,
            created_at__lt=created_at__lt,
            updated_at__gte=updated_at__gte,
            updated_at__lt=updated_at__lt,
            page_id=page_id,
            limit=limit,
        )
        conversations = await self._build_sandboxed_conversations(page.items) # type: ignore
        return ConversationPage(conversations, page.next_page_id)

    async def count_sandboxed_conversations(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
    ) -> int:
        return await self.sandboxed_conversation_info_service.count_sandboxed_conversation_info(
            title__contains=title__contains,
            created_at__gte=created_at__gte,
            created_at__lt=created_at__lt,
            updated_at__gte=updated_at__gte,
            updated_at__lt=updated_at__lt,
        )

    async def get_sandboxed_conversation(
        self, conversation_id: UUID
    ) -> SandboxedConversation | None:
        info = await self.sandboxed_conversation_info_service.get_sandboxed_conversation_info(conversation_id)
        result = await self._build_sandboxed_conversations([info])
        return result[0]

    async def batch_get_sandboxed_conversations(
        self, conversation_ids: list[UUID]
    ) -> list[SandboxedConversation | None]:
        info = await self.sandboxed_conversation_info_service.batch_get_sandboxed_conversation_info(conversation_ids)
        conversations = await self._build_sandboxed_conversations(info)
        return conversations

    async def start_sandboxed_conversation(
        self, request: StartSandboxedConversationRequest
    ) -> SandboxedConversation:
        """Start a conversation, optionally specifying a sandbox in which to start. If
        no sandbox is specified a default may be used or started. This is a convenience
        method - the same effect should be achievable by creating / getting a sandbox
        id, starting a conversation, attaching a callback, and then running the
        conversation.
        """
        sandbox = await self._wait_for_sandbox_start(request.sandbox_id)
        agent_server_url = self._get_agent_server_url(sandbox)
        start_conversation_request = (
            await self._build_start_conversation_request_for_user(
                request.initial_message
            )
        )

        # Start conversation...
        response = await self.httpx_client.post(
            f"{agent_server_url}/conversations",
            json=start_conversation_request.model_dump(),
            headers={"X-Session-API-Key": sandbox.session_api_key},
        )
        response.raise_for_status()
        info = ConversationInfo.model_validate(response.json())

        # Store info...
        #TODO: many fields to fill in here...
        sandboxed_conversation_info = SandboxedConversationInfo(
            id=info.id, title=f"Conversation {info.id}", sandbox_id=sandbox.id
        )
        await self.sandboxed_conversation_info_service.save_sandboxed_conversation_info(sandboxed_conversation_info)

        return SandboxedConversation(
            **sandboxed_conversation_info.model_dump(),
            sandbox_status=sandbox.status,
            agent_status=AgentExecutionStatus.RUNNING,  #TODO: We don't seem to have a STARTING status yet
        )

    async def _build_sandboxed_conversations(self, sandboxed_conversation_infos: list[SandboxedConversationInfo | None]) -> list[SandboxedConversation | None]:
        sandbox_id_to_conversation_ids = self._get_sandbox_id_to_conversation_ids(sandboxed_conversation_infos)

        # Get referenced sandboxes in a single batch operation...
        sandboxes = await self.sandbox_service.batch_get_sandboxes(list(sandbox_id_to_conversation_ids))
        sandboxes_by_id = {sandbox.id: sandbox for sandbox in sandboxes if sandbox}

        # Gather the running conversations
        tasks = [
            self._get_live_conversation_info(sandbox, sandbox_id_to_conversation_ids[sandbox.id])
            for sandbox in sandboxes
            if sandbox and sandbox.status == SandboxStatus.RUNNING
        ]
        if tasks:
            sandbox_conversation_infos = await asyncio.gather(*tasks)
        else:
            sandbox_conversation_infos = []

        # Collect the results into a single dictionary
        conversation_info_by_id = {}
        for conversation_infos in sandbox_conversation_infos:
            for conversation_info in conversation_infos:
                conversation_info_by_id[conversation_info.id] = conversation_info

        # Build sandboxed_conversation from info
        result = [
            self._build_conversation(sandboxed_conversation_info, sandboxes_by_id.get(sandboxed_conversation_info.sandbox_id), conversation_info_by_id.get(sandboxed_conversation_info.id)) if sandboxed_conversation_info else None
            for sandboxed_conversation_info in sandboxed_conversation_infos
        ]

        return result

    async def _get_live_conversation_info(
        self,
        sandbox: SandboxInfo,
        conversation_ids: list[str],
    ) -> list[ConversationInfo]:
        """Get agent status for multiple conversations from the Agent Server."""
        # Build the URL with query parameters
        agent_server_url = self._get_agent_server_url(sandbox)
        url = f"{agent_server_url.rstrip('/')}/conversations"
        params = {"ids": conversation_ids}

        # Set up headers
        headers = {}
        if sandbox.session_api_key:
            headers["X-Session-API-Key"] = sandbox.session_api_key

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()
            conversation_info = _conversation_info_type_adapter.validate_python(
                data
            )
            conversation_info = [c for c in conversation_info if c]
            return conversation_info

    def _build_conversation(self, sandboxed_conversation_info: SandboxedConversationInfo | None, sandbox: SandboxInfo | None, conversation_info: ConversationInfo | None) -> SandboxedConversation | None:
        if sandboxed_conversation_info is None:
            return None
        sandbox_status = sandbox.status if sandbox else SandboxStatus.ERROR # TODO: Maybe it was deleted?
        agent_status = conversation_info.agent_status if conversation_info else None
        return SandboxedConversation(
            **sandboxed_conversation_info.model_dump(),
            sandbox_status=sandbox_status,
            agent_status=agent_status,
        )

    def _get_sandbox_id_to_conversation_ids(self, stored_conversations: list[SandboxedConversationInfo | None]):
        result = defaultdict(list)
        for stored_conversation in stored_conversations:
            if stored_conversation:
                result[stored_conversation.sandbox_id].append(stored_conversation.id)
        return result


    async def _wait_for_sandbox_start(self, sandbox_id: str | None) -> SandboxInfo:
        """Wait for sandbox to start and return info"""
        sandbox_service = self.sandbox_service
        if not sandbox_id:
            sandbox = await sandbox_service.start_sandbox()
            sandbox_id = sandbox.id
        else:
            sandbox_info = await sandbox_service.get_sandbox(sandbox_id)
            if sandbox_info is None:
                raise SandboxError(f"Sandbox not found: {sandbox_id}")
            sandbox = sandbox_info

        if sandbox.status == SandboxStatus.PAUSED:
            await sandbox_service.resume_sandbox(sandbox_id)
        if sandbox.status in (SandboxStatus.DELETED, SandboxStatus.ERROR):
            raise SandboxError(f"Sandbox status: {sandbox.status}")
        if sandbox.status == SandboxStatus.RUNNING:
            return sandbox

        start = time()
        while time() - start <= self.sandbox_startup_timeout:
            await asyncio.sleep(self.sandbox_startup_poll_frequency)
            sandbox_info = await sandbox_service.get_sandbox(sandbox_id)
            if sandbox_info is None:
                raise SandboxError(f"Sandbox not found: {sandbox_id}")
            if sandbox_info.status == SandboxStatus.RUNNING:
                return sandbox_info
        raise SandboxError(f"Sandbox failed to start: {sandbox_id}")

    def _get_agent_server_url(self, sandbox: SandboxInfo) -> str:
        """Get agent server url for running sandbox"""
        exposed_urls = sandbox.exposed_urls
        assert exposed_urls is not None
        agent_server_url = next(
            exposed_url.url
            for exposed_url in exposed_urls
            if exposed_url.name == AGENT_SERVER
        )
        return agent_server_url

    async def _build_start_conversation_request_for_user(
        self, initial_message: SendMessageRequest | None
    ) -> StartConversationRequest:
        user = await self.user_service.get_current_user()

        llm = LLM(
            model=user.llm_model,
            base_url=user.llm_base_url,
            api_key=user.llm_api_key,
            service_id="agent",
        )
        agent = get_default_agent(llm=llm, working_dir="/workspace")
        start_conversation_request = StartConversationRequest(
            agent=agent,
            # confirmation_policy=NeverConfirm(), # TODO: Add this to user
            initial_message=initial_message,
        )
        return start_conversation_request


class LiveStatusSandboxedConversationServiceResolver(SandboxedConversationServiceResolver):
    sandbox_startup_timeout: int = Field(
        default=120, description="The max timeout time for sandbox startup"
    )
    sandbox_startup_poll_frequency: int = Field(
        default=2, description="The frequency to poll for sandbox readiness"
    )

    def get_resolver_for_user(self) -> Callable:
        user_service_resolver = (
            get_dependency_resolver().user.get_resolver_for_user()
        )
        sandbox_service_resolver = (
            get_dependency_resolver().sandbox.get_resolver_for_user()
        )
        sandbox_conversation_info_service_resolver = (
            get_dependency_resolver().sandbox_conversation_info.get_resolver_for_user()
        )

        def _resolve_for_user(
            user_service: UserService = Depends(user_service_resolver),
            sandbox_service: SandboxService = Depends(sandbox_service_resolver),
            sandboxed_conversation_info_service = Depends(sandbox_conversation_info_service_resolver),
            httpx_client: httpx.AsyncClient = Depends(get_httpx_client),
        ) -> SandboxedConversationService:
            return LiveStatusSandboxedConversationService(user_service=user_service, sandbox_service=sandbox_service, sandboxed_conversation_info_service=sandboxed_conversation_info_service, sandbox_startup_timeout=self.sandbox_startup_timeout, sandbox_startup_poll_frequency=self.sandbox_startup_poll_frequency, httpx_client=httpx_client)

        return _resolve_for_user
