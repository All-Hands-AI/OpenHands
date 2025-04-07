#!/usr/bin/env python3
"""
Migration script to update existing conversation metadata files with new cost and token metrics fields.
This script adds the following fields to all existing conversation metadata files:
- accumulated_cost
- prompt_tokens
- completion_tokens
- total_tokens
"""

import asyncio
import json
import os
from pathlib import Path

from openhands.core.logger import openhands_logger as logger
from openhands.storage import get_file_store
from openhands.storage.locations import CONVERSATION_BASE_DIR, get_conversation_metadata_filename


async def migrate_conversation_metadata():
    """
    Migrate all conversation metadata files to include the new cost and token metrics fields.
    """
    logger.info("Starting conversation metadata migration")
    
    file_store = get_file_store()
    
    # Get all conversation directories
    try:
        conversation_dirs = [
            d for d in Path(CONVERSATION_BASE_DIR).iterdir() if d.is_dir()
        ]
    except FileNotFoundError:
        logger.info(f"No conversation directory found at {CONVERSATION_BASE_DIR}")
        return
    
    migration_count = 0
    error_count = 0
    
    for conversation_dir in conversation_dirs:
        # Process each conversation directory
        for user_dir in conversation_dir.iterdir():
            if not user_dir.is_dir():
                continue
                
            for conversation_id_dir in user_dir.iterdir():
                if not conversation_id_dir.is_dir():
                    continue
                
                # Get the metadata file path
                metadata_path = conversation_id_dir / "metadata.json"
                if not metadata_path.exists():
                    continue
                
                try:
                    # Read the metadata file
                    metadata_json = json.loads(file_store.read(str(metadata_path)))
                    
                    # Add new fields if they don't exist
                    updated = False
                    if "accumulated_cost" not in metadata_json:
                        metadata_json["accumulated_cost"] = 0.0
                        updated = True
                    if "prompt_tokens" not in metadata_json:
                        metadata_json["prompt_tokens"] = 0
                        updated = True
                    if "completion_tokens" not in metadata_json:
                        metadata_json["completion_tokens"] = 0
                        updated = True
                    if "total_tokens" not in metadata_json:
                        metadata_json["total_tokens"] = 0
                        updated = True
                    
                    # Write back the updated metadata if changes were made
                    if updated:
                        file_store.write(str(metadata_path), json.dumps(metadata_json))
                        migration_count += 1
                        if migration_count % 100 == 0:
                            logger.info(f"Migrated {migration_count} conversation metadata files")
                
                except Exception as e:
                    logger.error(f"Error migrating metadata for conversation {conversation_id_dir}: {e}")
                    error_count += 1
    
    logger.info(f"Migration completed. Updated {migration_count} files. Errors: {error_count}")


if __name__ == "__main__":
    asyncio.run(migrate_conversation_metadata())