from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import LevelProgressOut, ProgressOut

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("", response_model=ProgressOut)
async def progress(c: Container = Depends(get_container)) -> ProgressOut:
    report = await c.get_progress.execute()
    return ProgressOut(
        levels=[
            LevelProgressOut(
                level=level.level.value,
                completed=level.completed,
                total=level.total,
            )
            for level in report.levels
        ],
        overall_percent=report.overall_percent,
        streak=report.streak,
        has_reviewed=report.has_reviewed,
    )
