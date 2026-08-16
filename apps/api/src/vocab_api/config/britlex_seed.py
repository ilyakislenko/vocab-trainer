import logging
from dataclasses import dataclass
from importlib.resources import files

from vocab_api.application.use_cases.decks import CreateDeck, ListDecks
from vocab_api.application.use_cases.importing import ImportWords

logger = logging.getLogger(__name__)

BRITLEX_DECK_NAME = "Britlex English"
# (section, filename) — each bundled file is one section of the PDF word list.
DATA_FILES = (
    ("main", "5000-main.md"),
    ("international", "1502-international.md"),
    ("elementary", "602-elementary.md"),
)

IT_DECK_NAME = "IT Interview"
# IT terms used to prepare for a developer job interview (frontend + backend).
IT_DATA_FILES = (("interview", "it-interview.md"),)


@dataclass(frozen=True, slots=True)
class SeedResult:
    deck_id: int | None
    imported: int
    already_present: bool


class BritlexSeeder:
    """Idempotently create the default Britlex deck with the bundled word list.

    Runs at application startup (composition root). Skips seeding when a deck
    with BRITLEX_DECK_NAME already exists so a restarted app does not duplicate
    words and a user-deleted default deck stays deleted.
    """

    def __init__(
        self,
        list_decks: ListDecks,
        create_deck: CreateDeck,
        import_words: ImportWords,
    ) -> None:
        self._list_decks = list_decks
        self._create_deck = create_deck
        self._import_words = import_words

    async def execute(self, sources: list[tuple[str, str, str]]) -> SeedResult:
        decks = await self._list_decks.execute()
        if any(deck.name == BRITLEX_DECK_NAME for deck in decks):
            return SeedResult(deck_id=None, imported=0, already_present=True)

        deck = await self._create_deck.execute(BRITLEX_DECK_NAME)
        assert deck.id is not None  # freshly persisted deck always has an id
        imported = 0
        for section, name, raw in sources:
            result = await self._import_words.execute(
                deck.id, raw, "markdown", dry_run=False, section=section
            )
            imported += len(result.imported)
            for error in result.errors:
                logger.warning("britlex seed: %s:%s %s", name, error.line, error.reason)
        logger.info("seeded deck %r with %d words", BRITLEX_DECK_NAME, imported)
        return SeedResult(deck_id=deck.id, imported=imported, already_present=False)


class ItInterviewSeeder:
    """Idempotently create the IT Interview deck with bundled tech terms.

    Runs alongside the Britlex seeder at startup (composition root). Skips when
    a deck named IT_DECK_NAME already exists.
    """

    def __init__(
        self,
        list_decks: ListDecks,
        create_deck: CreateDeck,
        import_words: ImportWords,
    ) -> None:
        self._list_decks = list_decks
        self._create_deck = create_deck
        self._import_words = import_words

    async def execute(self, sources: list[tuple[str, str, str]]) -> SeedResult:
        decks = await self._list_decks.execute()
        if any(deck.name == IT_DECK_NAME for deck in decks):
            return SeedResult(deck_id=None, imported=0, already_present=True)

        deck = await self._create_deck.execute(IT_DECK_NAME)
        assert deck.id is not None  # freshly persisted deck always has an id
        imported = 0
        for section, name, raw in sources:
            result = await self._import_words.execute(
                deck.id, raw, "markdown", dry_run=False, section=section
            )
            imported += len(result.imported)
            for error in result.errors:
                logger.warning("it seed: %s:%s %s", name, error.line, error.reason)
        logger.info("seeded deck %r with %d words", IT_DECK_NAME, imported)
        return SeedResult(deck_id=deck.id, imported=imported, already_present=False)


def load_britlex_sources() -> list[tuple[str, str, str]]:
    package = files("vocab_api.seed").joinpath("data")
    return [
        (section, name, (package / name).read_text(encoding="utf-8"))
        for section, name in DATA_FILES
    ]


def load_it_sources() -> list[tuple[str, str, str]]:
    package = files("vocab_api.seed").joinpath("data")
    return [
        (section, name, (package / name).read_text(encoding="utf-8"))
        for section, name in IT_DATA_FILES
    ]
