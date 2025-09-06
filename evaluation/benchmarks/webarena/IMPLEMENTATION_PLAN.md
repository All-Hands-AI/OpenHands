# WebArena CDP Integration Implementation Plan

## Overview

This document outlines the proper solution for integrating OpenHands with the official WebArena evaluation harness using Chrome DevTools Protocol (CDP) session logging.

## The Problem

WebArena evaluators require:
1. Live browser state (DOM, cookies, localStorage, etc.)
2. CDPSession object for making CDP calls
3. Page object for accessing current URL, title, content

OpenHands only provides:
1. Action/observation pairs in text format
2. No live browser state
3. No CDP access during evaluation

## The Solution: CDP Session Logging

### Phase 1: Capture Browser State During Inference

**Modify `openhands/runtime/browser/browser_env.py`:**

```python
class BrowserEnv:
    def __init__(self, ...):
        # ... existing code ...
        self.cdp_logger = CDPSessionLogger() if should_log_cdp() else None

    def step(self, action):
        # ... existing action execution ...

        # Log CDP state after each action
        if self.cdp_logger:
            self.cdp_logger.capture_state_snapshot(f"after_action_{action.action}")

        # ... return observation ...

    def close(self):
        # Save final CDP session
        if self.cdp_logger:
            instance_id = get_current_instance_id()  # from evaluation context
            self.cdp_logger.save_session(instance_id)
```

**Add CDP Logger Integration:**

```python
class CDPSessionLogger:
    def attach_to_browsergym_env(self, env):
        """Attach to BrowserGym environment's Playwright page."""
        # Access the underlying Playwright page from BrowserGym
        playwright_page = env.page  # or however BrowserGym exposes it
        self.attach_to_page(playwright_page)

    def capture_state_snapshot(self, trigger: str):
        """Capture complete browser state using CDP."""
        # DOM snapshot (key for WebArena evaluators)
        dom_snapshot = self.cdp_session.send("DOMSnapshot.captureSnapshot", {
            "computedStyles": [],
            "includeDOMRects": True,
            "includePaintOrder": True,
        })

        # All other state (cookies, localStorage, etc.)
        # ... as shown in POC ...
```

### Phase 2: Mock Objects for Evaluation

**Create Mock Page/CDPSession:**

```python
class MockCDPSession:
    def __init__(self, saved_state):
        self.saved_state = saved_state

    def send(self, method: str, params=None):
        """Return saved state instead of making live CDP calls."""
        if method == "DOMSnapshot.captureSnapshot":
            return self.saved_state["dom_snapshot"]
        elif method == "Network.getAllCookies":
            return self.saved_state["cookies"]
        # ... handle all CDP methods WebArena uses ...

class MockPage:
    def __init__(self, saved_state):
        self.saved_state = saved_state

    def url(self): return self.saved_state["final_url"]
    def title(self): return self.saved_state["final_title"]
    def context(self): return MockBrowserContext(self.saved_state)
    # ... implement all Page methods WebArena uses ...
```

### Phase 3: Updated Evaluation Script

**Modify `eval_infer.py`:**

```python
def evaluate_with_official_webarena_harness(instance_data, config_file):
    """Use official WebArena evaluators with saved CDP state."""

    # Load saved CDP session
    cdp_integration = WebArenaCDPIntegration()
    mock_page, mock_client = cdp_integration.create_mock_page_and_client(
        instance_data["instance_id"]
    )

    # Convert OpenHands trajectory to WebArena format
    trajectory = convert_openhands_trajectory_to_webarena_format(instance_data)

    # Use official WebArena evaluator with mock objects
    evaluator = evaluator_router(config_file)
    score = evaluator(
        trajectory=trajectory,
        config_file=config_file,
        page=mock_page,        # Mock page with saved state
        client=mock_client,    # Mock CDP session with saved state
    )

    return score
```

## Implementation Steps

### Step 1: Integrate CDP Logger into BrowserEnv

1. **Add CDP logging to `browser_env.py`:**
   - Detect when running WebArena evaluation
   - Attach CDP logger to BrowserGym's Playwright page
   - Capture state snapshots after each action
   - Save final session with instance ID

2. **Environment variable setup:**
   ```bash
   export WEBARENA_CDP_LOGGING=true
   export WEBARENA_CDP_SESSION_DIR=/tmp/cdp_sessions
   ```

### Step 2: Create Mock Objects

1. **Implement `MockCDPSession`:**
   - Handle all CDP methods WebArena evaluators use
   - Return saved state instead of making live calls
   - Support `DOMSnapshot.captureSnapshot`, `Network.getAllCookies`, etc.

2. **Implement `MockPage`:**
   - Provide saved URL, title, content
   - Mock JavaScript evaluation with saved state
   - Support element queries using DOM snapshot

### Step 3: Update Evaluation Pipeline

1. **Modify `run_infer.py`:**
   - Enable CDP logging for WebArena tasks
   - Ensure instance IDs are properly set
   - Save CDP sessions to accessible location

2. **Update `eval_infer.py`:**
   - Load saved CDP sessions
   - Create mock objects
   - Use official WebArena evaluators
   - Remove all heuristic evaluation logic

### Step 4: Testing and Validation

1. **Test with known tasks:**
   - Run inference with CDP logging
   - Verify CDP sessions are saved correctly
   - Test evaluation with mock objects
   - Compare results with expected outcomes

2. **Validate DOM snapshot format:**
   - Ensure saved DOM snapshots match WebArena expectations
   - Test all CDP methods used by evaluators
   - Verify JavaScript evaluation works correctly

## Benefits of This Approach

1. **✅ Uses Official WebArena Evaluation:** No heuristics or approximations
2. **✅ Preserves Exact Browser State:** DOM, cookies, localStorage, etc.
3. **✅ No Live Browser Needed:** Evaluation works offline with saved state
4. **✅ Scalable:** Can evaluate many instances without browser overhead
5. **✅ Accurate:** Evaluators get exactly the state they expect

## File Structure

```
/tmp/cdp_sessions/
├── webarena.1.json          # CDP session for task 1
├── webarena.2.json          # CDP session for task 2
├── webarena.3.json          # CDP session for task 3
└── webarena.4.json          # CDP session for task 4

evaluation/benchmarks/webarena/
├── run_infer.py             # Modified to enable CDP logging
├── eval_infer.py            # Uses mock objects with saved state
├── cdp_integration.py       # Mock Page/CDPSession implementation
└── IMPLEMENTATION_PLAN.md   # This document
```

## Next Steps

1. **Implement CDP logger integration in `browser_env.py`**
2. **Create comprehensive mock objects**
3. **Update evaluation scripts**
4. **Test with actual WebArena tasks**
5. **Validate results against expected outcomes**

This approach solves the fundamental problem: WebArena evaluators need live browser state, but OpenHands only provides action/observation pairs. By capturing and replaying the exact browser state, we can use the official WebArena evaluation harness without any compromises.
