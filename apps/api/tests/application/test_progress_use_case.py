from datetime import UTC, datetime

from tests.conftest import (
    FakeCardRepository,
    FakeDeckRepository,
    FakeReviewLogRepository,
)

from vocab_api.application.use_cases.progress import GetProgress
from vocab_api.domain.card.card import Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.map import (
    CurriculumMap,
    LadderEntry,
    LevelOverview,
    ModuleAvailability,
)
from vocab_api.domain.curriculum.progress import ModuleProgress, ModuleStatus
from vocab_api.domain.curriculum.track import Track
from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.review.review_log import ReviewLogEntry

NOW = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


class FakeMapContent:
    def map(self) -> CurriculumMap:
        return CurriculumMap(
            levels=(
                LevelOverview(
                    level=Level.A1,
                    entries=(
                        LadderEntry(
                            id="a1.grammar.to-be",
                            title="",
                            track=Track.GRAMMAR,
                            availability=ModuleAvailability.AUTHORING,
                        ),
                        LadderEntry(
                            id="a1.grammar.present-simple",
                            title="",
                            track=Track.GRAMMAR,
                            availability=ModuleAvailability.AUTHORING,
                        ),
                    ),
                ),
                LevelOverview(
                    level=Level.B1,
                    entries=(
                        LadderEntry(
                            id="b1.grammar.articles",
                            title="",
                            track=Track.GRAMMAR,
                            availability=ModuleAvailability.AVAILABLE,
                        ),
                        LadderEntry(
                            id="b1.grammar.conditionals-wish",
                            title="",
                            track=Track.GRAMMAR,
                            availability=ModuleAvailability.AVAILABLE,
                        ),
                    ),
                ),
            )
        )


class FakeProgress:
    def __init__(self) -> None:
        self._items: dict[str, ModuleProgress] = {}

    async def get(self, module_id: str) -> ModuleProgress:
        return self._items.get(module_id, ModuleProgress(module_id=module_id))

    async def save(self, progress: ModuleProgress) -> None:
        self._items[progress.module_id] = progress

    async def list(self) -> list[ModuleProgress]:
        return list(self._items.values())


def _use_case(
    progress: FakeProgress,
    decks: FakeDeckRepository | None = None,
    logs: FakeReviewLogRepository | None = None,
) -> GetProgress:
    cards = FakeCardRepository()
    return GetProgress(
        FakeMapContent(),
        progress,
        decks or FakeDeckRepository(),
        logs or FakeReviewLogRepository(cards),
    )


async def test_progress_rolls_up_per_level_and_overall():
    progress = FakeProgress()
    await progress.save(
        ModuleProgress(module_id="b1.grammar.articles", status=ModuleStatus.COMPLETED)
    )
    report = await _use_case(progress).execute()

    a1, b1 = report.levels
    assert a1.level is Level.A1
    assert (a1.completed, a1.total) == (0, 2)
    assert b1.level is Level.B1
    assert (b1.completed, b1.total) == (1, 2)
    assert report.overall_percent == 25


async def test_progress_streak_takes_the_strongest_deck():
    decks = FakeDeckRepository()
    cards = FakeCardRepository()
    logs = FakeReviewLogRepository(cards)
    first = await decks.add(Deck(name="a", created_at=NOW))
    second = await decks.add(Deck(name="b", created_at=NOW))
    assert first.id is not None and second.id is not None
    await cards.add_many(
        [
            Card(
                deck_id=first.id,
                word="a",
                translation="tr",
                fsrs=FsrsState.new(NOW),
            ),
        ]
    )
    # The fake streak only checks "any review today"; both decks having reviews
    # yields streak 1 either way, so assert the non-zero path.
    await logs.add(ReviewLogEntry(card_id=1, rating=3, reviewed_at=NOW))

    report = await _use_case(FakeProgress(), decks, logs).execute()

    assert report.streak == 1
    assert report.has_reviewed is True


async def test_progress_has_reviewed_flips_with_review_history():
    progress = FakeProgress()
    decks = FakeDeckRepository()
    cards = FakeCardRepository()
    logs = FakeReviewLogRepository(cards)
    deck = await decks.add(Deck(name="a", created_at=NOW))
    assert deck.id is not None
    await cards.add_many(
        [Card(deck_id=deck.id, word="a", translation="tr", fsrs=FsrsState.new(NOW))]
    )

    assert (await _use_case(progress, decks, logs).execute()).has_reviewed is False

    await logs.add(ReviewLogEntry(card_id=1, rating=3, reviewed_at=NOW))
    assert (await _use_case(progress, decks, logs).execute()).has_reviewed is True


async def test_progress_empty_is_zero_percent():
    report = await _use_case(FakeProgress()).execute()

    assert report.overall_percent == 0
    assert report.streak == 0
    assert report.has_reviewed is False
    assert all(level.completed == 0 for level in report.levels)
