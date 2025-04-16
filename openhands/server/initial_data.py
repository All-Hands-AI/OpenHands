import asyncio
import logging

from openhands.server.migrations.run_migration import run_migration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init() -> None:
    await run_migration()


async def main() -> None:
    logger.info('Creating initial data')
    await init()
    logger.info('Initial data created')


if __name__ == '__main__':
    asyncio.run(main())
