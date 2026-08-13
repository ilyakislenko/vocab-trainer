import json
import re

import httpx

from vocab_api.application.errors import LlmUnavailable
from vocab_api.application.ports.llm import LlmProvider
from vocab_api.domain.practice.feedback import Feedback, Verdict

_CHECK_SYSTEM = (
    "You are an English tutor. The learner is practising a target word. "
    "Judge whether their sentence uses the word correctly and naturally. "
    "Reply with ONLY a JSON object with keys: "
    '"verdict" ("ok" or "needs_work"), "feedback" (one short sentence), '
    '"corrected" (a corrected sentence, or null if none needed), '
    '"example" (a natural example sentence using the word).'
)
_EXAMPLE_SYSTEM = (
    "You are an English tutor. Reply with ONLY one short, natural example "
    "sentence that uses the given word. No preamble, no quotes."
)


class OpenAiCompatibleProvider(LlmProvider):
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._client = client

    async def _chat(self, system: str, user: str) -> str:
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        client = self._client or httpx.AsyncClient(timeout=30.0)
        try:
            try:
                response = await client.post(
                    f"{self._base_url}/chat/completions", json=payload, headers=headers
                )
                response.raise_for_status()
                data = response.json()
                return str(data["choices"][0]["message"]["content"])
            except httpx.HTTPError as exc:
                raise LlmUnavailable("The language model is unavailable.") from exc
        finally:
            if self._client is None:
                await client.aclose()

    async def check_sentence(self, word: str, sentence: str) -> Feedback:
        raw = await self._chat(_CHECK_SYSTEM, f"Word: {word}\nSentence: {sentence}")
        return _parse_feedback(raw)

    async def suggest_example(self, word: str) -> str:
        return (await self._chat(_EXAMPLE_SYSTEM, f"Word: {word}")).strip()


def _parse_feedback(raw: str) -> Feedback:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match is not None:
        try:
            data = json.loads(match.group(0))
            verdict = Verdict.OK if str(data.get("verdict")) == "ok" else Verdict.NEEDS_WORK
            return Feedback(
                verdict=verdict,
                feedback=str(data.get("feedback", "")).strip() or "No feedback.",
                corrected=_opt(data.get("corrected")),
                example=_opt(data.get("example")),
            )
        except (ValueError, TypeError):
            pass
    return Feedback(verdict=Verdict.NEEDS_WORK, feedback=raw.strip() or "No feedback.")


def _opt(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
