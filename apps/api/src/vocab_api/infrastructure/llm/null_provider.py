from vocab_api.application.ports.llm import LlmProvider
from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.practice.interview import InterviewEvaluation
from vocab_api.domain.practice.word_hint import WordHint


class NullProvider(LlmProvider):
    async def check_sentence(self, word: str, sentence: str) -> Feedback:
        return Feedback(
            verdict=Verdict.OK,
            feedback="LLM feedback is disabled. Set LLM_PROVIDER=api to enable it.",
        )

    async def suggest_example(self, word: str) -> str:
        return f"(LLM disabled) Try writing a sentence with '{word}'."

    async def select_topic_words(self, topic: str, limit: int) -> list[str]:
        return []

    async def describe_word(self, word: str) -> WordHint:
        return WordHint(
            meaning="LLM descriptions are disabled. Set LLM_PROVIDER=api to enable them.",
        )

    async def drill_word(self, word: str, user_message: str) -> tuple[str, str]:
        return f"(LLM disabled) Good try with '{word}'!", ""

    async def translate_sentence(self, text: str) -> tuple[str, list[dict[str, str]]]:
        return "", []

    async def interview(
        self, topic: str, lang: str, messages: list[dict[str, str]]
    ) -> InterviewEvaluation:
        return InterviewEvaluation(
            verdict=None,
            feedback=None,
            corrected=None,
            advance=False,
            next_question=None,
        )
