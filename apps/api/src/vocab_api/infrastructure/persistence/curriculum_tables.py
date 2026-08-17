from datetime import datetime

from sqlmodel import Field, SQLModel


class LearnerProfileRow(SQLModel, table=True):
    """The single learner's state; a get-or-create singleton row (id=1)."""

    __tablename__ = "learner_profile"
    id: int | None = Field(default=1, primary_key=True)
    placement_level: str | None = None
    current_module_id: str | None = None


class ModuleProgressRow(SQLModel, table=True):
    __tablename__ = "module_progress"
    module_id: str = Field(primary_key=True)
    status: str = "not_started"
    lesson_read_at: datetime | None = None
    quiz_best_score: float | None = None
    completed_at: datetime | None = None