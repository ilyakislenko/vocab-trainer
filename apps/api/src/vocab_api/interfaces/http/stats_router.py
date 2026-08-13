from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import StatsOut

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsOut)
async def stats(deck_id: int, c: Container = Depends(get_container)) -> StatsOut:
    result = await c.get_stats.execute(deck_id)
    return StatsOut(due_today=result.due_today, total_reviews=result.total_reviews)
