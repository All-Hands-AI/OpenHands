import base64
import datetime
import json
import pickle
import sys
import time
from pathlib import Path

from openhands.controller.state.state import State
from openhands.core.config import load_app_config
from openhands.core.database import db_pool
from openhands.core.logger import openhands_logger as logger

# Checkpoint file to track migration progress
CHECKPOINT_FILE = 'migration_checkpoint.json'
migrated_conversations_ids = set()


def get_checkpoint():
    """Get the last migration checkpoint timestamp."""
    try:
        checkpoint_path = Path(CHECKPOINT_FILE)
        if checkpoint_path.exists():
            with open(checkpoint_path, 'r') as f:
                data = json.load(f)
                return datetime.datetime.fromisoformat(data.get('last_migration_time'))
    except Exception as e:
        logger.warning(f'Could not load checkpoint: {e}')

    # Default to a very old date if no checkpoint exists
    return datetime.datetime.min


def save_checkpoint(timestamp):
    """Save the migration checkpoint timestamp."""
    try:
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump({'last_migration_time': timestamp.isoformat()}, f)
        logger.info(f'Checkpoint saved: {timestamp.isoformat()}')
    except Exception as e:
        logger.error(f'Could not save checkpoint: {e}')


# get migrated conversations ids from database


def get_migrated_conversations_ids(start_date: datetime.datetime):
    """
    Get IDs of conversations that have already been migrated to the database.

    This function fetches conversations that were created at or before the checkpoint time,
    as these are the ones we've already processed in previous migration runs.
    """
    with db_pool.get_connection_context() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT conversation_id FROM conversations WHERE created_at <= %s',
                (start_date,),
            )
            ids = [row[0] for row in cursor.fetchall()]
            migrated_conversations_ids.update(ids)
            logger.info(
                f'Found {len(ids)} conversations already migrated before {start_date}'
            )


def should_migrate_conversation(conversation_dir, last_checkpoint):
    """Determine if a conversation should be migrated based on modification time."""
    # Always check metadata file first as it's most likely to be updated
    metadata_file = conversation_dir / 'metadata.json'
    if metadata_file.exists():
        mod_time = datetime.datetime.fromtimestamp(metadata_file.stat().st_mtime)
        if mod_time >= last_checkpoint:
            return True

    # Check if any event files were modified after the checkpoint
    events_dir = conversation_dir / 'events'
    if events_dir.exists():
        for event_file in events_dir.glob('*.json'):
            mod_time = datetime.datetime.fromtimestamp(event_file.stat().st_mtime)
            if mod_time >= last_checkpoint:
                return True

    # Check agent state file
    agent_state_file = conversation_dir / 'agent_state.pkl'
    if agent_state_file.exists():
        mod_time = datetime.datetime.fromtimestamp(agent_state_file.stat().st_mtime)
        if mod_time >= last_checkpoint:
            return True

    # If conversation ID is not in the database, migrate it anyway
    conversation_id = conversation_dir.name
    return conversation_id not in migrated_conversations_ids


def migrate_conversation_data(
    cursor, user_id: str, conversation_id: str, conversation_dir: Path
) -> int:
    """Migrate all data for a single conversation. Returns number of events migrated."""
    events_migrated = 0

    # Migrate metadata
    metadata_file = conversation_dir / 'metadata.json'
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        cursor.execute(
            'SELECT id FROM conversations WHERE conversation_id = %s AND user_id = %s',
            (conversation_id, user_id),
        )

        if cursor.fetchone():
            cursor.execute(
                'UPDATE conversations SET metadata = %s, title = %s WHERE conversation_id = %s AND user_id = %s',
                (
                    json.dumps(metadata),
                    metadata.get('title', ''),
                    conversation_id,
                    user_id,
                ),
            )
        else:
            cursor.execute(
                'INSERT INTO conversations (user_id, conversation_id, metadata, published, title, created_at) VALUES (%s, %s, %s, %s, %s, %s)',
                (
                    user_id,
                    conversation_id,
                    json.dumps(metadata),
                    False,
                    metadata.get('title', ''),
                    metadata.get('created_at'),
                ),
            )

    # Migrate events in bulk
    events_dir = conversation_dir / 'events'
    if events_dir.exists():
        event_files = sorted(
            [f for f in events_dir.glob('*.json') if f.stem.isdigit()],
            key=lambda x: int(x.stem),
        )

        # Collect and filter events
        events_to_insert = []
        events_to_update = []

        for event_file in event_files:
            event_id = int(event_file.stem)
            with open(event_file, 'r') as f:
                event_data = json.load(f)

            # Filter out streaming_action events
            if (
                event_data.get('action') == 'streaming_action'
                or event_data.get('observation') == 'streaming_action'
            ):
                continue

            # Check if event already exists
            cursor.execute(
                'SELECT id FROM conversation_events WHERE conversation_id = %s AND event_id = %s',
                (conversation_id, event_id),
            )

            if cursor.fetchone():
                events_to_update.append(
                    (json.dumps(event_data), conversation_id, event_id)
                )
            else:
                events_to_insert.append(
                    (conversation_id, event_id, json.dumps(event_data))
                )

        # Bulk insert new events
        if events_to_insert:
            cursor.executemany(
                'INSERT INTO conversation_events (conversation_id, event_id, metadata, created_at) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)',
                events_to_insert,
            )
            events_migrated += len(events_to_insert)

        # Bulk update existing events
        if events_to_update:
            cursor.executemany(
                'UPDATE conversation_events SET metadata = %s WHERE conversation_id = %s AND event_id = %s',
                events_to_update,
            )
            events_migrated += len(events_to_update)

    # Migrate agent state
    agent_state_file = conversation_dir / 'agent_state.pkl'
    if agent_state_file.exists():
        state: State
        try:
            with open(agent_state_file, 'rb') as f:
                data = f.read()
                pickled = base64.b64decode(data)
                state = pickle.loads(pickled)
            state_json = state.to_json()

        except Exception:
            state_json = json.dumps({'error': 'Could not serialize agent state'})

        cursor.execute(
            'SELECT id FROM agent_states WHERE conversation_id = %s', (conversation_id,)
        )

        if cursor.fetchone():
            cursor.execute(
                'UPDATE agent_states SET metadata = %s, updated_at = CURRENT_TIMESTAMP WHERE conversation_id = %s',
                (state_json, conversation_id),
            )
        else:
            cursor.execute(
                'INSERT INTO agent_states (conversation_id, metadata, created_at, updated_at) VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                (conversation_id, state_json),
            )

    return events_migrated


def migrate_user_settings(cursor, user_id: str, settings_file: Path) -> None:
    """Migrate user settings."""
    if not settings_file.exists():
        return

    with open(settings_file, 'r') as f:
        settings_data = json.load(f)

    cursor.execute('SELECT id FROM user_settings WHERE user_id = %s', (user_id,))

    if cursor.fetchone():
        cursor.execute(
            'UPDATE user_settings SET settings = %s WHERE user_id = %s',
            (json.dumps(settings_data), user_id),
        )
    else:
        cursor.execute(
            'INSERT INTO user_settings (user_id, settings) VALUES (%s, %s)',
            (user_id, json.dumps(settings_data)),
        )


def reconcile_database_with_filestore(file_store_path):
    """
    Reconcile database with filestore to ensure no conversations were missed.
    This is a final check to guarantee data consistency.
    """
    logger.info('Starting database-filestore reconciliation...')
    users_dir = file_store_path / 'users'

    total_reconciled = 0

    with db_pool.get_connection_context() as conn:
        with conn.cursor() as cursor:
            # Get all conversation IDs from database
            cursor.execute('SELECT conversation_id FROM conversations')
            db_conversation_ids = {row[0] for row in cursor.fetchall()}

            for user_dir in users_dir.iterdir():
                if not user_dir.is_dir():
                    continue

                user_id = user_dir.name
                conversations_dir = user_dir / 'conversations'
                if not conversations_dir.exists():
                    continue

                for conversation_dir in conversations_dir.iterdir():
                    if not conversation_dir.is_dir():
                        continue

                    conversation_id = conversation_dir.name
                    if conversation_id not in db_conversation_ids:
                        logger.info(
                            f'Reconciling missing conversation: {conversation_id}'
                        )

                        try:
                            events_count = migrate_conversation_data(
                                cursor, user_id, conversation_id, conversation_dir
                            )
                            conn.commit()
                            total_reconciled += 1
                            logger.info(
                                f'✓ Reconciled conversation {conversation_id} - {events_count} events'
                            )
                        except Exception as e:
                            logger.error(
                                f'✗ Error reconciling conversation {conversation_id}: {e}'
                            )
                            conn.rollback()

    logger.info(
        f'Reconciliation completed. Found and migrated {total_reconciled} missing conversations.'
    )
    return total_reconciled


def migration_from_local_to_database():
    """Main migration function."""
    config_app = load_app_config()

    if not isinstance(config_app.file_store_path, str):
        logger.error('file_store_path must be configured')
        return

    file_store_path = Path(config_app.file_store_path)
    users_dir = file_store_path / 'users'

    if not users_dir.exists():
        logger.info('No users directory found in file store')
        return

    # Record migration start time for checkpoint
    migration_start_time = datetime.datetime.now()

    # Get the last checkpoint time
    last_checkpoint = get_checkpoint()
    logger.info(
        f'Starting migration from {file_store_path}, using checkpoint: {last_checkpoint}'
    )

    # Load migrated IDs from database if we have a meaningful checkpoint
    if last_checkpoint > datetime.datetime.min:
        get_migrated_conversations_ids(last_checkpoint)
        logger.info(
            f'Loaded {len(migrated_conversations_ids)} conversation IDs from database since {last_checkpoint}'
        )

    db_pool.init_pool()

    total_conversations = 0
    total_events = 0
    total_users = 0

    with db_pool.get_connection_context() as conn:
        with conn.cursor() as cursor:
            for user_dir in users_dir.iterdir():
                if not user_dir.is_dir():
                    continue

                user_id = user_dir.name
                total_users += 1

                # Migrate user settings
                settings_file = user_dir / 'settings.json'
                if settings_file.exists() and (
                    datetime.datetime.fromtimestamp(settings_file.stat().st_mtime)
                    >= last_checkpoint
                ):
                    migrate_user_settings(cursor, user_id, settings_file)

                # Migrate conversations
                conversations_dir = user_dir / 'conversations'
                if not conversations_dir.exists():
                    continue

                for conversation_dir in conversations_dir.iterdir():
                    if not conversation_dir.is_dir():
                        continue

                    conversation_id = conversation_dir.name

                    # Skip if not modified since last checkpoint and already in DB
                    if not should_migrate_conversation(
                        conversation_dir, last_checkpoint
                    ):
                        continue

                    total_conversations += 1

                    # Time the conversation processing
                    start_time = time.time()

                    try:
                        events_count = migrate_conversation_data(
                            cursor, user_id, conversation_id, conversation_dir
                        )
                        conn.commit()

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
                        conn.rollback()

    # Run reconciliation to catch any missed conversations
    total_reconciled = reconcile_database_with_filestore(file_store_path)

    # Save the checkpoint for next migration
    save_checkpoint(migration_start_time)

    logger.info(
        f'🎉 All migration completed! Users: {total_users}, Conversations: {total_conversations}, Events: {total_events}, Reconciled: {total_reconciled}, on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    )


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--reset-checkpoint':
            # Delete checkpoint file to start fresh
            try:
                Path(CHECKPOINT_FILE).unlink(missing_ok=True)
                logger.info('Checkpoint reset. Will migrate all conversations.')
            except Exception as e:
                logger.error(f'Error resetting checkpoint: {e}')
        else:
            # Treat argument as start date
            start_date = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
            get_migrated_conversations_ids(start_date)

    migration_from_local_to_database()
