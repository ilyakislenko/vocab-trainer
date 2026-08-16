import json
import re

import httpx

from vocab_api.application.errors import LlmUnavailable
from vocab_api.application.ports.llm import LlmProvider
from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.practice.interview import InterviewEvaluation
from vocab_api.domain.practice.word_hint import WordHint

_TRANSLATE_SYSTEM = (
    "Translate the given English sentence to Russian. "
    "Return ONLY a JSON object with keys: "
    '"full" (the full Russian translation), '
    '"words" (a list of {"word": english_word, "translation": russian}). '
    "Break down each word individually, including articles and prepositions."
)

_CHECK_SYSTEM = (
    "You are an English tutor helping a learner practise a target word. "
    "Check their sentence for spelling, grammar, and natural use of the word. "
    "Fix any typos or misspelled words (e.g. 'ever' -> 'every'). "
    "Name the ACTUAL mistake precisely — do not claim a word is 'missing' unless one "
    "truly is; a misspelled word is a spelling error, not a missing word. "
    "When the sentence has errors, your feedback MUST include: "
    "1) what exactly is wrong, 2) how to fix it, 3) a brief grammar rule (1 sentence). "
    "When the sentence is correct, keep feedback short and encouraging. "
    "Reply with ONLY a JSON object with keys: "
    '"verdict" ("ok" only if the sentence is fully correct and natural, else "needs_work"), '
    '"feedback" (detailed explanation: what is wrong, how to fix it, and a brief grammar rule; '
    "or a short praise if correct), "
    '"corrected" (the FULL corrected sentence; use null only when nothing needs changing), '
    '"example" (a natural example sentence using the target word).'
)
_EXAMPLE_SYSTEM = (
    "You are an English tutor. Reply with ONLY one short, natural example "
    "sentence that uses the given word. No preamble, no quotes."
)
_TOPIC_SYSTEM = (
    "You are an English vocabulary expert. Reply with ONLY a JSON array of "
    'single English words related to the given topic, e.g. ["word", "word"]. '
    "No explanations, no markdown, one word per element."
)
_DESCRIBE_SYSTEM = (
    "You are an English vocabulary tutor. Explain the given word to a learner. "
    "Reply with ONLY a JSON object with keys: "
    '"meaning" (one or two clear sentences in Russian: what the word means and how/when '
    "it is used, including the part of speech), "
    '"example" (one short, natural example sentence in English using the word).'
)
_DRILL_SYSTEM = (
    "You are an English conversation partner. The learner is practising a specific word. "
    "Your job is to keep a short, natural conversation that encourages them to use that word. "
    "Always mention the target word in your response so the learner sees it. "
    "Keep responses short (1-2 sentences). Ask a follow-up question that naturally invites "
    "the learner to use the target word again. "
    "Reply with ONLY a JSON object with keys: "
    '"response" (your conversational reply in English, mentioning the target word), '
    '"question" (a short follow-up question to keep them talking).'
)
_INTERVIEW_SYSTEM = (
    "You are a friendly but strict technical interviewer for a software developer job. "
    "The candidate is preparing for an interview in {language}. "
    "You are given the conversation history. The last message is the candidate's reply. "
    "Read the candidate's intent before grading: "
    "- If the reply is a request to move on (e.g. 'next', 'дальше', 'next question', 'change "
    "the question', 'random question', 'following question', 'other question') set \"advance\" "
    "to true and \"next_question\" to null. Do not grade such a request. "
    "- If the reply is a request for an explanation or the candidate says they do not know "
    "(e.g. 'explain', 'объясни', 'не знаю', 'what does X mean'), do NOT grade it as an answer. "
    "Set \"verdict\" to null, explain clearly in \"feedback\" in Russian, and set "
    "\"next_question\" to a re-asked, simpler version of the current question in {language} "
    "so the candidate can try again. Set \"advance\" to false. "
    "- Otherwise the candidate gave a real answer: evaluate its grammar, clarity, and whether "
    "it answered the question. Set \"verdict\" to \"ok\" or \"needs_work\", give feedback in "
    "Russian, and continue the interview with a short follow-up \"next_question\" in "
    "{language}, unless the discussion is exhausted, in which case set \"advance\" to true. "
    "Reply with ONLY a JSON object with keys: "
    '"verdict" ("ok", "needs_work", or null when explaining), '
    '"feedback" (one or two clear sentences in Russian — an explanation when verdict is null, '
    "otherwise what was good and what to improve), "
    '"corrected" (a natural {language} rewrite of the answer, or null), '
    '"advance" (true only when the app should supply the next question), '
    '"next_question" (a question in {language}, or null when advance is true).'
)


class OpenAiCompatibleProvider(LlmProvider):
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 60.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout = timeout
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
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
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

    async def select_topic_words(self, topic: str, limit: int) -> list[str]:
        raw = await self._chat(_TOPIC_SYSTEM, f"Topic: {topic}")
        return _parse_word_list(raw, limit)

    async def describe_word(self, word: str) -> WordHint:
        raw = await self._chat(_DESCRIBE_SYSTEM, f"Word: {word}")
        return _parse_hint(raw)

    async def drill_word(self, word: str, user_message: str) -> tuple[str, str]:
        raw = await self._chat(_DRILL_SYSTEM, f"Target word: {word}\nLearner says: {user_message}")
        return _parse_drill(raw)

    async def interview(
        self, topic: str, lang: str, messages: list[dict[str, str]]
    ) -> InterviewEvaluation:
        history = (
            "\n".join(
                f"{'Candidate' if m['role'] == 'user' else 'Interviewer'}: {m['content']}"
                for m in messages
            )
            or "(no messages yet)"
        )
        language = "Russian" if lang == "ru" else "English"
        system = _INTERVIEW_SYSTEM.format(language=language)
        raw = await self._chat(system, f"Topic: {topic}\nHistory:\n{history}")
        return _parse_interview(raw)

    async def translate_sentence(self, text: str) -> tuple[str, list[dict[str, str]]]:
        raw = await self._chat(_TRANSLATE_SYSTEM, f"Sentence: {text}")
        return _parse_translation(raw)


def _parse_feedback(raw: str) -> Feedback:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match is not None:
        try:
            data = json.loads(match.group(0))
            raw_verdict = str(data.get("verdict", "")).lower()
            ok_verdicts = {"ok", "correct", "good", "fine"}
            verdict = Verdict.OK if raw_verdict in ok_verdicts else Verdict.NEEDS_WORK
            raw_feedback = data.get("feedback")
            feedback = _opt(raw_feedback) or "No feedback."
            return Feedback(
                verdict=verdict,
                feedback=feedback,
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
    if text.lower() in ("none", "null", ""):
        return None
    return text


def _parse_word_list(raw: str, limit: int) -> list[str]:
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match is not None:
        try:
            data = json.loads(match.group(0))
        except (ValueError, TypeError):
            data = None
        if isinstance(data, list):
            words: list[str] = []
            for item in data:
                text = _opt(item)
                if text is not None:
                    words.append(text)
            return words[:limit]
    return []


def _parse_hint(raw: str) -> WordHint:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match is not None:
        try:
            data = json.loads(match.group(0))
            return WordHint(
                meaning=_opt(data.get("meaning")) or "No description available.",
                example=_opt(data.get("example")),
            )
        except (ValueError, TypeError):
            pass
    return WordHint(meaning=raw.strip() or "No description available.")


def _parse_drill(raw: str) -> tuple[str, str]:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match is not None:
        try:
            data = json.loads(match.group(0))
            response = _opt(data.get("response")) or "Good try!"
            question = _opt(data.get("question")) or "Can you try again?"
            return response, question
        except (ValueError, TypeError):
            pass
    return raw.strip() or "Good try!", ""


def _parse_interview(raw: str) -> InterviewEvaluation:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match is not None:
        try:
            data = json.loads(match.group(0))
            raw_verdict = str(data.get("verdict") or "").lower()
            ok_verdicts = {"ok", "correct", "good", "fine"}
            verdict = (
                None
                if raw_verdict in ("none", "null", "")
                else (Verdict.OK if raw_verdict in ok_verdicts else Verdict.NEEDS_WORK)
            )
            advance = str(data.get("advance") or "").strip().lower() in ("true", "1", "yes")
            return InterviewEvaluation(
                verdict=verdict,
                feedback=_opt(data.get("feedback")),
                corrected=_opt(data.get("corrected")),
                advance=advance,
                next_question=_opt(data.get("next_question")),
            )
        except (ValueError, TypeError):
            pass
    return InterviewEvaluation(
        verdict=None,
        feedback=raw.strip() or None,
        corrected=None,
        advance=False,
        next_question=None,
    )


def _parse_translation(raw: str) -> tuple[str, list[dict[str, str]]]:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match is not None:
        try:
            data = json.loads(match.group(0))
            full = _opt(data.get("full")) or ""
            words = data.get("words", [])
            if isinstance(words, list):
                cleaned = []
                for w in words:
                    if isinstance(w, dict):
                        word = _opt(w.get("word"))
                        translation = _opt(w.get("translation"))
                        if word and translation:
                            cleaned.append({"word": word, "translation": translation})
                return full, cleaned
        except (ValueError, TypeError):
            pass
    return "", []
