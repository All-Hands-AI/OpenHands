import json
import re
from typing import Any, List, Optional

from openhands.core.database import db_pool
from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event
from openhands.events.event_store import EventStore
from openhands.events.serialization.event import (
    _extract_content_from_event,
    _extract_from_finish_event,
    _extract_from_message_event,
    _extract_from_read_event,
    event_to_dict,
)


def _try_extract_json(content: str) -> dict | None:
    """Try to extract JSON from content using various patterns."""
    if not content:
        return None

    json_patterns = [
        r'```json\s*\n?(.*?)\n?```',  # JSON in code blocks
        r'```\s*\n?(.*?)\n?```',  # General code blocks
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # JSON objects with nested braces
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                clean_match = match.strip()
                logger.debug(f'clean_match_json: {clean_match}')
                if not clean_match.startswith('{'):
                    continue

                # Try to parse as JSON
                parsed_json = json.loads(clean_match)

                # Validate it's actually a dictionary/object
                if isinstance(parsed_json, dict):
                    return parsed_json
            except json.JSONDecodeError:
                continue

    # Fallback: try to find any JSON-like structure in the content
    try:
        # Look for content that starts and ends with braces
        brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(brace_pattern, content, re.DOTALL)

        for match in matches:
            try:
                parsed_json = json.loads(match)
                if isinstance(parsed_json, dict):
                    return parsed_json
            except json.JSONDecodeError:
                continue
    except Exception:
        pass

    return None


def _reconstruct_final_file_content(events: list[Event]) -> str | None:
    """
    Reconstruct final file content by tracking file operations (create/edit).
    Prioritizes markdown files and returns the final content after all edits.
    """
    try:
        # Track file operations by path
        file_operations: dict[str, Any] = {}  # path -> list of operations

        for event in reversed(events):  # Process in chronological order
            try:
                event_dict = event_to_dict(event)
                source = event_dict.get('source')
                action = event_dict.get('action')

                if source != 'agent' or action != 'edit':
                    continue

                # Extract file operation details
                tool_call_metadata = event_dict.get('tool_call_metadata', {})
                model_response = tool_call_metadata.get('model_response', {})
                choices = model_response.get('choices', [])

                if not choices or 'message' not in choices[0]:
                    continue

                message_obj = choices[0]['message']
                tool_calls = message_obj.get('tool_calls', [])

                if not tool_calls or 'function' not in tool_calls[0]:
                    continue

                arguments_str = tool_calls[0]['function'].get('arguments')
                if not arguments_str:
                    continue

                arguments_json = json.loads(arguments_str)
                path = arguments_json.get('path')
                command = arguments_json.get('command')

                if not path:
                    continue

                # Initialize file operations for this path
                if path not in file_operations:
                    file_operations[path] = []

                operation = {
                    'command': command,
                    'file_text': arguments_json.get('file_text'),
                    'old_str': arguments_json.get('old_str'),
                    'new_str': arguments_json.get('new_str'),
                    'timestamp': event_dict.get('timestamp'),
                }
                file_operations[path].append(operation)

            except Exception:
                continue

        # Find the most likely result file (prioritize .md files)
        target_path = None
        max_operations = 0

        for path, operations in file_operations.items():
            if not path.endswith(('.md', '.txt')):
                continue

            if len(operations) > max_operations:
                max_operations = len(operations)
                target_path = path

        if not target_path or target_path not in file_operations:
            return None

        operations = file_operations[target_path]
        final_content = None

        # Reconstruct final content
        for op in operations:
            if op['command'] == 'create' and op['file_text']:
                final_content = op['file_text']
            elif (
                op['command'] == 'str_replace'
                and final_content
                and op['old_str']
                and op['new_str']
            ):
                # Apply string replacement
                if op['old_str'] in final_content:
                    final_content = final_content.replace(
                        op['old_str'], op['new_str'], 1
                    )

        if final_content and len(final_content.strip()) > 50:
            logger.info(
                f'Reconstructed final content from {target_path} ({len(operations)} operations)'
            )
            return final_content

    except Exception as e:
        logger.error(f'Error reconstructing file content: {str(e)}')

    return None


async def save_final_result_to_database(
    conversation_id: str, final_result: str
) -> bool:
    """
    Save the final result directly to the database as a new column.

    Args:
        conversation_id: The conversation ID to update
        final_result: The final result content to save

    Returns:
        bool: True if successfully saved, False otherwise
    """
    with db_pool.get_connection_context() as conn:
        try:
            with conn.cursor() as cursor:
                # Update the conversations table with final_result
                cursor.execute(
                    """
                    UPDATE conversations
                    SET final_result = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE conversation_id = %s
                    """,
                    (final_result, conversation_id),
                )

                # Commit the transaction
                conn.commit()

                if cursor.rowcount == 0:
                    logger.warning(
                        f'No conversation found to update with conversation_id: {conversation_id}'
                    )
                    return False
                else:
                    logger.info(
                        f'Successfully saved final result to database for conversation {conversation_id}'
                    )
                    return True
        except Exception as e:
            logger.error(f'Error saving final result to database: {str(e)}')
            conn.rollback()
            return False


async def extract_final_result(
    events: List[Event],
    conversation_id: str,
    save_to_database: bool = True,
) -> Optional[str]:
    """
    Extract final result from conversation events and optionally save to database.

    This utility function can be used by any component to extract the final result
    from a conversation's event stream. It uses similar logic to the original
    _extract_and_save_final_result method but is designed as a standalone utility.

    Args:
        events: List of events from the conversation
        conversation_id: The conversation ID for database operations
        save_to_database: Whether to save the result to database (default: True)

    Returns:
        Optional[str]: The extracted final result, or None if no result found
    """
    try:
        final_result = None

        # Categorize events by type
        finish_events = []
        edit_events = []
        message_events = []
        read_events = []

        for event in events:
            event_dict = None
            try:
                event_dict = event_to_dict(event)
            except Exception:
                continue

            source = event_dict.get('source')
            action = event_dict.get('action')
            observation = event_dict.get('observation')

            if source == 'agent':
                if action == 'finish':
                    finish_events.append(event_dict)
                elif action == 'edit':
                    edit_events.append(event_dict)
                elif observation == 'read':
                    read_events.append(event_dict)
                elif _extract_content_from_event(event_dict):
                    message_events.append(event_dict)

        # Try to reconstruct final file content first (prioritize edit events)
        if edit_events:
            logger.info('Prioritizing edit events for final result extraction')
            final_file_content = _reconstruct_final_file_content(events)

            if final_file_content:
                final_result = final_file_content

        # If no edit events or couldn't extract from edit, try read events for .md/.txt files
        if not final_result and read_events:
            logger.info(
                'Trying read events for final result extraction (.md/.txt files)'
            )
            for event_dict in read_events:
                result = _extract_from_read_event(event_dict)
                if result:
                    final_result = result
                    break

        # Try finish events
        if not final_result and finish_events:
            logger.info('Trying finish events for final result extraction')
            for event_dict in finish_events:
                result = _extract_from_finish_event(event_dict)
                if result:
                    final_result = result
                    break

        # If still no result, try message events
        if not final_result and message_events:
            logger.info('Trying message events for final result extraction')
            for event_dict in message_events:
                result = _extract_from_message_event(event_dict)
                if result:
                    final_result = result
                    break

        # Save the final result to database if requested and result found
        if final_result and save_to_database:
            success = await save_final_result_to_database(conversation_id, final_result)
            if not success:
                logger.warning(
                    f'Failed to save final result to database for conversation {conversation_id}'
                )

        logger.info(
            f'Final result extracted: {final_result is not None}, conversation_id: {conversation_id}'
        )
        return final_result

    except Exception as e:
        logger.error(f'Error extracting final result: {str(e)}')
        return None


async def get_final_result_from_conversation(
    conversation_id: str,
    event_stream: EventStore,
    save_to_database: bool = True,
) -> Optional[str]:
    """
    Get final result from a conversation using its event stream.

    This is a convenience function that combines event retrieval with result extraction.

    Args:
        conversation_id: The conversation ID
        event_stream: The event stream object with get_events_by_action method
        save_to_database: Whether to save the result to database (default: True)

    Returns:
        Optional[str]: The extracted final result, or None if no result found
    """
    try:
        # Get recent events from the event stream to find the final result
        recent_events = list(
            event_stream.get_events_by_action(
                actions=['edit', 'finish', 'message'],
                observations=['read'],
                limit=50,
                reverse=True,
                sid=conversation_id,
            )
        )

        return await extract_final_result(
            events=recent_events,
            conversation_id=conversation_id,
            save_to_database=save_to_database,
        )

    except Exception as e:
        logger.error(
            f'Error getting final result from conversation {conversation_id}: {str(e)}'
        )
        return None
