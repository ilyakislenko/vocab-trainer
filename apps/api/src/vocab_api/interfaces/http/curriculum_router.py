from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.progress import ModuleStatus
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
    CurriculumQuizGradeIn,
    CurriculumQuizGradeOut,
    CurriculumQuizItemOut,
    CurriculumQuizItemResultOut,
    CurriculumQuizOut,
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
    profile = await c.learner_profile.get()
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
        placement_level=(
            profile.placement_level.value if profile.placement_level is not None else None
        ),
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
            CurriculumReferenceOut(book=ref.book, locator=ref.locator) for ref in module.references
        ],
        has_quiz=c.get_module.has_quiz(module_id),
        estimated_minutes=module.estimated_minutes,
        quiz_best_score=progress.quiz_best_score,
        vocab=list(module.vocab),
        interview_topic=module.interview_topic,
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
                CurriculumReferenceOut(book=ref[0], locator=ref[1]) for ref in lesson.references
            ],
            vocab=list(lesson.vocab),
            interview_topic=lesson.interview_topic,
        ),
    )


@router.post("/lessons/{module_id}/read", response_model=CurriculumModuleProgressOut)
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


@router.get("/modules/{module_id}/quiz", response_model=CurriculumQuizOut)
async def module_quiz(module_id: str, c: Container = Depends(get_container)) -> CurriculumQuizOut:
    quiz, progress = await c.get_module_quiz.execute(module_id)
    return CurriculumQuizOut(
        module_id=quiz.module_id,
        status=progress.status.value,
        items=[
            CurriculumQuizItemOut(
                id=item.id,
                type=item.type.value,
                skill=item.skill,
                prompt=item.prompt,
                options=list(item.options) if item.options is not None else None,
                tokens=list(item.tokens) if item.tokens is not None else None,
            )
            for item in quiz.items
        ],
    )


@router.post("/quiz/grade", response_model=CurriculumQuizGradeOut)
async def grade_quiz(
    body: CurriculumQuizGradeIn, c: Container = Depends(get_container)
) -> CurriculumQuizGradeOut:
    outcome = await c.grade_quiz.execute(
        body.module_id,
        [(a.item_id, a.given) for a in body.answers],
    )
    return CurriculumQuizGradeOut(
        module_id=outcome.module_id,
        score=outcome.score,
        status=outcome.status.value,
        completed=outcome.status is ModuleStatus.COMPLETED,
        next_module_id=outcome.next_module_id,
        items=[
            CurriculumQuizItemResultOut(
                item_id=item.item_id,
                skill=item.skill,
                correct=item.correct,
                explanation=item.explanation,
                prompt=item.prompt,
                needs_llm=item.needs_llm,
            )
            for item in outcome.items
        ],
    )
