from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker, AsyncSession
import asyncio
from atuguigu.conf.config import settings

engine: AsyncEngine | None = None
async_session: async_sessionmaker[AsyncSession] | None = None


def init_db_engine():
    global engine, async_session
    engine = create_async_engine(
        settings.database_url,
        echo=True
    )

    async_session = async_sessionmaker(
        engine,
        expire_on_commit=False
    )


async def close_db_engine():
    if engine:
        await engine.dispose()


async def main():
    init_db_engine()
    async with async_session() as session:
        result = await session.execute(text("select 1"))
        print(result.fetchall())
    await close_db_engine()


if __name__ == '__main__':
    asyncio.run(main())
