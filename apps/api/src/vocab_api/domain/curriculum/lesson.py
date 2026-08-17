from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Lesson:
    """The readable teaching document for a module.

    `markdown` is authored bilingual prose (English target language with
    Russian explanations); `frontmatter` fields are validated at load time and
    mirrored onto the Module aggregate.
    """

    id: str
    markdown: str
    estimated_minutes: int = 5
    objectives: tuple[str, ...] = ()
    skills: tuple[str, ...] = ()
    references: tuple[tuple[str, str], ...] = ()
    title: str = ""