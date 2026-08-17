# rtx GOP inference service

Standalone FastAPI service that does **full phoneme (GOP) scoring** on the rtx
GPU box (`192.168.1.84`, hostname `DESKTOP-HP7DKR9`). The main API (`apps/api`)
never touches torch — it talks to this service over the LAN through the thin
`RtxGopScorer` HTTP client. This directory is **not** part of the main app's CI;
its tests need torch and the model and run on the rtx box itself.

## Endpoints

- `GET /healthz` → `{"status": "ok"}` — lets `RtxGopScorer` fail fast.
- `POST /gop` — multipart `audio` (16 kHz mono wav), `target` (text), optional
  `accent` (default `en-US`). Returns JSON matching `PronunciationAssessment`:
  `{overall, words: [{word, score, phonemes: [{phoneme, score, verdict}]}],
  transcript, scored_phonemes}`.

## Scoring model

Average-posterior GOP: the CTC phoneme model (`bookbot/wav2vec2-libriphoneme`)
emits a phoneme path over the clip; each expected phoneme (from G2P via espeak,
en-us) gets the mean posterior of the emitted run it matches, in order. A
phoneme the decoder never emitted scores 0. Verdict thresholds mirror the main
app: `good ≥ 0.8`, `fair ≥ 0.5`, else `weak`.

## Installing on rtx (Windows + GPU)

Pick one PyTorch install path and pin it in a venv:

1. **Native Windows + CUDA wheels** (simplest for the RTX GPU):
   ```
   python -m venv .venv && .venv\Scripts\activate
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
   pip install -r requirements.txt
   ```
2. **WSL2 + CUDA** (Linux tooling; needs the WSL CUDA driver). Docker Desktop
   with GPU passthrough also works but is heavier.

`phonemizer` needs **espeak-ng** on the system (`choco install espeak-ng` on
Windows, or `apt install espeak-ng` in WSL).

## Running

Bind to the LAN interface, not just localhost, and pin port 8900:

```
set RTX_GOP_DEVICE=cuda
uvicorn app:create_app --factory --host 0.0.0.0 --port 8900
```

Run it as a persistent process so it survives reboots and is up when the main
app calls: a Windows service, a Task Scheduler "at logon" task, or an NSSM
wrapper (or systemd/tmux inside WSL).

## Windows Firewall

Open inbound **TCP 8900** for the private/LAN profile, or the request from the
main API host (`192.168.1.100`) is dropped:

```
netsh advfirewall firewall add rule name="rtx-gop" dir=in action=allow protocol=TCP localport=8900 profile=private
```

The main app is configured via `VOCAB_PRONUNCIATION_RTX_URL` (default
`http://192.168.1.84:8900`); the hostname form `http://DESKTOP-HP7DKR9:8900`
also works if the LAN IP changes. LAN-only — do not expose to the internet; no
auth beyond the private network for now.

## Access to deploy/operate rtx

Over the LAN via RDP, or enable the optional OpenSSH Server Windows feature and
`ssh user@192.168.1.84`.

## Tests (run on the rtx box)

```
python -m pytest tests -q
```
## Deploy with Docker (recommended — keeps the host clean)

Everything (CUDA torch, the wav2vec2 model, espeak-ng) lives in one container, so
nothing is installed on the Windows host directly. Remove the container and no
trace is left.

**Prerequisites on the rtx box (one-time):**
- Docker Desktop with the **WSL2 backend**.
- A current **NVIDIA driver** with WSL CUDA support + the **NVIDIA Container
  Toolkit** (for GPU passthrough). Without a GPU you can still run CPU-only.

**Run:**
```bash
cd apps/rtx_service
docker compose up -d --build      # first build pulls the CUDA base + downloads the model
docker compose logs -f gop        # watch it load the model, then "Application startup complete"
curl http://localhost:8900/healthz
```
- The wav2vec2 model downloads once into the `hf-models` volume and is cached.
- **Open inbound TCP 8900** for the private/LAN profile in Windows Firewall, or the
  main API on `192.168.1.100` can't reach `http://192.168.1.84:8900`.
- **CPU-only (no GPU):** set `RTX_GOP_DEVICE: cpu` and delete the `deploy:` GPU block
  in `docker-compose.yml`. Slower; fine for a smoke test.

**Point the main API at it:** set `VOCAB_PRONUNCIATION_PROVIDER=rtx` (the rtx URL
already defaults to `http://192.168.1.84:8900`).
