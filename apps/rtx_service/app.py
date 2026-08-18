"""rtx GOP inference service (FastAPI) — full phoneme scoring over the LAN.

Run with uvicorn's factory mode so the model loads once at boot:
    uvicorn app:create_app --factory --host 0.0.0.0 --port 8900
"""

import asyncio
import os

from fastapi import FastAPI, File, Form, HTTPException

from gop import DEFAULT_MODEL, GopScorer


def create_app(scorer: GopScorer | None = None) -> FastAPI:
    model = scorer or GopScorer(
        model_name=os.environ.get("RTX_GOP_MODEL", DEFAULT_MODEL),
        device=os.environ.get("RTX_GOP_DEVICE", "cuda"),
    )
    app = FastAPI(title="rtx GOP inference service")

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok"}

    @app.post("/gop")
    async def gop(
        audio: bytes = File(...),
        target: str = Form(...),
        accent: str = Form("en-US"),
    ) -> dict:
        if not audio:
            raise HTTPException(status_code=422, detail="empty audio")
        target = target.strip()
        if not target:
            raise HTTPException(status_code=422, detail="empty target")
        try:
            return await asyncio.to_thread(model.score, audio, target)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return app