# Pronunciation scoring (phoneme-level GOP) — design & hand-off

Server-side pronunciation assessment that scores **individual phonemes**
(Goodness of Pronunciation), replacing the browser Web Speech word-match. Built
behind a provider port so inference can run on the **rtx GPU box** or a **cloud**
backend, switchable by env — mirroring the existing LLM provider pattern.

**Owner decisions (2026-08-17):** phoneme-level GOP (not just word STT); runtime =
rtx GPU service **and** cloud, switchable. This is why the backend is Python
(in-process/near-process ML), per the project's founding rationale.

**Rules:** obey `CONTRIBUTING.md` — Hexagonal + DDD, `domain/` framework-free, use
cases depend only on ports, wiring only in the composition root, mypy strict, no
placeholders, tests over in-memory fakes, all gates green. The LLM/`NullProvider`
rule applies: a provider failure must never break the request.

---

## 1. What exists now (baseline)
- Browser Web Speech (`shared/lib/speech.ts`, `features/pronounce`): `webkitSpeechRecognition`
  transcribes speech and the app word-matches it to the target. No phonemes, browser-only,
  inconsistent across browsers.
- Backend has **no** ML deps. This spec adds the first ML subsystem.

The browser TTS (`speak`) stays. Browser STT stays only as a last-resort fallback.

## 2. Architecture (three layers + a separate inference service)

```
domain/pronunciation/          ← pure value objects (no framework)
  assessment.py                  PhonemeScore, WordScore, PronunciationAssessment, Verdict
application/ports/pronunciation.py
  PronunciationScorer (Protocol) ← score(audio, target_text, accent) -> PronunciationAssessment
application/use_cases/pronounce.py
  ScorePronunciation             ← validates input, calls the port, maps failures to a safe result
infrastructure/pronunciation/
  rtx_gop_scorer.py              ← HTTP client → the rtx inference service (full GOP)
  cloud_stt_scorer.py            ← cloud Whisper STT → word-level match only (degraded)
  null_scorer.py                 ← offline self-check; never raises
config/                          ← wiring; env VOCAB_PRONUNCIATION_PROVIDER=rtx|cloud|none
interfaces/http/pronounce_router.py
  POST /pronounce/score          ← multipart audio + target → assessment DTO
```

The heavy model does **not** live in the FastAPI process. It runs in a **separate
inference service** (§5) the `rtx_gop_scorer` calls over HTTP. This keeps the main
API light and lets the model sit on the GPU box ([[reference_windows_pc]]).

## 3. Domain (pure)
```python
class Verdict(StrEnum): GOOD; FAIR; WEAK
@dataclass(frozen=True) class PhonemeScore: phoneme: str; score: float; verdict: Verdict  # score 0..1 (GOP, normalised)
@dataclass(frozen=True) class WordScore: word: str; score: float; phonemes: tuple[PhonemeScore, ...]
@dataclass(frozen=True) class PronunciationAssessment:
    overall: float                 # 0..1
    words: tuple[WordScore, ...]
    transcript: str                # what was heard (for display / STT-only mode)
    scored_phonemes: bool          # False when a degraded backend returned word-match only
```
Named thresholds (constants): `GOOD_THRESHOLD`, `WEAK_THRESHOLD` map a phoneme
score → `Verdict`. Pure functions; unit-tested.

## 4. GOP method (what the scorer computes)

**Whisper alone is not enough — and is not the phoneme model.** Whisper outputs
orthographic words/BPE tokens, not phonemes. Its only role here is an *optional*
transcript + rough word timings ("what did they say", for the degraded/STT path).
The actual pronunciation scoring is a **wav2vec2 phoneme model + forced alignment
+ GOP** — do not expect Whisper to score sounds.

Pipeline:
1. **G2P:** target text → expected phoneme sequence (`g2p_en`, or espeak-ng
   `phonemizer`), so we know which phonemes each word should contain.
2. **Phoneme acoustic model:** a wav2vec2 CTC phoneme model — concrete candidate
   `facebook/wav2vec2-lv-60-espeak-cv-ft` (IPA/espeak output) — giving per-frame
   phoneme posteriors.
3. **Forced alignment:** align the audio to the expected phoneme sequence
   (torchaudio `forced_align`; or Montreal Forced Aligner / Gentle as a Kaldi-based
   alternative).
4. **GOP per phoneme:** mean frame-level log-posterior of the *target* phoneme over
   its aligned segment, normalised to 0..1. Low → mispronounced. Aggregate to word
   and overall scores. (Classic GOP; wav2vec2 variant.)
5. Output the `PronunciationAssessment`.

**Tooling menu (implementer/owner picks; the port contract is what's fixed):**
- **WhisperX** — Whisper + wav2vec2 forced alignment in one package; convenient if
  we also want the transcript. Gives char/near-phoneme timings, *not* GOP scores by
  itself — still pair with posteriors for scoring.
- **wav2vec2-lv-60-espeak-cv-ft** — direct IPA phoneme output; the recommended core
  for GOP scoring.
- **Allosaurus** — universal phoneme recogniser (free phoneme decoding, no target
  needed). Good complement for **mispronunciation detection**: decode what was
  actually said, diff against the expected phonemes → "said /s/ instead of /θ/".
  Consider running it alongside GOP to power the per-phoneme feedback text.
- **MFA / Gentle** — industrial Kaldi forced aligners for precise phoneme timings if
  torchaudio alignment proves too coarse.

Recommended default: **wav2vec2-lv-60-espeak-cv-ft for GOP scoring**, optionally
**Allosaurus** for the "what you actually said" diff, Whisper/WhisperX only if a
word transcript is wanted. The exact stack is the implementer's call as long as the
port contract and output shape hold.

## 5. The rtx inference service (separate component)
A minimal standalone Python service (its own venv/deps: torch, transformers,
torchaudio, phonemizer) on the rtx box:
- `POST /gop` (multipart wav + target text) → JSON matching `PronunciationAssessment`.
- Loads the model once at boot (GPU). Accepts 16 kHz mono wav; the caller converts.
- No auth beyond LAN binding (owner's local network, per [[feedback_ask_before_changing_network]]);
  document the bind address, don't hardcode a public one.
- Health endpoint so `rtx_gop_scorer` can fail fast → fall back.
This service is deployed/run separately from the main app; the main repo holds a
thin client only (no torch in `apps/api`).

## 6. Adapters & switching
- `RtxGopScorer(base_url, http)`: POSTs audio to the rtx service; returns full
  phoneme assessment (`scored_phonemes=True`). On timeout/unreachable → raise a
  typed `PronunciationUnavailable` (application maps to fallback, never 500 to the user).
- `CloudSttScorer`: cloud Whisper (or `faster-whisper`) → transcript → word-level
  match against target; `scored_phonemes=False`, phoneme lists empty. Degraded but useful.
- `NullScorer`: returns a neutral self-check assessment, `scored_phonemes=False`;
  **never raises** (offline-safe, base-spec rule).
- Env `VOCAB_PRONUNCIATION_PROVIDER=rtx|cloud|none` selects the primary; a provider
  error degrades to the next sensible option and the response is marked accordingly.

## 7. API
- `POST /pronounce/score` — multipart: `audio` (webm/opus or wav), `target` (text),
  optional `accent` (en-US default). Returns the assessment DTO. Validation → 422;
  upstream failure → a degraded assessment (200) with `scored_phonemes=false`, never 502
  to the learner. **Audio is never persisted or logged** (privacy; base-spec §6).
- Reuse the existing pronounce endpoints where they fit; add this as the scoring path.

## 8. Frontend
- Record with `MediaRecorder` (webm/opus), send to `/pronounce/score`.
- Render: overall %, per-word chips coloured by verdict, and on tap the per-phoneme
  breakdown ("your /θ/ was weak — try …"). When `scored_phonemes=false`, show the
  word-match view (today's UX) with a subtle "phoneme scoring offline" note.
- Keep browser TTS for "hear it"; drop reliance on browser STT for scoring.
- Lives in `features/pronounce` (extend); business logic in `*/model`, not components.

## 9. Testing
- Domain: threshold→verdict, aggregation, edge cases (empty transcript, silence). No IO.
- Use case: fake `PronunciationScorer` (returns canned assessments incl. a failing/degraded
  one); assert the fallback path and that `NullScorer` never raises.
- HTTP: `AsyncClient` with a fake scorer — 422 on bad input, 200 degraded on provider failure.
- The rtx service has its own tests (in its own repo/dir): G2P correctness, a golden
  audio→score fixture. Not gated by the main app's CI.
- Frontend: Vitest with a mocked client; MSW for the multipart call.

## 10. Non-goals / risks
- No torch/transformers in `apps/api` — the client is HTTP-only; the model lives in
  the rtx service. (Keeps the main image light and CI fast.)
- No storing user audio. No accents beyond en-* initially.
- Risk: forced-alignment quality on short/noisy clips → mitigate with a minimum-duration
  check and a confidence floor that degrades to word-match.
- Risk: rtx availability → the provider switch + `NullScorer` keep the app usable offline.

## 11. Sequencing
1. Domain + port + `NullScorer` + use case + API + frontend wired to Null (ships a working,
   honest "offline" path). 2. `CloudSttScorer` (word-level, real STT). 3. The rtx GOP
   service + `RtxGopScorer` (full phoneme scoring). Each step independently shippable.
