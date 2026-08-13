from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.domain.card.rating import Rating
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import CardOut, ReviewIn

router = APIRouter(tags=["review"])


@router.get("/review/queue", response_model=list[CardOut])
async def review_queue(
    deck_id: int, limit: int = 20, c: Container = Depends(get_container)
) -> list[CardOut]:
    cards = await c.get_review_queue.execute(deck_id, limit)
    return [
        CardOut(id=card.id, word=card.word, translation=card.translation,
                transcription=card.transcription)
        for card in cards
    ]


@router.post("/review", response_model=CardOut)
async def record_review(body: ReviewIn, c: Container = Depends(get_container)) -> CardOut:
    card = await c.record_review.execute(body.card_id, Rating(body.rating))
    return CardOut(id=card.id, word=card.word, translation=card.translation,
                   transcription=card.transcription)
