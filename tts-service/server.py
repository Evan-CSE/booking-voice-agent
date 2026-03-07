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

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PIPER_VOICE_MODEL: str = "/models/en_US-lessac-medium.onnx"

settings = Settings()
VOICE_MODEL = settings.PIPER_VOICE_MODEL

logger.info(f"Loading Piper voice: {VOICE_MODEL}")
try:
    voice = PiperVoice.load(VOICE_MODEL)
    logger.info("Piper voice loaded successfully.")
except Exception as e:
    logger.warning(f"Could not load Piper voice: {e}")
    voice = None

# logger.info("Loading Kokoro pipeline...")
# kokoro_pipeline = None
# try:
#     from kokoro import KPipeline
#     kokoro_pipeline = KPipeline(lang_code='a')
#     logger.info("Kokoro pipeline loaded successfully.")
# except ImportError:
#     logger.warning("kokoro package not found. Kokoro TTS will be unavailable.")
# except Exception as e:
#     logger.warning(f"Could not load Kokoro pipeline: {e}")


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


async def stream_kokoro_chunks(text: str, voice_name: str = "af_heart"):
    """Yield raw PCM audio chunks (24kHz) from Kokoro."""
    if not kokoro_pipeline:
        logger.error("Kokoro pipeline is not initialized")
        yield b""
        return
    
    try:
        generator = kokoro_pipeline(text, voice=voice_name, speed=1.0)
        for _, _, audio in generator:
            if audio is None:
                continue
            
            if np.issubdtype(audio.dtype, np.floating):
                audio = np.clip(audio, -1.0, 1.0)
                audio_int16 = (audio * 32767.0).astype(np.int16)
            else:
                audio_int16 = audio.astype(np.int16)
                
            yield audio_int16.tobytes()
            await asyncio.sleep(0)
    except Exception as e:
        logger.error(f"Error synthesizing with Kokoro: {e}")
        yield b""


@app.post("/v1/audio/speech")
async def create_speech(request: SpeechRequest):
    """OpenAI-compatible streaming text-to-speech endpoint."""
    logger.info(f"Streaming TTS [{request.model}]: {request.input[:80]}...")
    
    # if request.model == "kokoro":
    #     voice_name = request.voice
    #     if voice_name == "alloy":
    #         voice_name = "af_alloy"
            
    #     return StreamingResponse(
    #         stream_kokoro_chunks(request.input, voice_name=voice_name),
    #         media_type="audio/wav"
    #     )
    
    if voice is None:
        logger.error("Piper is not initialized")
        return StreamingResponse(iter([b""]), media_type="audio/wav")

    # Livekit expects "audio/wav" content type even for raw PCM streams when response_format="pcm"
    return StreamingResponse(
        stream_pcm_chunks(request.input),
        media_type="audio/wav"
    )


@app.get("/health")
async def health():
    return {"status": "ok", "voice": VOICE_MODEL}
