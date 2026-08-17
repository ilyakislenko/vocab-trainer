from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import CurriculumSkillItemOut

router = APIRouter(prefix="/session", tags=["session"])


@router.get("/focus", response_model=list[CurriculumSkillItemOut])
async def focus(
    limit: int = 3, c: Container = Depends(get_container)
) -> list[CurriculumSkillItemOut]:
    leeches = await c.get_focus_leeches.execute(limit)
    return [
        CurriculumSkillItemOut(
            id=item.id or 0,
            skill=item.skill,
            module_id=item.module_id,
            source_item_id=item.source_item_id,
            is_leech=item.is_leech,
        )
        for item in leeches
    ]