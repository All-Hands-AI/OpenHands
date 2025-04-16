import os
import asyncio
from pathlib import Path
import asyncpg


async def run_migration():
    # Get database connection info from environment
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT')

    # Read SQL file
    migration_path = Path(__file__).parent / 'init.sql'
    with open(migration_path, 'r') as f:
        sql = f.read()

    # Replace environment variables in SQL
    sql = sql.replace('${POSTGRES_DB}', POSTGRES_DB)

    try:
        # Connect to default database first to create new database if needed
        conn = await asyncpg.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database='postgres'  # Connect to default database first
        )

        # Execute migration
        await conn.execute(sql)
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {str(e)}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
