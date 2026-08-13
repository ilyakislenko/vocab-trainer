from vocab_api.application.ports.llm import LlmProvider
from vocab_api.application.use_cases.decks import CreateDeck, ListDecks
from vocab_api.application.use_cases.importing import ImportWords
from vocab_api.application.use_cases.practice import CheckSentence, SuggestExample
from vocab_api.application.use_cases.review import GetReviewQueue, RecordReview
from vocab_api.application.use_cases.stats import GetStats
from vocab_api.config.settings import Settings
from vocab_api.infrastructure.clock import SystemClock
from vocab_api.infrastructure.llm.null_provider import NullProvider
from vocab_api.infrastructure.llm.openai_compatible_provider import OpenAiCompatibleProvider
from vocab_api.infrastructure.persistence.card_repo import SqlCardRepository
from vocab_api.infrastructure.persistence.deck_repo import SqlDeckRepository
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.review_log_repo import SqlReviewLogRepository
from vocab_api.infrastructure.persistence.sentence_attempt_repo import (
    SqlSentenceAttemptRepository,
)
from vocab_api.infrastructure.scheduling.py_fsrs_scheduler import PyFsrsScheduler


class Container:
    def __init__(self, settings: Settings) -> None:
        self._db = Database(settings.database_url)
        clock = SystemClock()
        scheduler = PyFsrsScheduler()
        decks = SqlDeckRepository(self._db)
        cards = SqlCardRepository(self._db)
        logs = SqlReviewLogRepository(self._db)

        self.create_deck = CreateDeck(decks, clock)
        self.list_decks = ListDecks(decks)
        self.import_words = ImportWords(decks, cards, clock)
        self.get_review_queue = GetReviewQueue(cards, clock)
        self.record_review = RecordReview(cards, logs, scheduler, clock)
        self.get_stats = GetStats(cards, logs, clock)

        attempts = SqlSentenceAttemptRepository(self._db)
        provider: LlmProvider = (
            OpenAiCompatibleProvider(
                settings.llm_base_url, settings.llm_model, settings.llm_api_key
            )
            if settings.llm_provider == "api"
            else NullProvider()
        )
        self.check_sentence = CheckSentence(cards, attempts, provider, clock)
        self.suggest_example = SuggestExample(cards, provider)

    async def init(self) -> None:
        await self._db.init()
