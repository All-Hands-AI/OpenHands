"""Check if the status column exists in the users table."""
import asyncio
import logging
import os
import sys

from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from openhands.server.db import database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_column() -> None:
    """Check if the status column exists in the users table."""
    try:
        await database.connect()
        
        # Check if column exists and get its type
        query = text("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'status'
        """)
        
        result = await database.fetch_all(query)
        
        if result:
            print("Status column exists in users table:")
            for row in result:
                print(f"Column: {row['column_name']}, Type: {row['data_type']}, UDT: {row['udt_name']}")
        else:
            print("Status column does not exist in users table")
            
        # Check if the user_status enum type exists
        enum_query = text("""
            SELECT typname, typcategory 
            FROM pg_type 
            WHERE typname = 'user_status'
        """)
        
        enum_result = await database.fetch_all(enum_query)
        
        if enum_result:
            print("user_status enum type exists:")
            for row in enum_result:
                print(f"Type: {row['typname']}, Category: {row['typcategory']}")
        else:
            print("user_status enum type does not exist")
            
    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(check_column())