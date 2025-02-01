# OpenHands Initialization Sequence Guide

This guide details the complete initialization sequence of OpenHands, focusing on runtime and event handling systems.

## System Initialization Flow

### 1. Server Startup
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

### 2. Socket.IO Integration
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

### 3. Event System Initialization
```python
# File: openhands/events/stream.py

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

### 4. Runtime System Initialization
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

### 5. Event Handler Registration
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

## System Interaction Flow

### 1. Client Connection Flow
```plaintext
Client Connection Request
    │
    ▼
Socket.IO connect event (listen_socket.py)
    │
    ├─► Parse query parameters
    │   - Get conversation_id
    │   - Get latest_event_id
    │
    ├─► Validate user (if not OSS mode)
    │   - Check github_auth cookie
    │   - Decode JWT token
    │   - Verify user permissions
    │
    ├─► Load user settings
    │   - Get settings store
    │   - Load settings
    │
    └─► Join conversation
        │
        ├─► Create/Get Runtime
        │   - Initialize event stream
        │   - Setup runtime environment
        │   - Register event handlers
        │
        ├─► Initialize Agent
        │   - Create agent instance
        │   - Setup LLM
        │   - Register with event stream
        │
        └─► Start Processing
            - Begin event handling
            - Process messages
            - Execute actions
```

### 2. Event Processing Flow
```plaintext
Event Received
    │
    ▼
EventStream._process_queue
    │
    ├─► Get event from queue
    │
    └─► For each subscriber:
        │
        ├─► Get subscriber callbacks
        │
        ├─► Execute in thread pool
        │   - Run callback
        │   - Handle errors
        │
        └─► Process results
            - Update state
            - Generate responses
            - Store events
```

### 3. Runtime Action Flow
```plaintext
Action Event Received
    │
    ▼
Runtime.on_event
    │
    ├─► Validate action
    │   - Check runnable
    │   - Verify confirmation
    │   - Check capabilities
    │
    ├─► Execute action
    │   - Get handler
    │   - Run action
    │   - Generate observation
    │
    └─► Process result
        - Create observation
        - Add to event stream
        - Update state
```

## Component Dependencies

```plaintext
FastAPI Server
    │
    ├─► Socket.IO Server
    │   - Real-time communication
    │   - Event handling
    │
    ├─► Event Stream
    │   - Event processing
    │   - State management
    │   - Subscriber handling
    │
    ├─► Runtime System
    │   - Action execution
    │   - Environment management
    │   - Plugin handling
    │
    └─► Agent System
        - LLM integration
        - Task processing
        - Action generation
```

## Best Practices

1. **Initialization Order**
   - Server components first
   - Event system second
   - Runtime/agents as needed

2. **Event Handling**
   - Use appropriate subscriber IDs
   - Handle errors properly
   - Clean up resources

3. **Runtime Management**
   - Initialize plugins properly
   - Handle environment variables
   - Manage resources

4. **Error Handling**
   - Handle initialization errors
   - Clean up on failures
   - Log issues properly