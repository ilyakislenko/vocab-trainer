class LlmUnavailable(Exception):
    """Raised when the configured LLM provider cannot fulfil a request."""


class PronunciationUnavailable(Exception):
    """Raised when the configured pronunciation scorer cannot fulfil a request.

    The application maps this to a degraded assessment, never an error to the
    learner (mirrors the LLM NullProvider rule).
    """
