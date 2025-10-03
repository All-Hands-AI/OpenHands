# ACP Integration - SDK-Only Implementation ✅

**Date**: 2025-10-03  
**Integration Target**: openhands-cli  
**Approach**: Direct SDK integration (no agent-server dependency)  
**Status**: Complete - Ready for Testing

---

## Summary

We successfully integrated the Agent Client Protocol (ACP) into openhands-cli by:
1. **Copying** ACP implementation from agent-sdk
2. **Rewriting** to use SDK's `Conversation` class directly instead of agent-server's `ConversationService`
3. **Eliminating** the agent-server dependency entirely

---

## What Changed

### 1. ACP Implementation Copied & Modified

**Copied from** `agent-sdk/openhands/agent_server/acp/` **to** `openhands-cli/openhands_cli/acp/`

**Files**:
- `__init__.py` - Package initialization
- `__main__.py` - Standalone entry point
- `server.py` - **MODIFIED** to use SDK Conversation directly
- `events.py` - Event subscriber (unchanged)
- `utils.py` - Utility functions (unchanged)
- `README.md` - Original documentation
- `acp-server.spec` - PyInstaller spec
- `INTEGRATION.md` - New integration documentation

### 2. Key Rewrites in `server.py`

#### Before (Used agent-server):
```python
from openhands.agent_server.conversation_service import ConversationService
from openhands.agent_server.models import StartConversationRequest

class OpenHandsACPAgent:
    def __init__(self, conn, persistence_dir):
        self._conversation_service = ConversationService(
            event_services_path=persistence_dir
        )
        self._sessions: dict[str, str] = {}  # session_id -> conversation_id
        
    async def newSession(self, params):
        # Create agent...
        create_request = StartConversationRequest(agent=agent, workspace=workspace)
        conversation_info = await self._conversation_service.start_conversation(create_request)
        self._sessions[session_id] = str(conversation_info.id)
        
    async def prompt(self, params):
        conversation_id = self._sessions[session_id]
        event_service = await self._conversation_service.get_event_service(UUID(conversation_id))
        await event_service.send_message(message)
        await event_service.run()
```

#### After (Uses SDK directly):
```python
from openhands.sdk import (
    Agent,
    Conversation,
    Message,
    TextContent,
    Workspace,
)

class OpenHandsACPAgent:
    def __init__(self, conn, persistence_dir):
        self._persistence_dir = persistence_dir
        self._sessions: dict[str, Conversation] = {}  # session_id -> Conversation
        
    async def newSession(self, params):
        # Create agent...
        conversation = Conversation(
            agent=agent,
            workspace=workspace,
            persistence_dir=self._persistence_dir,
            conversation_id=UUID(session_id),
        )
        self._sessions[session_id] = conversation
        
    async def prompt(self, params):
        conversation = self._sessions[session_id]
        subscriber = EventSubscriber(session_id, self._conn)
        conversation.subscribe(subscriber)
        await conversation.send_message(message)
        conversation.unsubscribe(subscriber)
```

### 3. Dependencies Updated

**`pyproject.toml`**:

```toml
dependencies = [
  "openhands-sdk",      # ✅ Already had
  "openhands-tools",    # ✅ Already had
  "acp>=0.1.0",         # ✅ NEW - ACP protocol
  "prompt-toolkit>=3",
  "typer>=0.17.4",
]

# NO openhands-agent-server dependency needed! ✅
```

###4. CLI Integration

**`simple_main.py`** - Added ACP mode:

```python
def main() -> None:
    parser.add_argument("--acp", action="store_true", 
                       help="Run in ACP mode for editor integration")
    parser.add_argument("--persistence-dir", type=str,
                       help="Directory for storing ACP session data")
    
    if args.acp:
        from openhands_cli.acp.server import run_acp_server
        asyncio.run(run_acp_server(persistence_dir=Path(args.persistence_dir)))
        return
```

---

## Architecture

### Dependency Flow

```
openhands-cli
├── openhands-sdk ✅
│   ├── Agent
│   ├── Conversation  ← We use this!
│   ├── Message
│   └── ...
├── openhands-tools ✅
│   ├── BashTool
│   ├── FileEditorTool
│   └── ...
└── acp ✅
    └── Protocol implementation

NO agent-server dependency! ✨
```

### Execution Flow

```
User: openhands-cli --acp
  ↓
simple_main.py
  ↓
openhands_cli/acp/server.py::run_acp_server()
  ↓
OpenHandsACPAgent
  ├── newSession() → Creates SDK Conversation
  ├── prompt() → conversation.send_message()
  └── loadSession() → conversation.state.history
  ↓
SDK Conversation
  ├── Agent (LLM + tools)
  ├── Workspace
  └── Event subscribers
  ↓
Editor (via ACP protocol over stdin/stdout)
```

---

## Benefits of SDK-Only Approach

### ✅ Advantages

1. **Fewer Dependencies**: No agent-server needed
2. **Simpler Architecture**: Direct SDK usage
3. **Consistent with openhands-cli**: Same pattern as TUI mode
4. **Easier to Maintain**: Fewer layers of abstraction
5. **Smaller Bundle**: Less code to package
6. **Faster**: No extra service layer

### 🔄 Comparison

| Aspect | agent-server Approach | SDK-Only Approach |
|--------|----------------------|-------------------|
| **Dependencies** | +1 (agent-server) | 0 extra |
| **Complexity** | ConversationService + EventService | Conversation only |
| **Code Lines** | More abstraction layers | Direct SDK calls |
| **Consistency** | Different from TUI | Same as TUI |
| **Maintenance** | Track agent-server changes | Track SDK changes |

---

## Usage

### Installation

```bash
cd openhands-cli
uv sync
```

### Running

```bash
# Basic ACP mode
openhands-cli --acp

# With custom persistence directory
openhands-cli --acp --persistence-dir ~/.my-openhands

# With debug logging
DEBUG=true openhands-cli --acp
```

### Editor Configuration (Zed)

```json
{
  "agent_servers": {
    "OpenHands": {
      "command": "openhands-cli",
      "args": ["--acp"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

---

## Testing

### Manual Testing

1. **Start ACP server**:
   ```bash
   openhands-cli --acp
   ```

2. **Test initialize request**:
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":1,"clientCapabilities":{}}}' | openhands-cli --acp
   ```

3. **Test with editor**: Configure Zed and use agent commands

### Automated Testing

Create `tests/test_acp_integration.py`:

```python
import pytest
from unittest.mock import Mock, patch
from openhands_cli.acp.server import OpenHandsACPAgent

def test_acp_agent_initialization():
    """Test ACP agent can be created."""
    mock_conn = Mock()
    agent = OpenHandsACPAgent(mock_conn, Path("/tmp/test"))
    assert agent is not None
    assert len(agent._sessions) == 0

@pytest.mark.asyncio
async def test_new_session():
    """Test creating a new session."""
    mock_conn = Mock()
    agent = OpenHandsACPAgent(mock_conn, Path("/tmp/test"))
    
    # Create session request
    params = Mock()
    params.cwd = "/tmp/workspace"
    params.mcpServers = None
    
    response = await agent.newSession(params)
    
    assert response.sessionId in agent._sessions
    assert isinstance(agent._sessions[response.sessionId], Conversation)
```

---

## Files Changed

### Modified
1. **`pyproject.toml`** - Added acp dependency
2. **`simple_main.py`** - Added --acp flag and handler
3. **`README.md`** - Added ACP mode documentation

### Added
1. **`openhands_cli/acp/__init__.py`**
2. **`openhands_cli/acp/__main__.py`**
3. **`openhands_cli/acp/server.py`** (modified from agent-sdk)
4. **`openhands_cli/acp/events.py`**
5. **`openhands_cli/acp/utils.py`**
6. **`openhands_cli/acp/README.md`**
7. **`openhands_cli/acp/acp-server.spec`**
8. **`openhands_cli/acp/INTEGRATION.md`**

---

## Implementation Details

### Session Management

- **Before**: Session ID → Conversation ID → EventService
- **After**: Session ID → Conversation (direct)

### Message Handling

- **Before**: `event_service.send_message()` → `event_service.run()`
- **After**: `conversation.send_message()` (runs agent automatically)

### Event Streaming

- **Before**: `event_service.subscribe_to_events(subscriber)`
- **After**: `conversation.subscribe(subscriber)` (same pattern as TUI)

### Session Persistence

- **Before**: ConversationService manages persistence via EventService
- **After**: Conversation handles persistence directly via `persistence_dir`

---

## Troubleshooting

### Issue: Module not found errors

**Solution**: Run `uv sync` to install dependencies

### Issue: Conversation not persisting

**Solution**: Check `--persistence-dir` is writable

### Issue: Editor can't connect

**Solution**:
1. Check editor configuration
2. Verify API keys in environment
3. Enable debug: `DEBUG=true openhands-cli --acp`

### Debug Mode

```bash
DEBUG=true openhands-cli --acp 2>&1 | tee acp-debug.log
```

---

## Next Steps

### Immediate
1. [ ] Test basic functionality
2. [ ] Verify with Zed editor
3. [ ] Add automated tests
4. [ ] Update documentation

### Short-term
1. [ ] Performance testing
2. [ ] Edge case handling
3. [ ] Error handling improvements
4. [ ] CI/CD integration

### Long-term
1. [ ] Build standalone binary with ACP
2. [ ] Support more editors
3. [ ] Advanced ACP features
4. [ ] Performance optimizations

---

## Success Criteria

- [x] ACP files copied to openhands-cli
- [x] Rewritten to use SDK only
- [x] No agent-server dependency
- [x] CLI integration added (--acp flag)
- [x] Documentation updated
- [ ] Tests passing (to be added)
- [ ] Manual testing successful

---

## Why This Approach is Better

### 1. **Alignment with openhands-cli Architecture**

openhands-cli already uses SDK Conversation directly:
```python
# openhands_cli/setup.py
conversation = Conversation(
    agent=agent,
    workspace=Workspace(working_dir=WORK_DIR),
    persistence_dir=CONVERSATIONS_DIR,
    conversation_id=conversation_id
)
```

Our ACP implementation now uses the **exact same pattern**! ✅

### 2. **Simpler Dependency Graph**

**Before**:
```
openhands-cli
  → openhands-sdk
  → openhands-tools  
  → openhands-agent-server
      → openhands-sdk (duplicate!)
      → ConversationService
      → EventService
      → pub_sub module
```

**After**:
```
openhands-cli
  → openhands-sdk ✅
  → openhands-tools ✅
  → acp ✅
```

### 3. **Code Reuse**

Both TUI mode and ACP mode now share the same Conversation management:
- Same Agent creation
- Same Workspace setup
- Same event subscription pattern
- Same persistence mechanism

### 4. **Maintainability**

- Fewer dependencies to update
- Same patterns throughout codebase
- Easier to debug (fewer layers)
- Consistent behavior across modes

---

## Comparison: agent-server vs SDK-Only

| Feature | agent-server | SDK-Only |
|---------|--------------|----------|
| Create session | `ConversationService.start_conversation()` | `Conversation()` |
| Send message | `event_service.send_message()` | `conversation.send_message()` |
| Subscribe events | `event_service.subscribe_to_events()` | `conversation.subscribe()` |
| Get history | `conversation_info.events` | `conversation.state.history` |
| Persistence | EventService manages | Conversation manages |
| Dependencies | +agent-server | SDK only |
| Complexity | High | Low |
| Lines of code | More | Less |

---

## Resources

- **ACP Protocol**: https://agentclientprotocol.com
- **Agent-SDK**: https://github.com/All-Hands-AI/agent-sdk  
- **ACP Python SDK**: https://github.com/PsiACE/agent-client-protocol-python
- **Integration Guide**: `openhands_cli/acp/INTEGRATION.md`

---

## Summary

**What we did**: 
1. Copied ACP implementation from agent-sdk
2. Rewrote to use SDK Conversation directly
3. Eliminated agent-server dependency
4. Integrated with openhands-cli via --acp flag

**Result**: 
- Clean, simple integration
- Consistent with rest of openhands-cli
- Fewer dependencies
- Ready for testing

**Time**: ~1 hour

**Risk**: Low (additive feature, SDK-only)

**Impact**: High (enables editor ecosystem)

---

**Status**: ✅ Integration Complete (SDK-Only)  
**Next**: Testing with `uv sync && openhands-cli --acp`  
**Dependencies**: Only SDK + ACP (no agent-server!)

🎉 **ACP is now integrated into openhands-cli using SDK only!**
