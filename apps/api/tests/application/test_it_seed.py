from tests.conftest import FakeCardRepository, FakeDeckRepository, FixedClock

from vocab_api.application.use_cases.decks import CreateDeck, ListDecks
from vocab_api.application.use_cases.importing import ImportWords
from vocab_api.config.britlex_seed import IT_DECK_NAME, ItInterviewSeeder

SOURCES = [
    (
        "interview",
        "it.md",
        "useState | | стейт | useState lets a component hold data.\n"
        "props | | свойства | Props are read-only inputs.",
    ),
]


async def _seeder():
    deck_repo = FakeDeckRepository()
    card_repo = FakeCardRepository()
    clock = FixedClock()
    return (
        ItInterviewSeeder(
            ListDecks(deck_repo),
            CreateDeck(deck_repo, clock),
            ImportWords(deck_repo, card_repo, clock),
        ),
        deck_repo,
        card_repo,
    )


async def test_it_seed_creates_deck_and_imports_terms():
    seeder, deck_repo, _ = await _seeder()
    result = await seeder.execute(SOURCES)
    assert result.already_present is False
    assert result.imported == 2
    assert result.deck_id == 1
    decks = await ListDecks(deck_repo).execute()
    assert [d.name for d in decks] == [IT_DECK_NAME]


async def test_it_seed_stores_example_notes():
    seeder, _, card_repo = await _seeder()
    await seeder.execute(SOURCES)
    cards = await card_repo.list_all(1, 100, 0, None)
    notes = {c.word: c.notes for c in cards}
    assert notes == {
        "useState": "useState lets a component hold data.",
        "props": "Props are read-only inputs.",
    }


async def test_it_seed_tags_section():
    seeder, _, card_repo = await _seeder()
    await seeder.execute(SOURCES)
    cards = await card_repo.list_all(1, 100, 0, None)
    assert {c.section for c in cards} == {"interview"}


async def test_it_seed_is_idempotent():
    seeder, _, _ = await _seeder()
    first = await seeder.execute(SOURCES)
    second = await seeder.execute(SOURCES)
    assert first.imported == 2
    assert second.already_present is True
    assert second.imported == 0


async def test_bundled_it_data_parses_with_notes():
    from vocab_api.application.importing.parser import parse_words
    from vocab_api.config.britlex_seed import load_it_sources

    total = 0
    for _section, name, raw in load_it_sources():
        rows, errors = parse_words(raw, "markdown")
        assert errors == [], f"{name} has parse errors: {errors}"
        for row in rows:
            assert row.notes, f"{name}: {row.word} missing example"
        total += len(rows)
    assert total >= 50
