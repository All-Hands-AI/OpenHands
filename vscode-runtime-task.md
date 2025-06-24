# VSCode Runtime Implementation Analysis - Corrected

## What a VSCode Runtime Should Be

A VSCode Runtime should implement the OpenHands Runtime interface to execute actions within the VSCode environment. Based on the actual Actions and Observations defined in `openhands.events`:

### Actual Actions in OpenHands
From `openhands/events/action/__init__.py`:
- `CmdRunAction` - Execute shell commands
- `FileReadAction` - Read file contents
- `FileWriteAction` - Write file contents
- `FileEditAction` - Edit files (create, str_replace, insert, undo_edit, view)
- `BrowseURLAction` - Browse URLs
- `BrowseInteractiveAction` - Interactive browsing
- `IPythonRunCellAction` - Execute Python code
- `AgentFinishAction`, `MessageAction`, etc.

### Actual Observations in OpenHands
From `openhands/events/observation/__init__.py`:
- `CmdOutputObservation` - Command execution results
- `FileReadObservation` - File read results
- `FileWriteObservation` - File write results
- `FileEditObservation` - File edit results
- `BrowserOutputObservation` - Browse results
- `IPythonRunCellObservation` - Python execution results
- `ErrorObservation` - Error results
- `NullObservation` - No-op results

### Required Abstract Methods (from Runtime base class)
```python
@abstractmethod
def run(self, action: CmdRunAction) -> Observation:
@abstractmethod
def run_ipython(self, action: IPythonRunCellAction) -> Observation:
@abstractmethod
def read(self, action: FileReadAction) -> Observation:
@abstractmethod
def write(self, action: FileWriteAction) -> Observation:
@abstractmethod
def edit(self, action: FileEditAction) -> Observation:
@abstractmethod
def browse(self, action: BrowseURLAction) -> Observation:
@abstractmethod
def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
@abstractmethod
async def call_tool_mcp(self, action: MCPAction) -> Observation:
```

## Current Implementation Issues

### ❌ **Hallucinated Actions and Methods**

**Problem**: VSCode runtime implements methods for actions that don't exist:

```python
async def mkdir(self, action: Action) -> Observation:  # ❌ MkdirAction doesn't exist
async def rmdir(self, action: Action) -> Observation:  # ❌ RmdirAction doesn't exist
async def rm(self, action: Action) -> Observation:    # ❌ RemoveAction doesn't exist
```

**Reality**: These action types are not defined in OpenHands. Directory operations are handled through:
- `CmdRunAction` for shell commands like `mkdir`, `rmdir`, `rm`
- `FileEditAction` with `command='create'` for creating files/directories

**Fix**: Remove these methods entirely.

### ❌ **Missing Required Abstract Methods**

**Problem**: VSCode runtime is missing required abstract methods:

```python
# Missing:
def edit(self, action: FileEditAction) -> Observation:           # ❌ Required
def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:  # ❌ Required
async def call_tool_mcp(self, action: MCPAction) -> Observation:  # ❌ Required
```

**Fix**: Implement all required abstract methods from Runtime base class.

### ❌ **Incorrect Method Signatures**

**Problem**: Some methods have wrong signatures:

```python
# Current (wrong):
async def run(self, action: CmdRunAction) -> Observation:  # ❌ Should not be async
async def read(self, action: FileReadAction) -> Observation:  # ❌ Should not be async

# Correct (from base class):
def run(self, action: CmdRunAction) -> Observation:  # ✅ Sync method
def read(self, action: FileReadAction) -> Observation:  # ✅ Sync method
```

**Fix**: Match the exact signatures from Runtime base class.

### ❌ **Non-Standard Methods**

**Problem**: VSCode runtime implements methods not in the Runtime interface:

```python
async def recall(self, action: RecallAction) -> Observation:     # ❌ Not in Runtime interface
async def finish(self, action: AgentFinishAction) -> Observation:  # ❌ Not in Runtime interface
async def send_message(self, action: MessageAction) -> Observation:  # ❌ Not in Runtime interface
```

**Reality**: These actions are handled by the AgentController, not the Runtime.

**Fix**: Remove these methods. Runtime only handles execution actions.

## Corrected Implementation Requirements

### ✅ **Required Methods Only**
```python
class VsCodeRuntime(Runtime):
    # Required abstract methods:
    def run(self, action: CmdRunAction) -> Observation:
    def run_ipython(self, action: IPythonRunCellAction) -> Observation:
    def read(self, action: FileReadAction) -> Observation:
    def write(self, action: FileWriteAction) -> Observation:
    def edit(self, action: FileEditAction) -> Observation:
    def browse(self, action: BrowseURLAction) -> Observation:
    def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
    async def call_tool_mcp(self, action: MCPAction) -> Observation:
```

### ✅ **Correct Action-Observation Mapping**
```python
# CmdRunAction → CmdOutputObservation
def run(self, action: CmdRunAction) -> Observation:
    # Send to VSCode, expect CmdOutputObservation back

# FileReadAction → FileReadObservation
def read(self, action: FileReadAction) -> Observation:
    # Send to VSCode, expect FileReadObservation back

# FileWriteAction → FileWriteObservation
def write(self, action: FileWriteAction) -> Observation:
    # Send to VSCode, expect FileWriteObservation back

# FileEditAction → FileEditObservation
def edit(self, action: FileEditAction) -> Observation:
    # Send to VSCode, expect FileEditObservation back
```

### ✅ **Directory Operations via Existing Actions**
```python
# Instead of mkdir/rmdir/rm methods, handle via:

# Directory creation via shell command:
CmdRunAction(command="mkdir -p /path/to/dir")  # → CmdOutputObservation

# File creation via edit:
FileEditAction(path="/path/to/file", command="create", file_text="content")  # → FileEditObservation

# File/directory removal via shell command:
CmdRunAction(command="rm -rf /path/to/target")  # → CmdOutputObservation
```

## Socket.IO Integration (Correct)

### ✅ **Architecture is Sound**
The Socket.IO integration is correct:
- Uses existing `socketio.AsyncServer` from `openhands/server/shared.py`
- Emits `oh_event` to VSCode extension client
- Expects observations back via Socket.IO
- Proper event correlation with UUIDs

### ✅ **Event Protocol**
```python
oh_event_payload = {
    'event_id': str(uuid.uuid4()),
    'action': action.__class__.__name__,  # e.g., "CmdRunAction"
    'args': action.__dict__,
    'message': getattr(action, 'message', '')
}
```

## Next Steps

1. **Remove hallucinated methods**: Delete `mkdir`, `rmdir`, `rm`, `recall`, `finish`, `send_message`
2. **Add missing required methods**: Implement `edit`, `browse_interactive`, `call_tool_mcp`
3. **Fix method signatures**: Remove `async` from sync methods, match base class exactly
4. **Test with actual actions**: Verify runtime works with real Action instances
5. **Implement VSCode extension**: Create TypeScript side to handle the Socket.IO events

## Conclusion

The VSCode Runtime has the **correct architectural approach** with Socket.IO, but implements **wrong action types**. The main issues are:

1. **Hallucinated actions** - implementing methods for actions that don't exist
2. **Missing required methods** - not implementing all abstract methods from base class
3. **Wrong signatures** - async methods that should be sync
4. **Scope creep** - implementing agent-level actions instead of just execution actions

Once these are fixed, the runtime should work correctly with OpenHands' existing infrastructure.
