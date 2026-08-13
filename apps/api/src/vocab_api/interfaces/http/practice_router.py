from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import CheckSentenceIn, ExampleOut, FeedbackOut

router = APIRouter(tags=["practice"])


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
