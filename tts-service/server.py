"""
Self-hosted TTS service using Piper.
Implements OpenAI-compatible POST /v1/audio/speech endpoint.
"""
import io
import os
import wave
import struct
import logging

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from piper import PiperVoice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tts-service")

app = FastAPI(title="Self-Hosted Piper TTS")

VOICE_MODEL = os.getenv("PIPER_VOICE_MODEL", "/models/en_US-lessac-medium.onnx")

logger.info(f"Loading Piper voice: {VOICE_MODEL}")
voice = PiperVoice.load(VOICE_MODEL)
logger.info("Piper voice loaded successfully.")


class SpeechRequest(BaseModel):
    model: str = "piper"
    input: str
    voice: str = "alloy"  # ignored, we use the pre-loaded model
    response_format: str = "wav"


import numpy as np
import librosa
import asyncio

async def stream_pcm_chunks(text: str):
    """Yield raw PCM audio chunks (24kHz) as Piper synthesizes them."""
    # Piper yields AudioResult objects which contain audio_int16_bytes
    for chunk in voice.synthesize(text):
        raw_pcm = chunk.audio_int16_bytes
        if not raw_pcm:
            continue

        # Convert to float for librosa
        audio_int16 = np.frombuffer(raw_pcm, dtype=np.int16)
        audio_float = audio_int16.astype(np.float32) / 32768.0
        
        # Resample chunk from Piper's native sample rate to 24000Hz
        resampled_float = librosa.resample(audio_float, orig_sr=voice.config.sample_rate, target_sr=24000)
        
        # Convert back to 16-bit PCM bytes
        resampled_int16 = (resampled_float * 32767.0).astype(np.int16)
        
        yield resampled_int16.tobytes()
        
        # Yield to event loop to allow concurrent requests
        await asyncio.sleep(0)


@app.post("/v1/audio/speech")
async def create_speech(request: SpeechRequest):
    """OpenAI-compatible streaming text-to-speech endpoint."""
    logger.info(f"Streaming TTS: {request.input[:80]}...")
    
    # Livekit expects "audio/wav" content type even for raw PCM streams when response_format="pcm"
    return StreamingResponse(
        stream_pcm_chunks(request.input),
        media_type="audio/wav"
    )


@app.get("/health")
async def health():
    return {"status": "ok", "voice": VOICE_MODEL}
