import asyncio
import json
import os
import pickle
from asyncio import Task
from typing import Any, Dict, Optional

import asyncpg
from asyncpg.exceptions import PostgresError
from asyncpg.pool import Pool
from google.cloud.sql.connector import Connector
from socketio.async_pubsub_manager import AsyncPubSubManager


def has_binary(obj: Any, to_json: bool = False) -> bool:
    if not obj or not isinstance(obj, (dict, list, bytes, bytearray, memoryview)):
        return False

    if isinstance(obj, (bytes, bytearray, memoryview)):
        return True

    if isinstance(obj, list):
        return any(has_binary(item) for item in obj)

    if isinstance(obj, dict):
        return any(has_binary(v) for v in obj.values())

    if hasattr(obj, 'to_json') and callable(obj.to_json) and not to_json:
        return has_binary(obj.to_json(), True)

    return False


class AsyncPostgresAdapter(AsyncPubSubManager):
    def __init__(
        self,
        channel: str = 'socketio',
        table_name: str = 'socket_io_attachments',
        payload_threshold: int = 8000,
        cleanup_interval: int = 30000,
    ):
        self.channel = channel
        super().__init__(channel=channel)
        self.table_name = table_name
        self.payload_threshold = payload_threshold
        self.cleanup_interval = cleanup_interval
        self._cleanup_timer: Optional[Task] = None
        self._client: Optional[asyncpg.Connection] = None
        self.pool: Optional[Pool] = None

        # Connection configs
        self.db_host = os.environ.get('DB_HOST')
        self.db_user = os.environ.get('DB_USER')
        self.db_pass = os.environ.get('DB_PASS', '').strip()
        self.db_name = os.environ.get('DB_NAME')

        # GCP configs
        self.gcp_instance = os.environ.get('GCP_DB_INSTANCE')
        self.gcp_project = os.environ.get('GCP_PROJECT')
        self.gcp_region = os.environ.get('GCP_REGION')

        self.connector = Connector() if self.gcp_instance else None

    async def setup(self):
        if not self.pool:
            self.pool = await self._create_pool()
            await self._create_db()
            await self._init_client()

    async def _create_pool(self) -> Pool:
        if self.gcp_instance:
            return await asyncpg.create_pool(
                lambda: self._get_gcp_connection(self.db_name)
            )
        else:
            return await asyncpg.create_pool(
                user=self.db_user,
                password=self.db_pass,
                host=self.db_host,
                database=self.db_name,
            )

    async def _get_gcp_connection(
        self, db_name: Optional[str] = None
    ) -> asyncpg.Connection:
        instance_string = f'{self.gcp_project}:{self.gcp_region}:{self.gcp_instance}'

        conn = await self.connector.connect_async(
            instance_connection_string=instance_string,
            driver='asyncpg',
            user=self.db_user,
            password=self.db_pass,
            db=db_name or self.db_name,
        )
        return conn

    async def _init_client(self) -> None:
        if not self.pool:
            raise RuntimeError('Pool not initialized')

        try:
            self._client = await self.pool.acquire()
            await self._client.execute(f'LISTEN "{self.channel}"')

            self._client.add_listener(self.channel, self._on_notification)

            if not self._cleanup_timer:
                self._schedule_cleanup()

        except PostgresError as e:
            self.logger.error(f'Error initializing client: {e}')
            await asyncio.sleep(2)
            await self._init_client()

    def _schedule_cleanup(self) -> None:
        async def cleanup() -> None:
            if not self.pool:
                return

            try:
                await self.pool.execute(
                    f"DELETE FROM {self.table_name} WHERE created_at < now() - interval '{self.cleanup_interval} milliseconds'"
                )
            except PostgresError as e:
                self.logger.error(f'Cleanup error: {e}')

            self._cleanup_timer = asyncio.create_task(cleanup())
            await asyncio.sleep(self.cleanup_interval / 1000)

        self._cleanup_timer = asyncio.create_task(cleanup())

    async def _publish_with_attachment(self, data: Dict) -> None:
        if not self.pool:
            raise RuntimeError('Pool not initialized')

        payload = pickle.dumps(data)
        result = await self.pool.fetchrow(
            f'INSERT INTO {self.table_name} (payload) VALUES ($1) RETURNING id', payload
        )
        if not result:
            raise RuntimeError('Failed to insert payload')

        notification = {
            'uid': self.uid,
            'type': data['type'],
            'attachmentId': result['id'],
        }
        await self.pool.execute(
            'SELECT pg_notify($1, $2)', self.channel, json.dumps(notification)
        )

    async def _publish(self, data: Dict) -> None:
        if not self.pool:
            raise RuntimeError('Pool not initialized')

        try:
            data['uid'] = self.uid

            if has_binary(data) or len(json.dumps(data)) > self.payload_threshold:
                await self._publish_with_attachment(data)
                return

            await self.pool.execute(
                'SELECT pg_notify($1, $2)', self.channel, json.dumps(data)
            )

        except PostgresError as e:
            self.logger.error(f'Publish error: {e}')
            raise

    async def _on_notification(self, conn, pid, channel, payload) -> None:
        if not self.pool:
            return

        try:
            data = json.loads(payload)

            if data.get('uid') == self.uid:
                return

            if 'attachmentId' in data:
                result = await self.pool.fetchrow(
                    f'SELECT payload FROM {self.table_name} WHERE id = $1',
                    data['attachmentId'],
                )
                if not result:
                    self.logger.error(f"Attachment {data['attachmentId']} not found")
                    return

                data = pickle.loads(result['payload'])

            await self._handle_message(data)

        except Exception as e:
            self.logger.error(f'Notification error: {e}')

    async def close(self) -> None:
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
        if self._client and self.pool:
            await self.pool.release(self._client)
        if self.connector:
            await self.connector.close_async()
        await super().close()

    async def _create_db(self) -> None:
        try:
            # Connect to default postgres DB first
            if self.gcp_instance:
                sys_conn = await self._get_gcp_connection('postgres')
            else:
                sys_conn = await asyncpg.connect(
                    user=self.db_user,
                    password=self.db_pass,
                    host=self.db_host,
                    database='postgres',
                )

            try:
                # Create DB if needed
                exists = await sys_conn.fetchval(
                    'SELECT 1 FROM pg_database WHERE datname = $1', self.db_name
                )
                if not exists:
                    await sys_conn.execute(f'CREATE DATABASE "{self.db_name}"')
            finally:
                await sys_conn.close()

            # Create attachments table
            if not self.pool:
                raise RuntimeError('Pool not initialized')

            await self.pool.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    payload BYTEA NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except Exception as e:
            self.logger.error(f'Database creation error: {e}')
            raise
