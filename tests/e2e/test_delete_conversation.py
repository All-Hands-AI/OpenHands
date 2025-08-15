"""
E2E: Delete conversation test

This test verifies that a conversation can be deleted from the conversation list.
It assumes the environment is properly set up and focuses on the core deletion functionality.

Test flow:
1. Navigate to OpenHands application
2. Look for existing conversations or create one if needed
3. Open conversation panel/list
4. Find a conversation and open its context menu
5. Click delete and confirm
6. Verify conversation is removed from UI
"""

import os
from playwright.sync_api import Page, expect


def test_delete_conversation(page: Page):
    """
    Test deleting a conversation from the conversation list.
    
    This test assumes there are existing conversations or creates one if needed.
    """
    # Create test-results directory
    os.makedirs('test-results', exist_ok=True)

    print('=== Starting Delete Conversation E2E Test ===')

    # Step 1: Navigate to OpenHands application
    print('Step 1: Navigating to OpenHands...')
    page.goto('http://localhost:12000')
    page.wait_for_load_state('networkidle', timeout=30000)
    page.screenshot(path='test-results/delete_01_app_loaded.png')

    # Step 2: Handle any initial modals quickly
    print('Step 2: Handling initial modals...')
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
        print(f'Modal handling: {e}')

    page.screenshot(path='test-results/delete_02_modals_handled.png')

    # Step 3: Look for conversation panel or create a conversation if needed
    print('Step 3: Looking for conversations...')
    
    # First, check if we're already in a conversation view
    current_url = page.url
    if '/conversation/' in current_url:
        print('Already in conversation view, navigating to home')
        page.goto('http://localhost:12000')
        page.wait_for_load_state('networkidle', timeout=15000)

    # Look for conversation panel or conversation cards
    conversation_cards = page.locator('[data-testid="conversation-card"]')
    
    # Wait a bit for any existing conversations to load
    page.wait_for_timeout(3000)
    
    conversation_count = conversation_cards.count()
    print(f'Found {conversation_count} existing conversation(s)')

    # If no conversations exist, create one quickly
    if conversation_count == 0:
        print('No existing conversations, creating one...')
        
        # Look for home screen elements
        home_screen = page.locator('[data-testid="home-screen"]')
        if home_screen.is_visible(timeout=5000):
            # Try to create a simple conversation
            repo_dropdown = page.locator('[data-testid="repo-dropdown"]')
            if repo_dropdown.is_visible(timeout=5000):
                repo_dropdown.click()
                page.wait_for_timeout(500)
                
                # Type a simple repo name
                page.keyboard.type('test/repo')
                page.wait_for_timeout(1000)
                page.keyboard.press('Enter')
                page.wait_for_timeout(1000)

                # Click launch if available
                launch_button = page.locator('[data-testid="repo-launch-button"]')
                if launch_button.is_visible(timeout=5000) and not launch_button.is_disabled():
                    launch_button.click()
                    
                    # Wait for conversation to be created (max 15 seconds)
                    for _ in range(15):
                        if '/conversation/' in page.url:
                            print('Conversation created, navigating back to home')
                            page.goto('http://localhost:12000')
                            page.wait_for_load_state('networkidle', timeout=10000)
                            break
                        page.wait_for_timeout(1000)

        # Check again for conversations
        page.wait_for_timeout(2000)
        conversation_count = conversation_cards.count()
        print(f'After creation attempt: {conversation_count} conversation(s)')

    if conversation_count == 0:
        page.screenshot(path='test-results/delete_03_no_conversations.png')
        raise AssertionError('No conversations available for deletion test')

    page.screenshot(path='test-results/delete_03_conversations_found.png')

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

    page.screenshot(path='test-results/delete_04_context_menu_opened.png')

    # Step 5: Click delete button
    print('Step 5: Clicking delete button...')

    delete_button = context_menu.locator('[data-testid="delete-button"]')
    expect(delete_button).to_be_visible(timeout=5000)
    delete_button.click()
    page.wait_for_timeout(1000)

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
    page.wait_for_timeout(3000)  # Wait for deletion to process

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

    page.screenshot(path='test-results/delete_08_test_completed.png')
    print('✅ Delete conversation test completed successfully!')
