# VSCode Runtime Analysis and Architecture

## What a VSCode Runtime Should Be Like

A VSCode Runtime should serve as an execution environment that allows OpenHands to perform actions directly within a user's VSCode instance.

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

**Architecture Documentation**:
- `/Users/enyst/repos/odie/vscode.md` - Overall VSCode integration architecture
- `/Users/enyst/repos/odie/openhands/integrations/vscode/README.md` - Extension documentation
