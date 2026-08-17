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
        # place when an older database lacks columns added after the first release.
        await self._ensure_card_columns()

    async def _ensure_card_columns(self) -> None:
        async with self._engine.begin() as conn:
            columns = await conn.exec_driver_sql("PRAGMA table_info(cards)")
            names = {row[1] for row in columns}
            if "section" not in names:
                await conn.exec_driver_sql("ALTER TABLE cards ADD COLUMN section VARCHAR")
            if "introduced_at" not in names:
                await conn.exec_driver_sql(
                    "ALTER TABLE cards ADD COLUMN introduced_at VARCHAR"
                )

    def session(self) -> AsyncSession:
        return self._session_factory()

    async def dispose(self) -> None:
        """Close the engine's connection pool. Callers that own a Database
        (the composition root, tests) should dispose it so aiosqlite
        connections are closed instead of being garbage-collected."""
        await self._engine.dispose()
