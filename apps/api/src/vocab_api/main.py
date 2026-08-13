from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Vocab Trainer API")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
