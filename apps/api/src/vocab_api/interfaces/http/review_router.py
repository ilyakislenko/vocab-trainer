from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.domain.card.rating import Rating
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import (
    CardOut,
    CurriculumSkillItemOut,
    CurriculumSkillReviewOut,
    ReviewIn,
    SkillReviewIn,
)

router = APIRouter(tags=["review"])


@router.get("/review/queue", response_model=list[CardOut])
async def review_queue(
    deck_id: int, limit: int = 20, c: Container = Depends(get_container)
) -> list[CardOut]:
    cards = await c.get_review_queue.execute(deck_id, limit)
    return [
        CardOut(id=card.id, word=card.word, translation=card.translation,
                transcription=card.transcription, section=card.section)
        for card in cards
    ]


@router.post("/review", response_model=CardOut)
async def record_review(body: ReviewIn, c: Container = Depends(get_container)) -> CardOut:
    card = await c.record_review.execute(body.card_id, Rating(body.rating))
    return CardOut(id=card.id, word=card.word, translation=card.translation,
                   transcription=card.transcription, section=card.section)


@router.get("/review/skills/queue", response_model=list[CurriculumSkillReviewOut])
async def skill_review_queue(
    limit: int = 20, c: Container = Depends(get_container)
) -> list[CurriculumSkillReviewOut]:
    items = await c.get_skill_review_queue.execute(limit)
    return [
        CurriculumSkillReviewOut(
            id=item.id,
            skill=item.skill,
            module_id=item.module_id,
            source_item_id=item.source_item_id,
            is_leech=item.is_leech,
            type=item.type.value,
            prompt=item.prompt,
            options=list(item.options) if item.options is not None else None,
            answers=list(item.answers),
            explanation=item.explanation,
        )
        for item in items
    ]


@router.post("/review/skills", response_model=CurriculumSkillItemOut)
async def record_skill_review(
    body: SkillReviewIn, c: Container = Depends(get_container)
) -> CurriculumSkillItemOut:
    item = await c.record_skill_review.execute(body.skill_item_id, Rating(body.rating))
    return CurriculumSkillItemOut(
        id=item.id or 0,
        skill=item.skill,
        module_id=item.module_id,
        source_item_id=item.source_item_id,
        is_leech=item.is_leech,
    )
