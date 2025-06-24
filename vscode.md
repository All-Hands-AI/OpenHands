# VSCode Integration Approaches

OpenHands can integrate with VSCode in three different ways, each serving different use cases:

## 1. VSCode Extension Approach
**Purpose**: Bring OpenHands functionality directly into the VSCode editor interface.

**How it works**:
- VSCode extension (TypeScript) provides UI panels, commands, and editor integrations
- Extension communicates with OpenHands backend via Socket.IO (same protocol as web frontend)
- Users interact with OpenHands through VSCode's native interface (panels, command palette, etc.)

**Use cases**:
- Code assistance and generation within the editor
- File operations with visual feedback
- Integrated chat interface
- Code review and suggestions

## 2. VSCode Runtime Approach ⭐ **(Current Focus)**
**Purpose**: Use VSCode as the execution environment for OpenHands actions.

**How it works**:
- OpenHands AgentController sends actions to VSCode Runtime (Python)
- VSCode Runtime forwards actions to VSCode Extension via Socket.IO
- VSCode Extension executes actions using VSCode API (file ops, terminal, etc.)
- VSCode Extension sends observations back via Socket.IO
- VSCode Runtime returns observations to AgentController

**Architecture**:
```
AgentController → VSCodeRuntime → Socket.IO Server → VSCode Extension → VSCode API
                                      ↑                    ↓
                                 Socket.IO ← Observations ←
```

**Use cases**:
- Leverage VSCode's file system access and workspace management
- Use VSCode's integrated terminal and debugging capabilities
- Access VSCode's language services and extensions
- Work within user's existing VSCode setup and configuration

## 3. VSCode Tab Approach
**Purpose**: Embed OpenHands web interface as a tab within VSCode.

**How it works**:
- VSCode extension creates a webview panel
- Panel loads the OpenHands web interface
- Standard Socket.IO communication with OpenHands backend
- VSCode provides the container, OpenHands runs as usual

**Use cases**:
- Quick access to OpenHands without leaving VSCode
- Minimal integration effort
- Familiar web interface within editor context
- Good for users who prefer the web UI but want editor integration

---

## Socket.IO Infrastructure

OpenHands has existing Socket.IO infrastructure that all approaches leverage:

- **Server**: `openhands/server/shared.py` creates `socketio.AsyncServer`
- **Event Handlers**: `openhands/server/listen_socket.py` handles client connections
- **Event Flow**: Clients connect, send `oh_user_action` events, receive `oh_event` emissions
- **Consistency**: VSCode integrations use the same protocol as the web frontend

## Current Implementation Status

We are currently implementing the **VSCode Runtime approach** (`vscode_runtime.py`), which allows OpenHands to use VSCode as its execution environment.

### Implementation Issues Identified

The current VSCode Runtime implementation has several issues:

1. **Hallucinated Actions**: Implements methods for actions that don't exist in OpenHands:
   - `mkdir()`, `rmdir()`, `rm()` - these action types don't exist
   - Directory operations should use `CmdRunAction` or `FileEditAction`

2. **Missing Required Methods**: Doesn't implement all abstract methods from Runtime base class:
   - `edit()` for `FileEditAction`
   - `browse_interactive()` for `BrowseInteractiveAction`
   - `call_tool_mcp()` for `MCPAction`

3. **Wrong Method Signatures**: Some methods are async when they should be sync to match base class

4. **Scope Issues**: Implements agent-level actions (`finish`, `recall`, `send_message`) that should be handled by AgentController

### Actual OpenHands Actions
- `CmdRunAction` - Execute shell commands
- `FileReadAction` - Read files
- `FileWriteAction` - Write files
- `FileEditAction` - Edit files (create, str_replace, insert, etc.)
- `BrowseURLAction` - Browse URLs
- `IPythonRunCellAction` - Execute Python code

The Socket.IO architecture is correct, but the action handling needs to be fixed to match OpenHands' actual event system.
