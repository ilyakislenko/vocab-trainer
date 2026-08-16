from datetime import datetime

from fsrs import Card as FsrsCard
from fsrs import Rating as FsrsRating
from fsrs import Scheduler as _FsrsScheduler

from vocab_api.application.ports.scheduler import Scheduler
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating


class PyFsrsScheduler(Scheduler):
    def __init__(self) -> None:
        self._scheduler = _FsrsScheduler(enable_fuzzing=False)

    def review(self, state: FsrsState, rating: Rating, now: datetime) -> FsrsState:
        card = FsrsCard.from_dict(self._to_dict(state))
        updated, _log = self._scheduler.review_card(
            card=card, rating=FsrsRating(rating.value), review_datetime=now
        )
        return self._from_dict(updated.to_dict())

    @staticmethod
    def _to_dict(state: FsrsState) -> dict[str, object]:
        # py-fsrs has no New(0) state: an unreviewed card is Learning(1)/step 0.
        fsrs_state = state.state or 1
        return {
            "card_id": 1,
            "state": fsrs_state,
            "step": state.step,
            "stability": state.stability,
            "difficulty": state.difficulty,
            "due": state.due.isoformat(),
            "last_review": state.last_review.isoformat() if state.last_review else None,
        }

    @staticmethod
    def _from_dict(data: dict[str, object]) -> FsrsState:
        last = data["last_review"]
        return FsrsState(
            due=datetime.fromisoformat(str(data["due"])),
            state=int(data["state"]),  # type: ignore[call-overload]  # CardDict.state is int
            step=data["step"],  # type: ignore[arg-type]  # CardDict.step is int | None; to_dict() types values loosely
            stability=data["stability"],  # type: ignore[arg-type]  # CardDict.stability is float | None
            difficulty=data["difficulty"],  # type: ignore[arg-type]  # CardDict.difficulty is float | None
            last_review=datetime.fromisoformat(str(last)) if last else None,
        )
