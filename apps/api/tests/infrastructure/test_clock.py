from datetime import UTC

from vocab_api.infrastructure.clock import SystemClock


def test_system_clock_returns_utc_aware():
    now = SystemClock().now()
    assert now.tzinfo is not None
    assert now.utcoffset() == UTC.utcoffset(now)
