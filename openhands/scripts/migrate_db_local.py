import base64
import datetime
import json
import pickle
import sys
import time
from pathlib import Path
from typing import Dict, List

from openhands.controller.state.state import State
from openhands.core.config import load_app_config
from openhands.core.database import db_pool
from openhands.core.logger import openhands_logger as logger

existing_conversations_ids = set()


def get_existing_conversations_ids(
    file_store_path: Path, start_date: datetime.datetime = None
):
    """Get existing conversation IDs from local file store to avoid duplicates."""
    users_dir = file_store_path / 'users'
    if not users_dir.exists():
        return

    for user_dir in users_dir.iterdir():
        if not user_dir.is_dir():
            continue

        conversations_dir = user_dir / 'conversations'
        if not conversations_dir.exists():
            continue

        for conversation_dir in conversations_dir.iterdir():
            if not conversation_dir.is_dir():
                continue

            # Check metadata file date if start_date provided
            if start_date:
                metadata_file = conversation_dir / 'metadata.json'
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        created_at = metadata.get('created_at')
                        if created_at:
                            file_date = datetime.datetime.fromisoformat(
                                created_at.replace('Z', '+00:00')
                            )
                            if file_date >= start_date:
                                existing_conversations_ids.add(conversation_dir.name)
                    except Exception:
                        pass
            else:
                existing_conversations_ids.add(conversation_dir.name)


def create_conversation_files(
    user_id: str,
    conversation_id: str,
    conversation_data: Dict,
    events_data: List[Dict],
    agent_state_data: Dict,
    file_store_path: Path,
) -> int:
    """Create local files for a single conversation. Returns number of events created."""

    # Create directory structure
    conversation_dir = (
        file_store_path / 'users' / user_id / 'conversations' / conversation_id
    )
    conversation_dir.mkdir(parents=True, exist_ok=True)

    events_created = 0

    # Create metadata.json
    if conversation_data:
        metadata_file = conversation_dir / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(conversation_data, f, indent=2)

    # Create events files
    if events_data:
        events_dir = conversation_dir / 'events'
        events_dir.mkdir(exist_ok=True)

        for event in events_data:
            event_id = event.get('event_id', 0)
            event_file = events_dir / f'{event_id}.json'

            # Extract metadata from the database record
            event_metadata = event.get('metadata', {})
            if isinstance(event_metadata, str):
                event_metadata = json.loads(event_metadata)

            with open(event_file, 'w') as f:
                json.dump(event_metadata, f, separators=(',', ':'))
            events_created += 1

    # Create agent_state.pkl
    if agent_state_data and agent_state_data.get('metadata'):
        try:
            agent_state_file = conversation_dir / 'agent_state.pkl'
            metadata = agent_state_data['metadata']

            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            # Try to reconstruct State object if it's not an error
            if not metadata.get('error'):
                try:
                    # Convert JSON back to State object then pickle
                    state = State.from_json(json.dumps(metadata))
                    pickled_data = pickle.dumps(state)
                    encoded_data = base64.b64encode(pickled_data)

                    with open(agent_state_file, 'wb') as f:
                        f.write(encoded_data)
                except Exception:
                    # Fallback: create a simple pickle with the raw data
                    pickled_data = pickle.dumps(metadata)
                    encoded_data = base64.b64encode(pickled_data)

                    with open(agent_state_file, 'wb') as f:
                        f.write(encoded_data)
        except Exception as e:
            logger.warning(
                f'Could not create agent state file for {conversation_id}: {e}'
            )

    return events_created


def create_user_settings_file(
    user_id: str, settings_data: Dict, file_store_path: Path
) -> None:
    """Create settings.json file for a user."""
    if not settings_data:
        return

    user_dir = file_store_path / 'users' / user_id
    user_dir.mkdir(parents=True, exist_ok=True)

    settings_file = user_dir / 'settings.json'

    # Extract settings from database record
    settings = settings_data.get('settings', {})
    if isinstance(settings, str):
        settings = json.loads(settings)

    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)


def migration_from_database_to_local():
    """Main migration function from database to local file store."""
    config_app = load_app_config()

    if not isinstance(config_app.file_store_path, str):
        logger.error('file_store_path must be configured')
        return

    file_store_path = Path(config_app.file_store_path)
    file_store_path.mkdir(parents=True, exist_ok=True)

    logger.info(f'Starting migration from database to {file_store_path}')
    db_pool.init_pool()

    total_conversations = 0
    total_events = 0
    total_users = 0

    with db_pool.get_connection_context() as conn:
        with conn.cursor() as cursor:
            # Get all users from conversations
            cursor.execute(
                'SELECT DISTINCT user_id FROM conversations ORDER BY user_id'
            )
            user_ids = [row[0] for row in cursor.fetchall()]

            for user_id in user_ids:
                if not user_id:  # Skip empty user_ids
                    continue

                total_users += 1
                logger.info(f'Migrating data for user: {user_id}')

                # Migrate user settings
                cursor.execute(
                    'SELECT settings FROM user_settings WHERE user_id = %s', (user_id,)
                )
                user_settings = cursor.fetchone()
                if user_settings:
                    create_user_settings_file(
                        user_id, {'settings': user_settings[0]}, file_store_path
                    )

                # Get all conversations for this user
                cursor.execute(
                    'SELECT conversation_id, metadata, title, created_at FROM conversations WHERE user_id = %s ORDER BY created_at',
                    (user_id,),
                )
                conversations = cursor.fetchall()

                for conv_row in conversations:
                    conversation_id, metadata, title, created_at = conv_row

                    # Skip if already exists (when using start_date filter)
                    if conversation_id in existing_conversations_ids:
                        continue

                    total_conversations += 1
                    start_time = time.time()

                    try:
                        # Prepare conversation metadata
                        if isinstance(metadata, str):
                            conversation_data = json.loads(metadata)
                        else:
                            conversation_data = metadata or {}

                        # Ensure required fields
                        conversation_data.update(
                            {
                                'conversation_id': conversation_id,
                                'user_id': user_id,
                                'title': title or conversation_data.get('title', ''),
                                'created_at': created_at.isoformat()
                                if created_at
                                else None,
                            }
                        )

                        # Get events for this conversation
                        cursor.execute(
                            'SELECT event_id, metadata FROM conversation_events WHERE conversation_id = %s ORDER BY event_id',
                            (conversation_id,),
                        )
                        events_data = [
                            {'event_id': row[0], 'metadata': row[1]}
                            for row in cursor.fetchall()
                        ]

                        # Get agent state for this conversation
                        cursor.execute(
                            'SELECT metadata FROM agent_states WHERE conversation_id = %s',
                            (conversation_id,),
                        )
                        agent_state_row = cursor.fetchone()
                        agent_state_data = (
                            {'metadata': agent_state_row[0]}
                            if agent_state_row
                            else None
                        )

                        # Create local files
                        events_count = create_conversation_files(
                            user_id,
                            conversation_id,
                            conversation_data,
                            events_data,
                            agent_state_data,
                            file_store_path,
                        )

                        end_time = time.time()
                        processing_time = end_time - start_time
                        total_events += events_count

                        logger.info(
                            f'✓ Conversation {conversation_id} completed - {events_count} events, {processing_time:.4f}s'
                        )

                    except Exception as e:
                        end_time = time.time()
                        processing_time = end_time - start_time
                        logger.error(
                            f'✗ Error migrating conversation {conversation_id} after {processing_time:.4f}s: {e}'
                        )

    logger.info(
        f'🎉 All migration completed! Users: {total_users}, Conversations: {total_conversations}, Events: {total_events}, on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    )


if __name__ == '__main__':
    config_app = load_app_config()
    file_store_path = (
        Path(config_app.file_store_path)
        if config_app.file_store_path
        else Path('/tmp/openhands_file_store')
    )

    # Handle start date filter
    start_date = None
    if len(sys.argv) > 1:
        start_date = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
        logger.info(f'Filtering conversations created after: {start_date}')
        get_existing_conversations_ids(file_store_path, start_date)
    else:
        get_existing_conversations_ids(file_store_path)

    migration_from_database_to_local()
