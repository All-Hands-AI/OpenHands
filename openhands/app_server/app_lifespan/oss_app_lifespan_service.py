from __future__ import annotations

from sqlmodel import SQLModel

from openhands.app_server.app_lifespan.app_lifespan_service import AppLifespanService


class OssAppLifespanService(AppLifespanService):

    async def __aenter__(self):
        # Internal imports to guard against circular dependencies
        from openhands.app_server.config import db_service

        with db_service().get_db_engine().begin() as conn:
            await conn.run(SQLModel.metadata.create_all)

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass
        #from openhands.app_server.config import db_service
        #with db_service().get_db_engine().begin() as conn:
            # TODO: Really don't let this get into SAAS!
            #await conn.run_sync(SQLModel.metadata.drop_all)
