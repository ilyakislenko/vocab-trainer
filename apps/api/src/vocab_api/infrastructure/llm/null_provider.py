from vocab_api.application.ports.llm import LlmProvider
from vocab_api.domain.practice.feedback import Feedback, Verdict


class NullProvider(LlmProvider):
    async def check_sentence(self, word: str, sentence: str) -> Feedback:
        return Feedback(
            verdict=Verdict.OK,
            feedback="LLM feedback is disabled. Set LLM_PROVIDER=api to enable it.",
        )

    async def suggest_example(self, word: str) -> str:
        return f"(LLM disabled) Try writing a sentence with '{word}'."
