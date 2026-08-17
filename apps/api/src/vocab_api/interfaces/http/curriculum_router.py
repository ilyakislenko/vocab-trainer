from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.track import Track
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import (
    CurriculumLessonMetaOut,
    CurriculumLessonOut,
    CurriculumLevelOut,
    CurriculumMapOut,
    CurriculumModuleDetailOut,
    CurriculumModuleOut,
    CurriculumModuleProgressOut,
    CurriculumReferenceOut,
)

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


def _module_level(module_id: str) -> str:
    return Level(module_id.split(".")[0].upper()).value


def _module_track(module_id: str) -> str:
    return Track(module_id.split(".")[1]).value


@router.get("", response_model=CurriculumMapOut)
async def curriculum_map(c: Container = Depends(get_container)) -> CurriculumMapOut:
    curriculum = await c.get_curriculum_map.execute()
    recommended = await c.get_recommended_module.execute()
    return CurriculumMapOut(
        levels=[
            CurriculumLevelOut(
                level=section.level.value,
                modules=[
                    CurriculumModuleOut(
                        id=row.id,
                        title=row.title,
                        level=section.level.value,
                        track=row.track.value,
                        availability=row.availability.value,
                        status=row.status.value,
                        quiz_best_score=row.quiz_best_score,
                    )
                    for row in section.entries
                ],
            )
            for section in curriculum.levels
        ],
        recommended_module_id=recommended,
    )


@router.get("/modules/{module_id}", response_model=CurriculumModuleDetailOut)
async def module_detail(
    module_id: str, c: Container = Depends(get_container)
) -> CurriculumModuleDetailOut:
    module, progress = await c.get_module.execute(module_id)
    return CurriculumModuleDetailOut(
        id=module.id,
        title=module.title,
        level=_module_level(module.id),
        track=_module_track(module.id),
        status=progress.status.value,
        objectives=list(module.objectives),
        references=[
            CurriculumReferenceOut(book=ref.book, locator=ref.locator)
            for ref in module.references
        ],
        has_quiz=c.get_module.has_quiz(module_id),
        estimated_minutes=module.estimated_minutes,
        quiz_best_score=progress.quiz_best_score,
    )


@router.get("/lessons/{module_id}", response_model=CurriculumLessonOut)
async def lesson(module_id: str, c: Container = Depends(get_container)) -> CurriculumLessonOut:
    lesson, _ = await c.get_lesson.execute(module_id)
    return CurriculumLessonOut(
        markdown=lesson.markdown,
        meta=CurriculumLessonMetaOut(
            id=lesson.id,
            title=lesson.title,
            level=_module_level(module_id),
            track=_module_track(module_id),
            estimated_minutes=lesson.estimated_minutes,
            objectives=list(lesson.objectives),
            skills=list(lesson.skills),
            references=[
                CurriculumReferenceOut(book=ref[0], locator=ref[1])
                for ref in lesson.references
            ],
        ),
    )


@router.post(
    "/lessons/{module_id}/read", response_model=CurriculumModuleProgressOut
)
async def mark_lesson_read(
    module_id: str, c: Container = Depends(get_container)
) -> CurriculumModuleProgressOut:
    progress = await c.mark_lesson_read.execute(module_id)
    return CurriculumModuleProgressOut(
        module_id=progress.module_id,
        status=progress.status.value,
        lesson_read_at=progress.lesson_read_at,
        quiz_best_score=progress.quiz_best_score,
        completed_at=progress.completed_at,
    )