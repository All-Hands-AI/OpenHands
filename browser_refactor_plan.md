# Browser Refactoring Plan: Replacing BrowserGym with Browser-Use

## Overview

This document outlines the plan to refactor OpenHands' browser functionality from BrowserGym to Browser-Use library. The goal is to replace the current BrowserGym-based implementation with Browser-Use's low-level APIs while maintaining all existing functionality.

## Current Architecture Analysis

### Current BrowserGym Integration Points

1. **Core Browser Environment** (`openhands/runtime/browser/browser_env.py`)
   - Uses BrowserGym's gym environment interface
   - Supports evaluation modes (webarena, miniwob, visualwebarena)
   - Multiprocessing architecture with pipe communication
   - Handles screenshots, DOM extraction, and accessibility tree

2. **Action Definitions** (`openhands/events/action/browse.py`)
   - `BrowseURLAction`: Simple URL navigation
   - `BrowseInteractiveAction`: Full BrowserGym action support
   - Includes `browsergym_send_msg_to_user` field

3. **Observation Definitions** (`openhands/events/observation/browse.py`)
   - `BrowserOutputObservation`: Rich observation data
   - Includes screenshots, DOM objects, accessibility tree, etc.

4. **Agent Implementations**
   - `BrowsingAgent` (`openhands/agenthub/browsing_agent/`)
   - `VisualBrowsingAgent` (`openhands/agenthub/visualbrowsing_agent/`)
   - `CodeActAgent` browser tool (`openhands/agenthub/codeact_agent/tools/browser.py`)

5. **Configuration** (`openhands/core/config/sandbox_config.py`)
   - `browsergym_eval_env` configuration option

6. **Evaluation Benchmarks**
   - WebArena, MiniWoB, VisualWebArena evaluation scripts
   - Success rate calculation scripts

## Browser-Use Library Analysis

### Key Components

1. **Controller Service** (`browser_use/controller/service.py`)
   - Action registry system
   - Built-in actions: search_google, go_to_url, click_element, input_text, etc.
   - Extensible action system

2. **Action Models** (`browser_use/controller/views.py`)
   - Structured action parameters
   - Type-safe action definitions

3. **Browser Session** (`browser_use/browser/`)
   - Playwright-based browser control
   - Tab management
   - Page navigation and interaction

4. **Types** (`browser_use/browser/types.py`)
   - Unified Playwright/Patchright types
   - Page, Browser, ElementHandle abstractions

## Refactoring Strategy

### Phase 1: Core Browser Environment Replacement

#### 1.1 Create New Browser Environment
- **File**: `openhands/runtime/browser/browser_use_env.py`
- **Purpose**: Replace `browser_env.py` with Browser-Use implementation
- **Key Changes**:
  - Remove gymnasium dependency
  - Use Browser-Use's BrowserSession directly
  - Maintain multiprocessing architecture for compatibility
  - Implement equivalent observation structure

#### 1.2 Browser-Use Action Integration
- **Purpose**: Use Browser-Use's native action system directly
- **Strategy**:
  - Remove BrowserGym action string parsing
  - Use Browser-Use's structured action models directly
  - Update agents to generate Browser-Use actions instead of BrowserGym strings

#### 1.3 Observation Adapter
- **File**: `openhands/runtime/browser/observation_adapter.py`
- **Purpose**: Convert Browser-Use observations to OpenHands format
- **Key Features**:
  - Screenshot capture and base64 encoding
  - DOM extraction and flattening
  - Accessibility tree generation
  - Error handling and status reporting

### Phase 2: Action and Observation Updates

#### 2.1 Update Action Definitions
- **File**: `openhands/events/action/browse.py`
- **Changes**:
  - Remove `browsergym_send_msg_to_user` field
  - Update to use Browser-Use action models directly
  - Replace string-based actions with structured Browser-Use actions

#### 2.2 Update Observation Definitions
- **File**: `openhands/events/observation/browse.py`
- **Changes**:
  - Ensure compatibility with new observation structure
  - Add any Browser-Use specific fields
  - Maintain existing field names for compatibility

### Phase 3: Agent Updates

#### 3.1 Update BrowsingAgent
- **File**: `openhands/agenthub/browsing_agent/browsing_agent.py`
- **Changes**:
  - Remove BrowserGym HighLevelActionSet dependency
  - Implement Browser-Use action generation using structured action models
  - Update response parsing for Browser-Use action format

#### 3.2 Update VisualBrowsingAgent
- **File**: `openhands/agenthub/visualbrowsing_agent/visualbrowsing_agent.py`
- **Changes**:
  - Similar updates to BrowsingAgent
  - Ensure visual capabilities are maintained

#### 3.3 Update CodeActAgent Browser Tool
- **File**: `openhands/agenthub/codeact_agent/tools/browser.py`
- **Changes**:
  - Replace BrowserGym action descriptions with Browser-Use action models
  - Update tool parameter descriptions to match Browser-Use action fields
  - Maintain existing API for tool calls

### Phase 4: Configuration and Infrastructure

#### 4.1 Update Configuration
- **File**: `openhands/core/config/sandbox_config.py`
- **Changes**:
  - Replace `browsergym_eval_env` with `browser_use_config`
  - Add Browser-Use specific configuration options
  - Remove BrowserGym configuration entirely

#### 4.2 Update Action Execution Server
- **File**: `openhands/runtime/action_execution_server.py`
- **Changes**:
  - Replace BrowserEnv with BrowserUseEnv
  - Update initialization parameters
  - Maintain existing API

#### 4.3 Update Command Generation
- **File**: `openhands/runtime/utils/command.py`
- **Changes**:
  - Replace browsergym arguments with browser-use arguments
  - Update startup command generation

### Phase 5: Evaluation and Testing

#### 5.1 Update Evaluation Scripts
- **Files**:
  - `evaluation/benchmarks/webarena/run_infer.py`
  - `evaluation/benchmarks/miniwob/run_infer.py`
  - `evaluation/benchmarks/visualwebarena/run_infer.py`
- **Changes**:
  - Remove BrowserGym imports
  - Update evaluation environment setup
  - Maintain evaluation metrics and success rate calculations

#### 5.2 Update Success Rate Scripts
- **Files**:
  - `evaluation/benchmarks/webarena/get_success_rate.py`
  - `evaluation/benchmarks/miniwob/get_avg_reward.py`
  - `evaluation/benchmarks/visualwebarena/get_success_rate.py`
- **Changes**:
  - Remove BrowserGym environment registration
  - Update metric calculation logic

### Phase 6: Dependencies and Cleanup

#### 6.1 Update Dependencies
- **File**: `pyproject.toml`
- **Changes**:
  - Remove BrowserGym dependencies:
    - `browsergym-core`
    - `browsergym`
    - `browsergym-webarena`
    - `browsergym-miniwob`
    - `browsergym-visualwebarena`
  - Add Browser-Use dependency:
    - `browser-use`

#### 6.2 Cleanup Imports
- **Files**: All files with BrowserGym imports
- **Changes**:
  - Remove all `browsergym` imports
  - Update import statements to use Browser-Use
  - Remove unused imports

## Implementation Details

### Browser-Use Integration Architecture

```python
# New Browser Environment Structure
class BrowserUseEnv:
    def __init__(self, config: BrowserUseConfig):
        self.browser_session: BrowserSession
        self.observation_adapter: ObservationAdapter

    async def step(self, action: BrowserUseAction) -> dict:
        # 1. Execute Browser-Use action directly
        # 2. Get observation from BrowserSession
        # 3. Convert observation to OpenHands format
        # 4. Return observation dict
```

### Browser-Use Action Integration

```python
# Direct Browser-Use Action Usage
from browser_use.controller.service import GoToUrlAction, ClickElementAction, InputTextAction

# Instead of string parsing, use structured actions directly
goto_action = GoToUrlAction(url="https://example.com", new_tab=False)
click_action = ClickElementAction(index=123)
input_action = InputTextAction(index=456, text="Hello World")
```

### Observation Structure Compatibility

```python
# Maintain existing observation structure
{
    'url': str,
    'screenshot': str,  # base64 encoded
    'screenshot_path': str | None,
    'dom_object': dict,
    'axtree_object': dict,
    'text_content': str,
    'open_pages_urls': list[str],
    'active_page_index': int,
    'last_browser_action': str,
    'last_browser_action_error': str,
    'focused_element_bid': str,
    # ... other existing fields
}
```

## Migration Strategy

### Direct Replacement
1. **Complete Removal**: Remove BrowserGym entirely and replace with Browser-Use
2. **No Feature Flags**: No dual support period - direct replacement
3. **Structured Actions**: Use Browser-Use's native action models throughout

### Testing Strategy
1. **Unit Tests**: Test each component individually
2. **Integration Tests**: Test browser environment end-to-end
3. **Evaluation Tests**: Ensure evaluation benchmarks still work
4. **Performance Tests**: Compare performance between implementations

### Rollback Plan
1. **Git Revert**: Use git revert to rollback to previous BrowserGym implementation
2. **Version Tagging**: Tag releases before and after migration
3. **Documentation**: Clear migration instructions

## Timeline

### Week 1-2: Core Environment
- Implement BrowserUseEnv
- Create action mapper and observation adapter
- Basic functionality testing

### Week 3-4: Agent Updates
- Update BrowsingAgent and VisualBrowsingAgent
- Update CodeActAgent browser tool
- Agent functionality testing

### Week 5-6: Infrastructure
- Update configuration and command generation
- Update action execution server
- Integration testing

### Week 7-8: Evaluation
- Update evaluation scripts
- Update success rate calculations
- Evaluation testing

### Week 9-10: Cleanup and Polish
- Remove BrowserGym dependencies
- Clean up imports and unused code
- Final testing and documentation

## Risk Assessment

### High Risk
1. **Action Mapping Complexity**: BrowserGym and Browser-Use have different action models
2. **Evaluation Compatibility**: Ensuring evaluation benchmarks work correctly
3. **Performance Impact**: Browser-Use might have different performance characteristics

### Medium Risk
1. **API Changes**: Browser-Use API might change during development
2. **Dependency Conflicts**: Potential conflicts with existing dependencies
3. **Testing Coverage**: Ensuring all edge cases are covered

### Low Risk
1. **Documentation Updates**: Updating documentation and examples
2. **Configuration Changes**: Updating configuration files

## Success Criteria

1. **Functional Parity**: All existing browser functionality works with Browser-Use
2. **Performance**: Browser-Use implementation performs at least as well as BrowserGym
3. **Evaluation**: All evaluation benchmarks pass with similar or better results
4. **Stability**: No regressions in browser functionality
5. **Maintainability**: Cleaner, more maintainable codebase

## Conclusion

This refactoring plan provides a comprehensive approach to replacing BrowserGym with Browser-Use while maintaining all existing functionality. The phased approach ensures minimal disruption and allows for thorough testing at each stage. The focus on backward compatibility and gradual migration reduces risk and ensures a smooth transition.
