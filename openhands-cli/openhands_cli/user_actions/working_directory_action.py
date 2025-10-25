"""Working directory configuration actions for OpenHands CLI."""

import os
from pathlib import Path

from prompt_toolkit import HTML, print_formatted_text
from prompt_toolkit.completion import PathCompleter

from openhands_cli.locations import get_configured_working_directory, save_working_directory
from openhands_cli.user_actions.utils import cli_confirm, cli_text_input


def prompt_working_directory_configuration() -> str:
    """Prompt user to configure working directory at conversation start.
    
    Returns:
        The selected working directory path.
    """
    current_configured = get_configured_working_directory()
    current_cwd = os.getcwd()
    
    # Display current status
    print_formatted_text(HTML('<yellow>Working Directory Configuration</yellow>'))
    print_formatted_text(HTML(f'<grey>Current directory:</grey> <white>{current_cwd}</white>'))
    
    if current_configured:
        print_formatted_text(HTML(f'<grey>Configured directory:</grey> <white>{current_configured}</white>'))
        
        # Ask if user wants to use configured directory or change it
        choices = [
            f'Use configured directory ({current_configured})',
            f'Use current directory ({current_cwd})',
            'Choose a different directory'
        ]
        
        question = '\nWhich working directory would you like to use?'
        choice_index = cli_confirm(question, choices, escapable=False)
        
        if choice_index == 0:
            return current_configured
        elif choice_index == 1:
            # Save current directory as new configured directory
            save_working_directory(current_cwd)
            print_formatted_text(HTML(f'<green>✓ Working directory updated to: {current_cwd}</green>'))
            return current_cwd
        else:
            # Choice 2: Choose different directory
            return _prompt_custom_directory()
    else:
        # No configured directory, ask user to set one
        print_formatted_text(HTML('<yellow>No working directory configured.</yellow>'))
        
        choices = [
            f'Use current directory ({current_cwd})',
            'Choose a different directory'
        ]
        
        question = '\nWhich working directory would you like to use?'
        choice_index = cli_confirm(question, choices, escapable=False)
        
        if choice_index == 0:
            # Save current directory as configured directory
            save_working_directory(current_cwd)
            print_formatted_text(HTML(f'<green>✓ Working directory set to: {current_cwd}</green>'))
            return current_cwd
        else:
            # Choice 1: Choose different directory
            return _prompt_custom_directory()


def _prompt_custom_directory() -> str:
    """Prompt user to enter a custom directory path.
    
    Returns:
        The validated directory path.
    """
    while True:
        question = '\nEnter working directory path (TAB for completion): '
        
        try:
            directory_path = cli_text_input(
                question,
                escapable=False,
                completer=PathCompleter(only_directories=True)
            )
            
            # Expand user path and resolve
            expanded_path = os.path.expanduser(directory_path)
            resolved_path = os.path.abspath(expanded_path)
            
            if not os.path.exists(resolved_path):
                print_formatted_text(HTML(f'<red>Directory does not exist: {resolved_path}</red>'))
                
                # Ask if user wants to create it
                create_choices = ['Yes', 'No, choose different path']
                create_question = f'Would you like to create the directory?'
                create_index = cli_confirm(create_question, create_choices, escapable=False)
                
                if create_index == 0:
                    try:
                        os.makedirs(resolved_path, exist_ok=True)
                        print_formatted_text(HTML(f'<green>✓ Created directory: {resolved_path}</green>'))
                    except OSError as e:
                        print_formatted_text(HTML(f'<red>Failed to create directory: {e}</red>'))
                        continue
                else:
                    continue
            
            if not os.path.isdir(resolved_path):
                print_formatted_text(HTML(f'<red>Path is not a directory: {resolved_path}</red>'))
                continue
            
            # Save the configured directory
            save_working_directory(resolved_path)
            print_formatted_text(HTML(f'<green>✓ Working directory set to: {resolved_path}</green>'))
            return resolved_path
            
        except KeyboardInterrupt:
            # If user cancels, fall back to current directory
            current_cwd = os.getcwd()
            save_working_directory(current_cwd)
            print_formatted_text(HTML(f'\n<yellow>Using current directory: {current_cwd}</yellow>'))
            return current_cwd


def configure_working_directory_in_settings() -> None:
    """Configure working directory from the settings screen."""
    current_configured = get_configured_working_directory()
    current_cwd = os.getcwd()
    
    print_formatted_text(HTML('\n<yellow>Working Directory Configuration</yellow>'))
    print_formatted_text(HTML(f'<grey>Current directory:</grey> <white>{current_cwd}</white>'))
    
    if current_configured:
        print_formatted_text(HTML(f'<grey>Configured directory:</grey> <white>{current_configured}</white>'))
    else:
        print_formatted_text(HTML('<grey>No working directory configured (using current directory)</grey>'))
    
    choices = [
        f'Set to current directory ({current_cwd})',
        'Choose a different directory',
        'Go back'
    ]
    
    question = '\nWhat would you like to do?'
    choice_index = cli_confirm(question, choices, escapable=True)
    
    if choice_index == 0:
        # Set to current directory
        save_working_directory(current_cwd)
        print_formatted_text(HTML(f'<green>✓ Working directory set to: {current_cwd}</green>'))
    elif choice_index == 1:
        # Choose different directory
        _prompt_custom_directory()
    # choice_index == 2 or KeyboardInterrupt: Go back (do nothing)