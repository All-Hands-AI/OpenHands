import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from time import time
from typing import AsyncGenerator, Sequence
from uuid import UUID, uuid4

import httpx
from fastapi import Request
from pydantic import Field, SecretStr, TypeAdapter

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
    AppConversationServiceInjector,
)
from openhands.app_server.app_conversation.app_conversation_start_task_service import (
    AppConversationStartTaskService,
)
from openhands.app_server.app_conversation.git_app_conversation_service import (
    GitAppConversationService,
)
from openhands.app_server.errors import SandboxError
from openhands.app_server.sandbox.docker_sandbox_service import DockerSandboxService
from openhands.app_server.sandbox.sandbox_models import (
    AGENT_SERVER,
    SandboxInfo,
    SandboxStatus,
)
from openhands.app_server.sandbox.sandbox_service import SandboxService
from openhands.app_server.sandbox.sandbox_spec_service import SandboxSpecService
from openhands.app_server.services.injector import InjectorState
from openhands.app_server.services.jwt_service import JwtService
from openhands.app_server.user.user_context import UserContext
from openhands.experiments.experiment_manager import ExperimentManagerImpl
from openhands.integrations.provider import ProviderType
from openhands.sdk import LocalWorkspace
from openhands.sdk.conversation.secret_source import LookupSecret, StaticSecret
from openhands.sdk.llm import LLM
from openhands.sdk.security.confirmation_policy import AlwaysConfirm
from openhands.sdk.workspace.remote.async_remote_workspace import AsyncRemoteWorkspace
from openhands.tools.preset.default import get_default_agent

_conversation_info_type_adapter = TypeAdapter(list[ConversationInfo | None])
_logger = logging.getLogger(__name__)
GIT_TOKEN = 'GIT_TOKEN'


@dataclass
class LiveStatusAppConversationService(GitAppConversationService):
    """AppConversationService which combines live status info from the sandbox with stored data."""

    user_context: UserContext
    app_conversation_info_service: AppConversationInfoService
    app_conversation_start_task_service: AppConversationStartTaskService
    sandbox_service: SandboxService
    sandbox_spec_service: SandboxSpecService
    jwt_service: JwtService
    sandbox_startup_timeout: int
    sandbox_startup_poll_frequency: int
    httpx_client: httpx.AsyncClient
    web_url: str | None
    access_token_hard_timeout: timedelta | None

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
        user_id = await self.user_context.get_user_id()
        task = AppConversationStartTask(
            created_by_user_id=user_id,
            request=request,
        )
        yield task

        try:
            async for updated_task in self._wait_for_sandbox_start(task):
                yield updated_task

            # Get the sandbox
            sandbox_id = task.sandbox_id
            assert sandbox_id is not None
            sandbox = await self.sandbox_service.get_sandbox(sandbox_id)
            assert sandbox is not None
            agent_server_url = self._get_agent_server_url(sandbox)

            # Get the working dir
            sandbox_spec = await self.sandbox_spec_service.get_sandbox_spec(
                sandbox.sandbox_spec_id
            )
            assert sandbox_spec is not None

            # Run setup scripts
            workspace = AsyncRemoteWorkspace(
                host=agent_server_url, api_key=sandbox.session_api_key
            )
            async for updated_task in self.run_setup_scripts(
                task, workspace, sandbox_spec.working_dir
            ):
                yield updated_task

            # Build the start request
            start_conversation_request = (
                await self._build_start_conversation_request_for_user(
                    request.initial_message,
                    request.git_provider,
                    sandbox_spec.working_dir,
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
                    mode='json', context={'expose_secrets': True}
                ),
                headers={'X-Session-API-Key': sandbox.session_api_key},
                timeout=self.sandbox_startup_timeout,
            )
            response.raise_for_status()
            info = ConversationInfo.model_validate(response.json())

            # Store info...
            user_id = await self.user_context.get_user_id()
            app_conversation_info = AppConversationInfo(
                id=info.id,
                # TODO: As of writing, StartConversationRequest from AgentServer does not have a title
                title=f'Conversation {info.id}',
                sandbox_id=sandbox.id,
                created_by_user_id=user_id,
                llm_model=start_conversation_request.agent.llm.model,
                # Git parameters
                selected_repository=request.selected_repository,
                selected_branch=request.selected_branch,
                git_provider=request.git_provider,
                trigger=request.trigger,
                pr_number=request.pr_number,
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
            (
                self._build_conversation(
                    app_conversation_info,
                    sandboxes_by_id.get(app_conversation_info.sandbox_id),
                    conversation_info_by_id.get(app_conversation_info.id),
                )
                if app_conversation_info
                else None
            )
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

            response = await self.httpx_client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()
            conversation_info = _conversation_info_type_adapter.validate_python(data)
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
            conversation_url=conversation_url,
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
        if not task.request.sandbox_id:
            sandbox = await self.sandbox_service.start_sandbox()
            task.sandbox_id = sandbox.id
        else:
            sandbox_info = await self.sandbox_service.get_sandbox(
                task.request.sandbox_id
            )
            if sandbox_info is None:
                raise SandboxError(f'Sandbox not found: {task.request.sandbox_id}')
            sandbox = sandbox_info

        # Update the listener
        task.status = AppConversationStartTaskStatus.WAITING_FOR_SANDBOX
        task.sandbox_id = sandbox.id
        yield task

        if sandbox.status == SandboxStatus.PAUSED:
            await self.sandbox_service.resume_sandbox(sandbox.id)
        if sandbox.status in (None, SandboxStatus.ERROR):
            raise SandboxError(f'Sandbox status: {sandbox.status}')
        if sandbox.status == SandboxStatus.RUNNING:
            return
        if sandbox.status != SandboxStatus.STARTING:
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
        self,
        initial_message: SendMessageRequest | None,
        git_provider: ProviderType | None,
        working_dir: str,
    ) -> StartConversationRequest:
        user = await self.user_context.get_user_info()

        # Set up a secret for the git token
        secrets = await self.user_context.get_secrets()
        if git_provider:
            if self.web_url:
                # If there is a web url, then we create an access token to access it.
                # For security reasons, we are explicit here - only this user, and
                # only this provider, with a timeout
                access_token = self.jwt_service.create_jws_token(
                    payload={
                        'user_id': user.id,
                        'provider_type': git_provider.value,
                    },
                    expires_in=self.access_token_hard_timeout,
                )
                secrets[GIT_TOKEN] = LookupSecret(
                    url=self.web_url + '/ap/v1/webhooks/secrets',
                    headers={'X-Access-Token': access_token},
                )
            else:
                # If there is no URL specified where the sandbox can access the app server
                # then we supply a static secret with the most recent value. Depending
                # on the type, this may eventually expire.
                static_token = await self.user_context.get_latest_token(git_provider)
                if static_token:
                    secrets[GIT_TOKEN] = StaticSecret(value=SecretStr(static_token))

        workspace = LocalWorkspace(working_dir=working_dir)

        llm = LLM(
            model=user.llm_model,
            base_url=user.llm_base_url,
            api_key=user.llm_api_key,
            usage_id='agent',
        )
        agent = get_default_agent(llm=llm)

        conversation_id = uuid4()
        agent = ExperimentManagerImpl.run_agent_variant_tests__v1(
            user.id, conversation_id, agent
        )

        start_conversation_request = StartConversationRequest(
            conversation_id=conversation_id,
            agent=agent,
            workspace=workspace,
            confirmation_policy=(
                AlwaysConfirm() if user.confirmation_mode else NeverConfirm()
            ),
            initial_message=initial_message,
            secrets=secrets,
        )
        return start_conversation_request

    async def update_agent_server_conversation_title(
        self,
        conversation_id: str,
        new_title: str,
        app_conversation_info: AppConversationInfo,
    ) -> None:
        """Update the conversation title in the agent-server.

        Args:
            conversation_id: The conversation ID as a string
            new_title: The new title to set
            app_conversation_info: The app conversation info containing sandbox_id
        """
        # Get the sandbox info to find the agent-server URL
        sandbox = await self.sandbox_service.get_sandbox(
            app_conversation_info.sandbox_id
        )
        assert sandbox is not None, (
            f'Sandbox {app_conversation_info.sandbox_id} not found for conversation {conversation_id}'
        )
        assert sandbox.exposed_urls is not None, (
            f'Sandbox {app_conversation_info.sandbox_id} has no exposed URLs for conversation {conversation_id}'
        )

        # Use the existing method to get the agent-server URL
        agent_server_url = self._get_agent_server_url(sandbox)

        # Prepare the request
        url = f'{agent_server_url.rstrip("/")}/api/conversations/{conversation_id}'
        headers = {}
        if sandbox.session_api_key:
            headers['X-Session-API-Key'] = sandbox.session_api_key

        payload = {'title': new_title}

        # Make the PATCH request to the agent-server
        response = await self.httpx_client.patch(
            url,
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()

        _logger.info(
            f'Successfully updated agent-server conversation {conversation_id} title to "{new_title}"'
        )


class LiveStatusAppConversationServiceInjector(AppConversationServiceInjector):
    sandbox_startup_timeout: int = Field(
        default=120, description='The max timeout time for sandbox startup'
    )
    sandbox_startup_poll_frequency: int = Field(
        default=2, description='The frequency to poll for sandbox readiness'
    )
    init_git_in_empty_workspace: bool = Field(
        default=True,
        description='Whether to initialize a git repo when the workspace is empty',
    )
    access_token_hard_timeout: int | None = Field(
        default=14 * 86400,
        description=(
            'A security measure - the time after which git tokens may no longer '
            'be retrieved by a sandboxed conversation.'
        ),
    )

    async def inject(
        self, state: InjectorState, request: Request | None = None
    ) -> AsyncGenerator[AppConversationService, None]:
        from openhands.app_server.config import (
            get_app_conversation_info_service,
            get_app_conversation_start_task_service,
            get_global_config,
            get_httpx_client,
            get_jwt_service,
            get_sandbox_service,
            get_sandbox_spec_service,
            get_user_context,
        )

        async with (
            get_user_context(state, request) as user_context,
            get_sandbox_service(state, request) as sandbox_service,
            get_sandbox_spec_service(state, request) as sandbox_spec_service,
            get_app_conversation_info_service(
                state, request
            ) as app_conversation_info_service,
            get_app_conversation_start_task_service(
                state, request
            ) as app_conversation_start_task_service,
            get_jwt_service(state, request) as jwt_service,
            get_httpx_client(state, request) as httpx_client,
        ):
            access_token_hard_timeout = None
            if self.access_token_hard_timeout:
                access_token_hard_timeout = timedelta(
                    seconds=float(self.access_token_hard_timeout)
                )
            config = get_global_config()

            # If no web url has been set and we are using docker, we can use host.docker.internal
            web_url = config.web_url
            if web_url is None:
                if isinstance(sandbox_service, DockerSandboxService):
                    web_url = f'http://host.docker.internal:{sandbox_service.host_port}'

            yield LiveStatusAppConversationService(
                init_git_in_empty_workspace=self.init_git_in_empty_workspace,
                user_context=user_context,
                sandbox_service=sandbox_service,
                sandbox_spec_service=sandbox_spec_service,
                app_conversation_info_service=app_conversation_info_service,
                app_conversation_start_task_service=app_conversation_start_task_service,
                jwt_service=jwt_service,
                sandbox_startup_timeout=self.sandbox_startup_timeout,
                sandbox_startup_poll_frequency=self.sandbox_startup_poll_frequency,
                httpx_client=httpx_client,
                web_url=web_url,
                access_token_hard_timeout=access_token_hard_timeout,
            )
