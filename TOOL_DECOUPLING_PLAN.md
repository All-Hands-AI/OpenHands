# OpenHands Tool Decoupling - Complete Implementation Plan

## 🎯 Goal
Decouple AI agent tools into their own classes to encapsulate tool definitions, error validation, and response interpretation separate from regular agent LLM response processing.

## 📊 Current Status: CRITICAL MILESTONE ACHIEVED ✅

**function_calling.py Migration Complete**: Successfully migrated CodeActAgent to use unified tool validation for all 4 core tools!

### 🏗️ Architecture Summary
- **CodeActAgent**: 4 base tools (BashTool, FileEditorTool, BrowserTool, FinishTool)
- **ReadOnlyAgent**: Inherits FinishTool + adds 3 safe tools (ViewTool, GrepTool, GlobTool)
- **LocAgent**: Inherits all CodeAct tools + adds 3 search tools (SearchEntityTool, SearchRepoTool, ExploreStructureTool)

### 🚀 Migration Achievement: function_calling.py Complete
- ✅ **Fixed legacy tool import conflicts** with proper aliasing (LegacyBrowserTool, LegacyFinishTool)
- ✅ **Updated BrowserTool interface** to match legacy (code parameter instead of action)
- ✅ **All 4 core tools using unified validation**:
  - BashTool: `validate_parameters()` with proper error handling
  - FinishTool: `validate_parameters()` with parameter mapping (summary/outputs)
  - FileEditorTool: `validate_parameters()` with command handling (view/edit)
  - BrowserTool: `validate_parameters()` with code parameter validation
- ✅ **Fixed tool name constant references** throughout function_calling.py
- ✅ **Created comprehensive integration tests** verifying tool validation works
- ✅ **Maintained backward compatibility** with legacy fallback paths

### 🧪 Testing Status
- **192 total tests** (all passing)
- **Integration tests passing** for all 4 core tools
- **163 original tests**: Base Tool class, validation, error handling, inheritance patterns
- **29 new LocAgent tests**: Complete coverage of search tools and inheritance

### 🔧 Implementation Status
- ✅ **Tool base class** with abstract methods and validation framework
- ✅ **CodeAct tools** with full parameter validation and schema generation
- ✅ **ReadOnly tools** with inheritance pattern and safety validation
- ✅ **LocAgent tools** with complex parameter validation and search capabilities
- ✅ **Comprehensive test suite** covering all tools and edge cases
- ✅ **CodeActAgent function_calling.py migration** with unified tool validation

## Architecture Decision: Agent-Specific Tool Organization

After exploring the codebase, we discovered that **agent-specific tool organization** is the correct approach because:

1. **CodeActAgent** is the base agent with comprehensive tools (bash, file editing, browsing, etc.)
2. **ReadOnlyAgent** and **LocAgent** inherit from CodeActAgent but completely override `_get_tools()`
3. Each agent has its own `tools/` directory and `function_calling.py` module
4. Child agents can selectively inherit parent tools and add their own

## Current Architecture

```
openhands/agenthub/codeact_agent/tools/unified/
├── __init__.py          # Exports all CodeAct tools
├── base.py              # Tool base class with validation
├── bash_tool.py         # Full bash access
├── file_editor_tool.py  # File editing capabilities
├── browser_tool.py      # Web browsing
└── finish_tool.py       # Task completion

openhands/agenthub/readonly_agent/tools/unified/
├── __init__.py          # Imports FinishTool from CodeAct + own tools
├── view_tool.py         # Safe file/directory viewing
├── grep_tool.py         # Safe text search
└── glob_tool.py         # Safe file pattern matching

openhands/agenthub/loc_agent/tools/unified/
└── [TODO] Inherit from CodeAct + add search tools
```

## Implementation Status

### ✅ COMPLETED (Phase 1: Tool Architecture)
- [x] Base Tool class with schema definition and parameter validation
- [x] CodeAct unified tools (BashTool, FileEditorTool, BrowserTool, FinishTool)
- [x] ReadOnly unified tools (ViewTool, GrepTool, GlobTool)
- [x] Inheritance pattern: ReadOnly imports FinishTool from CodeAct parent
- [x] Parameter validation with comprehensive error handling
- [x] Schema generation compatible with LiteLLM function calling

### ✅ COMPLETED (Phase 2: Tool Architecture & Testing)
- [x] **Comprehensive unit tests** (192 tests, all passing)
- [x] **LocAgent tool organization** (inherit from CodeAct + add search tools)
- [x] All agent-specific tool architectures complete

### 🔄 IN PROGRESS (Phase 3: Integration & Migration)
- ✅ **CodeActAgent function_calling.py migration** (COMPLETED!)
- [ ] ReadOnlyAgent function_calling.py migration (NEXT)
- [ ] LocAgent function_calling.py migration (NEXT)

### 📋 TODO (Phase 3: Full Migration)
- [ ] Remove old tool definitions after migration complete
- [ ] Documentation and cleanup
- [ ] Performance testing and optimization

## Detailed Implementation Plan

### Phase 2: Testing & Integration (CURRENT)

#### 2.1 Comprehensive Unit Tests (IMMEDIATE)
Create `tests/unit/tools/` with complete test coverage:

**Base Infrastructure Tests:**
- `test_base_tool.py` - Tool base class, validation, error handling
- `test_tool_inheritance.py` - Agent inheritance patterns

**CodeAct Tool Tests:**
- `test_bash_tool.py` - BashTool schema and validation
- `test_file_editor_tool.py` - FileEditorTool schema and validation
- `test_browser_tool.py` - BrowserTool schema and validation
- `test_finish_tool.py` - FinishTool schema and validation

**ReadOnly Tool Tests:**
- `test_view_tool.py` - ViewTool schema and validation
- `test_grep_tool.py` - GrepTool schema and validation
- `test_glob_tool.py` - GlobTool schema and validation

**Integration Tests:**
- `test_agent_tool_integration.py` - Agent-specific tool loading
- `test_function_call_validation.py` - End-to-end function call processing

#### 2.2 Bridge Layer Implementation
- Create adapter functions in each agent's function_calling.py
- Gradual migration: new tools alongside existing ones
- Validation layer that uses new Tool classes

#### 2.3 Integration Points
- Update `openhands/agenthub/codeact_agent/function_calling.py`
- Update `openhands/agenthub/readonly_agent/function_calling.py`
- Ensure backward compatibility during transition

### Phase 3: Full Migration

#### 3.1 LocAgent Tool Organization ✅
```
openhands/agenthub/loc_agent/tools/unified/
├── __init__.py                    # Inherit from CodeAct + add search tools
├── search_entity_tool.py          # SearchEntityTool for entity retrieval
├── search_repo_tool.py            # SearchRepoTool for code snippet search
└── explore_structure_tool.py      # ExploreStructureTool for dependency analysis
```

#### 3.2 Complete Migration
- Replace all old tool definitions with new unified classes
- Update all function_calling.py modules
- Remove legacy tool code
- Update agent `_get_tools()` methods to use new architecture

#### 3.3 Cleanup & Documentation
- Remove unused tool files
- Update documentation
- Add migration guide for future tool additions

## Key Benefits of This Architecture

1. **Encapsulation**: Tool logic separated from agent processing
2. **Inheritance**: Child agents can reuse parent tools selectively
3. **Validation**: Centralized parameter validation with clear error messages
4. **Extensibility**: Easy to add new tools or modify existing ones
5. **Type Safety**: Proper typing and schema validation
6. **Testing**: Each tool can be unit tested independently

## Testing Strategy

### Unit Test Coverage Requirements
- **Schema Generation**: Verify correct LiteLLM-compatible schemas
- **Parameter Validation**: Test all validation rules and edge cases
- **Error Handling**: Test all error conditions and messages
- **Inheritance**: Verify child agents can inherit and extend parent tools
- **Integration**: Test function call processing end-to-end

### Test Categories
1. **Positive Tests**: Valid inputs produce expected outputs
2. **Negative Tests**: Invalid inputs produce appropriate errors
3. **Edge Cases**: Boundary conditions, empty values, type mismatches
4. **Integration Tests**: Agent-tool interaction, function calling flow

## Migration Strategy

1. **Parallel Implementation**: New tools alongside existing ones
2. **Gradual Adoption**: Migrate one agent at a time
3. **Backward Compatibility**: Maintain existing functionality during transition
4. **Validation**: Comprehensive testing at each step
5. **Cleanup**: Remove old code only after full migration

## Success Criteria

- [ ] All agents use unified tool architecture
- [ ] 100% test coverage for tool functionality
- [ ] No regression in existing functionality
- [ ] Clear separation of concerns between tools and agents
- [ ] Easy to add new tools or modify existing ones
- [ ] Comprehensive error handling and validation

## Current State Summary

**MAJOR MILESTONE ACHIEVED**: ReadOnlyAgent function_calling.py migration complete!

### Phase 2 Complete: Agent-Specific Tool Implementation ✅
- **CodeActAgent tools**: 4 unified tools (BashTool, FileEditorTool, BrowserTool, FinishTool)
- **ReadOnlyAgent tools**: 4 unified tools (ViewTool, GrepTool, GlobTool, FinishTool inherited)
- **LocAgent tools**: 3 specialized tools + all CodeAct tools inherited
- **All 192 tests passing** (163 original + 29 LocAgent tests)

### Phase 3 In Progress: function_calling.py Migration 🔄
- **CodeActAgent function_calling.py**: ✅ COMPLETE (unified validation for all 4 tools)
- **ReadOnlyAgent function_calling.py**: ✅ COMPLETE (unified validation for all 4 tools)
- **LocAgent function_calling.py**: ⏳ PENDING (next step)

### Architecture Summary
- **Tool Classes**: Encapsulate schema definition and parameter validation
- **Inheritance Pattern**: Child agents import parent tools + add their own
- **Validation Strategy**: Unified validation with legacy fallbacks
- **Error Handling**: Comprehensive ToolValidationError system
- **Testing**: 192 comprehensive unit tests covering all scenarios

**CURRENT**: LocAgent function_calling.py migration
**NEXT**: Final integration testing and cleanup
**GOAL**: Complete tool decoupling with zero regression
