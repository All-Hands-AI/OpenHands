import asyncio
import logging

from .db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init() -> None:
    await init_db()


async def main() -> None:
    logger.info('Creating initial data')
    await init()
    logger.info('Initial data created')


if __name__ == '__main__':
    asyncio.run(main())
