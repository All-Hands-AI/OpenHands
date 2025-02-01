# OpenHands System Understanding Guide

This guide provides a detailed explanation of OpenHands' actual implementation, focusing on its core components and their interactions.

## System Architecture Overview

### 1. Core Components and File Structure

```plaintext
openhands/
├── server/
│   ├── app.py                    # FastAPI application and router setup
│   ├── listen.py                 # Socket.IO and middleware configuration
│   ├── listen_socket.py          # Socket.IO event handlers
│   ├── conversation_manager/     # Conversation management
│   │   ├── conversation_manager.py    # Abstract base class
│   │   └── standalone_conversation_manager.py  # Main implementation
│   └── session/                  # Session handling
│       ├── conversation.py       # Conversation implementation
│       └── session.py           # Session management
├── events/
│   ├── stream.py                # Event streaming system
│   ├── action/                  # Action definitions
│   │   ├── action.py           # Base action class
│   │   ├── message.py          # Message actions
│   │   └── ...
│   └── observation/             # Observation handling
│       ├── observation.py       # Base observation class
│       ├── agent.py            # Agent observations
│       └── ...
└── controller/
    ├── agent.py                 # Base agent implementation
    └── agent_controller.py      # Agent control logic
```

### 2. Application Initialization

```python
# server/app.py - Main application setup
@asynccontextmanager
async def _lifespan(app: FastAPI):
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

### 3. Socket.IO Integration

```python
# server/listen_socket.py - Socket.IO event handlers
@sio.event
async def connect(connection_id: str, environ, auth):
    # Get conversation ID from query params
    query_params = parse_qs(environ.get('QUERY_STRING', ''))
    conversation_id = query_params.get('conversation_id', [None])[0]
    
    # Get user settings
    settings_store = await SettingsStoreImpl.get_instance(config, user_id)
    settings = await settings_store.load()
    
    # Join conversation
    event_stream = await conversation_manager.join_conversation(
        conversation_id, 
        connection_id, 
        settings, 
        user_id
    )

@sio.event
async def oh_action(connection_id: str, data: dict):
    await conversation_manager.send_to_event_stream(connection_id, data)

@sio.event
async def disconnect(connection_id: str):
    await conversation_manager.disconnect_from_session(connection_id)
```

## Key Components

### 1. Conversation Manager

The ConversationManager is the core component managing conversations and sessions:

```python
# server/conversation_manager/conversation_manager.py
class ConversationManager(ABC):
    """Abstract base class for managing conversations"""
    
    sio: socketio.AsyncServer
    config: AppConfig
    file_store: FileStore

    @abstractmethod
    async def attach_to_conversation(self, sid: str) -> Conversation | None:
        """Attach to an existing conversation or create a new one"""
        
    @abstractmethod
    async def join_conversation(
        self,
        sid: str,
        connection_id: str,
        settings: Settings,
        user_id: str | None
    ) -> EventStream | None:
        """Join a conversation and return its event stream"""

    @abstractmethod
    async def get_running_agent_loops(
        self,
        user_id: str | None = None,
        filter_to_sids: set[str] | None = None
    ) -> set[str]:
        """Get all running agent loops"""
```

The actual implementation is in StandaloneConversationManager:

```python
# server/conversation_manager/standalone_conversation_manager.py
@dataclass
class StandaloneConversationManager(ConversationManager):
    """Manages conversations in standalone mode"""
    
    _local_agent_loops_by_sid: dict[str, Session]
    _local_connection_id_to_session_id: dict[str, str]
    _active_conversations: dict[str, tuple[Conversation, int]]
    _detached_conversations: dict[str, tuple[Conversation, float]]
    
    async def attach_to_conversation(self, sid: str) -> Conversation | None:
        async with self._conversations_lock:
            # Check active conversations
            if sid in self._active_conversations:
                conversation, count = self._active_conversations[sid]
                self._active_conversations[sid] = (conversation, count + 1)
                return conversation
                
            # Check detached conversations
            if sid in self._detached_conversations:
                conversation, _ = self._detached_conversations.pop(sid)
                self._active_conversations[sid] = (conversation, 1)
                return conversation
                
            # Create new conversation
            conversation = Conversation(sid, self.file_store, self.config)
            await conversation.connect()
            self._active_conversations[sid] = (conversation, 1)
            return conversation
```

### 2. Event System

The event system handles communication between components:

```python
# events/stream.py
class EventStream:
    """Event streaming system"""
    
    subscribers: Dict[str, List[Callable]]
    history: List[Event]
    
    async def emit(self, event: Event):
        """Emit event to subscribers"""
        # Store in history
        self.history.append(event)
        
        # Notify subscribers
        for subscriber in self.subscribers:
            await subscriber(event)

# Wrapper for async iteration
class AsyncEventStreamWrapper:
    def __init__(self, event_stream: EventStream, start_index: int):
        self.event_stream = event_stream
        self.current_index = start_index
        
    async def __aiter__(self):
        while True:
            if self.current_index < len(self.event_stream.history):
                event = self.event_stream.history[self.current_index]
                self.current_index += 1
                yield event
```

### 3. Session Management

Sessions handle the lifecycle of conversations:

```python
# server/session/session.py
class Session:
    """Manages a user session"""
    
    def __init__(
        self,
        sid: str,
        file_store: FileStore,
        config: AppConfig,
        sio: socketio.AsyncServer,
        user_id: str | None
    ):
        self.sid = sid
        self.file_store = file_store
        self.config = config
        self.sio = sio
        self.user_id = user_id
        self.last_active_ts = time.time()
        
    async def initialize_agent(
        self,
        settings: Settings,
        initial_msg: MessageAction | None = None
    ):
        """Initialize agent for session"""
        self.agent_session = await create_agent_session(
            self.sid,
            self.file_store,
            self.config,
            settings
        )
        if initial_msg:
            await self.agent_session.event_stream.emit(initial_msg)
            
    async def dispatch(self, data: dict):
        """Dispatch action to agent"""
        self.last_active_ts = time.time()
        await self.agent_session.dispatch(data)
        
    async def close(self):
        """Close session"""
        if self.agent_session:
            await self.agent_session.close()
```

## System Flows

### 1. Connection Flow

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
        ├─► Attach to conversation
        │   - Get existing or create new
        │   - Initialize if new
        │
        ├─► Start agent loop
        │   - Create agent session
        │   - Initialize agent
        │   - Setup event handlers
        │
        └─► Setup event stream
            - Create AsyncEventStreamWrapper
            - Start event processing
```

### 2. Message Processing Flow

```plaintext
Client Action
    │
    ▼
Socket.IO oh_action event
    │
    ▼
ConversationManager.send_to_event_stream
    │
    ├─► Get session
    │   - Find session by connection ID
    │   - Validate session exists
    │
    └─► Session.dispatch
        │
        ├─► Update last active timestamp
        │
        └─► Agent session dispatch
            │
            ├─► Process action
            │   - Parse action
            │   - Update state
            │   - Generate response
            │
            └─► Emit events
                - Create observation
                - Notify subscribers
                - Update state
```

### 3. Cleanup Flow

```plaintext
Cleanup Task (runs every 15 seconds)
    │
    ├─► Clean detached conversations
    │   - Disconnect conversations
    │   - Clear from storage
    │
    ├─► Check inactive sessions
    │   - Find sessions past close_delay
    │   - Check agent state
    │   - Mark for closure
    │
    └─► Close marked sessions
        - Remove connection mappings
        - Close agent session
        - Clear from storage
```

## State Management

### 1. Connection State
- Managed by StandaloneConversationManager
- Maps connection IDs to session IDs
- Tracks active and detached conversations
- Handles session cleanup

### 2. Conversation State
- Managed by Conversation class
- Maintains event stream
- Handles agent sessions
- Manages file storage

### 3. Session State
- Managed by Session class
- Tracks last active timestamp
- Manages agent initialization
- Handles message dispatch

### 4. Agent State
- Managed by agent session
- Processes actions
- Maintains conversation context
- Generates responses

## Key Integration Points

### 1. FastAPI and Socket.IO
```python
# server/listen.py
base_app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi')
app = socketio.ASGIApp(sio, other_asgi_app=base_app)
```

### 2. Conversation and Event Stream
```python
# server/session/conversation.py
class Conversation:
    async def connect(self):
        self.event_stream = EventStream()
        await self.event_stream.initialize()
```

### 3. Session and Agent
```python
# server/session/session.py
class Session:
    async def initialize_agent(self, settings: Settings):
        self.agent_session = await create_agent_session(
            self.sid,
            self.file_store,
            self.config,
            settings
        )
```

## Best Practices

1. **Session Management**
   - Always check session existence before operations
   - Handle disconnections gracefully
   - Clean up resources properly

2. **Event Handling**
   - Use proper event types
   - Handle event errors gracefully
   - Maintain event order

3. **State Management**
   - Keep state consistent across components
   - Handle state transitions properly
   - Clean up state on session close

4. **Error Handling**
   - Handle connection errors
   - Manage session timeouts
   - Handle agent failures