from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.domain.card.card import Card
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import (
    CardOut,
    CreateDeckIn,
    DeckOut,
    ImportIn,
    ImportOut,
    RowErrorOut,
)

router = APIRouter(tags=["decks"])


def _card_out(card: Card) -> CardOut:
    return CardOut(
        id=card.id, word=card.word, translation=card.translation,
        transcription=card.transcription,
    )


@router.post("/decks", response_model=DeckOut)
async def create_deck(body: CreateDeckIn, c: Container = Depends(get_container)) -> DeckOut:
    deck = await c.create_deck.execute(body.name)
    assert deck.id is not None
    return DeckOut(id=deck.id, name=deck.name)


@router.get("/decks", response_model=list[DeckOut])
async def list_decks(c: Container = Depends(get_container)) -> list[DeckOut]:
    decks = await c.list_decks.execute()
    out: list[DeckOut] = []
    for d in decks:
        assert d.id is not None  # persisted decks always have an id
        out.append(DeckOut(id=d.id, name=d.name))
    return out


@router.post("/decks/{deck_id}/import", response_model=ImportOut)
async def import_words(
    deck_id: int, body: ImportIn, c: Container = Depends(get_container)
) -> ImportOut:
    result = await c.import_words.execute(deck_id, body.raw, body.format, body.dry_run)
    return ImportOut(
        committed=result.committed,
        imported=[_card_out(card) for card in result.imported],
        errors=[RowErrorOut(line=e.line, reason=e.reason) for e in result.errors],
    )
