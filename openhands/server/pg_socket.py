import asyncio
import json
import os
import pickle

import asyncpg
from asyncpg.exceptions import PostgresError
from socketio.async_pubsub_manager import AsyncPubSubManager

from openhands.core.logger import openhands_logger as logger

DB_HOST = os.environ.get('DB_HOST')  # for non-GCP environments
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS', '').strip()
DB_NAME = os.environ.get('DB_NAME')

GCP_DB_INSTANCE = os.environ.get('GCP_DB_INSTANCE')  # for GCP environments
GCP_PROJECT = os.environ.get('GCP_PROJECT')
GCP_REGION = os.environ.get('GCP_REGION')


class AsyncPostgresManager(AsyncPubSubManager):
    """PostgreSQL based client manager for asyncio servers.

    Uses PostgreSQL's LISTEN/NOTIFY functionality for event sharing across processes.

    Usage:
        url = 'postgresql://user:pass@hostname:port/dbname'
        server = socketio.AsyncServer(
            client_manager=socketio.AsyncPostgresManager(url))
    """

    name = 'asyncpg'

    def __init__(
        self,
        channel='socketio',
        write_only=False,
    ):
        logger.info('Initializing PostgresManager')
        self.conn = None
        super().__init__(channel=channel, write_only=write_only, logger=logger)

    async def setup(self):
        await self._create_database_if_not_exists()

    async def _get_gcp_connection(self, db_name=DB_NAME):
        instance_string = f'{GCP_PROJECT}:{GCP_REGION}:{GCP_DB_INSTANCE}'
        logger.info(f'Connecting to GCP instance: {instance_string}')

        async def get_async_conn():
            conn = await self.connector.connect_async(
                instance_connection_string=instance_string,
                driver='asyncpg',
                user=DB_USER,
                password=DB_PASS,
                db=db_name,
            )
            return conn

        return await get_async_conn()

    async def _get_postgres_connection(self, db_name=DB_NAME):
        logger.info(f'Connecting to Postgres: {DB_HOST}')
        return await asyncpg.connect(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            database=db_name,
        )

    async def _postgres_connect(self):
        if self.conn:
            try:
                await self.conn.close()
            except PostgresError:
                pass

        if GCP_DB_INSTANCE:
            self.conn = await self._get_gcp_connection()
        else:
            self.conn = await self._get_postgres_connection()

    async def _publish(self, data):
        print('PUBLISH')
        retry = True
        if not self.conn:
            raise RuntimeError('Postgres connection not established')
        while True:
            try:
                if not retry:
                    await self._postgres_connect()
                # Convert data to JSON string since NOTIFY payload must be str
                await self.conn.execute(
                    'SELECT pg_notify($1, $2)',
                    self.channel,
                    json.dumps({'data': pickle.dumps(data).decode('latin1')}),
                )
                return
            except PostgresError:
                if retry:
                    self._get_logger().error(
                        'Cannot publish to postgres... ' 'retrying'
                    )
                    retry = False
                else:
                    self._get_logger().error(
                        'Cannot publish to postgres... ' 'giving up'
                    )
                    break

    async def _postgres_listen_with_retries(self):
        retry_sleep = 1
        connect = False
        while True:
            try:
                if connect:
                    await self._postgres_connect()
                    if not self.conn:
                        raise RuntimeError('Postgres connection not established')
                    await self.conn.add_listener(self.channel, self._on_notification)
                    retry_sleep = 1
                # Keep connection alive
                while True:
                    await asyncio.sleep(1)
            except PostgresError:
                self._get_logger().error(
                    'Cannot receive from postgres... ' f'retrying in {retry_sleep} secs'
                )
                connect = True
                await asyncio.sleep(retry_sleep)
                retry_sleep *= 2
                if retry_sleep > 60:
                    retry_sleep = 60

    async def _listen(self):
        print('LISTEN')
        await self._postgres_connect()
        if not self.conn:
            raise RuntimeError('Postgres connection not established')
        await self.conn.add_listener(self.channel, self._on_notification)
        self._listen_queue: asyncio.Queue = asyncio.Queue()

        # Start background listener
        self._listen_task = asyncio.create_task(self._postgres_listen_with_retries())

        try:
            while True:
                data = await self._listen_queue.get()
                yield data
        finally:
            if self.conn:
                await self.conn.remove_listener(self.channel, self._on_notification)
                self._listen_task.cancel()
                try:
                    await self._listen_task
                except asyncio.CancelledError:
                    pass

    async def _on_notification(self, connection, pid, channel, payload):
        """Handle incoming notifications from Postgres."""
        print('ON NOTIF')
        try:
            data = json.loads(payload)
            decoded_data = pickle.loads(data['data'].encode('latin1'))
            await self._listen_queue.put(decoded_data)
        except (json.JSONDecodeError, KeyError, pickle.UnpicklingError) as e:
            self._get_logger().error(f'Error processing notification: {e}')

    async def _create_database_if_not_exists(self):
        if GCP_DB_INSTANCE:
            sys_conn = await self._get_gcp_connection('postgres')
        else:
            sys_conn = await self._get_postgres_connection('postgres')

        try:
            # Check if database exists
            exists = await sys_conn.fetchval(
                'SELECT 1 FROM pg_database WHERE datname = $1',
                DB_NAME,
            )
            if not exists:
                # Create database if it doesn't exist
                await sys_conn.execute(f'CREATE DATABASE "{DB_NAME}"')
        except Exception as e:
            raise e
        finally:
            await sys_conn.close()
