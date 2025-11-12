from contextlib import asynccontextmanager
from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Fintech(Base):
    __tablename__ = "fintech"
    id: Mapped[int] = mapped_column(primary_key=True)
    api_key: Mapped[str] = mapped_column(String(30), index=True)
    name: Mapped[str] = mapped_column(String(30))
    email: Mapped[str]
    template: Mapped[str]

    def __repr__(self) -> str:
        return f"Fintech(id={self.id!r}, name={self.name!r})"


@lru_cache(1)
def _get_async_sessionmaker() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///./signet.db")
    # create_all must be run in async context later using `init_db`
    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session_maker = _get_async_sessionmaker()
    async with session_maker() as session:
        yield session


async def init_db() -> None:
    async_engine = _get_async_sessionmaker().bind
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
