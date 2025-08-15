"""
E2E: Microagent trigger tests (flarglebargle, kubernetes)

This suite verifies that global knowledge microagents are triggered correctly via the UI.
It follows robust patterns from other E2E tests with timeouts, retries and screenshots.
"""

import os
import time
from typing import Iterable

import httpx
import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.getenv('OPENHANDS_E2E_URL', 'http://localhost:12000')
RESULTS_DIR = 'test-results'
REPO_NAME = os.getenv('OPENHANDS_E2E_REPO', 'openhands-agent/OpenHands')


def _screenshot(page: Page, name: str) -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    try:
        page.screenshot(path=os.path.join(RESULTS_DIR, name))
    except Exception:
        pass


def _first_visible(page: Page, selectors: Iterable[str], timeout_ms: int = 5000):
    for selector in selectors:
        try:
            el = page.locator(selector)
            if el.is_visible(timeout=timeout_ms):
                return el
        except Exception:
            continue
    return None


def _ensure_server_or_skip() -> None:
    try:
        with httpx.Client(timeout=3.0) as c:
            c.get(BASE_URL)
    except Exception as e:
        pytest.skip(f'OpenHands UI not reachable at {BASE_URL}: {e}')


def _ensure_conversation_started(page: Page) -> None:
    _ensure_server_or_skip()
    # Navigate to app
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle', timeout=30000)
    _screenshot(page, 'micro_01_initial.png')

    # If conversation already present, return
    existing_chat = _first_visible(
        page,
        [
            '[data-testid="chat-input"]',
            '[data-testid="conversation-screen"]',
            '.conversation-container',
        ],
        timeout_ms=3000,
    )
    if existing_chat:
        return

    # Ensure home screen
    home = page.locator('[data-testid="home-screen"]')
    expect(home).to_be_visible(timeout=20000)

    # Select repository
    repo_dropdown = page.locator('[data-testid="repo-dropdown"]')
    expect(repo_dropdown).to_be_visible(timeout=15000)
    repo_dropdown.click()
    page.wait_for_timeout(1000)

    try:
        page.keyboard.press('Control+a')
    except Exception:
        pass
    page.keyboard.type(REPO_NAME)
    page.wait_for_timeout(2000)

    # Click option
    option = _first_visible(
        page,
        [
            '[data-testid="repo-dropdown"] [role="option"]:has-text("%s")' % REPO_NAME,
            '[role="option"]:has-text("%s")' % REPO_NAME,
            'div:has-text("%s"):not([id="aria-results"])' % REPO_NAME,
        ],
        timeout_ms=3000,
    )
    if option:
        try:
            option.click(force=True)
        except Exception:
            pass
    else:
        # Fallback keyboard navigation
        page.keyboard.press('ArrowDown')
        page.wait_for_timeout(500)
        page.keyboard.press('Enter')

    _screenshot(page, 'micro_02_repo_selected.png')

    # Launch
    launch_btn = page.locator('[data-testid="repo-launch-button"]')
    expect(launch_btn).to_be_visible(timeout=15000)

    # Wait until enabled or force click
    enabled = False
    for _ in range(30):
        try:
            if not launch_btn.is_disabled():
                enabled = True
                break
        except Exception:
            pass
        page.wait_for_timeout(1000)

    if enabled:
        launch_btn.click()
    else:
        page.evaluate(
            """
            () => { const b = document.querySelector('[data-testid="repo-launch-button"]'); if (b) { b.removeAttribute('disabled'); b.click(); return true;} return false; }
            """
        )

    _screenshot(page, 'micro_03_after_launch.png')

    # Wait for conversation UI
    start = time.time()
    while time.time() - start < 180:
        chat = _first_visible(
            page,
            [
                '[data-testid="chat-input"]',
                '[data-testid="conversation-screen"]',
                '.conversation-container',
                'textarea',
            ],
            timeout_ms=2000,
        )
        if chat:
            _screenshot(page, 'micro_04_conv_ready.png')
            return
        page.wait_for_timeout(2000)

    _screenshot(page, 'micro_04_conv_timeout.png')
    raise AssertionError('Conversation did not load in time')


def _send_message(page: Page, text: str) -> None:
    input_sel = _first_visible(
        page,
        [
            '[data-testid="chat-input"] textarea',
            '[data-testid="message-input"]',
            'textarea',
            'form textarea',
        ],
        timeout_ms=5000,
    )
    if not input_sel:
        _screenshot(page, 'micro_input_missing.png')
        raise AssertionError('Message input not found')

    input_sel.fill(text)

    submit = _first_visible(
        page,
        [
            '[data-testid="chat-input"] button[type="submit"]',
            'button[type="submit"]',
        ],
        timeout_ms=3000,
    )

    if submit:
        # Wait to be enabled or press Enter
        ready = False
        start = time.time()
        while time.time() - start < 30:
            try:
                if not submit.is_disabled():
                    ready = True
                    break
            except Exception:
                pass
            page.wait_for_timeout(500)
        try:
            if ready:
                submit.click()
            else:
                input_sel.press('Enter')
        except Exception:
            input_sel.press('Enter')
    else:
        input_sel.press('Enter')

    _screenshot(page, 'micro_msg_sent.png')


def _wait_for_agent_text(page: Page, timeout_s: int = 180) -> list[str]:
    start = time.time()
    texts: list[str] = []

    def collect_texts() -> list[str]:
        collected: list[str] = []
        try:
            # 1) ChatMessage rendered messages (preferred)
            msgs = page.locator('[data-testid="agent-message"]').all()
            for m in msgs:
                try:
                    t = (m.text_content() or '').strip()
                    if t:
                        collected.append(t)
                except Exception:
                    continue
        except Exception:
            pass

        try:
            # 2) GenericEventMessage (e.g., RECALL observations) — expand then read
            containers = page.locator('div.border-l-2').all()
            for i, c in enumerate(containers):
                try:
                    # Expand details if a toggle button exists
                    btns = c.locator('button').all()
                    for b in btns:
                        try:
                            b.click(timeout=500)
                        except Exception:
                            continue
                    # Give time for details to render
                    page.wait_for_timeout(200)
                    t = (c.text_content() or '').strip()
                    if t:
                        collected.append(t)
                except Exception:
                    continue
        except Exception:
            pass
        return collected

    while time.time() - start < timeout_s:
        texts = collect_texts()
        if texts:
            return texts
        page.wait_for_timeout(2000)

    _screenshot(page, 'micro_agent_timeout.png')
    return texts


def test_microagent_flarglebargle(page: Page):
    _ensure_conversation_started(page)

    _send_message(page, 'flarglebargle')

    texts = _wait_for_agent_text(page, timeout_s=180)
    combined = '\n'.join(texts).lower()

    # Expect either praise from the agent or the microagent knowledge to be shown
    praise = any(w in combined for w in ['smart', 'genius', 'intelligent'])
    knowledge = (
        'magic word' in combined or (
            'triggered microagent knowledge' in combined and 'flarglebargle' in combined
        )
    )
    assert praise or knowledge, (
        'Expected praise or flarglebargle microagent knowledge when flarglebargle is sent'
    )

    # Avoid obvious unrelated technical guidance
    forbidden = ['docker', 'kubectl', 'kind ', 'git clone', 'error:']
    assert not any(w in combined for w in forbidden), (
        'Unexpected unrelated guidance in flarglebargle response'
    )

    _screenshot(page, 'micro_flarglebargle_done.png')


def test_microagent_kubernetes(page: Page):
    _ensure_conversation_started(page)

    _send_message(page, 'kubernetes')

    texts = _wait_for_agent_text(page, timeout_s=240)
    combined = '\n'.join(texts).lower()

    # Expect guidance aligned with microagents/kubernetes.md
    expected_any = [
        'kind',  # Kubernetes in Docker
        'kubectl',
        'create cluster',  # from `kind create cluster`
        'curl -lo',
    ]
    ok = any(token in combined for token in expected_any)
    if not ok:
        # Also allow recall panel content to satisfy the expectation
        ok = 'triggered microagent knowledge' in combined and 'kubernetes' in combined
    assert ok, 'Expected kubernetes guidance (KIND/kubectl setup) in response'

    _screenshot(page, 'micro_kubernetes_done.png')
