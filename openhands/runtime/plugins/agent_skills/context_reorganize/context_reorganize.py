"""Context reorganization tool for the agent runtime."""

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import FileReadAction
from openhands.events.action.agent import ContextReorganizationAction
from openhands.events.observation import FileReadObservation
from openhands.events.observation.context_reorganization import (
    ContextReorganizationObservation,
)


def context_reorganize_tool(
    runtime, action: ContextReorganizationAction
) -> ContextReorganizationObservation:
    """Handle a context reorganization action.

    This method:
    1. Creates FileReadAction instances for each file in the action
    2. Executes these actions to get the file contents
    3. Combines the file contents into a single string
    4. Creates a ContextReorganizationObservation with the summary and combined file contents

    Args:
        runtime: The runtime instance
        action: The ContextReorganizationAction to handle

    Returns:
        A ContextReorganizationObservation with the summary and file contents
    """
    logger.info(
        f'Handling context reorganization action with {len(action.files)} files'
    )

    # Create a list to store file contents
    file_contents = []

    # Create and execute FileReadAction instances for each file
    for file_info in action.files:
        file_path = file_info.get('path')
        view_range = file_info.get('view_range')

        if not file_path:
            logger.warning(f'Skipping file with missing path: {file_info}')
            continue

        # Create a FileReadAction for this file
        file_read_action = FileReadAction(path=file_path, view_range=view_range)

        # Execute the action and get the observation
        try:
            observation = runtime.read(file_read_action)
            if isinstance(observation, FileReadObservation):
                # Add the file content to our list
                file_contents.append(
                    f'\n\n--- File: {file_path} ---\n{observation.content}'
                )
            else:
                logger.warning(f'Failed to read file {file_path}: {observation}')
                file_contents.append(
                    f'\n\n--- File: {file_path} ---\nError: Could not read file content'
                )
        except Exception as e:
            logger.error(f'Error reading file {file_path}: {e}')
            file_contents.append(f'\n\n--- File: {file_path} ---\nError: {str(e)}')

    # Combine the summary and file contents
    combined_content = action.summary
    if file_contents:
        combined_content += '\n\nFile Contents:' + ''.join(file_contents)

    # Create and return the observation
    return ContextReorganizationObservation(
        content=combined_content, summary=action.summary, files=action.files
    )


# Export the function
ContextReorganizeTool = context_reorganize_tool
