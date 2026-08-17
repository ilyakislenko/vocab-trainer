from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from vocab_api.application.errors import LlmUnavailable
from vocab_api.domain.shared.errors import (
    CardNotFound,
    CurriculumLessonNotFound,
    CurriculumModuleNotFound,
    CurriculumQuizNotFound,
    DeckNotFound,
    DomainError,
)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DeckNotFound)
    async def _deck_not_found(_: Request, exc: DeckNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(CardNotFound)
    async def _card_not_found(_: Request, exc: CardNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(CurriculumModuleNotFound)
    async def _module_not_found(_: Request, exc: CurriculumModuleNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(CurriculumLessonNotFound)
    async def _lesson_not_found(_: Request, exc: CurriculumLessonNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(CurriculumQuizNotFound)
    async def _quiz_not_found(_: Request, exc: CurriculumQuizNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(LlmUnavailable)
    async def _llm_unavailable(_: Request, exc: LlmUnavailable) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
