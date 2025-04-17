import os
import asyncio
from pathlib import Path
import asyncpg


async def create_database_if_not_exists(conn, db_name):
    """Create database if it doesn't exist"""
    exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1",
        db_name
    )
    if not exists:
        # Need to use a separate connection to create database
        # because we can't create a database inside a transaction
        await conn.execute(f'CREATE DATABASE "{db_name}"')
        print(f"Created database {db_name}")


async def run_migration():
    # Get database connection info from environment
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT')

    try:
        # First connect to default database to create new database if needed
        sys_conn = await asyncpg.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database='postgres'
        )

        try:
            await create_database_if_not_exists(sys_conn, POSTGRES_DB)
        finally:
            await sys_conn.close()

        # Now connect to our database to run migrations
        conn = await asyncpg.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB
        )

        try:
            # Read and execute migration SQL
            migration_path = Path(__file__).parent / 'migrate.sql'
            with open(migration_path, 'r') as f:
                sql = f.read()

            await conn.execute(sql)
            print("Migration completed successfully!")
        finally:
            await conn.close()

    except Exception as e:
        print(f"Error during migration: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_migration())
