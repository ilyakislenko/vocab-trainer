from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.map import ModuleAvailability
from vocab_api.domain.curriculum.track import Track
from vocab_api.infrastructure.curriculum.content_loader import ContentBundle


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