"""Shared placement answer map for HTTP tests.

The placement bank (48 items) is larger than one diagnostic attempt, and the
sampled selection varies per request. Tests fetch `GET /placement` and then
answer whatever was actually sampled. The correct `given` is the option index
(string) for mcq items and the first accepted answer for cloze/transform
items — matching `domain.curriculum.quiz.grade`.
"""

import httpx

CORRECT: dict[str, str] = {
    "pl.a2.1": "1",
    "pl.a2.2": "2",
    "pl.a2.3": "0",
    "pl.a2.4": "is going to",
    "pl.a2.5": "2",
    "pl.a2.6": "0",
    "pl.a2.7": "0",
    "pl.a2.8": "0",
    "pl.a2.9": "0",
    "pl.a2.10": "are",
    "pl.a2.11": "0",
    "pl.a2.12": "0",
    "pl.b1.1": "0",
    "pl.b1.2": "2",
    "pl.b1.3": "1",
    "pl.b1.4": "was",
    "pl.b1.5": "1",
    "pl.b1.6": "1",
    "pl.b1.7": "1",
    "pl.b1.8": "0",
    "pl.b1.9": "0",
    "pl.b1.10": "should",
    "pl.b1.11": "1",
    "pl.b1.12": "0",
    "pl.b2.1": "0",
    "pl.b2.2": "1",
    "pl.b2.3": "whose",
    "pl.b2.4": "1",
    "pl.b2.5": "2",
    "pl.b2.6": "0",
    "pl.b2.7": "0",
    "pl.b2.8": "0",
    "pl.b2.9": "off",
    "pl.b2.10": "0",
    "pl.b2.11": "0",
    "pl.b2.12": "0",
    "pl.c1.1": "0",
    "pl.c1.2": "Seen",
    "pl.c1.3": "1",
    "pl.c1.4": "1",
    "pl.c1.5": "No sooner",
    "pl.c1.6": "0",
    "pl.c1.7": "had",
    "pl.c1.8": "0",
    "pl.c1.9": "0",
    "pl.c1.10": "stiff",
    "pl.c1.11": "0",
    "pl.c1.12": "0",
}


async def fetch_diagnostic(client: httpx.AsyncClient) -> list[dict]:
    resp = await client.get("/placement")
    assert resp.status_code == 200
    return resp.json()["items"]


def correct_answers(items: list[dict], *, correct: bool = True) -> list[dict[str, str]]:
    return [
        {"item_id": item["id"], "given": CORRECT[item["id"]] if correct else "bogus"}
        for item in items
    ]
