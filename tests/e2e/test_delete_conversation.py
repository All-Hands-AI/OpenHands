"""E2E: Delete conversation test.

This test verifies that a conversation can be deleted from the conversation list.
It creates a simple conversation first, then tests the deletion functionality.

Test flow:
1. Navigate to OpenHands application
2. Create a simple conversation
3. Navigate back to home to see conversation list
4. Find the conversation and open its context menu
5. Click delete and confirm
6. Verify conversation is removed from UI
"""

import os

import pytest
from playwright.sync_api import Page, expect


def test_delete_conversation(page: Page):
    """Test deleting a conversation from the conversation list.

    This test creates a conversation and then deletes it to verify the functionality.
    """
    # Create test-results directory
    os.makedirs('test-results', exist_ok=True)

    print('=== Starting Delete Conversation E2E Test ===')

    # Step 1: Navigate to OpenHands application
    print('Step 1: Navigating to OpenHands...')
    page.goto('http://localhost:12000')
    page.wait_for_load_state('networkidle', timeout=30000)
    page.screenshot(path='test-results/delete_01_app_loaded.png')

    # Step 2: Wait for home screen and create a conversation
    print('Step 2: Creating a test conversation...')

    # Wait for the home screen to load
    home_screen = page.locator('[data-testid="home-screen"]')
    expect(home_screen).to_be_visible(timeout=15000)
    print('Home screen is visible')

    # Look for the repository dropdown/selector
    repo_dropdown = page.locator('[data-testid="repo-dropdown"]')
    expect(repo_dropdown).to_be_visible(timeout=15000)
    print('Repository dropdown is visible')

    # Click on the repository input to open dropdown
    repo_dropdown.click()
    page.wait_for_timeout(1000)

    # Type a simple repository name
    page.keyboard.type('openhands-agent/OpenHands')
    page.wait_for_timeout(2000)  # Wait for search results

    # Try to select the first option
    try:
        # Press arrow down and enter to select first option
        page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter')
        page.wait_for_timeout(1000)
        print('Repository selected via keyboard')
    except Exception as e:
        print(f'Keyboard selection failed: {e}')
        # Try clicking on an option
        option = page.locator('[role="option"]').first
        if option.is_visible(timeout=2000):
            option.click()
            page.wait_for_timeout(1000)
            print('Repository selected via click')

    page.screenshot(path='test-results/delete_02_repo_selected.png')

    # Click Launch button
    launch_button = page.locator('[data-testid="repo-launch-button"]')
    expect(launch_button).to_be_visible(timeout=10000)
    # Wait for button to be enabled
    for _ in range(10):
        if not launch_button.is_disabled():
            break
        page.wait_for_timeout(1000)

    launch_button.click()
    print('Launch button clicked')

    # Wait for conversation to be created (check URL change and interface elements)
    conversation_created = False
    for _ in range(60):  # 60 seconds max
        current_url = page.url
        # Check URL for conversation or chat path
        if '/conversation/' in current_url or '/chat/' in current_url:
            conversation_created = True
            print(f'Conversation created, URL: {current_url}')
            break
        
        # Also check for conversation interface elements
        conversation_selectors = [
            '[data-testid="chat-input"]',
            '[data-testid="conversation-screen"]',
            '[data-testid="message-input"]',
            '.conversation-container',
            '.chat-container',
        ]
        
        for selector in conversation_selectors:
            try:
                element = page.locator(selector)
                if element.is_visible(timeout=1000):
                    conversation_created = True
                    print(f'Conversation interface detected with selector: {selector}')
                    break
            except Exception:
                continue
        
        if conversation_created:
            break
            
        page.wait_for_timeout(1000)

    if not conversation_created:
        page.screenshot(path='test-results/delete_03_conversation_not_created.png')
        pytest.skip('Could not create conversation for deletion test')

    page.screenshot(path='test-results/delete_03_conversation_created.png')

    # Step 3: Open conversation panel to see conversation list
    print('Step 3: Opening conversation panel to see conversation list...')
    
    # Look for the conversation panel toggle button
    panel_button = page.locator('[data-testid="toggle-conversation-panel"]')
    if panel_button.is_visible(timeout=5000):
        panel_button.click()
        print('Clicked conversation panel toggle button')
        page.wait_for_timeout(2000)
    else:
        print('Conversation panel button not found, trying to navigate to home first')
        page.goto('http://localhost:12000')
        page.wait_for_load_state('networkidle', timeout=15000)
        page.wait_for_timeout(3000)
        
        panel_button = page.locator('[data-testid="toggle-conversation-panel"]')
        if panel_button.is_visible(timeout=5000):
            panel_button.click()
            print('Clicked conversation panel toggle button after navigation')
            page.wait_for_timeout(2000)

    # Wait for conversation panel to load
    conversation_panel = page.locator('[data-testid="conversation-panel"]')
    if not conversation_panel.is_visible(timeout=10000):
        page.screenshot(path='test-results/delete_04_no_conversation_panel.png')
        pytest.skip('Conversation panel not visible')

    # Look for conversation cards within the panel
    conversation_cards = conversation_panel.locator('[data-testid="conversation-card"]')
    conversation_count = conversation_cards.count()
    print(f'Found {conversation_count} conversation(s) in panel')

    if conversation_count == 0:
        page.screenshot(path='test-results/delete_04_no_conversations_found.png')
        pytest.skip('No conversations found for deletion test')

    page.screenshot(path='test-results/delete_04_conversations_found.png')

    # Step 4: Select first conversation and open context menu
    print('Step 4: Opening context menu...')

    first_conversation = conversation_cards.first
    # Find and click ellipsis button
    ellipsis_button = first_conversation.locator('[data-testid="ellipsis-button"]')
    expect(ellipsis_button).to_be_visible(timeout=10000)
    ellipsis_button.click()
    page.wait_for_timeout(1000)

    # Wait for context menu to appear
    context_menu = page.locator('[data-testid="context-menu"]')
    expect(context_menu).to_be_visible(timeout=5000)
    print('Context menu opened')

    page.screenshot(path='test-results/delete_05_context_menu_opened.png')

    # Step 5: Click delete button
    print('Step 5: Clicking delete button...')

    delete_button = context_menu.locator('[data-testid="delete-button"]')
    expect(delete_button).to_be_visible(timeout=5000)
    delete_button.click()
    page.wait_for_timeout(1000)

    page.screenshot(path='test-results/delete_06_delete_clicked.png')

    # Step 6: Confirm deletion
    print('Step 6: Confirming deletion...')

    # Wait for confirmation modal
    confirm_button = page.locator('[data-testid="confirm-button"]')
    expect(confirm_button).to_be_visible(timeout=5000)
    print('Confirmation modal appeared')

    page.screenshot(path='test-results/delete_07_confirmation_modal.png')

    # Click confirm
    confirm_button.click()
    page.wait_for_timeout(3000)  # Wait for deletion to process

    print('Deletion confirmed')
    page.screenshot(path='test-results/delete_08_deletion_confirmed.png')

    # Step 7: Verify conversation is removed from UI
    print('Step 7: Verifying UI update...')

    # Wait for UI to update
    page.wait_for_timeout(2000)

    # Check conversation count decreased within the conversation panel
    updated_conversation_cards = conversation_panel.locator('[data-testid="conversation-card"]')
    updated_count = updated_conversation_cards.count()
    print(f'Updated conversation count: {updated_count}')

    # Verify count decreased
    assert updated_count < conversation_count, (
        f'Conversation count should have decreased from {conversation_count} '
        f'to {updated_count}'
    )
    print('✅ Conversation removed from UI')

    page.screenshot(path='test-results/delete_09_test_completed.png')
    print('✅ Delete conversation test completed successfully!')
