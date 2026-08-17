"""Parse and validate the authored curriculum content bundle.

The bundle is the source of truth for what the Curriculum serves: the manifest
(`curriculum.json`), one markdown lesson per module, and quiz files. Loading
runs a strict validation pass — a broken bundle is a hard boot error
(§14 of the design spec), never served silently.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib.resources import files

import yaml

from vocab_api.domain.curriculum.lesson import Lesson
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.map import LadderEntry, LevelOverview, ModuleAvailability
from vocab_api.domain.curriculum.module import Module, Reference
from vocab_api.domain.curriculum.track import Track
from vocab_api.domain.shared.errors import ContentValidationError


@dataclass(frozen=True, slots=True)
class LoadedContent:
    levels: tuple[LevelOverview[LadderEntry], ...]
    modules: dict[str, Module]
    lessons: dict[str, Lesson]
    has_quiz: set[str]


_YAML_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _load_text(resource: str) -> str:
    package = files("vocab_api.seed").joinpath("content", resource)
    return package.read_text(encoding="utf-8")


def _split_frontmatter(raw: str) -> tuple[dict[str, object], str]:
    match = _YAML_FRONTMATTER.match(raw)
    if not match:
        raise ContentValidationError(f"lesson is missing YAML frontmatter: {raw[:60]!r}")
    frontmatter = yaml.safe_load(match.group(1))
    if not isinstance(frontmatter, dict):
        raise ContentValidationError("lesson frontmatter must be a mapping")
    return frontmatter, raw[match.end() :]


def _require_str(data: dict[str, object], key: str, context: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ContentValidationError(f"{context}: field {key!r} must be a non-empty string")
    return value.strip()


def _require_str_list(data: dict[str, object], key: str, context: str) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ContentValidationError(f"{context}: field {key!r} must be a list of strings")
    return tuple(value)


def _require_int(data: dict[str, object], key: str, context: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise ContentValidationError(f"{context}: field {key!r} must be an integer")
    return value


def _module_id_parts(module_id: str) -> tuple[Level, Track]:
    parts = module_id.split(".")
    if len(parts) < 3:
        raise ContentValidationError(f"module id {module_id!r} must be <level>.<track>.<slug>")
    level_str, track_str, slug = parts[0], parts[1], parts[2]
    if not slug.strip():
        raise ContentValidationError(f"module id {module_id!r} has an empty slug")
    try:
        level = Level(level_str.upper())
    except ValueError as exc:
        raise ContentValidationError(
            f"module id {module_id!r} has invalid level {level_str!r}"
        ) from exc
    try:
        track = Track(track_str)
    except ValueError as exc:
        raise ContentValidationError(
            f"module id {module_id!r} has invalid track {track_str!r}"
        ) from exc
    return level, track


class ContentBundle:
    """Parse and validate the whole bundle, exposing it to repositories."""

    def __init__(
        self,
        manifest: dict[str, object],
        lesson_texts: dict[str, str],
        quiz_texts: dict[str, str],
    ) -> None:
        self._manifest = manifest
        self._lesson_texts = lesson_texts
        self._quiz_texts = quiz_texts
        self._levels: tuple[LevelOverview[LadderEntry], ...] = ()
        self._modules: dict[str, Module] = {}
        self._lessons: dict[str, Lesson] = {}
        self._has_quiz: set[str] = set()
        self._validate()

    @staticmethod
    def from_files() -> ContentBundle:
        manifest_raw = json.loads(_load_text("curriculum.json"))
        if not isinstance(manifest_raw, dict):
            raise ContentValidationError("curriculum.json must be a JSON object")
        lesson_texts: dict[str, str] = {}
        quiz_texts: dict[str, str] = {}
        lessons_dir = files("vocab_api.seed").joinpath("content", "lessons")
        for resource in lessons_dir.iterdir():
            name = resource.name
            if name.startswith(".") or not name.endswith(".md"):
                continue
            lesson_texts[name[: -len(".md")]] = resource.read_text(encoding="utf-8")
        for resource in files("vocab_api.seed").joinpath("content").iterdir():
            name = resource.name
            if name.startswith(".") or name in {"curriculum.json", "placement.json"}:
                continue
            if name.endswith(".json"):
                quiz_texts[name[: -len(".json")]] = resource.read_text(encoding="utf-8")
        return ContentBundle(manifest_raw, lesson_texts, quiz_texts)

    def _validate(self) -> None:
        levels_raw = self._manifest.get("levels")
        if not isinstance(levels_raw, list):
            raise ContentValidationError("curriculum.json: 'levels' must be a list")

        seen_ids: set[str] = set()
        seen_levels: set[str] = set()
        levels_out: list[LevelOverview[LadderEntry]] = []

        for level_raw in levels_raw:
            if not isinstance(level_raw, dict):
                raise ContentValidationError("curriculum.json: each level must be an object")
            level = level_raw.get("level")
            if not isinstance(level, str):
                raise ContentValidationError("curriculum.json: each level needs a 'level' string")
            try:
                level_enum = Level(level)
            except ValueError as exc:
                raise ContentValidationError(f"curriculum.json: invalid level {level!r}") from exc
            if level in seen_levels:
                raise ContentValidationError(f"curriculum.json: duplicate level {level!r}")
            seen_levels.add(level)

            modules_raw = level_raw.get("modules")
            if not isinstance(modules_raw, list):
                raise ContentValidationError(
                    f"curriculum.json: level {level!r} needs a 'modules' list"
                )

            entries: list[LadderEntry] = []
            for module_raw in modules_raw:
                module_id: str
                title: str
                if isinstance(module_raw, str):
                    module_id = module_raw
                    availability = ModuleAvailability.AVAILABLE
                    title = ""
                elif isinstance(module_raw, dict):
                    raw_id = module_raw.get("id")
                    if not isinstance(raw_id, str):
                        raise ContentValidationError(
                            "curriculum.json: authoring module needs an 'id' string"
                        )
                    module_id = raw_id
                    status = module_raw.get("status")
                    if status != "authoring":
                        raise ContentValidationError(
                            "curriculum.json: module "
                            f"{module_id!r} object status must be 'authoring'"
                        )
                    availability = ModuleAvailability.AUTHORING
                    raw_title = module_raw.get("title")
                    title = raw_title if isinstance(raw_title, str) else ""
                else:
                    raise ContentValidationError(
                        "curriculum.json: module entries must be a string id or an authoring object"
                    )

                if module_id in seen_ids:
                    raise ContentValidationError(
                        f"curriculum.json: duplicate module id {module_id!r}"
                    )
                seen_ids.add(module_id)
                parsed_level, parsed_track = _module_id_parts(module_id)
                if parsed_level is not level_enum:
                    raise ContentValidationError(
                        f"curriculum.json: module {module_id!r} in level {level!r} "
                        f"but id says {parsed_level.value!r}"
                    )

                entries.append(
                    LadderEntry(
                        id=module_id,
                        title=title,
                        track=parsed_track,
                        availability=availability,
                    )
                )

            levels_out.append(LevelOverview(level=level_enum, entries=tuple(entries)))

        self._levels = tuple(levels_out)
        self._load_modules()
        self._load_quizzes()
        self._cross_validate()

    def _load_modules(self) -> None:
        for section in self._levels:
            for entry in section.entries:
                if entry.availability is ModuleAvailability.AUTHORING:
                    continue
                raw = self._lesson_texts.get(entry.id)
                if raw is None:
                    raise ContentValidationError(
                        f"available module {entry.id!r} has no lesson file"
                    )
                frontmatter, _ = _split_frontmatter(raw)
                title = _require_str(frontmatter, "title", f"lesson {entry.id}")
                objectives = _require_str_list(frontmatter, "objectives", f"lesson {entry.id}")
                skills = _require_str_list(frontmatter, "skills", f"lesson {entry.id}")
                estimated_minutes = _require_int(
                    frontmatter, "estimated_minutes", f"lesson {entry.id}"
                )
                references_raw = frontmatter.get("references")
                references: tuple[Reference, ...] = ()
                if references_raw is not None:
                    if not isinstance(references_raw, list):
                        raise ContentValidationError(
                            f"lesson {entry.id}: 'references' must be a list"
                        )
                    parsed = []
                    for ref in references_raw:
                        if not isinstance(ref, dict):
                            raise ContentValidationError(
                                f"lesson {entry.id}: reference must be an object"
                            )
                        book = ref.get("book")
                        locator = ref.get("locator")
                        if not isinstance(book, str) or not isinstance(locator, str):
                            raise ContentValidationError(
                                f"lesson {entry.id}: reference needs 'book' and 'locator' strings"
                            )
                        parsed.append(Reference(book=book, locator=locator))
                    references = tuple(parsed)
                if entry.title and entry.title != title:
                    raise ContentValidationError(
                        "lesson "
                        f"{entry.id}: frontmatter title {title!r} "
                        f"conflicts with manifest title {entry.title!r}"
                    )
                self._modules[entry.id] = Module(
                    id=entry.id,
                    title=title,
                    objectives=objectives,
                    skills=skills,
                    references=references,
                    estimated_minutes=estimated_minutes,
                    order=section.entries.index(entry),
                )
                self._lessons[entry.id] = Lesson(
                    id=entry.id,
                    title=title,
                    markdown=raw,
                    estimated_minutes=estimated_minutes,
                    objectives=objectives,
                    skills=skills,
                    references=tuple((r.book, r.locator) for r in references),
                )

    def _load_quizzes(self) -> None:
        for section in self._levels:
            for entry in section.entries:
                if entry.availability is ModuleAvailability.AUTHORING:
                    continue
                quiz_raw = self._quiz_texts.get(entry.id)
                if quiz_raw is not None:
                    # Quiz structure is validated in Phase 1 (quiz.py); for now
                    # we only register that a quiz file exists.
                    self._has_quiz.add(entry.id)

    def _cross_validate(self) -> None:
        for section in self._levels:
            for entry in section.entries:
                if entry.availability is ModuleAvailability.AVAILABLE:
                    if entry.id not in self._lessons:
                        raise ContentValidationError(f"available module {entry.id!r} has no lesson")
                else:
                    if entry.id in self._lessons or entry.id in self._has_quiz:
                        raise ContentValidationError(
                            f"authoring module {entry.id!r} must not have lesson/quiz files yet"
                        )

    # Public read API ---------------------------------------------------------

    def levels(self) -> tuple[LevelOverview[LadderEntry], ...]:
        return self._levels

    def module(self, module_id: str) -> Module | None:
        return self._modules.get(module_id)

    def lesson(self, module_id: str) -> Lesson | None:
        return self._lessons.get(module_id)

    def has_lesson(self, module_id: str) -> bool:
        return module_id in self._lessons

    def has_quiz(self, module_id: str) -> bool:
        return module_id in self._has_quiz