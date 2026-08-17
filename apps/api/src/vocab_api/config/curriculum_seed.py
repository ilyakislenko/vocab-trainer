from vocab_api.infrastructure.curriculum.content_loader import ContentBundle
from vocab_api.infrastructure.curriculum.file_curriculum import FileCurriculumRepository


def load_curriculum_content() -> FileCurriculumRepository:
    """Load and validate the bundled curriculum; raises on a broken bundle."""
    return FileCurriculumRepository(ContentBundle.from_files())