"""Unit tests for the GOP engine. Require torch + the model; run on the rtx box."""

import io
import math
import wave

import pytest
import torch
import torchaudio

from gop import GopScorer, target_words, verdict


def _tone_wav(seconds: float = 0.4, frequency: int = 440, sample_rate: int = 16000) -> bytes:
    frames = torch.sin(2 * math.pi * frequency * torch.arange(seconds * sample_rate) / sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes((frames * 16384).to(torch.int16).numpy().tobytes())
    return buffer.getvalue()


def test_verdict_thresholds():
    assert verdict(0.9) == "good"
    assert verdict(0.8) == "good"
    assert verdict(0.79) == "fair"
    assert verdict(0.5) == "fair"
    assert verdict(0.49) == "weak"


def test_target_words():
    assert target_words("I ran every day.") == ["i", "ran", "every", "day"]
    assert target_words("don't") == ["don't"]
    assert target_words("") == []


def test_phonemize_returns_expected_phonemes():
    scorer = GopScorer.__new__(GopScorer)
    phonemes = scorer.phonemize(["hello"])
    assert len(phonemes) == 1
    assert phonemes[0]  # non-empty; espeak en-us "hello" -> h ə l oʊ
    assert "h" in phonemes[0] or "h" == phonemes[0][0]


def test_phonemize_empty():
    scorer = GopScorer.__new__(GopScorer)
    assert scorer.phonemize([]) == []


def test_score_golden_shape():
    scorer = GopScorer(device="cpu")
    result = scorer.score(_tone_wav(), "hello")
    assert result["scored_phonemes"] is True
    assert len(result["words"]) == 1
    word = result["words"][0]
    assert word["score"] == pytest.approx(result["overall"])
    assert all(0.0 <= ph["score"] <= 1.0 for ph in word["phonemes"])
    assert all(ph["verdict"] in ("good", "fair", "weak") for ph in word["phonemes"])
    assert result["transcript"]


def test_score_empty_audio_rejected():
    scorer = GopScorer(device="cpu")
    with pytest.raises(ValueError):
        scorer.score(b"", "hello")