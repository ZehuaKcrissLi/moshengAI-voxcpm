import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Runtime environment
    ENVIRONMENT: str = "development"  # development | production
    PROJECT_NAME: str = "Mosheng AI"
    API_V1_STR: str = "/api/v1"
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ROOT_DIR: str = "/scratch/kcriss/MoshengAI"
    
    INDEX_TTS_ROOT: str = os.path.join(ROOT_DIR, "index-tts")
    VOICE_ASSETS_DIR: str = os.path.join(ROOT_DIR, "prompt_voice")
    STORAGE_DIR: str = os.path.join(ROOT_DIR, "storage")
    GENERATED_AUDIO_DIR: str = os.path.join(STORAGE_DIR, "generated")
    
    # TTS Config
    TTS_CONFIG_PATH: str = os.path.join(INDEX_TTS_ROOT, "checkpoints/config.yaml")
    TTS_MODEL_DIR: str = os.path.join(INDEX_TTS_ROOT, "checkpoints")
    
    # Database
    # Host-run default: Postgres from docker-compose exposed on localhost:5432
    # Docker-compose overrides this via service environment to use host "db".
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/mosheng"
    
    # Security
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:33000,http://10.212.227.125:33000"
    
    # Credits
    TTS_COST_PER_CHAR: int = 1
    NEW_USER_CREDITS: int = 100
    MIN_CREDITS_REQUIRED: int = 1
    
    # OAuth (Placeholders for future implementation)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.GENERATED_AUDIO_DIR, exist_ok=True)

