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

## Correct Architecture Based on OpenHands Runtime Pattern

After analyzing other OpenHands runtimes (DockerRuntime, etc.), the correct architecture should be:

### Standard OpenHands Runtime Pattern
1. **Runtime Class (Client)**: Inherits from `ActionExecutionClient`
2. **Action Execution Server**: Runs `action_execution_server.py` or equivalent
3. **Communication**: HTTP/REST API between client and server
4. **Server Startup**: Runtime class starts the server

### VSCode Runtime Should Follow This Pattern
1. **VsCodeRuntime (Client)**: Should inherit from `ActionExecutionClient` (not current Socket.IO approach)
2. **VSCode Extension (Server)**: Should run an HTTP server (not connect to main Socket.IO server)
3. **Communication**: HTTP/REST API between VsCodeRuntime and VSCode Extension
4. **Server Startup**: VsCodeRuntime should signal VSCode extension to start its HTTP server

### Current Implementation Problems
- **Wrong Architecture**: VsCodeRuntime tries to use main Socket.IO server as message broker
- **Wrong Inheritance**: Should inherit from `ActionExecutionClient`, not base `Runtime`
- **Wrong Communication**: Should use HTTP/REST API, not Socket.IO to main server
- **Wrong Server**: VSCode extension tries to connect as client, should act as server

### Questions for Implementation

1. **Server Startup**: How should VsCodeRuntime signal the VSCode extension to start its HTTP server?
   - File-based signaling (create a file that extension watches)
   - VSCode command that VsCodeRuntime can trigger
   - Environment variable or configuration file

2. **Port Management**: How should the HTTP server port be determined and communicated?
   - Fixed port (like 40000-49999 range mentioned in DockerRuntime)
   - Dynamic port discovery
   - Configuration-based port assignment

3. **Extension Lifecycle**: Should the HTTP server run continuously or only when needed?
   - Always running when extension is active
   - Start/stop on demand when VsCodeRuntime needs it

4. **Multiple Instances**: How to handle multiple OpenHands instances using VSCode runtime?
   - Multiple ports for multiple instances
   - Queue/multiplexing on single port
   - Reject additional instances

## References

**Source Code Analysis**:
- `/Users/enyst/repos/odie/openhands/integrations/vscode/src/extension.ts` - Main extension file with automatic connection logic
- `/Users/enyst/repos/odie/openhands/integrations/vscode/src/services/socket-service.ts` - Socket.IO client implementation
- `/Users/enyst/repos/odie/openhands/integrations/vscode/src/services/runtime-action-handler.ts` - Action handling logic
- `/Users/enyst/repos/odie/openhands/runtime/vscode/vscode_runtime.py` - Python runtime implementation

**Architecture Documentation**:
- `/Users/enyst/repos/odie/vscode.md` - Overall VSCode integration architecture
- `/Users/enyst/repos/odie/openhands/integrations/vscode/README.md` - Extension documentation