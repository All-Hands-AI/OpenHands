# Browser Refactoring Gotchas and Findings

## Initial Exploration

### Current BrowserGym Integration Points Found

1. **Core Browser Environment**: `openhands/runtime/browser/browser_env.py`
2. **Action Definitions**: `openhands/events/action/browse.py`
3. **Observation Definitions**: `openhands/events/observation/browse.py`
4. **Agent Implementations**:
   - `openhands/agenthub/browsing_agent/`
   - `openhands/agenthub/visualbrowsing_agent/`
   - `openhands/agenthub/codeact_agent/tools/browser.py`
5. **Configuration**: `openhands/core/config/sandbox_config.py`
6. **Evaluation Benchmarks**: Various evaluation scripts

### Key Findings

- BrowserGym uses a gymnasium-based environment interface
- Multiprocessing architecture with pipe communication
- Rich observation structure with screenshots, DOM, accessibility tree
- Multiple evaluation modes (webarena, miniwob, visualwebarena)

### Current Implementation Analysis

**Browser Environment (`browser_env.py`):**
- Uses multiprocessing with pipe communication between agent and browser processes
- Supports evaluation modes with different BrowserGym environments
- Handles screenshots, DOM extraction, accessibility tree, and text content
- Uses gymnasium environment interface with step() method

**Action Execution Flow:**
1. `ActionExecutor` initializes `BrowserEnv` in `_init_browser_async()`
2. Browser actions are executed via `browse()` utility function
3. Actions are converted to BrowserGym action strings (e.g., `goto("url")`, `click("bid")`)
4. BrowserGym environment executes actions and returns observations
5. Observations are converted to `BrowserOutputObservation` format

**Key Observation Fields:**
- `url`, `screenshot`, `screenshot_path`, `set_of_marks`
- `dom_object`, `axtree_object`, `extra_element_properties`
- `text_content`, `open_pages_urls`, `active_page_index`
- `last_browser_action`, `last_browser_action_error`, `focused_element_bid`

## Implementation Notes

### Phase 1: Core Browser Environment Replacement

**Next Steps:**
1. ✅ Examine current `browser_env.py` implementation
2. ✅ Research Browser-Use library structure and APIs
3. ✅ Create new `browser_use_env.py` with equivalent functionality
4. ✅ Implement observation adapter
5. **REVISED**: Remove action mapper - use Browser-Use actions directly
6. Test the new implementation
7. Update action execution server to use new environment

### Browser-Use Library Analysis

**Key Components Found:**
- `BrowserSession`: Main browser interface with methods like `navigate()`, `take_screenshot()`, `get_page_info()`, `go_back()`, `go_forward()`
- `Controller`: Action execution interface with `act()` method
- Action Models: Structured actions like `GoToUrlAction`, `ClickElementAction`, `InputTextAction`

**Available Actions:**
- `GoToUrlAction`: `url`, `new_tab` fields
- `ClickElementAction`: `index` field
- `InputTextAction`: `index`, `text` fields
- `ScrollAction`, `SearchGoogleAction`, `UploadFileAction`, etc.

**Key Differences from BrowserGym:**
- Browser-Use uses structured action models instead of string-based actions
- Actions can be executed via Controller.act() method OR direct BrowserSession methods
- BrowserSession provides rich state information via get_* methods
- No gymnasium dependency - direct Playwright-based control
- **✅ Direct Navigation Methods**: `go_back()`, `go_forward()`, `navigate()` available directly on BrowserSession

### Gotchas to Watch For

1. **Action Mapping Complexity**: BrowserGym and Browser-Use likely have different action models
2. **Multiprocessing Architecture**: Need to maintain pipe communication for compatibility
3. **Observation Structure**: Must maintain exact field names for backward compatibility
4. **Evaluation Compatibility**: Critical for maintaining benchmark functionality
5. **Browser-Use Installation**: Need to install and understand Browser-Use library first

### Important Implementation Details

**Current Action Format:**
- BrowserGym uses string-based actions like `goto("url")`, `click("bid")`, `fill("bid", "text")`
- Actions are executed via `browser.step(action_str)` method
- Need to map these to Browser-Use's action format

**Current Observation Format:**
- Rich observation dict with screenshots, DOM, accessibility tree
- Base64 encoded images
- Text content extracted from HTML
- Error handling and status reporting

## Progress Tracking

- [x] Phase 1: Core Browser Environment Replacement
  - [x] Create observation adapter (`observation_adapter.py`)
  - [x] Create Browser-Use environment (`browser_use_env.py`)
  - [x] **REVISED**: Remove action mapper, integrate Browser-Use actions directly
  - [x] **✅ Test the new implementation** - All navigation tests passing
  - [x] **✅ Fix async handling** - All async operations properly awaited
  - [x] **✅ Fix go_back/go_forward** - Using direct BrowserSession methods
  - [ ] Update action execution server to use new environment
- [ ] Phase 2: Action and Observation Updates
- [ ] Phase 3: Agent Updates
- [ ] Phase 4: Configuration and Infrastructure
- [ ] Phase 5: Evaluation and Testing
- [ ] Phase 6: Dependencies and Cleanup

## Implementation Notes

### Created Files

1. **`openhands/runtime/browser/observation_adapter.py`**
   - Converts Browser-Use observations to OpenHands format
   - Maintains compatibility with existing BrowserOutputObservation structure
   - Handles screenshots, HTML content, and page structure

2. **`openhands/runtime/browser/browser_use_env.py`**
   - Drop-in replacement for BrowserGym environment
   - Maintains same interface (step(), check_alive(), close())
   - Uses multiprocessing architecture for compatibility
   - Integrates Browser-Use BrowserSession and Controller
   - **REVISED**: Supports both string actions (backward compatibility) and direct Browser-Use action models

### Key Implementation Decisions

1. **REVISED**: **Hybrid Action Support**: Support both string actions (backward compatibility) and direct Browser-Use action models
2. **Observation Structure**: Maintained exact field names for backward compatibility
3. **Multiprocessing**: Kept the same pipe-based communication for compatibility
4. **Error Handling**: Implemented comprehensive error handling and fallbacks
5. **Complete Replacement**: Remove BrowserGym entirely, no feature flags or dual support
6. **✅ Direct Method Usage**: Use BrowserSession methods directly (go_back, go_forward, navigate) instead of controller when possible
7. **✅ Async-First Design**: All Browser-Use operations properly awaited and handled asynchronously

### Known Limitations

1. **REVISED**: **Element Identification**: Need to replace BID system with Browser-Use's element indexing
2. **Accessibility Tree**: Simplified implementation - needs proper tree flattening
3. **✅ Async Operations**: All async operations properly handled and awaited
4. **Evaluation Support**: Basic evaluation support implemented - needs testing
5. **Action Interface**: Need to update all agents to use Browser-Use action models instead of strings
6. **✅ Navigation Actions**: All navigation actions (goto, go_back, go_forward) working correctly

### Test Results

**✅ Successful Tests:**
- Browser-Use action model creation and validation
- Action string parsing for backward compatibility
- Environment initialization and basic communication
- Alive check functionality
- **✅ Navigation actions**: `goto()`, `go_back()`, `go_forward()` all working correctly
- **✅ No-op actions**: `noop()` with wait times working correctly
- **✅ Simple browsing**: Basic URL navigation working correctly

**🔧 Fixed Issues:**
- **✅ Async operations**: Properly awaited all async calls in Browser-Use environment
- **✅ Navigation actions**: Fixed `go_back()` and `go_forward()` by using direct `BrowserSession` methods instead of controller
- **✅ Screenshot capture**: Async handling implemented correctly
- **✅ Page content retrieval**: Working correctly with proper async handling

**Next Steps:**
- Update action execution server to use new environment
- Continue with Phase 2 (action/observation updates)
