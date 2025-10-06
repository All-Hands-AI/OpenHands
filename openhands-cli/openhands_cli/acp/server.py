"""OpenHands Agent Client Protocol (ACP) server implementation."""

import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Any
from uuid import UUID

from acp import (
    Agent as ACPAgent,
)
from acp import (
    AgentSideConnection,
    InitializeRequest,
    InitializeResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    SessionNotification,
    stdio_streams,
)
from acp.schema import (
    AgentCapabilities,
    AuthenticateRequest,
    AuthenticateResponse,
    AuthMethod,
    CancelNotification,
    ContentBlock1,
    LoadSessionRequest,
    McpCapabilities,
    McpServer1,
    McpServer2,
    McpServer3,
    PromptCapabilities,
    SessionUpdate1,
    SessionUpdate2,
    SetSessionModeRequest,
    SetSessionModeResponse,
)
from openhands.sdk import (
    Agent,
    Conversation,
    Message,
    TextContent,
    Workspace,
)
from openhands.sdk.event.llm_convertible.message import MessageEvent
from openhands.sdk.llm import LLM
from openhands.sdk.security.llm_analyzer import LLMSecurityAnalyzer
from openhands.tools.preset.default import (
    get_default_agent,
    get_default_condenser,
    get_default_tools,
)

from openhands_cli.commands import (
    format_help_text,
    get_acp_available_commands,
    is_slash_command,
    parse_slash_command,
)

from .events import EventSubscriber

logger = logging.getLogger(__name__)


def convert_acp_mcp_servers_to_openhands_config(
    acp_mcp_servers: list[McpServer1 | McpServer2 | McpServer3],
) -> dict[str, Any]:
    """Convert ACP MCP server configurations to OpenHands agent mcp_config format.

    Args:
        acp_mcp_servers: List of ACP MCP server configurations

    Returns:
        Dictionary in OpenHands mcp_config format
    """
    mcp_servers = {}

    for server in acp_mcp_servers:
        if isinstance(server, McpServer3):
            # Command-line executable MCP server (supported by OpenHands)
            mcp_servers[server.name] = {
                "command": server.command,
                "args": server.args,
            }
            # Add environment variables if provided
            if server.env:
                env_dict = {env_var.name: env_var.value for env_var in server.env}
                mcp_servers[server.name]["env"] = env_dict
        elif isinstance(server, McpServer1 | McpServer2):
            # HTTP/SSE MCP servers - not directly supported by OpenHands yet
            # Log a warning for now
            server_type = "HTTP" if isinstance(server, McpServer1) else "SSE"
            logger.warning(
                f"MCP server '{server.name}' uses {server_type} transport "
                f"which is not yet supported by OpenHands. Skipping."
            )
            continue

    return {"mcpServers": mcp_servers} if mcp_servers else {}


class OpenHandsACPAgent(ACPAgent):
    """OpenHands Agent Client Protocol implementation."""

    def __init__(self, conn: AgentSideConnection, persistence_dir: Path | None = None):
        """Initialize the OpenHands ACP agent.

        Args:
            conn: ACP connection for sending notifications
            persistence_dir: Directory for storing conversation data
        """
        self._conn = conn

        # Use same persistence directory as CLI if not specified
        if persistence_dir is None:
            from openhands_cli.locations import CONVERSATIONS_DIR

            os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
            self._persistence_dir = Path(CONVERSATIONS_DIR)
        else:
            self._persistence_dir = Path(persistence_dir)
            self._persistence_dir.mkdir(parents=True, exist_ok=True)

        # Session management: session_id -> Conversation instance
        self._sessions: dict[str, Conversation] = {}
        self._llm_params: dict[str, Any] = {}  # Store LLM parameters from auth

        logger.info(
            f"OpenHands ACP Agent initialized with persistence_dir: "
            f"{self._persistence_dir}"
        )

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:
        """Initialize the ACP protocol."""
        logger.info(f"Initializing ACP with protocol version: {params.protocolVersion}")

        # Check if we have API keys available from environment
        has_api_key = bool(
            os.getenv("OPENAI_API_KEY")
            or os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("LITELLM_API_KEY")
        )

        # Only require authentication if no API key is available
        auth_methods = []
        if not has_api_key:
            auth_methods = [
                AuthMethod(
                    id="llm_config",
                    name="LLM Configuration",
                    description=(
                        "Configure LLM settings including model, API key, "
                        "and other parameters"
                    ),
                )
            ]
            logger.info("No API key found in environment, requiring authentication")
        else:
            logger.info("API key found in environment, authentication not required")

        return InitializeResponse(
            protocolVersion=params.protocolVersion,
            authMethods=auth_methods,
            agentCapabilities=AgentCapabilities(
                loadSession=True,
                mcpCapabilities=McpCapabilities(http=True, sse=True),
                promptCapabilities=PromptCapabilities(
                    audio=False,
                    embeddedContext=False,
                    image=False,
                ),
            ),
        )

    async def authenticate(
        self, params: AuthenticateRequest
    ) -> AuthenticateResponse | None:
        """Authenticate the client and configure LLM settings."""
        logger.info(f"Authentication requested with method: {params.methodId}")

        if params.methodId == "llm_config":
            # Extract LLM configuration from the _meta field
            if params.field_meta:
                self._llm_params = params.field_meta
                logger.info("Received LLM configuration via authentication")
                logger.info(f"LLM parameters stored: {list(self._llm_params.keys())}")
            else:
                logger.warning("No LLM configuration provided in authentication")

            return AuthenticateResponse()
        else:
            logger.error(f"Unsupported authentication method: {params.methodId}")
            return None

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())

        try:
            # Create a properly configured agent for the conversation
            logger.info(f"Creating LLM with params: {list(self._llm_params.keys())}")

            # Create LLM with provided parameters or defaults
            llm_kwargs = {}
            if self._llm_params:
                # Use authenticated parameters
                llm_kwargs.update(self._llm_params)
            else:
                # Use environment defaults
                api_key = os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY")
                if api_key:
                    llm_kwargs["api_key"] = api_key
                    if os.getenv("LITELLM_API_KEY"):
                        llm_kwargs.update(
                            {
                                "model": (
                                    "litellm_proxy/anthropic/claude-sonnet-4-5-20250929"
                                ),
                                "base_url": "https://llm-proxy.eval.all-hands.dev",
                                "drop_params": True,
                            }
                        )
                    else:
                        llm_kwargs["model"] = "gpt-4o-mini"
                else:
                    logger.warning("No API key found. Using dummy key.")
                    llm_kwargs["api_key"] = "dummy-key"
                    llm_kwargs["model"] = "gpt-4o-mini"

            # Add required service_id
            llm_kwargs["service_id"] = "acp-agent"

            llm = LLM(**llm_kwargs)
            logger.info(f"Created LLM with model: {llm.model}")

            logger.info("Creating agent with MCP configuration")

            # Process MCP servers from the request
            mcp_config = {}
            if params.mcpServers:
                logger.info(
                    f"Processing {len(params.mcpServers)} MCP servers from request"
                )
                client_mcp_config = convert_acp_mcp_servers_to_openhands_config(
                    params.mcpServers
                )
                if client_mcp_config:
                    mcp_config.update(client_mcp_config)
                    server_names = list(client_mcp_config.get("mcpServers", {}).keys())
                    logger.info(f"Added client MCP servers: {server_names}")

            # Get default agent with custom MCP config if provided
            if mcp_config:
                # Create custom agent with MCP config
                tool_specs = get_default_tools(enable_browser=False)  # CLI mode
                agent = Agent(
                    llm=llm,
                    tools=tool_specs,
                    mcp_config=mcp_config,
                    filter_tools_regex="^(?!repomix)(.*)|^repomix.*pack_codebase.*$",
                    system_prompt_kwargs={"cli_mode": True},
                    condenser=get_default_condenser(
                        llm=llm.model_copy(update={"service_id": "condenser"})
                    ),
                    security_analyzer=LLMSecurityAnalyzer(),
                )
                server_names = list(mcp_config.get("mcpServers", {}).keys())
                logger.info(f"Created custom agent with MCP servers: {server_names}")
            else:
                # Use default agent
                agent = get_default_agent(llm=llm, cli_mode=True)
                logger.info("Created default agent with built-in MCP servers")

            # Validate working directory
            working_dir = params.cwd or str(Path.cwd())
            working_path = Path(working_dir)

            logger.info(f"Using working directory: {working_dir}")

            # Create directory if it doesn't exist
            if not working_path.exists():
                logger.warning(
                    f"Working directory {working_dir} doesn't exist, creating it"
                )
                working_path.mkdir(parents=True, exist_ok=True)

            if not working_path.is_dir():
                raise ValueError(
                    f"Working directory path is not a directory: {working_dir}"
                )

            # Create workspace
            workspace = Workspace(working_dir=str(working_path))

            # Create conversation directly using SDK
            conversation = Conversation(
                agent=agent,
                workspace=workspace,
                persistence_dir=self._persistence_dir,
                conversation_id=UUID(session_id),
            )

            # Store conversation
            self._sessions[session_id] = conversation

            logger.info(
                f"Created new session {session_id} with conversation {conversation.id}"
            )

            # Send available commands notification
            await self._send_available_commands(session_id)

            return NewSessionResponse(sessionId=session_id)

        except Exception as e:
            logger.error(f"Failed to create new session: {e}", exc_info=True)
            raise

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        """Handle a prompt request."""
        session_id = params.sessionId

        if session_id not in self._sessions:
            raise ValueError(f"Unknown session: {session_id}")

        conversation = self._sessions[session_id]

        # Extract text from prompt - handle both string and array formats
        prompt_text = ""
        if isinstance(params.prompt, str):
            prompt_text = params.prompt
        elif isinstance(params.prompt, list):
            for block in params.prompt:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        prompt_text += block.get("text", "")
                else:
                    # Handle ContentBlock objects
                    if hasattr(block, "type") and block.type == "text":
                        prompt_text += getattr(block, "text", "")
        else:
            # Handle single ContentBlock object
            if hasattr(params.prompt, "type") and params.prompt.type == "text":
                prompt_text = getattr(params.prompt, "text", "")

        if not prompt_text.strip():
            return PromptResponse(stopReason="end_turn")

        logger.info(
            f"Processing prompt for session {session_id}: {prompt_text[:100]}..."
        )

        try:
            # Check if this is a slash command
            if is_slash_command(prompt_text):
                command, args = parse_slash_command(prompt_text)
                logger.info(f"Processing slash command: /{command} {args}")

                # Handle the slash command
                handled = await self._handle_slash_command(session_id, command, args)

                if handled:
                    logger.info(f"Slash command /{command} handled successfully")
                    return PromptResponse(stopReason="end_turn")
                else:
                    logger.warning(f"Unknown slash command: /{command}")
                    # Fall through to send as regular message

            # Send the message and listen for events
            message = Message(role="user", content=[TextContent(text=prompt_text)])

            # Subscribe to events using the extracted EventSubscriber
            subscriber = EventSubscriber(session_id, self._conn)
            conversation.subscribe(subscriber)

            try:
                # Send message and run agent
                await conversation.send_message(message)
            finally:
                # Unsubscribe from events
                conversation.unsubscribe(subscriber)

            # Return the final response
            return PromptResponse(stopReason="end_turn")

        except Exception as e:
            logger.error(f"Error processing prompt: {e}")
            # Send error notification
            await self._conn.sessionUpdate(
                SessionNotification(
                    sessionId=session_id,
                    update=SessionUpdate2(
                        sessionUpdate="agent_message_chunk",
                        content=ContentBlock1(type="text", text=f"Error: {str(e)}"),
                    ),
                )
            )
            return PromptResponse(stopReason="error")

    async def _send_available_commands(self, session_id: str) -> None:
        """Send available commands notification to the client."""
        try:
            commands = get_acp_available_commands()

            # Import the notification types
            from acp.types.session_types import (
                SessionNotification,
                SessionUpdate,
            )

            await self._conn.sessionUpdate(
                SessionNotification(
                    sessionId=session_id,
                    update=SessionUpdate(
                        sessionUpdate="available_commands_update",
                        availableCommands=commands,
                    ),
                )
            )
            logger.info(
                f"Sent {len(commands)} available commands to session {session_id}"
            )
        except Exception as e:
            logger.error(f"Failed to send available commands: {e}")

    async def _handle_slash_command(
        self, session_id: str, command: str, args: str
    ) -> bool:
        """
        Handle a slash command.

        Args:
            session_id: Session ID
            command: Command name (without /)
            args: Command arguments

        Returns:
            True if command was handled, False otherwise
        """
        from acp.types.session_types import (
            ContentBlock1,
            SessionNotification,
            SessionUpdate2,
        )

        conversation = self._sessions.get(session_id)
        if not conversation:
            return False

        try:
            if command == "help":
                help_text = format_help_text()
                await self._conn.sessionUpdate(
                    SessionNotification(
                        sessionId=session_id,
                        update=SessionUpdate2(
                            sessionUpdate="agent_message_chunk",
                            content=ContentBlock1(type="text", text=help_text),
                        ),
                    )
                )
                return True

            elif command == "status":
                status_lines = [
                    f"Conversation ID: {conversation.id}",
                    "Status: Active",
                    f"Confirmation mode: {'enabled' if conversation.state.confirmation_mode else 'disabled'}",
                ]
                await self._conn.sessionUpdate(
                    SessionNotification(
                        sessionId=session_id,
                        update=SessionUpdate2(
                            sessionUpdate="agent_message_chunk",
                            content=ContentBlock1(
                                type="text", text="\n".join(status_lines)
                            ),
                        ),
                    )
                )
                return True

            elif command == "clear":
                # Just acknowledge the clear command
                await self._conn.sessionUpdate(
                    SessionNotification(
                        sessionId=session_id,
                        update=SessionUpdate2(
                            sessionUpdate="agent_message_chunk",
                            content=ContentBlock1(type="text", text="Screen cleared."),
                        ),
                    )
                )
                return True

            elif command == "mcp":
                # Show MCP server information
                mcp_info = ["MCP Servers:"]
                if (
                    hasattr(conversation.agent, "mcp_config")
                    and conversation.agent.mcp_config
                ):
                    servers = conversation.agent.mcp_config.get("mcpServers", {})
                    if servers:
                        for server_name in servers.keys():
                            mcp_info.append(f"  - {server_name}")
                    else:
                        mcp_info.append("  No MCP servers configured")
                else:
                    mcp_info.append("  No MCP servers configured")

                await self._conn.sessionUpdate(
                    SessionNotification(
                        sessionId=session_id,
                        update=SessionUpdate2(
                            sessionUpdate="agent_message_chunk",
                            content=ContentBlock1(
                                type="text", text="\n".join(mcp_info)
                            ),
                        ),
                    )
                )
                return True

            elif command == "settings":
                # Settings command - inform user this is not available in ACP mode
                await self._conn.sessionUpdate(
                    SessionNotification(
                        sessionId=session_id,
                        update=SessionUpdate2(
                            sessionUpdate="agent_message_chunk",
                            content=ContentBlock1(
                                type="text",
                                text="Settings management is not available in ACP mode. "
                                "Please use the CLI directly or configure via environment variables.",
                            ),
                        ),
                    )
                )
                return True

            elif command == "confirm":
                # Toggle confirmation mode
                conversation.state.confirmation_mode = (
                    not conversation.state.confirmation_mode
                )
                new_status = (
                    "enabled" if conversation.state.confirmation_mode else "disabled"
                )
                await self._conn.sessionUpdate(
                    SessionNotification(
                        sessionId=session_id,
                        update=SessionUpdate2(
                            sessionUpdate="agent_message_chunk",
                            content=ContentBlock1(
                                type="text",
                                text=f"Confirmation mode {new_status}",
                            ),
                        ),
                    )
                )
                return True

            elif command == "resume":
                # Resume command
                from openhands.sdk.conversation.state import AgentExecutionStatus

                if conversation.state.agent_status in (
                    AgentExecutionStatus.PAUSED,
                    AgentExecutionStatus.WAITING_FOR_CONFIRMATION,
                ):
                    # Actually resume the conversation
                    await conversation.send_message(
                        Message(role="user", content=[TextContent(text="continue")])
                    )
                else:
                    await self._conn.sessionUpdate(
                        SessionNotification(
                            sessionId=session_id,
                            update=SessionUpdate2(
                                sessionUpdate="agent_message_chunk",
                                content=ContentBlock1(
                                    type="text",
                                    text="No paused conversation to resume.",
                                ),
                            ),
                        )
                    )
                return True

            elif command == "exit":
                # Exit command - inform that session should be ended
                await self._conn.sessionUpdate(
                    SessionNotification(
                        sessionId=session_id,
                        update=SessionUpdate2(
                            sessionUpdate="agent_message_chunk",
                            content=ContentBlock1(
                                type="text",
                                text="To exit, please close the session from your editor.",
                            ),
                        ),
                    )
                )
                return True

        except Exception as e:
            logger.error(f"Error handling slash command /{command}: {e}")

        return False

    async def cancel(self, params: CancelNotification) -> None:
        """Cancel the current operation (no-op for now)."""
        logger.info("Cancel requested (no-op)")

    async def loadSession(self, params: LoadSessionRequest) -> None:
        """Load an existing session and replay conversation history."""
        session_id = params.sessionId
        logger.info(f"Loading session: {session_id}")

        try:
            # Check if session exists in our mapping
            if session_id not in self._sessions:
                raise ValueError(f"Session not found: {session_id}")

            conversation = self._sessions[session_id]

            # Get conversation state
            state = conversation.state
            if state is None:
                raise ValueError(f"Conversation state not found: {session_id}")

            logger.info(
                f"Found conversation {conversation.id} with {len(state.history)} events"
            )

            # Set up MCP servers if provided (similar to newSession)
            # Note: We don't recreate the agent here, just validate MCP servers
            if params.mcpServers:
                logger.info(
                    f"MCP servers provided for session load: "
                    f"{len(params.mcpServers)} servers"
                )
                # We could validate MCP server configs here if needed

            # Validate working directory
            working_dir = params.cwd or str(Path.cwd())
            working_path = Path(working_dir)
            if not working_path.exists():
                logger.warning(
                    f"Working directory {working_dir} doesn't exist for loaded session"
                )

            # Stream conversation history to client
            logger.info("Streaming conversation history to client")
            for event in state.history:
                if isinstance(event, MessageEvent):
                    # Convert MessageEvent to ACP session update
                    if event.source == "user":
                        # Stream user message
                        text_content = ""
                        for content in event.llm_message.content:
                            if isinstance(content, TextContent):
                                text_content += content.text

                        if text_content.strip():
                            await self._conn.sessionUpdate(
                                SessionNotification(
                                    sessionId=session_id,
                                    update=SessionUpdate1(
                                        sessionUpdate="user_message_chunk",
                                        content=ContentBlock1(
                                            type="text", text=text_content
                                        ),
                                    ),
                                )
                            )

                    elif event.source == "agent":
                        # Stream agent message
                        text_content = ""
                        for content in event.llm_message.content:
                            if isinstance(content, TextContent):
                                text_content += content.text

                        if text_content.strip():
                            await self._conn.sessionUpdate(
                                SessionNotification(
                                    sessionId=session_id,
                                    update=SessionUpdate2(
                                        sessionUpdate="agent_message_chunk",
                                        content=ContentBlock1(
                                            type="text", text=text_content
                                        ),
                                    ),
                                )
                            )

            logger.info(f"Successfully loaded session {session_id}")

            # Send available commands notification
            await self._send_available_commands(session_id)

        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}", exc_info=True)
            raise

    async def setSessionMode(
        self, params: SetSessionModeRequest
    ) -> SetSessionModeResponse | None:
        """Set session mode (no-op for now)."""
        logger.info("Set session mode requested (no-op)")
        return SetSessionModeResponse()

    async def extMethod(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Extension method (not supported)."""
        logger.info(f"Extension method '{method}' requested (not supported)")
        return {"error": "extMethod not supported"}

    async def extNotification(self, method: str, params: dict[str, Any]) -> None:
        """Extension notification (no-op for now)."""
        logger.info(f"Extension notification '{method}' received (no-op)")


async def run_acp_server(persistence_dir: Path | None = None) -> None:
    """Run the OpenHands ACP server."""
    logger.info("Starting OpenHands ACP server...")

    reader, writer = await stdio_streams()

    def create_agent(conn: AgentSideConnection) -> OpenHandsACPAgent:
        return OpenHandsACPAgent(conn, persistence_dir)

    AgentSideConnection(create_agent, writer, reader)

    # Keep the server running
    await asyncio.Event().wait()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )

    # Get persistence directory from command line args
    persistence_dir = None
    if len(sys.argv) > 1:
        persistence_dir = Path(sys.argv[1])

    asyncio.run(run_acp_server(persistence_dir))
