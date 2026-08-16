from tests.conftest import FakeCardRepository, FakeDeckRepository, FixedClock

from vocab_api.application.use_cases.decks import CreateDeck, ListDecks
from vocab_api.application.use_cases.importing import ImportWords
from vocab_api.config.britlex_seed import BRITLEX_DECK_NAME, BritlexSeeder

SOURCES = [
    ("main", "a.md", "run | rʌn | бежать\njump | dʒʌmp | прыгать"),
    ("international", "b.md", "cat | kæt | кот"),
]


async def test_seed_creates_deck_and_imports_all_rows():
    deck_repo = FakeDeckRepository()
    card_repo = FakeCardRepository()
    clock = FixedClock()
    seeder = BritlexSeeder(
        ListDecks(deck_repo),
        CreateDeck(deck_repo, clock),
        ImportWords(deck_repo, card_repo, clock),
    )
    result = await seeder.execute(SOURCES)
    assert result.already_present is False
    assert result.imported == 3
    assert result.deck_id == 1
    decks = await ListDecks(deck_repo).execute()
    assert [d.name for d in decks] == [BRITLEX_DECK_NAME]


async def test_seed_tags_each_row_with_its_section():
    deck_repo = FakeDeckRepository()
    card_repo = FakeCardRepository()
    clock = FixedClock()
    seeder = BritlexSeeder(
        ListDecks(deck_repo),
        CreateDeck(deck_repo, clock),
        ImportWords(deck_repo, card_repo, clock),
    )
    await seeder.execute(SOURCES)
    cards = await card_repo.list_all(1, 100, 0, None)
    assert {c.word: c.section for c in cards} == {
        "run": "main",
        "jump": "main",
        "cat": "international",
    }


async def test_seed_is_idempotent():
    deck_repo = FakeDeckRepository()
    card_repo = FakeCardRepository()
    clock = FixedClock()
    seeder = BritlexSeeder(
        ListDecks(deck_repo),
        CreateDeck(deck_repo, clock),
        ImportWords(deck_repo, card_repo, clock),
    )
    first = await seeder.execute(SOURCES)
    second = await seeder.execute(SOURCES)
    assert first.imported == 3
    assert second.already_present is True
    assert second.imported == 0
    assert second.deck_id is None


async def test_bundled_britlex_data_parses_without_errors():
    from vocab_api.application.importing.parser import parse_words
    from vocab_api.config.britlex_seed import load_britlex_sources

    total = 0
    for _section, name, raw in load_britlex_sources():
        rows, errors = parse_words(raw, "markdown")
        assert errors == [], f"{name} has parse errors: {errors}"
        total += len(rows)
    assert total == 9793
