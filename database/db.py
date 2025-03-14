import os
import asyncpg
from typing import Optional, List, Dict, Any
import json
from contextlib import asynccontextmanager

class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Connect to the database"""
        if self.pool is None:
            # Get connection details from environment variables
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "5432")
            user = os.getenv("DB_USER", "postgres")
            password = os.getenv("DB_PASSWORD", "postgres")
            database = os.getenv("DB_NAME", "openhands")
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
    
    async def disconnect(self):
        """Disconnect from the database"""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    async def execute(self, query: str, *args, **kwargs) -> str:
        """Execute a query"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args, **kwargs)
    
    async def fetch(self, query: str, *args, **kwargs) -> List[Dict[str, Any]]:
        """Fetch rows from a query"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args, **kwargs)
            return [dict(row) for row in rows]
    
    async def fetchrow(self, query: str, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """Fetch a single row from a query"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args, **kwargs)
            return dict(row) if row else None
    
    async def fetchval(self, query: str, *args, **kwargs) -> Any:
        """Fetch a single value from a query"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args, **kwargs)

# Global database instance
db = Database()
