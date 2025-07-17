import os
from contextlib import contextmanager

from psycopg_pool import ConnectionPool

from openhands.core.logger import openhands_logger as logger


class DBConnectionPool:
    """
    Singleton class for managing database connections.
    Uses connection pooling to efficiently handle database operations.
    """

    _instance = None
    _pool = None
    _initializing = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBConnectionPool, cls).__new__(cls)
        return cls._instance

    def init_pool(self):
        """Initialize the connection pool if not already initialized."""
        if self._pool is None and not self._initializing:
            try:
                self._initializing = True

                # Get database connection info from environment
                user = os.getenv('PGBOUNCER_DB_USER') or os.getenv('POSTGRES_USER')
                password = os.getenv('PGBOUNCER_DB_PASSWORD') or os.getenv(
                    'POSTGRES_PASSWORD'
                )
                database = os.getenv('PGBOUNCER_DB_NAME') or os.getenv('POSTGRES_DB')
                host = os.getenv('PGBOUNCER_DB_HOST') or os.getenv('POSTGRES_HOST')
                port = os.getenv('PGBOUNCER_DB_PORT') or os.getenv(
                    'POSTGRES_PORT', '5432'
                )

                # Build connection string for psycopg3
                conninfo = f'host={host} port={port} dbname={database} user={user} password={password}'

                # Create a connection pool with improved settings
                self._pool = ConnectionPool(
                    conninfo=conninfo,
                    min_size=3,  # Minimum connections
                    max_size=25,  # Increased maximum connections
                    timeout=10.0,  # Pool operation timeout
                    max_idle=300.0,  # 5 minutes max idle time
                    reconnect_timeout=30.0,  # Reconnection timeout
                )
                logger.info('Database connection pool initialized successfully')
            except Exception as e:
                logger.error(f'Failed to initialize connection pool: {str(e)}')
                self._pool = None
            finally:
                self._initializing = False

        return self._pool

    def get_connection(self):
        """Get a connection from the pool."""
        pool = self.init_pool()
        if pool:
            try:
                return pool.getconn(timeout=10.0)  # Reduced timeout
            except Exception as e:
                logger.error(f'Failed to get connection from pool: {str(e)}')
                return None
        return None

    @contextmanager
    def get_connection_context(self):
        """Get a connection from the pool as a context manager."""
        conn = None
        try:
            conn = self.get_connection()
            if not conn:
                raise ConnectionError('Failed to get database connection from pool')
            yield conn
        except Exception:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise
        finally:
            if conn:
                self.release_connection(conn)

    def release_connection(self, conn):
        """Return a connection to the pool."""
        if self._pool and conn:
            try:
                self._pool.putconn(conn)
            except Exception as e:
                logger.error(f'Failed to release connection: {str(e)}')

    def close_pool(self):
        """Close the connection pool."""
        if self._pool:
            self._pool.close()
            self._pool = None


db_pool = DBConnectionPool()
