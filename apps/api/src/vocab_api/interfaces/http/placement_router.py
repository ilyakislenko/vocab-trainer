from fastapi import APIRouter, Depends

from vocab_api.application.use_cases.placement import PlacementAnswer
from vocab_api.config.container import Container
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import (
    PlacementGradeIn,
    PlacementGradeOut,
    PlacementItemOut,
    PlacementItemResultOut,
    PlacementOut,
)

router = APIRouter(prefix="/placement", tags=["placement"])


@router.get("", response_model=PlacementOut)
async def placement(c: Container = Depends(get_container)) -> PlacementOut:
    placement = await c.get_placement.execute()
    return PlacementOut(
        items=[
            PlacementItemOut(
                id=item.id,
                level=item.level.value,
                skill=item.skill,
                type=item.type.value,
                prompt=item.prompt,
                options=list(item.options) if item.options is not None else None,
            )
            for item in placement.items
        ],
    )


@router.post("/grade", response_model=PlacementGradeOut)
async def grade_placement(
    body: PlacementGradeIn, c: Container = Depends(get_container)
) -> PlacementGradeOut:
    outcome = await c.grade_placement.execute(
        [PlacementAnswer(item_id=a.item_id, given=a.given) for a in body.answers]
    )
    return PlacementGradeOut(
        level=outcome.level.value,
        current_module_id=outcome.current_module_id,
        results=[
            PlacementItemResultOut(
                item_id=r.item_id,
                level=r.level.value,
                skill=r.skill,
                prompt=r.prompt,
                given=r.given,
                correct=r.correct,
                correct_answer=r.correct_answer,
                explanation=r.explanation,
            )
            for r in outcome.results
        ],
    )
