import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql+asyncpg://logiswarm:logiswarm@localhost:5432/logiswarm")


engine = create_async_engine(_database_url(), future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session for request-scoped DB operations."""
    async with SessionLocal() as session:
        yield session
