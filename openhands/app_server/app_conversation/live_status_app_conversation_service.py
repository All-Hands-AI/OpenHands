import asyncio
import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from time import time
from typing import AsyncGenerator, Callable, Sequence
from uuid import UUID

import httpx
from fastapi import Depends
from pydantic import Field, TypeAdapter

from openhands.agent_server.models import (
    ConversationInfo,
    NeverConfirm,
    SendMessageRequest,
    StartConversationRequest,
)
from openhands.app_server.app_conversation.app_conversation_info_service import (
    AppConversationInfoService,
)
from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversation,
    AppConversationInfo,
    AppConversationPage,
    AppConversationSortOrder,
    AppConversationStartRequest,
    AppConversationStartTask,
    AppConversationStartTaskStatus,
)
from openhands.app_server.app_conversation.app_conversation_service import (
    AppConversationService,
    AppConversationServiceResolver,
)
from openhands.app_server.app_conversation.app_conversation_start_task_service import (
    AppConversationStartTaskService,
)
from openhands.app_server.dependency import get_dependency_resolver, get_httpx_client
from openhands.app_server.errors import AuthError, SandboxError
from openhands.app_server.sandbox.sandbox_models import (
    AGENT_SERVER,
    SandboxInfo,
    SandboxStatus,
)
from openhands.app_server.sandbox.sandbox_service import SandboxService
from openhands.app_server.user.user_service import UserService
from openhands.sdk import LocalWorkspace
from openhands.sdk.llm import LLM
from openhands.sdk.security.confirmation_policy import AlwaysConfirm
from openhands.tools.preset.default import get_default_agent

_conversation_info_type_adapter = TypeAdapter(list[ConversationInfo | None])
_logger = logging.getLogger(__name__)


@dataclass
class LiveStatusAppConversationService(AppConversationService):
    """AppConversationService which combines live status info from the sandbox with stored data."""

    user_service: UserService
    app_conversation_info_service: AppConversationInfoService
    app_conversation_start_task_service: AppConversationStartTaskService
    sandbox_service: SandboxService
    sandbox_startup_timeout: int
    sandbox_startup_poll_frequency: int
    httpx_client: httpx.AsyncClient

    async def search_app_conversations(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
        sort_order: AppConversationSortOrder = AppConversationSortOrder.CREATED_AT_DESC,
        page_id: str | None = None,
        limit: int = 20,
    ) -> AppConversationPage:
        """Search for sandboxed conversations."""
        page = await self.app_conversation_info_service.search_app_conversation_info(
            title__contains=title__contains,
            created_at__gte=created_at__gte,
            created_at__lt=created_at__lt,
            updated_at__gte=updated_at__gte,
            updated_at__lt=updated_at__lt,
            sort_order=sort_order,
            page_id=page_id,
            limit=limit,
        )
        conversations: list[AppConversation] = await self._build_app_conversations(
            page.items
        )  # type: ignore
        return AppConversationPage(items=conversations, next_page_id=page.next_page_id)

    async def count_app_conversations(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
    ) -> int:
        return await self.app_conversation_info_service.count_app_conversation_info(
            title__contains=title__contains,
            created_at__gte=created_at__gte,
            created_at__lt=created_at__lt,
            updated_at__gte=updated_at__gte,
            updated_at__lt=updated_at__lt,
        )

    async def get_app_conversation(
        self, conversation_id: UUID
    ) -> AppConversation | None:
        info = await self.app_conversation_info_service.get_app_conversation_info(
            conversation_id
        )
        result = await self._build_app_conversations([info])
        return result[0]

    async def batch_get_app_conversations(
        self, conversation_ids: list[UUID]
    ) -> list[AppConversation | None]:
        info = await self.app_conversation_info_service.batch_get_app_conversation_info(
            conversation_ids
        )
        conversations = await self._build_app_conversations(info)
        return conversations

    async def start_app_conversation(
        self, request: AppConversationStartRequest
    ) -> AsyncGenerator[AppConversationStartTask, None]:
        async for task in self._start_app_conversation(request):
            await self.app_conversation_start_task_service.save_app_conversation_start_task(
                task
            )
            yield task

    async def _start_app_conversation(
        self, request: AppConversationStartRequest
    ) -> AsyncGenerator[AppConversationStartTask, None]:
        # Create and yield the start task
        user = await self.user_service.get_current_user()
        task = AppConversationStartTask(
            user_id=user.id,
            request=request,
        )
        yield task

        try:
            async for updated_task in self._wait_for_sandbox_start(task):
                yield updated_task

            # Build the start request
            sandbox_id = task.sandbox_id
            assert sandbox_id is not None
            sandbox = await self.sandbox_service.get_sandbox(sandbox_id)
            assert sandbox is not None
            agent_server_url = self._get_agent_server_url(sandbox)
            start_conversation_request = (
                await self._build_start_conversation_request_for_user(
                    request.initial_message
                )
            )

            # update status
            task.status = AppConversationStartTaskStatus.STARTING_CONVERSATION
            task.agent_server_url = agent_server_url
            yield task

            # Start conversation...
            response = await self.httpx_client.post(
                f'{agent_server_url}/api/conversations',
                json=start_conversation_request.model_dump(
                    context={'expose_secrets': True}
                ),
                headers={'X-Session-API-Key': sandbox.session_api_key},
                timeout=self.sandbox_startup_timeout,
            )
            response.raise_for_status()
            info = ConversationInfo.model_validate(response.json())

            # Store info...
            user = await self.user_service.get_current_user()
            app_conversation_info = AppConversationInfo(
                id=info.id,
                title=f'Conversation {info.id}',
                sandbox_id=sandbox.id,
                user_id=user.id,
                llm_model=start_conversation_request.agent.llm.model,
                # TODO: Lots of git parameters required
            )
            await self.app_conversation_info_service.save_app_conversation_info(
                app_conversation_info
            )

            # Update the start task
            task.status = AppConversationStartTaskStatus.READY
            task.app_conversation_id = info.id
            yield task

        except Exception as exc:
            _logger.exception('Error starting conversation', stack_info=True)
            task.status = AppConversationStartTaskStatus.ERROR
            task.detail = str(exc)
            yield task

    async def batch_get_app_conversation_start_tasks(
        self, app_conversation_start_task_ids
    ):
        return await self.app_conversation_start_task_service.batch_get_app_conversation_start_tasks(
            app_conversation_start_task_ids
        )

    async def _build_app_conversations(
        self, app_conversation_infos: Sequence[AppConversationInfo | None]
    ) -> list[AppConversation | None]:
        sandbox_id_to_conversation_ids = self._get_sandbox_id_to_conversation_ids(
            app_conversation_infos
        )

        # Get referenced sandboxes in a single batch operation...
        sandboxes = await self.sandbox_service.batch_get_sandboxes(
            list(sandbox_id_to_conversation_ids)
        )
        sandboxes_by_id = {sandbox.id: sandbox for sandbox in sandboxes if sandbox}

        # Gather the running conversations
        tasks = [
            self._get_live_conversation_info(
                sandbox, sandbox_id_to_conversation_ids.get(sandbox.id)
            )
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

        # Build app_conversation from info
        result = [
            self._build_conversation(
                app_conversation_info,
                sandboxes_by_id.get(app_conversation_info.sandbox_id),
                conversation_info_by_id.get(app_conversation_info.id),
            )
            if app_conversation_info
            else None
            for app_conversation_info in app_conversation_infos
        ]

        return result

    async def _get_live_conversation_info(
        self,
        sandbox: SandboxInfo,
        conversation_ids: list[str],
    ) -> list[ConversationInfo]:
        """Get agent status for multiple conversations from the Agent Server."""
        try:
            # Build the URL with query parameters
            agent_server_url = self._get_agent_server_url(sandbox)
            url = f'{agent_server_url.rstrip("/")}/api/conversations'
            params = {'ids': conversation_ids}

            # Set up headers
            headers = {}
            if sandbox.session_api_key:
                headers['X-Session-API-Key'] = sandbox.session_api_key

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()

                data = response.json()
                conversation_info = _conversation_info_type_adapter.validate_python(
                    data
                )
                conversation_info = [c for c in conversation_info if c]
                return conversation_info
        except Exception:
            # Not getting a status is not a fatal error - we just mark the conversation as stopped
            _logger.exception(
                f'Error getting conversation status from sandbox {sandbox.id}',
                stack_info=True,
            )
            return []

    def _build_conversation(
        self,
        app_conversation_info: AppConversationInfo | None,
        sandbox: SandboxInfo | None,
        conversation_info: ConversationInfo | None,
    ) -> AppConversation | None:
        if app_conversation_info is None:
            return None
        sandbox_status = sandbox.status if sandbox else SandboxStatus.MISSING
        agent_status = conversation_info.agent_status if conversation_info else None
        conversation_url = None
        session_api_key = None
        if sandbox and sandbox.exposed_urls:
            conversation_url = next(
                (
                    exposed_url.url
                    for exposed_url in sandbox.exposed_urls
                    if exposed_url.name == AGENT_SERVER
                ),
                None,
            )
            if conversation_url:
                conversation_url += f'/api/conversations/{app_conversation_info.id.hex}'
            session_api_key = sandbox.session_api_key

        return AppConversation(
            **app_conversation_info.model_dump(),
            sandbox_status=sandbox_status,
            agent_status=agent_status,
            converation_url=conversation_url,
            session_api_key=session_api_key,
        )

    def _get_sandbox_id_to_conversation_ids(
        self, stored_conversations: Sequence[AppConversationInfo | None]
    ):
        result = defaultdict(list)
        for stored_conversation in stored_conversations:
            if stored_conversation:
                result[stored_conversation.sandbox_id].append(stored_conversation.id)
        return result

    async def _wait_for_sandbox_start(
        self, task: AppConversationStartTask
    ) -> AsyncGenerator[AppConversationStartTask, None]:
        """Wait for sandbox to start and return info."""

        # Get the sandbox
        if not task.sandbox_id:
            sandbox = await self.sandbox_service.start_sandbox()
            task.sandbox_id = sandbox.id
        else:
            sandbox_info = await self.sandbox_service.get_sandbox(task.sandbox_id)
            if sandbox_info is None:
                raise SandboxError(f'Sandbox not found: {task.sandbox_id}')
            sandbox = sandbox_info

        # Update the listener
        task.status = AppConversationStartTaskStatus.WAITING_FOR_SANDBOX
        task.sandbox_id = sandbox.id
        yield task

        if sandbox.status == SandboxStatus.PAUSED:
            await self.sandbox_service.resume_sandbox(sandbox.id)
        if sandbox.status in (None, SandboxStatus.ERROR):
            raise SandboxError(f'Sandbox status: {sandbox.status}')
        if sandbox.status not in (SandboxStatus.STARTING, SandboxStatus.RUNNING):
            raise SandboxError(f'Sandbox not startable: {sandbox.id}')

        start = time()
        while time() - start <= self.sandbox_startup_timeout:
            await asyncio.sleep(self.sandbox_startup_poll_frequency)
            sandbox_info = await self.sandbox_service.get_sandbox(sandbox.id)
            if sandbox_info is None:
                raise SandboxError(f'Sandbox not found: {sandbox.id}')
            if sandbox.status not in (SandboxStatus.STARTING, SandboxStatus.RUNNING):
                raise SandboxError(f'Sandbox not startable: {sandbox.id}')
            if sandbox_info.status == SandboxStatus.RUNNING:
                return
        raise SandboxError(f'Sandbox failed to start: {sandbox.id}')

    def _get_agent_server_url(self, sandbox: SandboxInfo) -> str:
        """Get agent server url for running sandbox."""
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
        if user is None:
            raise AuthError()

        # Hack - because the workspace tries to create the dir on post init
        # we create one in cwd then set it afterwards
        workspace = LocalWorkspace(working_dir=os.getcwd())
        workspace.working_dir = '/home/openhands/workspace'

        llm = LLM(
            model=user.llm_model,
            base_url=user.llm_base_url,
            api_key=user.llm_api_key,
            service_id='agent',
        )
        agent = get_default_agent(llm=llm)
        start_conversation_request = StartConversationRequest(
            agent=agent,
            workspace=workspace,
            confirmation_policy=AlwaysConfirm()
            if user.confirmation_mode
            else NeverConfirm(),
            initial_message=initial_message,
        )
        return start_conversation_request


class LiveStatusAppConversationServiceResolver(AppConversationServiceResolver):
    sandbox_startup_timeout: int = Field(
        default=120, description='The max timeout time for sandbox startup'
    )
    sandbox_startup_poll_frequency: int = Field(
        default=2, description='The frequency to poll for sandbox readiness'
    )

    def get_resolver_for_user(self) -> Callable:
        user_service_resolver = get_dependency_resolver().user.get_resolver_for_user()
        sandbox_service_resolver = (
            get_dependency_resolver().sandbox.get_resolver_for_user()
        )
        sandbox_conversation_info_service_resolver = (
            get_dependency_resolver().app_conversation_info.get_resolver_for_user()
        )
        sandbox_conversation_start_task_service_resolver = get_dependency_resolver().app_conversation_start_task.get_resolver_for_user()

        def _resolve_for_user(
            user_service: UserService = Depends(user_service_resolver),
            sandbox_service: SandboxService = Depends(sandbox_service_resolver),
            app_conversation_info_service=Depends(
                sandbox_conversation_info_service_resolver
            ),
            app_conversation_start_task_service=Depends(
                sandbox_conversation_start_task_service_resolver
            ),
            httpx_client: httpx.AsyncClient = Depends(get_httpx_client),
        ) -> AppConversationService:
            return LiveStatusAppConversationService(
                user_service=user_service,
                sandbox_service=sandbox_service,
                app_conversation_info_service=app_conversation_info_service,
                app_conversation_start_task_service=app_conversation_start_task_service,
                sandbox_startup_timeout=self.sandbox_startup_timeout,
                sandbox_startup_poll_frequency=self.sandbox_startup_poll_frequency,
                httpx_client=httpx_client,
            )

        return _resolve_for_user
