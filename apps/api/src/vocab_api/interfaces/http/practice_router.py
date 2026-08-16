from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.domain.card.card import Card
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import (
    CardOut,
    CheckSentenceIn,
    DrillIn,
    DrillOut,
    ExampleOut,
    FeedbackOut,
    InterviewIn,
    InterviewOut,
    SentenceTranslation,
    WordHintOut,
    WordTranslation,
)

router = APIRouter(tags=["practice"])


def _card_out(card: Card) -> CardOut:
    return CardOut(
        id=card.id,
        word=card.word,
        translation=card.translation,
        transcription=card.transcription,
        section=card.section,
    )


@router.post("/practice/check", response_model=FeedbackOut)
async def check_sentence(
    body: CheckSentenceIn, c: Container = Depends(get_container)
) -> FeedbackOut:
    attempt = await c.check_sentence.execute(body.card_id, body.sentence)
    fb = attempt.feedback
    return FeedbackOut(
        verdict=fb.verdict, feedback=fb.feedback, corrected=fb.corrected, example=fb.example
    )


@router.get("/practice/example", response_model=ExampleOut)
async def practice_example(card_id: int, c: Container = Depends(get_container)) -> ExampleOut:
    return ExampleOut(example=await c.suggest_example.execute(card_id))


@router.get("/practice/topic", response_model=list[CardOut])
async def practice_topic(
    deck_id: int,
    topic: str,
    limit: int = 20,
    c: Container = Depends(get_container),
) -> list[CardOut]:
    cards = await c.select_topic_words.execute(deck_id, topic, limit)
    return [_card_out(card) for card in cards]


@router.get("/practice/hint", response_model=WordHintOut)
async def practice_hint(card_id: int, c: Container = Depends(get_container)) -> WordHintOut:
    hint = await c.describe_word.execute(card_id)
    return WordHintOut(meaning=hint.meaning, example=hint.example)


@router.post("/practice/drill", response_model=DrillOut)
async def practice_drill(body: DrillIn, c: Container = Depends(get_container)) -> DrillOut:
    response, question = await c.drill_word.execute(body.card_id, body.message)
    return DrillOut(response=response, question=question)


@router.get("/practice/translate", response_model=SentenceTranslation)
async def practice_translate(
    text: str, c: Container = Depends(get_container)
) -> SentenceTranslation:
    full, words = await c.translate_sentence.execute(text)
    return SentenceTranslation(
        full=full,
        words=[WordTranslation(word=w["word"], translation=w["translation"]) for w in words],
    )


@router.post("/practice/interview", response_model=InterviewOut)
async def practice_interview(
    body: InterviewIn, c: Container = Depends(get_container)
) -> InterviewOut:
    turn = await c.conduct_interview.execute(
        body.topic,
        body.lang,
        set(body.used_question_ids),
        [{"role": m.role, "content": m.content} for m in body.messages],
        body.mode,
        body.difficulty,
    )
    return InterviewOut(
        verdict=turn.verdict,
        feedback=turn.feedback,
        corrected=turn.corrected,
        question=turn.question,
        question_id=turn.question_id,
    )
