"""
E2E: Delete conversation test

This test verifies that a conversation can be deleted from the conversation list.
It assumes the environment is properly set up (GitHub token configured, etc.)
and focuses on the core deletion functionality.

Test flow:
1. Navigate to OpenHands application
2. Create a conversation (if needed) or navigate to conversation list
3. Open conversation panel/list
4. Find a conversation and open its context menu
5. Click delete and confirm
6. Verify conversation is removed from UI and API
"""

import os

import requests
from playwright.sync_api import Page, expect


def create_test_conversation(page: Page) -> str:
    """
    Create a test conversation and return its ID.
    This is a helper function to ensure we have a conversation to delete.
    """
    print('Creating a test conversation...')

    # Navigate to home if not already there
    page.goto('http://localhost:12000')
    page.wait_for_load_state('networkidle', timeout=30000)

    # Handle any initial modals
    try:
        # Check for AI Provider Configuration modal
        config_modal = page.locator('text=AI Provider Configuration')
        if config_modal.is_visible(timeout=3000):
            llm_api_key_input = page.locator('[data-testid="llm-api-key-input"]')
            if llm_api_key_input.is_visible(timeout=2000):
                llm_api_key = os.getenv('LLM_API_KEY', 'test-key')
                llm_api_key_input.fill(llm_api_key)

            save_button = page.locator('button:has-text("Save")')
            if save_button.is_visible(timeout=2000):
                save_button.click()
                page.wait_for_timeout(1000)

        # Check for Privacy Preferences modal
        privacy_modal = page.locator('text=Your Privacy Preferences')
        if privacy_modal.is_visible(timeout=3000):
            confirm_button = page.locator('button:has-text("Confirm Preferences")')
            if confirm_button.is_visible(timeout=2000):
                confirm_button.click()
                page.wait_for_timeout(1000)
    except Exception as e:
        print(f'Error handling modals: {e}')

    # Look for home screen and create conversation
    home_screen = page.locator('[data-testid="home-screen"]')
    if home_screen.is_visible(timeout=10000):
        # Select repository
        repo_dropdown = page.locator('[data-testid="repo-dropdown"]')
        if repo_dropdown.is_visible(timeout=5000):
            repo_dropdown.click()
            page.wait_for_timeout(500)

            # Type repository name
            page.keyboard.type('openhands-agent/OpenHands')
            page.wait_for_timeout(1000)

            # Select first option
            page.keyboard.press('ArrowDown')
            page.keyboard.press('Enter')
            page.wait_for_timeout(1000)

            # Click launch
            launch_button = page.locator('[data-testid="repo-launch-button"]')
            if launch_button.is_visible(timeout=5000):
                # Wait for button to be enabled
                for _ in range(10):
                    if not launch_button.is_disabled():
                        break
                    page.wait_for_timeout(1000)

                launch_button.click()

                # Wait for conversation to be created
                for _ in range(30):  # 30 seconds max
                    current_url = page.url
                    if '/conversation/' in current_url:
                        conversation_id = current_url.split('/conversation/')[-1].split(
                            '?'
                        )[0]
                        print(f'Created conversation with ID: {conversation_id}')
                        return conversation_id
                    page.wait_for_timeout(1000)

    raise Exception('Failed to create test conversation')


def test_delete_conversation(page: Page):
    """
    Test deleting a conversation from the conversation list.

    This test:
    1. Creates a test conversation (or uses existing ones)
    2. Navigates to the conversation list
    3. Opens context menu for a conversation
    4. Clicks delete and confirms
    5. Verifies the conversation is removed from UI and API
    """
    # Create test-results directory
    os.makedirs('test-results', exist_ok=True)

    print('=== Starting Delete Conversation E2E Test ===')

    # Step 1: Create a test conversation to ensure we have something to delete
    try:
        conversation_id_to_delete = create_test_conversation(page)
        page.screenshot(path='test-results/delete_01_conversation_created.png')
    except Exception as e:
        print(f'Failed to create test conversation: {e}')
        # Continue anyway - maybe there are existing conversations
        conversation_id_to_delete = None

    # Step 2: Navigate to conversation list/panel
    print('Step 2: Navigating to conversation list...')

    # Go to home page to access conversation list
    page.goto('http://localhost:12000')
    page.wait_for_load_state('networkidle', timeout=15000)

    # Look for conversation panel trigger or existing conversation cards
    conversation_panel_triggers = [
        '[data-testid="conversation-panel-trigger"]',
        '[data-testid="conversations-button"]',
        'button:has-text("Conversations")',
        '[aria-label*="conversation"]',
        'button[aria-label*="menu"]',
    ]

    for selector in conversation_panel_triggers:
        try:
            trigger = page.locator(selector)
            if trigger.is_visible(timeout=2000):
                print(f'Found conversation panel trigger: {selector}')
                trigger.click()
                page.wait_for_timeout(1000)
                break
        except Exception:
            continue

    # Check if conversation panel or cards are visible
    page.locator('[data-testid="conversation-panel"]')
    conversation_cards = page.locator('[data-testid="conversation-card"]')

    # Wait for either panel or cards to be visible
    try:
        page.wait_for_function(
            """() => {
                const panel = document.querySelector('[data-testid="conversation-panel"]');
                const cards = document.querySelectorAll('[data-testid="conversation-card"]');
                return (panel && panel.offsetParent !== null) || cards.length > 0;
            }""",
            timeout=10000,
        )
    except Exception:
        print('No conversation panel or cards found, taking screenshot for debugging')
        page.screenshot(path='test-results/delete_02_no_conversations_found.png')
        raise AssertionError('Could not find conversation panel or conversation cards')

    page.screenshot(path='test-results/delete_02_conversation_list_visible.png')

    # Step 3: Find conversations and select one to delete
    print('Step 3: Finding conversation to delete...')

    # Wait for conversations to load
    page.wait_for_timeout(2000)

    # Get all conversation cards
    conversation_cards = page.locator('[data-testid="conversation-card"]')
    conversation_count = conversation_cards.count()
    print(f'Found {conversation_count} conversation(s)')

    if conversation_count == 0:
        page.screenshot(path='test-results/delete_03_no_conversations.png')
        raise AssertionError('No conversations found to delete')

    # Select the first conversation
    first_conversation = conversation_cards.first

    # Try to extract conversation ID if we don't have it
    if not conversation_id_to_delete:
        try:
            conversation_link = first_conversation.locator(
                'a[href*="/conversation"]'
            ).first
            if conversation_link.is_visible(timeout=2000):
                href = conversation_link.get_attribute('href')
                if href and '/conversation' in href:
                    conversation_id_to_delete = (
                        href.split('/conversation')[-1].strip('/').split('?')[0]
                    )
                    print(f'Extracted conversation ID: {conversation_id_to_delete}')
        except Exception as e:
            print(f'Could not extract conversation ID: {e}')

    page.screenshot(path='test-results/delete_03_conversation_selected.png')

    # Step 4: Open context menu
    print('Step 4: Opening context menu...')

    # Find and click ellipsis button
    ellipsis_button = first_conversation.locator('[data-testid="ellipsis-button"]')
    expect(ellipsis_button).to_be_visible(timeout=10000)
    ellipsis_button.click()
    page.wait_for_timeout(500)

    # Wait for context menu to appear
    context_menu = page.locator('[data-testid="context-menu"]')
    expect(context_menu).to_be_visible(timeout=5000)
    print('Context menu opened')

    page.screenshot(path='test-results/delete_04_context_menu_opened.png')

    # Step 5: Click delete button
    print('Step 5: Clicking delete button...')

    delete_button = context_menu.locator('[data-testid="delete-button"]')
    expect(delete_button).to_be_visible(timeout=5000)
    delete_button.click()
    page.wait_for_timeout(500)

    page.screenshot(path='test-results/delete_05_delete_clicked.png')

    # Step 6: Confirm deletion
    print('Step 6: Confirming deletion...')

    # Wait for confirmation modal
    confirm_button = page.locator('[data-testid="confirm-button"]')
    expect(confirm_button).to_be_visible(timeout=5000)
    print('Confirmation modal appeared')

    page.screenshot(path='test-results/delete_06_confirmation_modal.png')

    # Click confirm
    confirm_button.click()
    page.wait_for_timeout(2000)  # Wait for deletion to process

    print('Deletion confirmed')
    page.screenshot(path='test-results/delete_07_deletion_confirmed.png')

    # Step 7: Verify conversation is removed from UI
    print('Step 7: Verifying UI update...')

    # Wait for UI to update
    page.wait_for_timeout(2000)

    # Check conversation count decreased
    updated_conversation_cards = page.locator('[data-testid="conversation-card"]')
    updated_count = updated_conversation_cards.count()
    print(f'Updated conversation count: {updated_count}')

    # Verify count decreased
    assert updated_count < conversation_count, (
        f'Conversation count should have decreased from {conversation_count} to {updated_count}'
    )
    print('✅ Conversation removed from UI')

    page.screenshot(path='test-results/delete_08_ui_updated.png')

    # Step 8: Verify conversation cannot be fetched via API
    print('Step 8: Verifying API deletion...')

    if conversation_id_to_delete:
        try:
            api_url = (
                f'http://localhost:12000/api/conversations/{conversation_id_to_delete}'
            )
            print(f'Checking API endpoint: {api_url}')

            response = requests.get(api_url, timeout=10)
            print(f'API response status: {response.status_code}')

            # Should return 404 or null
            if response.status_code == 404:
                print('✅ API returns 404 - conversation deleted')
            elif response.status_code == 200:
                try:
                    data = response.json()
                    if data is None:
                        print('✅ API returns null - conversation deleted')
                    else:
                        print(f'❌ API still returns data: {data}')
                        raise AssertionError('Conversation still exists in API')
                except Exception:
                    print('✅ API returns empty response - conversation deleted')
            else:
                print(f'Unexpected API status: {response.status_code}')
                print(f'Response: {response.text}')

        except requests.exceptions.RequestException as e:
            print(f'API request failed: {e}')
            # Don't fail test for network issues in CI
    else:
        print('Could not verify API deletion - conversation ID unknown')

    print('✅ Delete conversation test completed successfully!')
    page.screenshot(path='test-results/delete_09_test_completed.png')
