#!/usr/bin/env python3
"""
BrowserGym State Capture for WebArena Evaluation

This module leverages BrowserGym's existing state capture capabilities to save
browser state for proper WebArena evaluation. BrowserGym already provides:
- extract_dom_snapshot() - exactly what WebArena evaluators need
- Direct Playwright page access via env.page
- CDP session access via page.context.new_cdp_session()

This is much simpler than our original CDP logging approach because BrowserGym
already has all the infrastructure we need.
"""

import json
from pathlib import Path
from typing import Any, Optional

import browsergym.core.observation as obs


class BrowserGymStateCapture:
    """
    Captures browser state using BrowserGym's existing observation functions.
    This provides everything WebArena evaluators need without custom CDP logging.
    """

    def __init__(self, output_dir: str = '/tmp/webarena_states'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_instance_id: str | None = None

    def set_instance_id(self, instance_id: str) -> None:
        """Set the current WebArena instance ID for state saving."""
        self.current_instance_id = instance_id

    def capture_final_state(self, browsergym_env) -> dict[str, Any]:
        """
        Capture the final browser state using BrowserGym's observation functions.
        This captures everything WebArena evaluators need.
        """
        if not hasattr(browsergym_env, 'page'):
            raise RuntimeError('BrowserGym environment does not have page attribute')

        page = browsergym_env.page

        # Use BrowserGym's existing observation extraction functions
        state = {
            'instance_id': self.current_instance_id,
            'final_url': page.url,
            'final_title': page.title(),
            # This is the key - BrowserGym's extract_dom_snapshot uses CDP internally
            # and returns exactly the format WebArena evaluators expect
            'dom_snapshot': obs.extract_dom_snapshot(page),
            # Additional state that might be useful
            'screenshot': obs.extract_screenshot(page),
            'axtree': obs.extract_merged_axtree(page),
            'focused_element': obs.extract_focused_element_bid(page),
        }

        # Get additional browser state via CDP
        try:
            cdp_session = page.context.new_cdp_session(page)

            # Get cookies
            cookies_result = cdp_session.send('Network.getAllCookies')
            state['cookies'] = cookies_result

            # Get localStorage
            local_storage = cdp_session.send(
                'Runtime.evaluate',
                {'expression': 'JSON.stringify(localStorage)', 'returnByValue': True},
            )
            state['local_storage'] = local_storage.get('result', {}).get('value', '{}')

            # Get sessionStorage
            session_storage = cdp_session.send(
                'Runtime.evaluate',
                {'expression': 'JSON.stringify(sessionStorage)', 'returnByValue': True},
            )
            state['session_storage'] = session_storage.get('result', {}).get(
                'value', '{}'
            )

            cdp_session.detach()

        except Exception as e:
            print(f'Warning: Could not capture additional state via CDP: {e}')
            state['cookies'] = {'cookies': []}
            state['local_storage'] = '{}'
            state['session_storage'] = '{}'

        return state

    def save_state(self, browsergym_env) -> str:
        """Save the current browser state to disk."""
        if self.current_instance_id is None:
            raise RuntimeError('Instance ID not set. Call set_instance_id() first.')

        state = self.capture_final_state(browsergym_env)

        # Save to file
        state_file = self.output_dir / f'{self.current_instance_id}.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)

        print(f'✅ Saved browser state to: {state_file}')
        return str(state_file)

    def load_state(self, instance_id: str) -> dict[str, Any]:
        """Load saved browser state from disk."""
        state_file = self.output_dir / f'{instance_id}.json'

        if not state_file.exists():
            raise FileNotFoundError(f'State file not found: {state_file}')

        with open(state_file, 'r') as f:
            state = json.load(f)

        return state


class MockPageForWebArena:
    """
    Mock Page object that provides saved browser state for WebArena evaluation.
    This uses the exact state captured by BrowserGym's observation functions.
    """

    def __init__(self, saved_state: dict[str, Any]):
        self.saved_state = saved_state
        self._url = saved_state.get('final_url', '')
        self._title = saved_state.get('final_title', '')
        self._context = MockBrowserContextForWebArena(saved_state)

    def url(self) -> str:
        return self._url

    def title(self) -> str:
        return self._title

    @property
    def context(self):
        return self._context

    def evaluate(self, expression: str) -> Any:
        """Mock JavaScript evaluation using saved state."""
        if 'window.location.href' in expression:
            return self._url
        elif 'document.title' in expression:
            return self._title
        elif 'localStorage' in expression:
            return self.saved_state.get('local_storage', '{}')
        elif 'sessionStorage' in expression:
            return self.saved_state.get('session_storage', '{}')
        return None


class MockCDPSessionForWebArena:
    """
    Mock CDPSession that returns saved state from BrowserGym's observations.
    This is the key component that makes WebArena evaluators work.
    """

    def __init__(self, saved_state: dict[str, Any]):
        self.saved_state = saved_state

    def send(self, method: str, params: Optional[dict] = None) -> dict[str, Any]:
        """
        Mock CDP send method that returns BrowserGym's captured state.
        The key insight: BrowserGym's extract_dom_snapshot() already returns
        the exact format that WebArena evaluators expect from CDP calls.
        """
        if method == 'DOMSnapshot.captureSnapshot':
            # BrowserGym's extract_dom_snapshot already returns the right format!
            return self.saved_state.get('dom_snapshot', {})

        elif method == 'Network.getAllCookies':
            return self.saved_state.get('cookies', {'cookies': []})

        elif method == 'Runtime.evaluate':
            if params and 'expression' in params:
                expression = params['expression']
                if 'localStorage' in expression:
                    return {
                        'result': {'value': self.saved_state.get('local_storage', '{}')}
                    }
                elif 'sessionStorage' in expression:
                    return {
                        'result': {
                            'value': self.saved_state.get('session_storage', '{}')
                        }
                    }
                elif 'window.location.href' in expression:
                    return {'result': {'value': self.saved_state.get('final_url', '')}}
                elif 'document.title' in expression:
                    return {
                        'result': {'value': self.saved_state.get('final_title', '')}
                    }

        return {}

    def detach(self):
        """Mock detach method."""
        pass


class MockBrowserContextForWebArena:
    """Mock browser context for WebArena evaluation."""

    def __init__(self, saved_state: dict[str, Any]):
        self.saved_state = saved_state

    def new_cdp_session(self, page) -> MockCDPSessionForWebArena:
        """Return mock CDP session with BrowserGym's captured state."""
        return MockCDPSessionForWebArena(self.saved_state)


def integrate_with_openhands_browser_env():
    """
    Integration point for OpenHands browser_env.py.
    This shows how to add state capture to the existing BrowserGym usage.
    """

    # This would be added to browser_env.py in the browser_process method
    example_integration = """
    def browser_process(self) -> None:
        env = gym.make('browsergym/openended', ...)
        obs, info = env.reset()

        # Add state capture for WebArena evaluation
        state_capture = None
        if os.getenv('WEBARENA_EVALUATION'):
            state_capture = BrowserGymStateCapture()

        while should_continue():
            if self.browser_side.poll(timeout=0.01):
                unique_request_id, action_data = self.browser_side.recv()

                # Handle WebArena instance ID setting
                if unique_request_id == 'SET_WEBARENA_INSTANCE':
                    if state_capture:
                        state_capture.set_instance_id(action_data['instance_id'])
                    continue

                action = action_data['action']
                obs, reward, terminated, truncated, info = env.step(action)

                # Capture final state when task completes
                if terminated and state_capture:
                    state_capture.save_state(env)

                # ... rest of existing code ...
    """

    return example_integration


def demonstrate_integration():
    """Demonstrate how this integrates with WebArena evaluation."""
    print('🚀 BrowserGym State Capture for WebArena')
    print('=' * 50)

    print('✅ Key advantages of this approach:')
    print("   1. Uses BrowserGym's existing observation functions")
    print('   2. extract_dom_snapshot() already returns WebArena-compatible format')
    print('   3. No custom CDP logging needed')
    print('   4. Minimal changes to OpenHands browser_env.py')
    print('   5. Leverages existing, tested BrowserGym infrastructure')

    print('\n📋 Integration steps:')
    print('   1. Add BrowserGymStateCapture to browser_env.py')
    print('   2. Capture state when WebArena tasks complete')
    print(
        '   3. Use MockPageForWebArena and MockCDPSessionForWebArena in eval_infer.py'
    )
    print('   4. Official WebArena evaluators work with mock objects')

    print('\n🎯 This is much simpler than custom CDP logging because')
    print('   BrowserGym already provides everything we need!')


if __name__ == '__main__':
    demonstrate_integration()
