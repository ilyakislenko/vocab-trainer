from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from vocab_api.infrastructure.persistence import (  # noqa: F401  # register metadata
    curriculum_tables,
    tables,
)


class Database:
    def __init__(self, url: str) -> None:
        # In-memory SQLite gives each new connection its own empty database, which
        # breaks repositories that open a session per call. StaticPool pins a single
        # shared connection so the schema and data persist across sessions.
        # All app datetimes are UTC; SQLite stores them naive-UTC, so comparisons
        # (fsrs_due <= now) stay consistent.
        connect_args: dict[str, object] = {}
        engine_kwargs: dict[str, object] = {}
        if "memory" in url:
            connect_args["check_same_thread"] = False
            engine_kwargs["poolclass"] = StaticPool
        self._engine = create_async_engine(url, connect_args=connect_args, **engine_kwargs)
        self._session_factory = async_sessionmaker(self._engine, class_=AsyncSession)

    async def init(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        # create_all never alters existing tables, so migrate the cards table in
        # place when an older database lacks the section column (added later).
        await self._ensure_section_column()

    async def _ensure_section_column(self) -> None:
        async with self._engine.begin() as conn:
            columns = await conn.exec_driver_sql("PRAGMA table_info(cards)")
            has_section = any(row[1] == "section" for row in columns)
            if not has_section:
                await conn.exec_driver_sql("ALTER TABLE cards ADD COLUMN section VARCHAR")

    def session(self) -> AsyncSession:
        return self._session_factory()
