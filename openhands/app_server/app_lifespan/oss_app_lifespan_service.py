from __future__ import annotations

from openhands.app_server.app_lifespan.app_lifespan_service import AppLifespanService


class OssAppLifespanService(AppLifespanService):

    async def __aenter__(self):
        # Internal imports to guard against circular dependencies
        from openhands.app_server.database import create_tables

        await create_tables()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass
