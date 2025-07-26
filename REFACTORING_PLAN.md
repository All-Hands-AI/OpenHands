# Tool Decoupling Refactoring Plan

## Current State Analysis

**Where we are:**
- New `openhands/tools/` module with unified Tool architecture (✅ committed)
- Existing tools scattered in `openhands/agenthub/codeact_agent/tools/` (old approach)
- Function calling logic hardcoded in `function_calling.py` with manual validation
- Multiple agents (codeact, loc, readonly) each have their own function_calling.py
- Tool schemas defined as dictionaries in individual tool files

**Key Integration Points:**
1. `openhands/agenthub/codeact_agent/function_calling.py` - main function call processor
2. `openhands/agenthub/codeact_agent/codeact_agent.py` - imports tools for schema generation
3. `openhands/agenthub/loc_agent/function_calling.py` - similar pattern
4. `openhands/agenthub/readonly_agent/function_calling.py` - similar pattern

## Target State

**Where we need to get to:**
- All agents use the new Tool classes for consistent behavior
- Function calling delegates to `Tool.validate_function_call()` for parameter validation
- Tool schemas come from `Tool.get_schema()`
- Action creation remains in function_calling.py (simple, no over-abstraction)
- Remove duplicated tool logic across agents
- **No registry needed** - agents directly import and use the tools they need

## Minimal Refactoring Strategy

### Phase 1: Create Bridge Layer (Non-breaking)
**Goal:** Make new tools work alongside existing system without breaking anything

1. **Create tool adapter in function_calling.py**
   - Add import for new `openhands.tools` (BashTool, FileEditorTool, etc.)
   - Create helper function `validate_with_new_tools()` that attempts new tool validation
   - Fall back to existing hardcoded logic if tool not found
   - This allows gradual migration without breaking existing functionality

2. **Update tool imports in codeact_agent.py**
   - Import new Tool classes alongside existing tool imports
   - Modify `get_tools()` method to include schemas from both old and new tools
   - Ensure no duplicate tool names

### Phase 2: Migrate Core Tools (One by one)
**Goal:** Replace existing tools with new implementations

1. **Start with bash tool (lowest risk)**
   - Update function_calling.py to use BashTool for execute_bash calls
   - Remove old bash tool logic once confirmed working
   - Keep old bash.py file temporarily for reference

2. **Migrate str_replace_editor tool**
   - Update function_calling.py to use FileEditorTool
   - Remove complex str_replace_editor logic from function_calling.py
   - Keep old str_replace_editor.py temporarily

3. **Migrate remaining tools one by one**
   - finish, browser, think, ipython, condensation_request
   - Each migration should be a separate commit for easy rollback

### Phase 3: Clean Up (Remove old code)
**Goal:** Remove duplicate/obsolete code

1. **Remove old tool files**
   - Delete `openhands/agenthub/codeact_agent/tools/` directory
   - Update imports in codeact_agent.py

2. **Simplify function_calling.py**
   - Remove all hardcoded tool logic
   - Replace with simple registry lookup and delegation
   - Should be ~50 lines instead of ~250 lines

### Phase 4: Extend to Other Agents (Optional)
**Goal:** Apply same pattern to loc_agent and readonly_agent

1. **Update loc_agent and readonly_agent**
   - Replace their function_calling.py with registry-based approach
   - Reuse same tool implementations

## Implementation Details

### Bridge Function (Phase 1)
```python
def validate_with_new_tools(tool_call):
    """Try new tool classes for validation, fall back to old logic"""
    from openhands.tools import BashTool, FileEditorTool

    # Map tool names to tool instances
    tools = {
        'execute_bash': BashTool(),
        'str_replace_editor': FileEditorTool(),
    }

    tool = tools.get(tool_call.function.name)
    if tool:
        try:
            return tool.validate_function_call(tool_call.function)
        except ToolValidationError as e:
            raise FunctionCallValidationError(str(e))

    # Fall back to existing hardcoded validation
    return None  # Signal to use old logic
```

### Simplified function_calling.py (Phase 3)
```python
def response_to_actions(response: ModelResponse, mcp_tool_names: list[str] | None = None) -> list[Action]:
    """Convert LLM response to OpenHands actions using new tool classes"""
    from openhands.tools import BashTool, FileEditorTool

    # Create tool instances (could be module-level for efficiency)
    tools = {
        'execute_bash': BashTool(),
        'str_replace_editor': FileEditorTool(),
    }

    actions = []
    # ... existing response parsing logic ...

    for tool_call in assistant_msg.tool_calls:
        tool = tools.get(tool_call.function.name)
        if tool:
            # Validate parameters using tool
            try:
                validated_params = tool.validate_function_call(tool_call.function)
            except ToolValidationError as e:
                raise FunctionCallValidationError(str(e))

            # Create action based on tool type (simple logic remains here)
            if tool_call.function.name == 'execute_bash':
                action = CmdRunAction(command=validated_params['command'], ...)
            elif tool_call.function.name == 'str_replace_editor':
                action = FileEditAction(path=validated_params['path'], ...)
            # ... etc for other tools

            actions.append(action)
        elif mcp_tool_names and tool_call.function.name in mcp_tool_names:
            # Handle MCP tools
            actions.append(MCPAction(...))
        else:
            raise FunctionCallNotExistsError(f'Tool {tool_call.function.name} not found')

    return actions
```

## Risk Mitigation

1. **Incremental approach** - Each phase can be tested independently
2. **Backward compatibility** - Bridge layer ensures nothing breaks during transition
3. **Easy rollback** - Each tool migration is a separate commit
4. **Minimal changes** - Don't touch agent logic, only function calling layer
5. **Keep it simple** - Don't over-engineer, just replace existing functionality

## Success Criteria

- [ ] All existing tests pass
- [ ] Function calling behavior unchanged from user perspective
- [ ] Tool logic consolidated in single location
- [ ] Easy to add new tools by extending Tool base class
- [ ] Reduced code duplication across agents
- [ ] Cleaner, more maintainable codebase

## Files to Modify

**Phase 1:**
- `openhands/agenthub/codeact_agent/function_calling.py` (add bridge)
- `openhands/agenthub/codeact_agent/codeact_agent.py` (import registry)

**Phase 2:**
- `openhands/agenthub/codeact_agent/function_calling.py` (migrate tools one by one)

**Phase 3:**
- `openhands/agenthub/codeact_agent/function_calling.py` (simplify)
- Remove `openhands/agenthub/codeact_agent/tools/` directory

**Phase 4 (Optional):**
- `openhands/agenthub/loc_agent/function_calling.py`
- `openhands/agenthub/readonly_agent/function_calling.py`

This plan prioritizes **working incrementally** while **maintaining stability** throughout the refactoring process.
