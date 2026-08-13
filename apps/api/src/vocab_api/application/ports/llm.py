from typing import Protocol

from vocab_api.domain.practice.feedback import Feedback


class LlmProvider(Protocol):
    async def check_sentence(self, word: str, sentence: str) -> Feedback: ...
    async def suggest_example(self, word: str) -> str: ...
