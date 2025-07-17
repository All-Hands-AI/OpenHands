import json
from typing import List, Optional

import psycopg

from openhands.core.database import db_pool
from openhands.core.logger import openhands_logger as logger
from openhands.storage.files import FileStore
from openhands.storage.locations import parse_conversation_path


class DatabaseFileStore(FileStore):
    def write(self, path: str, contents: str | bytes) -> None:
        """Write contents to database based on path type."""
        if path == 'settings.json':
            return

        try:
            parsed_path = parse_conversation_path(path)
            if parsed_path is None:
                logger.error(f'Failed to parse conversation path: {path}')
                return

            user_id = parsed_path['user_id']
            session_id = parsed_path['session_id']
            event_id = parsed_path['event_id']
            path_type = parsed_path['type']

            with db_pool.get_connection_context() as conn:
                with conn.cursor() as cursor:
                    if path_type == 'events':
                        self._write_event(cursor, session_id, event_id, contents)
                    elif path_type == 'metadata':
                        self._write_metadata(cursor, session_id, contents, user_id)
                    elif path_type == 'settings' and user_id:
                        self._write_user_setting(cursor, user_id, contents)
                    elif path_type == 'agent_state':
                        self._write_agent_state(cursor, session_id, contents, user_id)
                    else:
                        logger.warning(f'Unsupported path type for write: {path_type}')
                        return

                    conn.commit()
                    logger.debug(
                        f'Successfully wrote {path_type} for session {session_id}'
                    )

        except Exception as e:
            logger.error(f'Error writing to database for path {path}: {str(e)}')
            raise

    def _write_event(
        self,
        cursor: psycopg.Cursor,
        conversation_id: str,
        event_id: int,
        contents: str | bytes,
    ) -> None:
        """Write event data to conversation_events table."""
        if isinstance(contents, bytes):
            contents = contents.decode('utf-8')

        try:
            metadata = json.loads(contents)
        except json.JSONDecodeError as e:
            logger.error(
                f'Failed to parse event JSON for conversation {conversation_id}, event {event_id}: {e}'
            )
            raise

        # First try to update existing event
        cursor.execute(
            """
            UPDATE conversation_events
            SET metadata = %s, created_at = CURRENT_TIMESTAMP
            WHERE conversation_id = %s AND event_id = %s
            """,
            (json.dumps(metadata), conversation_id, event_id),
        )

        # If no rows were updated, insert new event
        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO conversation_events (conversation_id, event_id, metadata, created_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                """,
                (conversation_id, event_id, json.dumps(metadata)),
            )

    def _write_metadata(
        self,
        cursor: psycopg.Cursor,
        conversation_id: str,
        contents: str | bytes,
        user_id: Optional[str],
    ) -> None:
        """Write metadata to conversations table."""
        if isinstance(contents, bytes):
            contents = contents.decode('utf-8')

        try:
            metadata = json.loads(contents)
        except json.JSONDecodeError as e:
            logger.error(
                f'Failed to parse metadata JSON for conversation {conversation_id}: {e}'
            )
            raise

        # First check if conversation exists
        cursor.execute(
            'SELECT id FROM conversations WHERE conversation_id = %s AND user_id = %s',
            (conversation_id, user_id or ''),
        )

        if cursor.fetchone():
            # Update existing conversation
            cursor.execute(
                """
                UPDATE conversations
                SET metadata = %s
                WHERE conversation_id = %s AND user_id = %s
                """,
                (json.dumps(metadata), conversation_id, user_id or ''),
            )
        else:
            # Insert new conversation
            cursor.execute(
                """
                INSERT INTO conversations (user_id, conversation_id, metadata, published, created_at)
                VALUES (%s, %s, %s, false, CURRENT_TIMESTAMP)
                """,
                (user_id or '', conversation_id, json.dumps(metadata)),
            )

    def _write_user_setting(
        self,
        cursor: psycopg.Cursor,
        user_id: str,
        contents: str | bytes,
    ) -> None:
        """Write user settings to user_settings table."""
        if isinstance(contents, bytes):
            contents = contents.decode('utf-8')
        try:
            settings = json.loads(contents)
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse settings JSON for user {user_id}: {e}')
            raise

        # Try to update existing settings
        cursor.execute(
            """
            UPDATE user_settings
            SET settings = %s
            WHERE user_id = %s
            """,
            (json.dumps(settings), user_id),
        )
        # If no rows were updated, insert new settings
        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO user_settings (user_id, settings)
                VALUES (%s, %s)
                """,
                (user_id, json.dumps(settings)),
            )

    def _write_agent_state(
        self,
        cursor: psycopg.Cursor,
        conversation_id: str,
        contents: str | bytes,
        user_id: Optional[str],
    ) -> None:
        """Write agent state to agent_states table."""

        if isinstance(contents, bytes):
            contents = contents.decode('utf-8')

        try:
            state = json.loads(contents)
        except json.JSONDecodeError as e:
            logger.error(
                f'Failed to parse agent state JSON for conversation {conversation_id}: {e}'
            )
            raise
        try:
            # First try to update existing state
            cursor.execute(
                """
                UPDATE agent_states
                SET metadata = %s, updated_at = CURRENT_TIMESTAMP
                WHERE conversation_id = %s
                """,
                (json.dumps(state), conversation_id),
            )

            # If no rows were updated, insert new state
            if cursor.rowcount == 0:
                logger.info(
                    f'Inserting new agent state for conversation {conversation_id}'
                )
                cursor.execute(
                    """
                    INSERT INTO agent_states (conversation_id, metadata, created_at, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (conversation_id, json.dumps(state)),
                )
                logger.debug(
                    f'Inserted new agent state for conversation {conversation_id}'
                )
            else:
                logger.debug(f'Updated agent state for conversation {conversation_id}')
        except Exception as e:
            logger.error(
                f'Failed to write agent state for conversation {conversation_id}: {e}'
            )
            raise

    def read(self, path: str) -> str:
        """Read contents from database based on path type."""
        if path == 'settings.json':
            return '{}'
        try:
            parsed_path = parse_conversation_path(path)
            if parsed_path is None:
                logger.error(f'Failed to parse conversation path: {path}')
                raise FileNotFoundError(f'Invalid path format: {path}')

            session_id = parsed_path['session_id']
            event_id = parsed_path['event_id']
            path_type = parsed_path['type']

            with db_pool.get_connection_context() as conn:
                with conn.cursor() as cursor:
                    if path_type == 'events':
                        return self._read_event(cursor, session_id, event_id)
                    elif path_type == 'metadata':
                        user_id = parsed_path['user_id']
                        return self._read_metadata(cursor, session_id, user_id)
                    elif path_type == 'settings' and parsed_path['user_id']:
                        return self._read_user_setting(cursor, parsed_path['user_id'])
                    elif path_type == 'agent_state':
                        return self._read_agent_state(
                            cursor, session_id, parsed_path['user_id']
                        )
                    else:
                        logger.warning(f'Unsupported path type for read: {path_type}')
                        raise FileNotFoundError(f'Unsupported path type: {path_type}')

        except Exception as e:
            logger.error(f'Error reading from database for path {path}: {str(e)}')
            raise

    def _read_event(
        self, cursor: psycopg.Cursor, conversation_id: str, event_id: int
    ) -> str:
        """Read event data from conversation_events table."""
        cursor.execute(
            'SELECT metadata FROM conversation_events WHERE conversation_id = %s AND event_id = %s',
            (conversation_id, event_id),
        )

        result = cursor.fetchone()
        if result is None:
            raise FileNotFoundError(
                f'Event {event_id} not found for conversation {conversation_id}'
            )

        return json.dumps(result[0]) if isinstance(result[0], dict) else result[0]

    def _read_metadata(
        self, cursor, conversation_id: str, user_id: Optional[str]
    ) -> str:
        """Read metadata from conversations table."""
        cursor.execute(
            'SELECT metadata FROM conversations WHERE conversation_id = %s AND user_id = %s',
            (conversation_id, user_id or ''),
        )

        result = cursor.fetchone()
        if result is None:
            raise FileNotFoundError(
                f'Metadata not found for conversation {conversation_id}'
            )

        return json.dumps(result[0]) if isinstance(result[0], dict) else result[0]

    def _read_user_setting(
        self,
        cursor: psycopg.Cursor,
        user_id: str,
    ) -> str:
        """Read user settings from user_settings table."""
        cursor.execute(
            'SELECT settings FROM user_settings WHERE user_id = %s',
            (user_id,),
        )
        result = cursor.fetchone()
        if result is None:
            return '{}'
        return json.dumps(result[0]) if isinstance(result[0], dict) else result[0]

    def _read_agent_state(
        self, cursor: psycopg.Cursor, conversation_id: str, user_id: Optional[str]
    ) -> str:
        cursor.execute(
            'SELECT metadata FROM agent_states WHERE conversation_id = %s',
            (conversation_id,),
        )

        result = cursor.fetchone()
        if result is None:
            raise FileNotFoundError(
                f'Agent state not found for conversation {conversation_id}'
            )

        return json.dumps(result[0]) if isinstance(result[0], dict) else result[0]

    def list(self, path: str) -> List[str]:
        """List files/events based on path pattern."""
        try:
            parsed_path = parse_conversation_path(path)
            if parsed_path is None:
                logger.error(f'Failed to parse conversation path for listing: {path}')
                return []

            session_id = parsed_path['session_id']
            path_type = parsed_path['type']

            with db_pool.get_connection_context() as conn:
                with conn.cursor() as cursor:
                    if path_type == 'events':
                        return self._list_events_for_conversation(cursor, session_id)
                    else:
                        logger.warning(
                            f'Listing not supported for path type: {path_type}'
                        )
                        return []

        except Exception as e:
            logger.error(f'Error listing database for path {path}: {str(e)}')
            return []

    def _list_events_for_conversation(
        self, cursor: psycopg.Cursor, conversation_id: str
    ) -> List[str]:
        """List all metadata entries for a conversation from conversation_events table."""
        cursor.execute(
            'SELECT metadata FROM conversation_events WHERE conversation_id = %s ORDER BY created_at',
            (conversation_id,),
        )

        results = cursor.fetchall()
        metadata_list = []
        for metadata in results:
            metadata_list.append(json.dumps(metadata[0]))
        return metadata_list

    def delete(self, path: str) -> None:
        """Delete data from database based on path type."""
        try:
            parsed_path = parse_conversation_path(path)
            if parsed_path is None:
                logger.error(f'Failed to parse conversation path: {path}')
                return

            session_id = parsed_path['session_id']
            event_id = parsed_path['event_id']
            path_type = parsed_path['type']

            with db_pool.get_connection_context() as conn:
                with conn.cursor() as cursor:
                    if path_type == 'events':
                        self._delete_event(cursor, session_id, event_id)
                    elif path_type == 'metadata':
                        user_id = parsed_path['user_id']
                        self._delete_metadata(cursor, session_id, user_id)
                    elif path_type == 'agent_state':
                        self._delete_agent_state(
                            cursor, session_id, parsed_path['user_id']
                        )
                    else:
                        logger.warning(f'Unsupported path type for delete: {path_type}')
                        return

                    conn.commit()
                    logger.debug(
                        f'Successfully deleted {path_type} for session {session_id}'
                    )

        except Exception as e:
            logger.error(f'Error deleting from database for path {path}: {str(e)}')
            raise

    def _delete_event(
        self, cursor: psycopg.Cursor, conversation_id: str, event_id: int
    ) -> None:
        """Delete event from conversation_events table."""
        cursor.execute(
            'DELETE FROM conversation_events WHERE conversation_id = %s AND event_id = %s',
            (conversation_id, event_id),
        )

    def _delete_metadata(
        self, cursor: psycopg.Cursor, conversation_id: str, user_id: Optional[str]
    ) -> None:
        """Delete conversation metadata (set metadata to empty)."""
        cursor.execute(
            """
            UPDATE conversations
            SET metadata = '{}'::jsonb
            WHERE conversation_id = %s AND user_id = %s
            """,
            (conversation_id, user_id or ''),
        )

    def _delete_agent_state(
        self, cursor: psycopg.Cursor, conversation_id: str, user_id: Optional[str]
    ) -> None:
        """Delete agent state from agent_states table."""
        logger.info(f'Deleting agent state for conversation {conversation_id}')
        cursor.execute(
            """
            DELETE FROM agent_states WHERE conversation_id = %s
            """,
            (conversation_id,),
        )

    def _get_latest_event_id(self, conversation_id: str) -> int:
        """Get the latest event id from conversation_events table."""
        with db_pool.get_connection_context() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    'SELECT MAX(event_id) FROM conversation_events WHERE conversation_id = %s',
                    (conversation_id,),
                )
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else 0

    def _get_events_from_start_id(
        self, conversation_id: str, start_id: int
    ) -> List[dict]:
        """Get the start event id from conversation_events table."""
        with db_pool.get_connection_context() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    'SELECT metadata FROM conversation_events WHERE conversation_id = %s AND event_id >= %s ORDER BY event_id',
                    (conversation_id, start_id),
                )
                return [event[0] for event in cursor.fetchall()]

    def _check_event_exists(self, conversation_id: str) -> bool:
        """Check if event exists in conversation_events table."""
        with db_pool.get_connection_context() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    'SELECT conversation_id FROM conversations WHERE conversation_id = %s AND status <> %s',
                    (conversation_id, 'deleted'),
                )
                result = cursor.fetchone()
                return result is not None


db_file_store = DatabaseFileStore()
