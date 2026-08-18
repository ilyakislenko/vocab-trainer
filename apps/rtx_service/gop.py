"""GOP phoneme scoring engine (framework-free; runs on the rtx GPU box).

Average-posterior GOP: for each expected phoneme we average the model's
posterior probability over the frames where the CTC decoder emitted that
phoneme (consecutive runs collapsed), matching emitted phonemes to the
G2P-transcribed target in order. A phoneme the decoder never emitted scores 0.
"""

import io
import re

import phonemizer
import torch
import torchaudio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

# Public espeak-phoneme wav2vec2 model — its output vocabulary is espeak IPA, so
# it lines up with the espeak G2P used below. Override with RTX_GOP_MODEL.
DEFAULT_MODEL = "facebook/wav2vec2-lv-60-espeak-cv-ft"

SAMPLE_RATE = 16000
GOOD_THRESHOLD = 0.8
WEAK_THRESHOLD = 0.5


def verdict(score: float) -> str:
    if score >= GOOD_THRESHOLD:
        return "good"
    if score >= WEAK_THRESHOLD:
        return "fair"
    return "weak"


def target_words(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.casefold())


class GopScorer:
    def __init__(self, model_name: str = DEFAULT_MODEL, device: str = "cuda") -> None:
        self.device = torch.device(device)
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name).to(self.device).eval()
        self.tokenizer = self.processor.tokenizer

    def phonemize(self, words: list[str]) -> list[list[str]]:
        if not words:
            return []
        raw = phonemizer.phonemize(
            " | ".join(words),
            language="en-us",
            backend="espeak",
            preserve_punctuation=True,
            with_stress=False,
            separator=phonemizer.separator.Separator(phone=" ", word="|"),
        )
        return [word.split() for word in raw.split("|") if word.strip()]

    @torch.inference_mode()
    def score(self, wav_bytes: bytes, target_text: str) -> dict:
        try:
            waveform, sample_rate = torchaudio.load(io.BytesIO(wav_bytes))
        except (RuntimeError, EOFError):
            raise ValueError("empty or unreadable audio") from None
        if waveform.numel() == 0:
            raise ValueError("empty audio")
        if sample_rate != SAMPLE_RATE:
            waveform = torchaudio.functional.resample(waveform, sample_rate, SAMPLE_RATE)
        waveform = waveform.mean(dim=0)
        features = self.processor(
            waveform, sampling_rate=SAMPLE_RATE, return_tensors="pt"
        ).input_values.to(self.device)
        logits = self.model(features).logits[0]
        probs = torch.softmax(logits, dim=-1)
        transcript = self.processor.decode(torch.argmax(logits, dim=-1))
        runs = self._emitted_runs(probs)
        words = self.phonemize(target_words(target_text))

        words_out = []
        for word_phonemes in words:
            phonemes = self._gop_for_word(word_phonemes, runs)
            word_score = sum(score for _, score in phonemes) / len(phonemes) if phonemes else 0.0
            words_out.append(
                {
                    "word": " ".join(word_phonemes),
                    "score": round(word_score, 4),
                    "phonemes": [
                        {"phoneme": ph, "score": round(score, 4), "verdict": verdict(score)}
                        for ph, score in phonemes
                    ],
                }
            )

        overall = (
            sum(word["score"] for word in words_out) / len(words_out) if words_out else 0.0
        )
        return {
            "overall": round(overall, 4),
            "words": words_out,
            "transcript": transcript,
            "scored_phonemes": True,
        }

    def _emitted_runs(self, probs: torch.Tensor) -> list[tuple[int, float]]:
        argmax = probs.argmax(dim=-1)
        runs = []
        index = 0
        while index < argmax.size(0):
            token = int(argmax[index])
            end = index
            while end < argmax.size(0) and int(argmax[end]) == token:
                end += 1
            runs.append((token, float(probs[index:end, token].mean())))
            index = end
        return runs

    def _gop_for_word(
        self, phonemes: list[str], runs: list[tuple[int, float]]
    ) -> list[tuple[str, float]]:
        # Align the expected phonemes to the emitted runs by longest common
        # subsequence, so a single mismatch (e.g. the model hearing "o" where the
        # target expects the diphthong "oʊ") does not swallow the runs that follow
        # and zero out the rest of the word. A matched phoneme scores its run's
        # posterior; an unmatched (missing/mispronounced) one scores 0.
        exp = [self.tokenizer.convert_tokens_to_ids(p) for p in phonemes]
        run_tokens = [token for token, _ in runs]
        m, n = len(exp), len(run_tokens)
        lcs = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m - 1, -1, -1):
            for j in range(n - 1, -1, -1):
                if exp[i] == run_tokens[j]:
                    lcs[i][j] = 1 + lcs[i + 1][j + 1]
                else:
                    lcs[i][j] = max(lcs[i + 1][j], lcs[i][j + 1])
        matched: dict[int, float] = {}
        i = j = 0
        while i < m and j < n:
            if exp[i] == run_tokens[j]:
                matched[i] = runs[j][1]
                i += 1
                j += 1
            elif lcs[i + 1][j] >= lcs[i][j + 1]:
                i += 1
            else:
                j += 1
        return [(phoneme, matched.get(k, 0.0)) for k, phoneme in enumerate(phonemes)]