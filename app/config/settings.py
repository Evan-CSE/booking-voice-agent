from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # LiveKit and LLM
    LIVEKIT_URL: str = "ws://localhost:7880"
    LIVEKIT_API_KEY: str = "devkey"
    LIVEKIT_API_SECRET: str = "secret"
    GOOGLE_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-3-flash-preview"
    
    # Internal Services
    STT_BASE_URL: str = "http://stt:8000/v1"
    TTS_BASE_URL: str = "http://tts:8001/v1"
    
    # SMTP Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    
    # Server
    PORT: int = 8080

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
