"""Script to run database migrations."""
import asyncio
import importlib
import logging
import os
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from openhands.server.db import engine  # noqa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migrations() -> None:
    """Run all migrations in order."""
    logger.info("Running migrations...")
    
    # Get all migration files
    migrations_dir = Path(__file__).parent / "migrations"
    migration_files = sorted([f for f in migrations_dir.glob("*.py") if not f.name.startswith("__")])
    
    logger.info(f"Found {len(migration_files)} migration files: {[f.name for f in migration_files]}")
    
    # Run each migration
    async with engine.begin() as conn:
        for migration_path in migration_files:
            migration_name = migration_path.stem
            logger.info(f"Running migration: {migration_name}")
            
            # Import the migration module
            module_path = f"openhands.server.database.migrations.{migration_name}"
            try:
                migration_module = importlib.import_module(module_path)
                
                # Run the upgrade function
                logger.info(f"Executing upgrade for {migration_name}")
                await migration_module.upgrade(conn)
                logger.info(f"Successfully applied migration: {migration_name}")
                
            except Exception as e:
                logger.error(f"Error running migration {migration_name}: {e}")
                raise
    
    logger.info("All migrations completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_migrations()) 