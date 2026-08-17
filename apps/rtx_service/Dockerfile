# rtx GOP inference service — containerised so nothing spreads across the host.
# Base already carries a CUDA-matched torch; we add the system + Python deps.
FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

# espeak-ng: phonemizer's G2P backend. libsndfile1/ffmpeg: torchaudio decoding.
RUN apt-get update && apt-get install -y --no-install-recommends \
      espeak-ng \
      libsndfile1 \
      ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# torchaudio matched to the base image's torch (cu121), then the rest of the deps.
# torch/torchaudio in requirements.txt are already satisfied, so pip skips them.
RUN pip install --no-cache-dir torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu121
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py gop.py ./

# HF_HOME points at the mounted volume so the wav2vec2 model is downloaded once
# and cached across restarts (see docker-compose.yml).
ENV RTX_GOP_DEVICE=cuda \
    HF_HOME=/models

EXPOSE 8900
# Factory mode loads the model once at boot.
CMD ["uvicorn", "app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8900"]
