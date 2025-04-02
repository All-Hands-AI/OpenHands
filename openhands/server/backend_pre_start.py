import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from .db import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60  # 1 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def init(db_engine: AsyncEngine) -> None:
    try:
        logger.info('Initializing database')
        # Try to create connection to check if DB is awake
        async with db_engine.connect() as connection:
            await connection.execute(text('SELECT 1'))
            await connection.commit()
    except Exception as e:
        logger.error(e)
        raise e


async def main() -> None:
    await init(engine)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
