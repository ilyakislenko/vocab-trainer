from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Reference:
    book: str
    locator: str


@dataclass(frozen=True, slots=True)
class Module:
    """One atomic step of the curriculum route.

    Content is authored and read-only; the object carries everything a learner
    needs to see the module on the map and open its lesson/quiz. `id` is a
    stable global key (`<level>.<track>.<slug>`) used as the DB key.
    """

    id: str
    title: str
    objectives: tuple[str, ...]
    skills: tuple[str, ...]
    references: tuple[Reference, ...]
    estimated_minutes: int = 5
    order: int = 0