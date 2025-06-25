# VSCode Runtime Analysis and Architecture

## What a VSCode Runtime Should Be Like

A VSCode Runtime should serve as an execution environment that allows OpenHands to perform actions directly within a user's VSCode instance. The key characteristics should be:

### Architecture
- **On-Demand Connection**: Only connects to OpenHands backend when explicitly configured as runtime (e.g., `openhands --runtime vscode`)
- **Bidirectional Communication**: Uses Socket.IO to receive actions from OpenHands backend and send back observations
- **VSCode API Integration**: Leverages VSCode's extension API to perform file operations, terminal commands, and editor interactions
- **Workspace Awareness**: Operates within the user's current VSCode workspace context

### Connection Flow
1. User starts OpenHands with `--runtime vscode`
2. OpenHands backend creates `VsCodeRuntime` instance (Python)
3. `VsCodeRuntime` connects to OpenHands Socket.IO server
4. VSCode extension connects to the same Socket.IO server (triggered by runtime activation)
5. Actions flow: Backend → Socket.IO → VSCode Extension → VSCode API
6. Observations flow: VSCode API → VSCode Extension → Socket.IO → Backend

### Capabilities
- **File Operations**: Read, write, create, delete files in workspace
- **Editor Control**: Open files, navigate to lines, make edits
- **Terminal Integration**: Execute commands in VSCode's integrated terminal
- **Workspace Navigation**: Browse directory structure, search files
- **Extension Ecosystem**: Potentially leverage other VSCode extensions

## What Current VSCode Implementation Does

### Current Behavior (Problematic)
The current implementation has architectural issues:

1. **Automatic Connection on Activation**:
   - Extension connects to backend immediately when VSCode starts
   - This happens regardless of whether OpenHands is actually using VSCode as runtime
   - Connection attempt occurs in `initializeRuntime()` during extension activation

2. **Always-On Socket Service**:
   - `SocketService` is initialized and attempts connection on every extension startup
   - Creates unnecessary network traffic and error logs when backend isn't running
   - Doesn't align with the intended on-demand usage pattern

3. **Mixed Responsibilities**:
   - Extension combines launcher functionality (which doesn't need socket connection) with runtime functionality (which does)
   - No clear separation between when socket connection is needed vs. not needed

### Current Code Structure
```typescript
// In extension.ts activate()
async function initializeRuntime(context: vscode.ExtensionContext): Promise<void> {
  // Creates socket service immediately
  socketService = new SocketService(serverUrl);

  // Attempts connection regardless of whether it's needed
  try {
    await socketService.connect();
    // Success message shown to user
  } catch (error) {
    // Error silently logged but extension continues
  }
}
```

### What Works
- **Socket.IO Communication**: The `SocketService` class correctly implements Socket.IO client
- **Action Handler**: `VSCodeRuntimeActionHandler` has proper structure for handling OpenHands actions
- **VSCode API Usage**: Extension properly uses VSCode APIs for file operations and terminal control
- **Event Flow**: Proper event listener setup for receiving actions and sending observations

### What's Broken
- **Connection Timing**: Connects too early (on activation) instead of on-demand
- **User Experience**: Shows connection success/failure messages when user hasn't requested runtime functionality
- **Resource Usage**: Maintains unnecessary connections and services when not needed
- **Architecture Mismatch**: Doesn't follow the intended runtime activation pattern

## Recommended Fixes

1. **Remove Automatic Connection**: Don't connect to backend on extension activation
2. **Add Runtime Activation Command**: Provide a way for OpenHands backend to signal the extension to connect
3. **Separate Concerns**: Clearly separate launcher functionality from runtime functionality
4. **Connection State Management**: Only initialize socket services when runtime mode is activated
5. **User Feedback**: Only show runtime-related messages when user is actually using runtime features

## BREAKTHROUGH: Socket.IO Architecture IS Correct!

After deeper analysis, I now understand that the Socket.IO approach is actually brilliant and correct:

### The Real Architecture (Socket.IO as Message Broker)
1. **Main OpenHands Socket.IO Server**: Central message broker (like in web frontend)
2. **VSCode Extension**: Connects as Socket.IO client (like web frontend)
3. **VsCodeRuntime**: Uses Socket.IO server to route events to specific connections
4. **Communication**: Socket.IO events routed through main server

### How It Actually Works
1. **VSCode Extension connects**: Gets conversation_id, becomes a Socket.IO client
2. **VsCodeRuntime gets connection**: Receives socket_connection_id of VSCode Extension
3. **Event routing**: `sio_server.emit('oh_event', payload, to=socket_connection_id)`
4. **VSCode Extension receives**: Executes action, sends back observation via Socket.IO

### This Architecture Makes Perfect Sense!
- **Reuses existing infrastructure**: Same Socket.IO server as web frontend
- **Consistent with OpenHands**: Web frontend and VSCode Extension are both "clients"
- **Elegant message routing**: Socket.IO server handles all the routing
- **No need for separate HTTP server**: VSCode Extension doesn't need to run its own server

### The Real Problems Identified

#### 1. **Missing Constructor Parameters**
VsCodeRuntime requires `sio_server` and `socket_connection_id` parameters, but AgentSession only passes standard runtime parameters:

```python
# In agent_session.py - only standard parameters passed
self.runtime = runtime_cls(
    config=config,
    event_stream=self.event_stream,
    sid=self.sid,
    plugins=agent.sandbox_plugins,
    # ... other standard params
    # ❌ Missing: sio_server, socket_connection_id
)

# In VsCodeRuntime constructor - VSCode-specific params default to None
def __init__(self,
    # ... standard params
    sio_server: socketio.AsyncServer | None = None,  # ❌ Defaults to None
    socket_connection_id: str | None = None,         # ❌ Defaults to None
):
```

#### 2. **Connection Coordination Problem**
- VSCode Extension connects to Socket.IO server and gets a connection_id
- VsCodeRuntime needs that same connection_id to send events
- **But there's no mechanism to pass the connection_id from extension to runtime!**

#### 3. **Timing Issues**
- VSCode Extension connects automatically on startup
- VsCodeRuntime is created later when user starts a conversation
- Connection happens before runtime needs it (should be on-demand)

#### 4. **Architecture Gap**
- Socket.IO server exists (`sio` in `shared.py`)
- VSCode Extension connects as client
- VsCodeRuntime needs reference to server + connection_id
- **Missing: coordination mechanism between extension and runtime**

## Proposed Solution: Runtime Registration Pattern

### Core Idea: VSCode Extension Registers with OpenHands Server

Instead of trying to pass connection_id to runtime, flip the approach:

1. **VSCode Extension connects** to Socket.IO server (as it does now)
2. **Extension registers itself** as available VSCode runtime via API call
3. **OpenHands server stores** the mapping: `vscode_instance_id → socket_connection_id`
4. **VsCodeRuntime queries server** for available VSCode connections
5. **Runtime uses server's Socket.IO** to communicate with extension

### Implementation Steps

#### Step 1: VSCode Extension Registration
```typescript
// After Socket.IO connection established
const response = await fetch(`${serverUrl}/api/vscode/register`, {
    method: 'POST',
    body: JSON.stringify({
        socket_connection_id: this.socket.id,
        workspace_path: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
        capabilities: ['file_operations', 'terminal', 'editor']
    })
});
```

#### Step 2: Server-Side Registry
```python
# New endpoint in OpenHands server
@app.post("/api/vscode/register")
async def register_vscode_runtime(request: VSCodeRegistrationRequest):
    # Store mapping in memory/redis
    vscode_registry[request.socket_connection_id] = {
        'workspace_path': request.workspace_path,
        'capabilities': request.capabilities,
        'registered_at': datetime.now()
    }
```

#### Step 3: VsCodeRuntime Integration
```python
class VsCodeRuntime(Runtime):
    def __init__(self, config, event_stream, sid, **kwargs):
        super().__init__(config, event_stream, sid, **kwargs)
        # Get sio_server from shared.py (already exists)
        from openhands.server.shared import sio
        self.sio_server = sio
        self.socket_connection_id = None  # Will be set on connect()

    async def connect(self):
        # Query server for available VSCode connections
        available_connections = await self._get_available_vscode_connections()
        if not available_connections:
            raise RuntimeError("No VSCode extension connected")

        # Use first available connection (or let user choose)
        self.socket_connection_id = available_connections[0]['socket_connection_id']
```

### Benefits of This Approach
1. **No constructor changes needed** - VsCodeRuntime gets sio_server from shared.py
2. **Dynamic connection discovery** - Runtime finds available VSCode instances
3. **Proper lifecycle management** - Extension registers/unregisters itself
4. **Multiple VSCode support** - Could support multiple VSCode instances
5. **Clean separation** - Extension handles connection, runtime handles execution

## Next Steps

1. **Implement VSCode registration API endpoint** in OpenHands server
2. **Update VSCode Extension** to register after Socket.IO connection
3. **Modify VsCodeRuntime.connect()** to discover available connections
4. **Test the coordination mechanism** end-to-end
5. **Handle edge cases** (disconnections, multiple instances, etc.)

## References

**Source Code Analysis**:
- `/Users/enyst/repos/odie/openhands/integrations/vscode/src/extension.ts` - Main extension file with automatic connection logic
- `/Users/enyst/repos/odie/openhands/integrations/vscode/src/services/socket-service.ts` - Socket.IO client implementation
- `/Users/enyst/repos/odie/openhands/integrations/vscode/src/services/runtime-action-handler.ts` - Action handling logic
- `/Users/enyst/repos/odie/openhands/runtime/vscode/vscode_runtime.py` - Python runtime implementation

**Architecture Documentation**:
- `/Users/enyst/repos/odie/vscode.md` - Overall VSCode integration architecture
- `/Users/enyst/repos/odie/openhands/integrations/vscode/README.md` - Extension documentation
