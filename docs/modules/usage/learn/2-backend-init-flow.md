# OpenHands Backend System Initialization

This guide details the complete backend server initialization sequence of OpenHands, showing how each component is loaded and initialized.


----
## Conversation Manager Initialization
### 0. Flow Diagram
```plaintext
Conversation Manager Initialization (openhands/server/conversation_manager/standalone_conversation_manager.py)
   │
   ├─► Create StandaloneConversationManager
   │   │
   │   ├─► Initialize State
   │   │   ├── _local_agent_loops_by_sid = {}
   │   │   ├── _local_connection_id_to_session_id = {}
   │   │   ├── _active_conversations = {}
   │   │   └── _detached_conversations = {}
   │   │
   │   └─► Start Cleanup Task
   │       └── _cleanup_task = asyncio.create_task(self._cleanup_stale())
   │
   └─► Setup Event Stream
       └── Initialize EventStream for each conversation
```

### 1. Conversation Manager Initialization
```python
# File: openhands/server/conversation_manager/conversation_manager.py

class ConversationManager(ABC):
     @abstractmethod
    async def attach_to_conversation(self, sid: str) -> Conversation | None:
        """Attach to an existing conversation or create a new one."""

    @abstractmethod
    async def detach_from_conversation(self, conversation: Conversation):
        """Detach from a conversation."""

    @abstractmethod
    async def join_conversation(
        self, sid: str, connection_id: str, settings: Settings, user_id: str | None
    ) -> EventStream | None:
        """Join a conversation and return its event stream."""

    async def is_agent_loop_running(self, sid: str) -> bool:
        """Check if an agent loop is running for the given session ID."""
        sids = await self.get_running_agent_loops(filter_to_sids={sid})
        return bool(sids)

    @abstractmethod
    async def get_running_agent_loops(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> set[str]:
        """Get all running agent loops, optionally filtered by user ID and session IDs."""

    @abstractmethod
    async def get_connections(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> dict[str, str]:
        """Get all connections, optionally filtered by user ID and session IDs."""

    @abstractmethod
    async def maybe_start_agent_loop(
        self,
        sid: str,
        settings: Settings,
        user_id: str | None,
        initial_user_msg: MessageAction | None = None,
    ) -> EventStream:
        """Start an event loop if one is not already running"""

    @abstractmethod
    async def send_to_event_stream(self, connection_id: str, data: dict):
        """Send data to an event stream."""

    @abstractmethod
    async def disconnect_from_session(self, connection_id: str):
        """Disconnect from a session."""

    @abstractmethod
    async def close_session(self, sid: str):
        """Close a session."""

    @classmethod
    @abstractmethod
    def get_instance(
        cls,
        sio: socketio.AsyncServer,
        config: AppConfig,
        file_store: FileStore,
    ) -> ConversationManager:
        """Get a store for the user represented by the token given"""

# File: openhands/server/conversation_manager/standalone_conversation_manager.py

@dataclass
class StandaloneConversationManager(ConversationManager):
    async def __aenter__(self):
        """Initialize conversation manager"""
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(
            self._cleanup_stale()
        )
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Cleanup on shutdown"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
```


----
## Backend Server Initialization
### 0. Flow Diagram
```plaintext
make run (defined in Makefile)
   |
poetry run uvicorn openhands.server.listen:app (defined in Makefile)
   │
Backend Server Start (openhands/server/listen.py)
   │    
   ├─► Create FastAPI Application (openhands/server/app.py)
   │   │
   │   ├─► Register Middleware
   │   │   ├── LocalhostCORSMiddleware (allow cross-origin)
   │   │   ├── CacheControlMiddleware (handle caching)
   │   │   ├── RateLimitMiddleware (rate limiting)
   │   │   ├── AttachConversationMiddleware (conversation handling)
   │   │   └── GitHubTokenMiddleware (authentication)
   │   │
   │   ├─► Register Routes
   │   │   ├── public_api_router
   │   │   ├── files_api_router
   │   │   ├── security_api_router
   │   │   ├── feedback_api_router
   │   │   ├── conversation_api_router
   │   │   ├── manage_conversation_api_router
   │   │   ├── settings_router
   │   │   ├── github_api_router
   │   │   └── trajectory_router
   │   │
   │   └─► Setup Lifespan Manager
   │       └── Initialize ConversationManager (described in previous chapter)
   │
   ├─► Create Socket.IO Server
   │   │
   │   ├─► Setup Event Handlers (openhands/server/listen_socket.py)
   │   │   ├── @sio.event async def connect()
   │   │   ├── @sio.event async def oh_action()
   │   │   └── @sio.event async def disconnect()
   │   │
   │   └─► Integrate with FastAPI
   │       └── Create ASGIApp(sio, other_asgi_app=base_app)
   │
   └─► Mount Static Files
       └── SPAStaticFiles(directory='./frontend/build')
```


### 1. Server Startup
create a FastAPI server app instance. 
```python
# File: openhands/server/app.py

@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Server lifespan management"""
    async with conversation_manager:
        yield

app = FastAPI(
    title='OpenHands',
    description='OpenHands: Code Less, Make More',
    version=__version__,
    lifespan=_lifespan,
)

# Register routes
app.include_router(public_api_router)
app.include_router(files_api_router)
app.include_router(security_api_router)
app.include_router(feedback_api_router)
app.include_router(conversation_api_router)
app.include_router(manage_conversation_api_router)
app.include_router(settings_router)
app.include_router(github_api_router)
app.include_router(trajectory_router)
```

### 2. Conversation Manager Initialization (see previous chapter)

### 3. Socket.IO Integration
create a socket.io server instance to include the FastAPI app and add middleware.
```python
# File: openhands/server/listen.py

# Create FastAPI and Socket.IO servers
base_app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi')

# Add middleware
base_app.add_middleware(LocalhostCORSMiddleware)
base_app.add_middleware(CacheControlMiddleware)
base_app.add_middleware(RateLimitMiddleware)
base_app.middleware('http')(AttachConversationMiddleware)
base_app.middleware('http')(GitHubTokenMiddleware)

# Create ASGI app
app = socketio.ASGIApp(sio, other_asgi_app=base_app)
```


----
## Client Connection Flow

### 0. Flow Diagram
```plaintext
Client Connection Flow
   │
   ├─► Socket.IO Connect Event
   │   │
   │   ├─► Parse Query Parameters
   │   │   ├── conversation_id
   │   │   └── latest_event_id
   │   │
   │   ├─► Validate User (if not OSS mode)
   │   │   ├── Check github_auth cookie
   │   │   ├── Decode JWT token
   │   │   └── Verify user permissions
   │   │
   │   └─► Load User Settings
   │       └── Get settings from SettingsStore
   │
   ├─► Join Conversation
   │   │
   │   ├─► Get or Create Conversation
   │   │   ├── Check active conversations
   │   │   ├── Check detached conversations
   │   │   └── Create new if needed
   │   │
   │   ├─► Initialize Event Stream
   │   │   ├── Create AsyncEventStreamWrapper
   │   │   └── Setup event processing
   │   │
   │   └─► Start Agent Loop
   │       ├── Create agent session
   │       ├── Initialize agent
   │       └── Setup event handlers
   │
   └─► Setup Event Processing
       └── Begin processing events through Socket.IO
```

### 1. Client Connection Handling
```python
# File: openhands/server/listen_socket.py

@sio.event
async def connect(connection_id: str, environ, auth):
    logger.info(f'sio:connect: {connection_id}')
    query_params = parse_qs(environ.get('QUERY_STRING', ''))
    latest_event_id = int(query_params.get('latest_event_id', [-1])[0])
    conversation_id = query_params.get('conversation_id', [None])[0]
    if not conversation_id:
        logger.error('No conversation_id in query params')
        raise ConnectionRefusedError('No conversation_id in query params')

    user_id = None
    if server_config.app_mode != AppMode.OSS:
        cookies_str = environ.get('HTTP_COOKIE', '')
        cookies = dict(cookie.split('=', 1) for cookie in cookies_str.split('; '))
        signed_token = cookies.get('github_auth', '')
        if not signed_token:
            logger.error('No github_auth cookie')
            raise ConnectionRefusedError('No github_auth cookie')
        if not config.jwt_secret:
            raise RuntimeError('JWT secret not found')

        jwt_secret = (
            config.jwt_secret.get_secret_value()
            if isinstance(config.jwt_secret, SecretStr)
            else config.jwt_secret
        )
        decoded = jwt.decode(signed_token, jwt_secret, algorithms=['HS256'])
        user_id = decoded['github_user_id']

        logger.info(f'User {user_id} is connecting to conversation {conversation_id}')

        conversation_store = await ConversationStoreImpl.get_instance(config, user_id)
        metadata = await conversation_store.get_metadata(conversation_id)

        if metadata.github_user_id != str(user_id):
            logger.error(
                f'User {user_id} is not allowed to join conversation {conversation_id}'
            )
            raise ConnectionRefusedError(
                f'User {user_id} is not allowed to join conversation {conversation_id}'
            )

    settings_store = await SettingsStoreImpl.get_instance(config, user_id)
    settings = await settings_store.load()

    if not settings:
        raise ConnectionRefusedError(
            'Settings not found', {'msg_id': 'CONFIGURATION$SETTINGS_NOT_FOUND'}
        )

    event_stream = await conversation_manager.join_conversation(
        conversation_id, connection_id, settings, user_id
    )

    agent_state_changed = None
    async_stream = AsyncEventStreamWrapper(event_stream, latest_event_id + 1)
    async for event in async_stream:
        if isinstance(
            event,
            (
                NullAction,
                NullObservation,
            ),
        ):
            continue
        elif isinstance(event, AgentStateChangedObservation):
            agent_state_changed = event
        else:
            await sio.emit('oh_event', event_to_dict(event), to=connection_id)
    if agent_state_changed:
        await sio.emit('oh_event', event_to_dict(agent_state_changed), to=connection_id)


@sio.event
async def oh_action(connection_id: str, data: dict):
    await conversation_manager.send_to_event_stream(connection_id, data)


@sio.event
async def disconnect(connection_id: str):
    logger.info(f'sio:disconnect:{connection_id}')
    await conversation_manager.disconnect_from_session(connection_id)
```



----
## Runtime Initialization
### 0. Flow Diagram
```plaintext
Runtime Initialization (When needed for a conversation)
   │
   ├─► Create Runtime Instance
   │   │
   │   ├─► Initialize Event Stream
   │   │   ├── Create FileStore
   │   │   └── Setup EventStream
   │   │
   │   ├─► Load Agent Class
   │   │   └── Get from registered agents
   │   │
   │   └─► Setup Runtime
   │       ├── Initialize plugins
   │       └── Setup capabilities
   │
   ├─► Create Agent
   │   │
   │   ├─► Load Configurations
   │   │   ├── Agent config
   │   │   └── LLM config
   │   │
   │   ├─► Initialize LLM
   │   │   └── Setup LLM client
   │   │
   │   └─► Setup Prompt Manager
   │       └── Load microagents
   │
   └─► Create Controller
       │
       ├─► Try Restore State
       │   └── Check for previous session
       │
       └─► Initialize Controller
           ├── Set max iterations
           ├── Set budget
           └── Setup confirmation mode
```

### 1. Event System Initialization
create EventStream instance which will be used by the runtime.
```python
# File: openhands/events/stream.py

class AsyncEventStreamWrapper:
    def __init__(self, event_stream: EventStream, start_index: int):
        self.event_stream = event_stream
        self.current_index = start_index
        
    async def __aiter__(self):
        while True:
            if self.current_index < len(self.event_stream.history):
                event = self.event_stream.history[self.current_index]# core/main.py
async def run_controller(
    config: AppConfig,
    initial_user_action: Action,
    sid: str | None = None,
    runtime: Runtime | None = None,
    agent: Agent | None = None,
    headless_mode: bool = True,
):
    """Initialize and run agent controller"""
    # Create components
    sid = sid or generate_sid(config)
    runtime = runtime or create_runtime(config, sid, headless_mode)
    await runtime.connect()
    
    agent = agent or create_agent(runtime, config)
    controller, initial_state = create_controller(
        agent,
        runtime,
        config,
        headless_mode
    )
    
    # Setup event handling
    event_stream = runtime.event_stream
    event_stream.subscribe(
        EventStreamSubscriber.MAIN,
        on_event,
        sid
    )
    
    # Start processing
    await run_agent_until_done(
        controller,
        runtime,
        end_states=[
            AgentState.FINISHED,
            AgentState.REJECTED,
            AgentState.ERROR,
            AgentState.PAUSED,
            AgentState.STOPPED,
        ]
    )# core/main.py
async def run_controller(
    config: AppConfig,
    initial_user_action: Action,
    sid: str | None = None,
    runtime: Runtime | None = None,
    agent: Agent | None = None,
    headless_mode: bool = True,
):
    """Initialize and run agent controller"""
    # Create components
    sid = sid or generate_sid(config)
    runtime = runtime or create_runtime(config, sid, headless_mode)
    await runtime.connect()
    
    agent = agent or create_agent(runtime, config)
    controller, initial_state = create_controller(
        agent,
        runtime,
        config,
        headless_mode
    )
    
    # Setup event handling
    event_stream = runtime.event_stream
    event_stream.subscribe(
        EventStreamSubscriber.MAIN,
        on_event,
        sid
    )
    
    # Start processing
    await run_agent_until_done(
        controller,
        runtime,
        end_states=[
            AgentState.FINISHED,
            AgentState.REJECTED,
            AgentState.ERROR,
            AgentState.PAUSED,
            AgentState.STOPPED,
        ]
    )# core/main.py
async def run_controller(
    config: AppConfig,
    initial_user_action: Action,
    sid: str | None = None,
    runtime: Runtime | None = None,
    agent: Agent | None = None,
    headless_mode: bool = True,
):
    """Initialize and run agent controller"""
    # Create components
    sid = sid or generate_sid(config)
    runtime = runtime or create_runtime(config, sid, headless_mode)
    await runtime.connect()
    
    agent = agent or create_agent(runtime, config)
    controller, initial_state = create_controller(
        agent,
        runtime,
        config,
        headless_mode
    )
    
    # Setup event handling
    event_stream = runtime.event_stream
    event_stream.subscribe(
        EventStreamSubscriber.MAIN,
        on_event,
        sid
    )
    
    # Start processing
    await run_agent_until_done(
        controller,
        runtime,
        end_states=[
            AgentState.FINISHED,
            AgentState.REJECTED,
            AgentState.ERROR,
            AgentState.PAUSED,
            AgentState.STOPPED,
        ]
    )# core/main.py
async def run_controller(
    config: AppConfig,
    initial_user_action: Action,
    sid: str | None = None,
    runtime: Runtime | None = None,
    agent: Agent | None = None,
    headless_mode: bool = True,
):
    """Initialize and run agent controller"""
    # Create components
    sid = sid or generate_sid(config)
    runtime = runtime or create_runtime(config, sid, headless_mode)
    await runtime.connect()
    
    agent = agent or create_agent(runtime, config)
    controller, initial_state = create_controller(
        agent,
        runtime,
        config,
        headless_mode
    )
    
    # Setup event handling
    event_stream = runtime.event_stream
    event_stream.subscribe(
        EventStreamSubscriber.MAIN,
        on_event,
        sid
    )
    
    # Start processing
    await run_agent_until_done(
        controller,
        runtime,
        end_states=[
            AgentState.FINISHED,
            AgentState.REJECTED,
            AgentState.ERROR,
            AgentState.PAUSED,
            AgentState.STOPPED,
        ]
    )# core/main.py
async def run_controller(
    config: AppConfig,
    initial_user_action: Action,
    sid: str | None = None,
    runtime: Runtime | None = None,
    agent: Agent | None = None,
    headless_mode: bool = True,
):
    """Initialize and run agent controller"""
    # Create components
    sid = sid or generate_sid(config)
    runtime = runtime or create_runtime(config, sid, headless_mode)
    await runtime.connect()
    
    agent = agent or create_agent(runtime, config)
    controller, initial_state = create_controller(
        agent,
        runtime,
        config,
        headless_mode
    )
    
    # Setup event handling
    event_stream = runtime.event_stream
    event_stream.subscribe(
        EventStreamSubscriber.MAIN,
        on_event,
        sid
    )
    
    # Start processing
    await run_agent_until_done(
        controller,
        runtime,
        end_states=[
            AgentState.FINISHED,
            AgentState.REJECTED,
            AgentState.ERROR,
            AgentState.PAUSED,
            AgentState.STOPPED,
        ]
    )# core/main.py
async def run_controller(
    config: AppConfig,
    initial_user_action: Action,
    sid: str | None = None,
    runtime: Runtime | None = None,
    agent: Agent | None = None,
    headless_mode: bool = True,
):
    """Initialize and run agent controller"""
    # Create components
    sid = sid or generate_sid(config)
    runtime = runtime or create_runtime(config, sid, headless_mode)
    await runtime.connect()
    
    agent = agent or create_agent(runtime, config)
    controller, initial_state = create_controller(
        agent,
        runtime,
        config,
        headless_mode
    )
    
    # Setup event handling
    event_stream = runtime.event_stream
    event_stream.subscribe(
        EventStreamSubscriber.MAIN,
        on_event,
        sid
    )
    
    # Start processing
    await run_agent_until_done(
        controller,
        runtime,
        end_states=[
            AgentState.FINISHED,
            AgentState.REJECTED,
            AgentState.ERROR,
            AgentState.PAUSED,
            AgentState.STOPPED,
        ]
    )# core/main.py
async def run_controller(
    config: AppConfig,
    initial_user_action: Action,
    sid: str | None = None,
    runtime: Runtime | None = None,
    agent: Agent | None = None,
    headless_mode: bool = True,
):
    """Initialize and run agent controller"""
    # Create components
    sid = sid or generate_sid(config)
    runtime = runtime or create_runtime(config, sid, headless_mode)
    await runtime.connect()
    
    agent = agent or create_agent(runtime, config)
    controller, initial_state = create_controller(
        agent,
        runtime,
        config,
        headless_mode
    )
    
    # Setup event handling
    event_stream = runtime.event_stream
    event_stream.subscribe(
        EventStreamSubscriber.MAIN,
        on_event,
        sid
    )
    
    # Start processing
    await run_agent_until_done(
        controller,
        runtime,
        end_states=[
            AgentState.FINISHED,
            AgentState.REJECTED,
            AgentState.ERROR,
            AgentState.PAUSED,
            AgentState.STOPPED,
        ]
    )
                self.current_index += 1
                yield event
            else:
                await asyncio.sleep(0.1)

class EventStream:
    """Core event handling system"""
    
    def __init__(self, sid: str, file_store: FileStore):
        # Initialize core components
        self.sid = sid
        self.file_store = file_store
        self._stop_flag = threading.Event()
        self._queue = queue.Queue()
        
        # Initialize thread management
        self._thread_pools = {}
        self._thread_loops = {}
        self._queue_loop = None
        
        # Start event processing thread
        self._queue_thread = threading.Thread(target=self._run_queue_loop)
        self._queue_thread.daemon = True
        self._queue_thread.start()
        
        # Initialize subscriber management
        self._subscribers = {}
        self._lock = threading.Lock()
        self._cur_id = 0
        self.secrets = {}
        
        # Load existing events
        self.__post_init__()
```

### 2. File Store Initialization
create FileStore instance which will be used by the runtime.
```python
# File: openhands/storage/__init__.py

def get_file_store(file_store: str, file_store_path: str | None = None) -> FileStore:
    if file_store == 'local':
        if file_store_path is None:
            raise ValueError('file_store_path is required for local file store')
        return LocalFileStore(file_store_path)
    elif file_store == 's3':
        return S3FileStore(file_store_path)
    elif file_store == 'google_cloud':
        return GoogleCloudFileStore(file_store_path)
    return InMemoryFileStore()

# File: openhands/storage/local.py

class LocalFileStore(FileStore):
    root: str
    def __init__(self, root: str):
        self.root = root
        os.makedirs(self.root, exist_ok=True)
```

### 3. Agent Initialization
create an agent instance which will be used in the runtime
```python
# File: core/setup.py

def create_agent(runtime: Runtime, config: AppConfig) -> Agent:
    """Create agent instance"""
    # Get agent class and configs
    agent_cls = Agent.get_cls(config.default_agent)
    agent_config = config.get_agent_config(config.default_agent)
    llm_config = config.get_llm_config_from_agent(config.default_agent)
    
    # Create agent
    agent = agent_cls(
        llm=LLM(config=llm_config),
        config=agent_config,
    )
    
    # Setup prompt manager if exists
    if agent.prompt_manager:
        microagents = runtime.get_microagents_from_selected_repo(None)
        agent.prompt_manager.load_microagents(microagents)
    
    # Setup security analyzer if configured
    if config.security.security_analyzer:
        analyzer_cls = options.SecurityAnalyzers.get(
            config.security.security_analyzer,
            SecurityAnalyzer
        )
        analyzer_cls(runtime.event_stream)
    
    return agent


# File: openhands/controller/agent.py

class Agent(ABC):
    _registry: dict[str, Type['Agent']] = {}
    sandbox_plugins: list[PluginRequirement] = []

    def __init__(
        self,
        llm: LLM,
        config: 'AgentConfig',
    ):
        self.llm = llm
        self.config = config
        self._complete = False
        self.prompt_manager: 'PromptManager' | None = None

    @classmethod
    def get_cls(cls, name: str) -> Type['Agent']:
        """Retrieves an agent class from the registry.

        Parameters:
        - name (str): The name of the class to retrieve

        Returns:
        - agent_cls (Type['Agent']): The class registered under the specified name.

        Raises:
        - AgentNotRegisteredError: If name not registered
        """
        if name not in cls._registry:
            raise AgentNotRegisteredError(name)
        return cls._registry[name]


# File: openhands/agenthub/codeact_agent/codeact_agent.py
class CodeActAgent(Agent):
    VERSION = '2.2'
    sandbox_plugins: list[PluginRequirement] = [
        # NOTE: AgentSkillsRequirement need to go before JupyterRequirement, since
        # AgentSkillsRequirement provides a lot of Python functions,
        # and it needs to be initialized before Jupyter for Jupyter to use those functions.
        AgentSkillsRequirement(),
        JupyterRequirement(),
    ]

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
    ) -> None:
        """Initializes a new instance of the CodeActAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm, config)
        self.pending_actions: deque[Action] = deque()
        self.reset()

        self.mock_function_calling = False
        if not self.llm.is_function_calling_active():
            logger.info(
                f'Function calling not enabled for model {self.llm.config.model}. '
                'Mocking function calling via prompting.'
            )
            self.mock_function_calling = True

        # Function calling mode
        self.tools = codeact_function_calling.get_tools(
            codeact_enable_browsing=self.config.codeact_enable_browsing,
            codeact_enable_jupyter=self.config.codeact_enable_jupyter,
            codeact_enable_llm_editor=self.config.codeact_enable_llm_editor,
        )
        logger.debug(
            f'TOOLS loaded for CodeActAgent: {json.dumps(self.tools, indent=2, ensure_ascii=False).replace("\\n", "\n")}'
        )
        self.prompt_manager = PromptManager(
            microagent_dir=os.path.join(
                os.path.dirname(os.path.dirname(openhands.__file__)),
                'microagents',
            )
            if self.config.enable_prompt_extensions
            else None,
            prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
            disabled_microagents=self.config.disabled_microagents,
        )

        self.condenser = Condenser.from_config(self.config.condenser)
        logger.debug(f'Using condenser: {self.condenser}')

```

### 4. Controller Initialization
```python
# File: core/setup.py

def create_controller(
    agent: Agent,
    runtime: Runtime,
    config: AppConfig,
    headless_mode: bool = True,
    replay_events: list[Event] | None = None,
) -> Tuple[AgentController, State | None]:
    """Create agent controller"""
    event_stream = runtime.event_stream
    
    # Try to restore previous state
    initial_state = None
    try:
        initial_state = State.restore_from_session(
            event_stream.sid,
            event_stream.file_store
        )
    except Exception:
        pass
    
    # Create controller
    controller = AgentController(
        agent=agent,
        max_iterations=config.max_iterations,
        max_budget_per_task=config.max_budget_per_task,
        agent_to_llm_config=config.get_agent_to_llm_config_map(),
        event_stream=event_stream,
        initial_state=initial_state,
        headless_mode=headless_mode,
        confirmation_mode=config.security.confirmation_mode,
        replay_events=replay_events,
    )
    
    return (controller, initial_state)


# File: core/main.py
async def run_controller(
    config: AppConfig,
    initial_user_action: Action,
    sid: str | None = None,
    runtime: Runtime | None = None,
    agent: Agent | None = None,
    headless_mode: bool = True,
):
    """Initialize and run agent controller"""
    # Create components
    sid = sid or generate_sid(config)
    runtime = runtime or create_runtime(config, sid, headless_mode)
    await runtime.connect()
    
    agent = agent or create_agent(runtime, config)
    controller, initial_state = create_controller(
        agent,
        runtime,
        config,
        headless_mode
    )
    
    # Setup event handling
    event_stream = runtime.event_stream
    event_stream.subscribe(
        EventStreamSubscriber.MAIN,
        on_event,
        sid
    )
    
    # Start processing
    await run_agent_until_done(
        controller,
        runtime,
        end_states=[
            AgentState.FINISHED,
            AgentState.REJECTED,
            AgentState.ERROR,
            AgentState.PAUSED,
            AgentState.STOPPED,
        ]
    )
```


### 4. Runtime System Initialization
create a runtime instance and register it as an event subscriber.
```python
# File: openhands/core/setup.py

def create_runtime(config: AppConfig, sid: str | None = None, headless_mode: bool = True) -> Runtime:
    """Runtime initialization sequence"""
    
    # 1. Generate or use session ID
    session_id = sid or generate_sid(config)
    
    # 2. Initialize file store and event stream
    file_store = get_file_store(config.file_store, config.file_store_path)
    event_stream = EventStream(session_id, file_store)
    
    # 3. Get agent class for plugins
    agent_cls = openhands.agenthub.Agent.get_cls(config.default_agent)
    
    # 4. Get and create runtime
    runtime_cls = get_runtime_cls(config.runtime)  # Get appropriate runtime class
    runtime = runtime_cls(
        config=config,
        event_stream=event_stream,
        sid=session_id,
        plugins=agent_cls.sandbox_plugins,
        headless_mode=headless_mode
    )
    
    return runtime

# File: openhands/runtime/base.py
class Runtime:
    """Base runtime implementation"""
    
    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str,
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = False,
    ):
        # Initialize core components
        self.sid = sid
        self.event_stream = event_stream
        
        # Register runtime as event subscriber
        self.event_stream.subscribe(
            EventStreamSubscriber.RUNTIME,
            self.on_event,
            self.sid
        )
        
        # Initialize plugins
        self.plugins = (
            copy.deepcopy(plugins)
            if plugins is not None and len(plugins) > 0
            else []
        )
        
        # Add VSCode plugin if not headless
        if not headless_mode:
            self.plugins.append(VSCodeRequirement())
            
        # Store configuration
        self.status_callback = status_callback
        self.attach_to_existing = attach_to_existing
        self.config = copy.deepcopy(config)
        
        # Register cleanup
        atexit.register(self.close)
        
        # Setup environment
        self.initial_env_vars = _default_env_vars(
            config.sandbox
        )
        if env_vars is not None:
            self.initial_env_vars.update(env_vars)
```

### 7. Event Handler Registration
```python
# File: openhands/events/stream.py

class EventStreamSubscriber(str, Enum):
    """Built-in event subscribers"""
    AGENT_CONTROLLER = 'agent_controller'
    SECURITY_ANALYZER = 'security_analyzer'
    RESOLVER = 'openhands_resolver'
    SERVER = 'server'
    RUNTIME = 'runtime'
    MAIN = 'main'
    TEST = 'test'

class EventStream:
    def subscribe(
        self,
        subscriber_id: EventStreamSubscriber,
        callback: Callable,
        callback_id: str
    ):
        """Register event handler"""
        # Create thread pool for handler
        initializer = partial(
            self._init_thread_loop,
            subscriber_id,
            callback_id
        )
        pool = ThreadPoolExecutor(
            max_workers=1,
            initializer=initializer
        )
        
        # Initialize subscriber storage
        if subscriber_id not in self._subscribers:
            self._subscribers[subscriber_id] = {}
            self._thread_pools[subscriber_id] = {}
            
        # Register callback
        if callback_id in self._subscribers[subscriber_id]:
            raise ValueError(
                f'Callback ID on subscriber {subscriber_id} '
                f'already exists: {callback_id}'
            )
            
        self._subscribers[subscriber_id][callback_id] = callback
        self._thread_pools[subscriber_id][callback_id] = pool
```


