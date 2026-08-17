import random

from vocab_api.application.ports.llm import LlmProvider
from vocab_api.application.ports.pronunciation import PronunciationScorer
from vocab_api.application.use_cases.curriculum import (
    GetCurriculumMap,
    GetLesson,
    GetModule,
    GetRecommendedModule,
    MarkLessonRead,
)
from vocab_api.application.use_cases.decks import CreateDeck, ListDeckCards, ListDecks
from vocab_api.application.use_cases.importing import ImportWords
from vocab_api.application.use_cases.placement import GetPlacement, GradePlacement
from vocab_api.application.use_cases.practice import (
    CheckSentence,
    ConductInterview,
    DescribeWord,
    DrillWord,
    SelectTopicWords,
    SuggestExample,
    TranslateSentence,
)
from vocab_api.application.use_cases.progress import GetProgress
from vocab_api.application.use_cases.pronounce import ScorePronunciation
from vocab_api.application.use_cases.quiz import GetModuleQuiz, GradeQuiz
from vocab_api.application.use_cases.review import (
    GetReviewQueue,
    GetReviewSummary,
    RecordReview,
)
from vocab_api.application.use_cases.skills import (
    GetFocusLeeches,
    GetSkillReviewQueue,
    RecordSkillReview,
)
from vocab_api.application.use_cases.stats import GetStats
from vocab_api.application.use_cases.today import BuildTodaySession
from vocab_api.config.britlex_seed import (
    BritlexSeeder,
    ItInterviewSeeder,
    load_britlex_sources,
    load_it_sources,
)
from vocab_api.config.curriculum_seed import load_curriculum_content
from vocab_api.config.settings import Settings
from vocab_api.infrastructure.clock import SystemClock
from vocab_api.infrastructure.curriculum.file_curriculum import FileCurriculumRepository
from vocab_api.infrastructure.llm.null_provider import NullProvider
from vocab_api.infrastructure.llm.openai_compatible_provider import OpenAiCompatibleProvider
from vocab_api.infrastructure.persistence.card_repo import SqlCardRepository
from vocab_api.infrastructure.persistence.curriculum_repos import (
    SqlLearnerProfileRepository,
    SqlModuleProgressRepository,
    SqlQuizAttemptRepository,
    SqlSkillItemRepository,
)
from vocab_api.infrastructure.persistence.deck_repo import SqlDeckRepository
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.review_log_repo import SqlReviewLogRepository
from vocab_api.infrastructure.persistence.sentence_attempt_repo import (
    SqlSentenceAttemptRepository,
)
from vocab_api.infrastructure.pronunciation.null_scorer import NullScorer
from vocab_api.infrastructure.question_bank import JsonQuestionBank, load_interview_questions
from vocab_api.infrastructure.scheduling.py_fsrs_scheduler import PyFsrsScheduler


class Container:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._db = Database(settings.database_url)
        clock = SystemClock()
        scheduler = PyFsrsScheduler()
        decks = SqlDeckRepository(self._db)
        cards = SqlCardRepository(self._db)
        logs = SqlReviewLogRepository(self._db)

        self.create_deck = CreateDeck(decks, clock)
        self.list_decks = ListDecks(decks)
        self.list_deck_cards = ListDeckCards(decks, cards)
        self.import_words = ImportWords(decks, cards, clock)
        self.get_review_queue = GetReviewQueue(cards, clock)
        self.record_review = RecordReview(cards, logs, scheduler, clock)
        self.get_review_summary = GetReviewSummary(cards, logs, clock)
        self.get_stats = GetStats(cards, logs, clock)

        attempts = SqlSentenceAttemptRepository(self._db)
        provider: LlmProvider = (
            OpenAiCompatibleProvider(
                settings.llm_base_url,
                settings.llm_model,
                settings.llm_api_key,
                timeout=settings.llm_timeout,
            )
            if settings.llm_provider == "api"
            else NullProvider()
        )
        self.check_sentence = CheckSentence(cards, attempts, provider, clock)
        self.suggest_example = SuggestExample(cards, provider)
        self.select_topic_words = SelectTopicWords(cards, provider)
        self.describe_word = DescribeWord(cards, provider)
        self.drill_word = DrillWord(cards, provider)
        self.translate_sentence = TranslateSentence(provider)
        self.conduct_interview = ConductInterview(
            provider, JsonQuestionBank(load_interview_questions())
        )

        curriculum: FileCurriculumRepository = load_curriculum_content()
        module_progress = SqlModuleProgressRepository(self._db)
        quiz_attempts = SqlQuizAttemptRepository(self._db)
        skill_items = SqlSkillItemRepository(self._db)
        learner_profile = SqlLearnerProfileRepository(self._db)
        self.get_curriculum_map = GetCurriculumMap(curriculum, module_progress)
        self.get_module = GetModule(curriculum, module_progress)
        self.get_lesson = GetLesson(curriculum, module_progress)
        self.mark_lesson_read = MarkLessonRead(curriculum, module_progress, clock)
        self.get_recommended_module = GetRecommendedModule(
            curriculum, module_progress, learner_profile
        )
        self.get_module_quiz = GetModuleQuiz(curriculum, module_progress)
        self.grade_quiz = GradeQuiz(
            curriculum,
            module_progress,
            quiz_attempts,
            clock,
            skill_items,
            scheduler,
            learner_profile,
        )
        self.get_skill_review_queue = GetSkillReviewQueue(skill_items, curriculum, clock)
        self.record_skill_review = RecordSkillReview(skill_items, scheduler, clock)
        self.get_focus_leeches = GetFocusLeeches(skill_items)
        self.learner_profile = learner_profile
        self.get_placement = GetPlacement(curriculum, random.Random())
        self.grade_placement = GradePlacement(curriculum, learner_profile)
        self.build_today_session = BuildTodaySession(
            curriculum,
            module_progress,
            decks,
            cards,
            logs,
            skill_items,
            self.get_recommended_module,
            clock,
        )
        self.get_progress = GetProgress(curriculum, module_progress, decks, logs)

        self.score_pronunciation = ScorePronunciation(self._pronunciation_scorer(), NullScorer())

        self._britlex_seed = BritlexSeeder(self.list_decks, self.create_deck, self.import_words)
        self._it_seed = ItInterviewSeeder(self.list_decks, self.create_deck, self.import_words)

    def _pronunciation_scorer(self) -> PronunciationScorer:
        provider = self._settings.pronunciation_provider
        if provider == "none":
            return NullScorer()
        raise ValueError(
            f"pronunciation provider {provider!r} is not wired yet; use 'none' "
            "(the rtx/cloud adapters land with their own steps)"
        )

    async def init(self) -> None:
        await self._db.init()
        if self._settings.seed_default_deck:
            await self._britlex_seed.execute(load_britlex_sources())
            await self._it_seed.execute(load_it_sources())

    async def dispose(self) -> None:
        await self._db.dispose()
