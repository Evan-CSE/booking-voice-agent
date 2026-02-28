"""
Self-hosted STT service using faster-whisper.
Implements OpenAI-compatible POST /v1/audio/transcriptions endpoint.
"""
import os
import tempfile
import logging

from fastapi import FastAPI, UploadFile, File, Form
from faster_whisper import WhisperModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stt-service")

app = FastAPI(title="Self-Hosted Whisper STT")

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WHISPER_MODEL_SIZE: str = "tiny"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

settings = Settings()
MODEL_SIZE = settings.WHISPER_MODEL_SIZE
DEVICE = settings.WHISPER_DEVICE
COMPUTE_TYPE = settings.WHISPER_COMPUTE_TYPE

logger.info(f"Loading Whisper model: {MODEL_SIZE} on {DEVICE} ({COMPUTE_TYPE})")
whisper_model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
logger.info("Whisper model loaded successfully.")

@app.post("/v1/audio/transcriptions")
async def transcribe(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    language: str = Form(None),
    response_format: str = Form("json"),
):
    """OpenAI-compatible transcription endpoint."""
    suffix = os.path.splitext(file.filename or ".wav")[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        segments, info = whisper_model.transcribe(tmp_path, language=language)
        text = " ".join(seg.text for seg in segments).strip()
        logger.info(f"Transcribed ({info.language}, {info.duration:.1f}s): {text[:80]}...")
        return {"text": text}
    finally:
        os.unlink(tmp_path)


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_SIZE}
