from fastapi import APIRouter, Depends, File, Form, UploadFile

from vocab_api.config.container import Container
from vocab_api.domain.pronunciation.assessment import PronunciationAssessment
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import (
    PhonemeScoreOut,
    PronunciationAssessmentOut,
    WordScoreOut,
)

router = APIRouter(tags=["pronounce"])


def _assessment_out(assessment: PronunciationAssessment) -> PronunciationAssessmentOut:
    return PronunciationAssessmentOut(
        overall=assessment.overall,
        words=[
            WordScoreOut(
                word=word.word,
                score=word.score,
                phonemes=[
                    PhonemeScoreOut(
                        phoneme=phoneme.phoneme,
                        score=phoneme.score,
                        verdict=phoneme.verdict.value,
                    )
                    for phoneme in word.phonemes
                ],
            )
            for word in assessment.words
        ],
        transcript=assessment.transcript,
        scored_phonemes=assessment.scored_phonemes,
    )


@router.post("/pronounce/score", response_model=PronunciationAssessmentOut)
async def score_pronunciation(
    audio: UploadFile = File(...),
    target: str = Form(...),
    accent: str = Form("en-US"),
    c: Container = Depends(get_container),
) -> PronunciationAssessmentOut:
    data = await audio.read()
    assessment = await c.score_pronunciation.execute(data, target, accent)
    return _assessment_out(assessment)
