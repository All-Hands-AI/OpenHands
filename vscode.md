# VSCode Integration Approaches

OpenHands can integrate with VSCode in three different ways, each serving different use cases:

## 1. VSCode Integration (Launcher) ✅ **Completed**
**Purpose**: Launch OpenHands from VSCode with context.

**How it works**:
- VSCode extension provides context menu commands and Command Palette entries
- User can start OpenHands with current file content, selected text, or new conversation
- Extension launches OpenHands in terminal with appropriate context
- Auto-installs when user runs OpenHands CLI in VSCode/Windsurf

**Use cases**:
- Quick OpenHands launch with file/selection context
- Seamless workflow from editing to AI assistance
- No need to manually copy-paste file contents

## 2. VSCode Runtime (Executor) ⭐ **Current Focus**
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

**Connection Flow**:
1. User starts OpenHands with `--runtime vscode`
2. OpenHands backend creates `VsCodeRuntime` instance (Python)
3. `VsCodeRuntime` connects to OpenHands Socket.IO server
4. VSCode extension connects to the same Socket.IO server (triggered by runtime activation)
5. Actions flow: Backend → Socket.IO → VSCode Extension → VSCode API
6. Observations flow: VSCode API → VSCode Extension → Socket.IO → Backend

**Use cases**:
- Leverage VSCode's file system access and workspace management
- Use VSCode's integrated terminal and debugging capabilities
- Access VSCode's language services and extensions
- Work within user's existing VSCode setup and configuration

## 3. VSCode Tab (Frontend)
**Purpose**: Display OpenHands UI as a tab within VSCode.

**How it works**:
- VSCode extension creates a webview panel
- Panel displays the OpenHands web interface
- Standard Socket.IO communication with OpenHands backend (running anywhere)
- Just another frontend client, like the web UI

**Use cases**:
- View OpenHands interface without leaving VSCode
- Alternative to browser-based UI
- Integrated development environment experience

---

## Extension Architecture Recommendation

### ✅ **Combine Tasks 1, 2, and 3 in One Extension**

**Rationale**:
- **Complementary workflows**: User launches OpenHands (Task 1) → OpenHands executes in VSCode (Task 2) → User views UI in VSCode tab (Task 3)
- **Shared infrastructure**: All three use Socket.IO communication and VSCode workspace utilities
- **Better user experience**: Single extension to install and configure
- **Natural user journey**: Complete VSCode ↔ OpenHands integration suite

**Architecture**:
```typescript
extension.ts
├── commands/           // Task 1: Context menu commands
├── runtime/           // Task 2: Action execution handler
├── webview/           // Task 3: OpenHands UI tab
├── services/
│   ├── socketio.ts    // Shared Socket.IO client/server
│   └── workspace.ts   // Shared VSCode utilities
└── types/             // Shared OpenHands types
```

**Activation patterns**:
- **Task 1**: On-demand (when user triggers commands)
- **Task 2**: Always listening (when OpenHands uses VSCode runtime)
- **Task 3**: On-demand (when user opens OpenHands tab)

**User stories**:
1. *"Launch OpenHands with my current file context"* → Task 1
2. *"Have OpenHands execute actions in my VSCode"* → Task 2
3. *"View OpenHands UI without leaving VSCode"* → Task 3

**Implementation strategy**:
- Rebase `vscode-runtime` branch on top of `vscode-integration` branch
- Expand existing extension with runtime capabilities (Task 2)
- Add webview panel for OpenHands UI (Task 3)
- Share Socket.IO service across all three tasks

---

## Socket.IO Infrastructure

OpenHands has existing Socket.IO infrastructure that all approaches leverage:

- **Server**: `openhands/server/shared.py` creates `socketio.AsyncServer`
- **Event Handlers**: `openhands/server/listen_socket.py` handles client connections
- **Event Flow**: Clients connect, send `oh_user_action` events, receive `oh_event` emissions
- **Consistency**: VSCode integrations use the same protocol as the web frontend

## Current Implementation Status

### ✅ **Task 1 - VSCode Integration (Completed)**
- Beautiful OpenHands submenu in context menu
- Smart dual naming strategy (short names in menu, full names in Command Palette)
- Auto-installation when running OpenHands CLI in VSCode/Windsurf
- Successfully tested and pushed to `vscode-integration` branch

### 🔧 **Task 2 - VSCode Runtime (In Progress)**
- VSCode Runtime implementation has been integrated with Task 1 extension
- Runtime action handler supports file operations (read, write, edit) and terminal commands
- Socket.IO communication established between OpenHands backend and VSCode extension
- VSCode extension can execute OpenHands actions within the VSCode environment
- Connection management with lazy initialization and error handling
- **Current work**: Refining functionality and ensuring robust operation

### 📋 **Task 3 - VSCode Tab (Planned)**
- Will be added to the combined extension
- Webview panel to display OpenHands UI
- Socket.IO client to connect to OpenHands backend

## Next Steps

1. ✅ **Rebase and combine**: Completed - `vscode-runtime` branch contains integrated functionality
2. 🔧 **Refine Task 2**: Currently working on making VSCode Runtime robust and reliable
3. **Add Task 3**: Implement webview panel for OpenHands UI
4. **Test integration**: Verify all three tasks work together seamlessly
5. **Update documentation**: Document the complete integration suite
