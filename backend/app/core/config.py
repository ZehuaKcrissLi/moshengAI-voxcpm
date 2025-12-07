import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
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
    DATABASE_URL: str = "sqlite+aiosqlite:///./mosheng.db" # Use SQLite for MVP, switch to Postgres later
    
    # Security
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.GENERATED_AUDIO_DIR, exist_ok=True)

