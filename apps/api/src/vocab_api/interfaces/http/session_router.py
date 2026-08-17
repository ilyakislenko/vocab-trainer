from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.today import (
    ProduceStep,
    ReadLessonStep,
    ReviewStep,
    TakeQuizStep,
    TodayStep,
)
from vocab_api.domain.curriculum.track import Track
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import CurriculumSkillItemOut, TodaySessionOut, TodayStepOut

router = APIRouter(prefix="/session", tags=["session"])


def _module_level(module_id: str) -> str:
    return Level(module_id.split(".")[0].upper()).value


def _module_track(module_id: str) -> str:
    return Track(module_id.split(".")[1]).value


def _to_out(step: TodayStep) -> TodayStepOut:
    if isinstance(step, ReviewStep):
        return TodayStepOut(
            kind=step.kind.value,
            vocab_due=step.vocab_due,
            skill_due=step.skill_due,
        )
    if isinstance(step, ReadLessonStep):
        return TodayStepOut(
            kind=step.kind.value,
            module_id=step.module_id,
            title=step.title,
            level=_module_level(step.module_id),
            track=_module_track(step.module_id),
        )
    if isinstance(step, TakeQuizStep):
        return TodayStepOut(
            kind=step.kind.value,
            module_id=step.module_id,
            title=step.title,
            level=_module_level(step.module_id),
            track=_module_track(step.module_id),
            items=step.items,
        )
    if isinstance(step, ProduceStep):
        return TodayStepOut(
            kind=step.kind.value,
            word=step.word,
            card_id=step.card_id,
            vocab_sections=list(step.vocab_sections),
            interview_topic=step.interview_topic,
        )
    # FocusStep — last branch, sequential fall-through like domain/grade().
    return TodayStepOut(
        kind=step.kind.value,
        leeches=[
            CurriculumSkillItemOut(
                id=item.id or 0,
                skill=item.skill,
                module_id=item.module_id,
                source_item_id=item.source_item_id,
                is_leech=item.is_leech,
            )
            for item in step.leeches
        ],
    )


@router.get("/today", response_model=TodaySessionOut)
async def today(c: Container = Depends(get_container)) -> TodaySessionOut:
    steps = await c.build_today_session.execute()
    return TodaySessionOut(steps=[_to_out(step) for step in steps])


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