"""Interactive settings configuration UI for OpenHands CLI."""

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import prompt
from pydantic import SecretStr

from openhands_cli.settings import CLISettings, SettingsManager
from openhands_cli.user_actions.utils import cli_confirm, prompt_user


def display_current_settings(settings: CLISettings) -> None:
    """Display current settings to the user."""
    print_formatted_text(HTML('<gold>📋 Current Settings</gold>'))
    print_formatted_text('')
    
    # LLM Configuration
    print_formatted_text(HTML('<white>LLM Configuration:</white>'))
    print_formatted_text(f'  Model: {settings.model}')
    api_key_display = '***' if settings.api_key else 'Not set'
    print_formatted_text(f'  API Key: {api_key_display}')
    base_url_display = settings.base_url or 'Not set'
    print_formatted_text(f'  Base URL: {base_url_display}')
    print_formatted_text('')
    
    # Agent Configuration
    print_formatted_text(HTML('<white>Agent Configuration:</white>'))
    print_formatted_text(f'  Agent Type: {settings.agent_type}')
    confirmation_status = 'Enabled' if settings.confirmation_mode else 'Disabled'
    print_formatted_text(f'  Confirmation Mode: {confirmation_status}')
    print_formatted_text('')
    
    # Optional Features
    print_formatted_text(HTML('<white>Optional Features:</white>'))
    search_key_display = '***' if settings.search_api_key else 'Not set'
    print_formatted_text(f'  Search API Key: {search_key_display}')
    print_formatted_text('')


def configure_llm_settings(settings_manager: SettingsManager) -> None:
    """Configure LLM settings interactively."""
    current_settings = settings_manager.load_settings()
    
    print_formatted_text(HTML('<gold>🤖 Configure LLM Settings</gold>'))
    print_formatted_text('')
    
    # Model selection
    print_formatted_text(HTML('<white>Select LLM Model:</white>'))
    model_choices = [
        'gpt-4o-mini',
        'gpt-4o', 
        'gpt-4-turbo',
        'claude-3-5-sonnet-20241022',
        'claude-3-5-haiku-20241022',
        'Other (specify)'
    ]
    
    current_model_idx = 0
    try:
        current_model_idx = model_choices.index(current_settings.model)
    except ValueError:
        current_model_idx = len(model_choices) - 1  # "Other"
    
    selected_idx = cli_confirm(
        'Choose a model:',
        choices=model_choices,
        initial_selection=current_model_idx,
        escapable=True
    )
    
    if selected_idx == len(model_choices) - 1:  # "Other" selected
        custom_model = prompt('Enter custom model name: ').strip()
        if custom_model:
            model = custom_model
        else:
            model = current_settings.model
    else:
        model = model_choices[selected_idx]
    
    # API Key
    print_formatted_text('')
    current_key_display = '***' if current_settings.api_key else 'Not set'
    print_formatted_text(f'Current API Key: {current_key_display}')
    
    update_key = cli_confirm(
        'Update API Key?',
        choices=['Keep current', 'Enter new key'],
        initial_selection=0,
        escapable=True
    )
    
    api_key = None
    if update_key == 1:  # Enter new key
        new_key = prompt('Enter API Key (hidden): ', is_password=True).strip()
        if new_key:
            api_key = new_key
        else:
            api_key = current_settings.api_key.get_secret_value() if current_settings.api_key else None
    else:
        api_key = current_settings.api_key.get_secret_value() if current_settings.api_key else None
    
    # Base URL
    print_formatted_text('')
    current_base_url = current_settings.base_url or 'Not set'
    print_formatted_text(f'Current Base URL: {current_base_url}')
    
    update_base_url = cli_confirm(
        'Update Base URL?',
        choices=['Keep current', 'Enter new URL', 'Clear URL'],
        initial_selection=0,
        escapable=True
    )
    
    base_url = current_settings.base_url
    if update_base_url == 1:  # Enter new URL
        new_url = prompt('Enter Base URL: ').strip()
        base_url = new_url if new_url else None
    elif update_base_url == 2:  # Clear URL
        base_url = None
    
    # Save settings
    settings_manager.update_settings(
        model=model,
        api_key=api_key,
        base_url=base_url
    )
    
    print_formatted_text(HTML('<green>✓ LLM settings updated successfully!</green>'))


def configure_agent_settings(settings_manager: SettingsManager) -> None:
    """Configure agent settings interactively."""
    current_settings = settings_manager.load_settings()
    
    print_formatted_text(HTML('<gold>🤖 Configure Agent Settings</gold>'))
    print_formatted_text('')
    
    # Agent Type
    print_formatted_text(HTML('<white>Select Agent Type:</white>'))
    agent_choices = [
        'CodeActAgent',
        'PlannerAgent',
        'Other (specify)'
    ]
    
    current_agent_idx = 0
    try:
        current_agent_idx = agent_choices.index(current_settings.agent_type)
    except ValueError:
        current_agent_idx = len(agent_choices) - 1  # "Other"
    
    selected_idx = cli_confirm(
        'Choose agent type:',
        choices=agent_choices,
        initial_selection=current_agent_idx,
        escapable=True
    )
    
    if selected_idx == len(agent_choices) - 1:  # "Other" selected
        custom_agent = prompt('Enter custom agent type: ').strip()
        if custom_agent:
            agent_type = custom_agent
        else:
            agent_type = current_settings.agent_type
    else:
        agent_type = agent_choices[selected_idx]
    
    # Confirmation Mode
    print_formatted_text('')
    confirmation_choices = ['Disabled', 'Enabled']
    current_confirmation_idx = 1 if current_settings.confirmation_mode else 0
    
    confirmation_idx = cli_confirm(
        'Confirmation Mode:',
        choices=confirmation_choices,
        initial_selection=current_confirmation_idx,
        escapable=True
    )
    
    confirmation_mode = confirmation_idx == 1
    
    # Save settings
    settings_manager.update_settings(
        agent_type=agent_type,
        confirmation_mode=confirmation_mode
    )
    
    print_formatted_text(HTML('<green>✓ Agent settings updated successfully!</green>'))


def configure_optional_settings(settings_manager: SettingsManager) -> None:
    """Configure optional settings interactively."""
    current_settings = settings_manager.load_settings()
    
    print_formatted_text(HTML('<gold>⚙️ Configure Optional Settings</gold>'))
    print_formatted_text('')
    
    # Search API Key
    current_search_key_display = '***' if current_settings.search_api_key else 'Not set'
    print_formatted_text(f'Current Search API Key: {current_search_key_display}')
    
    update_search_key = cli_confirm(
        'Update Search API Key?',
        choices=['Keep current', 'Enter new key', 'Clear key'],
        initial_selection=0,
        escapable=True
    )
    
    search_api_key = None
    if update_search_key == 1:  # Enter new key
        new_key = prompt('Enter Search API Key (hidden): ', is_password=True).strip()
        if new_key:
            search_api_key = new_key
        else:
            search_api_key = current_settings.search_api_key.get_secret_value() if current_settings.search_api_key else None
    elif update_search_key == 2:  # Clear key
        search_api_key = None
    else:
        search_api_key = current_settings.search_api_key.get_secret_value() if current_settings.search_api_key else None
    
    # Save settings
    settings_manager.update_settings(search_api_key=search_api_key)
    
    print_formatted_text(HTML('<green>✓ Optional settings updated successfully!</green>'))


def run_settings_configuration() -> None:
    """Run the interactive settings configuration."""
    settings_manager = SettingsManager()
    
    while True:
        print_formatted_text('')
        print_formatted_text(HTML('<gold>⚙️ OpenHands CLI Settings</gold>'))
        print_formatted_text('')
        
        # Display current settings
        current_settings = settings_manager.load_settings()
        display_current_settings(current_settings)
        
        # Main menu
        menu_choices = [
            'Configure LLM Settings',
            'Configure Agent Settings', 
            'Configure Optional Settings',
            'Reset to Defaults',
            'Exit Settings'
        ]
        
        try:
            choice = cli_confirm(
                'What would you like to configure?',
                choices=menu_choices,
                initial_selection=0,
                escapable=True
            )
            
            if choice == 0:  # Configure LLM Settings
                configure_llm_settings(settings_manager)
            elif choice == 1:  # Configure Agent Settings
                configure_agent_settings(settings_manager)
            elif choice == 2:  # Configure Optional Settings
                configure_optional_settings(settings_manager)
            elif choice == 3:  # Reset to Defaults
                confirm_reset = cli_confirm(
                    'Are you sure you want to reset all settings to defaults?',
                    choices=['No', 'Yes'],
                    initial_selection=0,
                    escapable=True
                )
                if confirm_reset == 1:
                    settings_manager.save_settings(CLISettings())
                    print_formatted_text(HTML('<green>✓ Settings reset to defaults!</green>'))
            elif choice == 4:  # Exit Settings
                break
                
        except KeyboardInterrupt:
            # User pressed Ctrl+C or Escape
            break
    
    print_formatted_text('')
    print_formatted_text(HTML('<yellow>Settings configuration complete.</yellow>'))