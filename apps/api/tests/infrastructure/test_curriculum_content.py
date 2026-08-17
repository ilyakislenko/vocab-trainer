import json

import pytest

from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.map import ModuleAvailability
from vocab_api.domain.curriculum.quiz import QuizItemType
from vocab_api.domain.curriculum.track import Track
from vocab_api.domain.shared.errors import ContentValidationError
from vocab_api.infrastructure.curriculum.content_loader import ContentBundle


def _make_bundle(quiz_items: list[dict]) -> ContentBundle:
    """A minimal bundle with one available module and a valid placement bank."""
    manifest = {"levels": [{"level": "A1", "modules": ["a1.grammar.present-simple"]}]}
    lesson = (
        "---\ntitle: Present Simple\nobjectives:\n  - objective\n"
        "skills:\n  - pres.he-she-it\nestimated_minutes: 15\n---\n# Lesson"
    )
    quiz = {"module_id": "a1.grammar.present-simple", "items": quiz_items}
    placement_items = []
    for level in ("A2", "B1", "B2", "C1"):
        for i in range(12):
            placement_items.append(
                {
                    "id": f"{level.lower()}.{i}",
                    "level": level,
                    "type": "cloze",
                    "skill": "placement.skill",
                    "prompt": f"Prompt {level} {i}",
                    "answers": ["answer"],
                    "explanation": "Explanation",
                }
            )
    return ContentBundle(
        manifest,
        {"a1.grammar.present-simple": lesson},
        {"a1.grammar.present-simple": json.dumps(quiz)},
        json.dumps({"items": placement_items}),
    )


def test_word_order_item_requires_non_empty_tokens():
    with pytest.raises(ContentValidationError, match="word_order needs non-empty string 'tokens'"):
        _make_bundle(
            [
                {
                    "id": "q1",
                    "type": "word_order",
                    "skill": "pres.he-she-it",
                    "prompt": "Arrange the words.",
                    "answers": ["She watches TV"],
                    "explanation": "Explanation",
                }
            ]
        )


def test_word_order_item_requires_answers():
    with pytest.raises(ContentValidationError, match="word_order needs non-empty string 'answers'"):
        _make_bundle(
            [
                {
                    "id": "q1",
                    "type": "word_order",
                    "skill": "pres.he-she-it",
                    "prompt": "Arrange the words.",
                    "tokens": ["She", "watches", "TV"],
                    "explanation": "Explanation",
                }
            ]
        )


def test_word_order_item_loads_with_tokens():
    bundle = _make_bundle(
        [
            {
                "id": "q1",
                "type": "word_order",
                "skill": "pres.he-she-it",
                "prompt": "Arrange the words.",
                "tokens": ["She", "watches", "TV", "every", "evening"],
                "answers": ["She watches TV every evening"],
                "explanation": "Explanation",
            }
        ]
    )
    item = bundle.quiz("a1.grammar.present-simple").items[0]
    assert item.type is QuizItemType.WORD_ORDER
    assert item.tokens == ("She", "watches", "TV", "every", "evening")
    assert item.answers == ("She watches TV every evening",)
    assert item.options is None


def test_listening_dictation_requires_answers():
    with pytest.raises(ContentValidationError, match="listening needs non-empty string 'answers'"):
        _make_bundle(
            [
                {
                    "id": "q1",
                    "type": "listening",
                    "skill": "pres.he-she-it",
                    "prompt": "She watches TV every evening.",
                    "explanation": "Explanation",
                }
            ]
        )


def test_listening_mcq_requires_answer_index():
    with pytest.raises(ContentValidationError, match="listening mcq needs a valid 'answer_index'"):
        _make_bundle(
            [
                {
                    "id": "q1",
                    "type": "listening",
                    "skill": "pres.he-she-it",
                    "prompt": "She watches TV every evening.",
                    "options": ["She watches TV.", "He watches TV."],
                    "explanation": "Explanation",
                }
            ]
        )


def test_listening_both_sub_modes_load():
    bundle = _make_bundle(
        [
            {
                "id": "q1",
                "type": "listening",
                "skill": "pres.he-she-it",
                "prompt": "She watches TV every evening.",
                "answers": ["she watches tv every evening"],
                "explanation": "Explanation",
            },
            {
                "id": "q2",
                "type": "listening",
                "skill": "pres.he-she-it",
                "prompt": "She watches TV every evening.",
                "options": ["She watches TV.", "He watches TV."],
                "answer_index": 0,
                "explanation": "Explanation",
            },
        ]
    )
    dictation, choice = bundle.quiz("a1.grammar.present-simple").items
    assert dictation.type is QuizItemType.LISTENING
    assert dictation.answers == ("she watches tv every evening",)
    assert dictation.options is None
    assert choice.options == ("She watches TV.", "He watches TV.")
    assert choice.answer_index == 0
    assert choice.answers is None


def test_bundle_loads_all_six_levels_in_order():
    bundle = ContentBundle.from_files()
    assert [section.level for section in bundle.levels()] == [
        Level.A1,
        Level.A2,
        Level.B1,
        Level.B2,
        Level.C1,
        Level.C2,
    ]


def test_bundle_available_modules_each_have_a_lesson():
    bundle = ContentBundle.from_files()
    available = [
        entry.id
        for section in bundle.levels()
        for entry in section.entries
        if entry.availability is ModuleAvailability.AVAILABLE
    ]
    assert len(available) > 0
    for module_id in available:
        lesson = bundle.lesson(module_id)
        assert lesson is not None
        assert lesson.id == module_id
        assert len(lesson.markdown) > 0


def test_bundle_available_modules_have_valid_ids():
    bundle = ContentBundle.from_files()
    for section in bundle.levels():
        for entry in section.entries:
            parts = entry.id.split(".")
            assert len(parts) == 3
            assert Level(parts[0].upper()) is section.level
            assert Track(parts[1]) is entry.track
            assert parts[2].strip()


def test_bundle_authoring_modules_have_no_lesson_or_quiz():
    bundle = ContentBundle.from_files()
    for section in bundle.levels():
        for entry in section.entries:
            if entry.availability is ModuleAvailability.AUTHORING:
                assert not bundle.has_lesson(entry.id)
                assert not bundle.has_quiz(entry.id)


def test_bundle_has_zero_authoring_modules_left():
    bundle = ContentBundle.from_files()
    remaining = [
        entry.id
        for section in bundle.levels()
        for entry in section.entries
        if entry.availability is ModuleAvailability.AUTHORING
    ]
    assert remaining == [], f"content not fully authored: {remaining}"


def test_bundle_every_available_module_lists_an_objective_and_skill():
    bundle = ContentBundle.from_files()
    for section in bundle.levels():
        for entry in section.entries:
            if entry.availability is ModuleAvailability.AVAILABLE:
                module = bundle.module(entry.id)
                assert module.objectives, f"{entry.id}: objectives must not be empty"
                assert module.skills, f"{entry.id}: skills must not be empty"


def test_bundle_lesson_frontmatter_titles_match_manifest_for_bare_ids():
    bundle = ContentBundle.from_files()
    for section in bundle.levels():
        for entry in section.entries:
            if entry.availability is ModuleAvailability.AVAILABLE and entry.title:
                assert entry.title == bundle.module(entry.id).title


def test_bundle_available_modules_each_have_a_quiz_with_two_types_and_six_items():
    bundle = ContentBundle.from_files()
    for section in bundle.levels():
        for entry in section.entries:
            if entry.availability is not ModuleAvailability.AVAILABLE:
                continue
            quiz = bundle.quiz(entry.id)
            assert quiz is not None
            assert quiz.module_id == entry.id
            assert len(quiz.items) >= 6
            types = {item.type for item in quiz.items}
            assert len(types) >= 2
            item_ids = [item.id for item in quiz.items]
            assert len(item_ids) == len(set(item_ids))


def test_bundle_quiz_item_skills_are_subset_of_lesson_skills():
    bundle = ContentBundle.from_files()
    for section in bundle.levels():
        for entry in section.entries:
            if entry.availability is not ModuleAvailability.AVAILABLE:
                continue
            lesson_skills = set(bundle.lesson(entry.id).skills)
            quiz = bundle.quiz(entry.id)
            for item in quiz.items:
                assert item.skill in lesson_skills, (
                    f"{item.id}: skill {item.skill!r} not in lesson skills"
                )


def test_bundle_placement_spans_levels_without_answers():
    bundle = ContentBundle.from_files()
    placement = bundle.placement()
    assert placement is not None
    assert len(placement.items) >= 48
    by_level: dict[Level, int] = {}
    for item in placement.items:
        assert item.level in {Level.A2, Level.B1, Level.B2, Level.C1}
        assert item.prompt
        assert item.explanation
        assert item.skill
        if item.type.value == "mcq":
            assert item.options
            assert item.answer_index is not None
            assert item.answers is None
        else:
            assert item.answers
            assert item.options is None
        by_level[item.level] = by_level.get(item.level, 0) + 1
    assert len(by_level) == 4
    assert all(count >= 12 for count in by_level.values())


def test_bundle_parses_pillar_links_into_modules_and_lessons():
    bundle = ContentBundle.from_files()

    phrasal = bundle.module("b1.phrasal_verbs.work-business")
    assert phrasal is not None
    assert phrasal.vocab == ("main",)
    assert phrasal.interview_topic is None
    phrasal_lesson = bundle.lesson("b1.phrasal_verbs.work-business")
    assert phrasal_lesson is not None
    assert phrasal_lesson.vocab == ("main",)

    tech = bundle.module("b2.vocabulary.technology")
    assert tech is not None
    assert tech.interview_topic == "Frontend"
    assert tech.vocab == ()
    tech_lesson = bundle.lesson("b2.vocabulary.technology")
    assert tech_lesson is not None
    assert tech_lesson.interview_topic == "Frontend"

    plain = bundle.module("b1.grammar.articles")
    assert plain is not None
    assert plain.vocab == ()
    assert plain.interview_topic is None
