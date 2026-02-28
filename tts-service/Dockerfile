FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libsndfile1 \
    wget \
    curl \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download a high-quality Piper English voice at build time
RUN mkdir -p /models && \
    wget -qO /models/en_US-lessac-medium.onnx \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" && \
    wget -qO /models/en_US-lessac-medium.onnx.json \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

COPY server.py .

EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
