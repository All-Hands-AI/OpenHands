"""Add user status field to users table."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

async def upgrade(conn: AsyncConnection) -> None:
    """Add status column to users table."""
    
    # Check if the table exists with case-insensitive check
    table_check = await conn.execute(
        text("""
        SELECT tablename FROM pg_tables 
        WHERE LOWER(tablename) = 'users' AND schemaname = 'public';
        """)
    )
    table_result = table_check.first()
    
    if not table_result:
        print("Table 'users' does not exist!")
        return
    
    # Get the actual table name with correct case
    actual_table_name = table_result[0]
    print(f"Found table: {actual_table_name}")
    
    # Create enum type
    await conn.execute(
        text("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_status') THEN
                CREATE TYPE user_status AS ENUM ('activated', 'non_activated', 'banned');
            END IF;
        END $$;
        """)
    )
    
    # Check if column exists
    column_check = await conn.execute(
        text(f"""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = :table_name
            AND column_name = 'status'
        );
        """),
        {"table_name": actual_table_name}
    )
    column_result = column_check.first()
    column_exists = column_result[0] if column_result else False
    
    if not column_exists:
        # Add the status column if it doesn't exist
        await conn.execute(
            text(f"""
            ALTER TABLE "{actual_table_name}" 
            ADD COLUMN status user_status 
            NOT NULL DEFAULT 'non_activated'::user_status
            """)
        )
        print(f"Added status column to {actual_table_name} table")
    else:
        print(f"Status column already exists in {actual_table_name} table")

async def downgrade(conn: AsyncConnection) -> None:
    """Remove status column from users table."""
    # Check if the table exists with case-insensitive check
    table_check = await conn.execute(
        text("""
        SELECT tablename FROM pg_tables 
        WHERE LOWER(tablename) = 'users' AND schemaname = 'public';
        """)
    )
    table_result = table_check.first()
    
    if not table_result:
        print("Table 'users' does not exist!")
        return
    
    # Get the actual table name with correct case
    actual_table_name = table_result[0]
    
    # Check if column exists
    column_check = await conn.execute(
        text(f"""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = :table_name
            AND column_name = 'status'
        );
        """),
        {"table_name": actual_table_name}
    )
    column_result = column_check.first()
    column_exists = column_result[0] if column_result else False
    
    if column_exists:
        # Drop the status column if it exists
        await conn.execute(
            text(f"""
            ALTER TABLE "{actual_table_name}" DROP COLUMN status;
            """)
        )
        print(f"Removed status column from {actual_table_name} table")
        
        # Drop the enum type
        await conn.execute(
            text("""
            DROP TYPE IF EXISTS user_status;
            """)
        )
        print("Dropped user_status enum type")
    else:
        print(f"Status column does not exist in {actual_table_name} table")