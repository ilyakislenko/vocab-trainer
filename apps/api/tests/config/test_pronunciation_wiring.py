from typing import Literal

from vocab_api.config.container import Container
from vocab_api.config.settings import Settings
from vocab_api.infrastructure.pronunciation.cloud_stt_scorer import CloudSttScorer
from vocab_api.infrastructure.pronunciation.null_scorer import NullScorer
from vocab_api.infrastructure.pronunciation.rtx_gop_scorer import RtxGopScorer


def _container(provider: Literal["rtx", "cloud", "none"]) -> Container:
    return Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
            pronunciation_provider=provider,
        )
    )


def test_none_provider_wires_null_scorer():
    assert isinstance(_container("none").score_pronunciation._scorer, NullScorer)


def test_cloud_provider_wires_cloud_scorer():
    assert isinstance(_container("cloud").score_pronunciation._scorer, CloudSttScorer)


def test_rtx_provider_wires_rtx_scorer():
    assert isinstance(_container("rtx").score_pronunciation._scorer, RtxGopScorer)
