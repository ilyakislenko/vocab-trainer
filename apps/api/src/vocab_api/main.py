from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from vocab_api.config.container import Container
from vocab_api.config.settings import Settings
from vocab_api.interfaces.http import (
    curriculum_router,
    decks_router,
    placement_router,
    practice_router,
    progress_router,
    review_router,
    session_router,
    stats_router,
)
from vocab_api.interfaces.http.errors import install_error_handlers


def create_app(container: Container | None = None) -> FastAPI:
    resolved = container or Container(Settings())

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await resolved.init()
        yield

    app = FastAPI(title="Vocab Trainer API", lifespan=lifespan)
    app.state.container = resolved
    install_error_handlers(app)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(decks_router.router)
    app.include_router(review_router.router)
    app.include_router(stats_router.router)
    app.include_router(practice_router.router)
    app.include_router(curriculum_router.router)
    app.include_router(session_router.router)
    app.include_router(placement_router.router)
    app.include_router(progress_router.router)
    return app


app = create_app()
