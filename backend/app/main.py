import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
# from backend.app.core.tts_wrapper import tts_engine  # IndexTTS - 兼容性问题
from backend.app.core.tts_wrapper_voxcpm import voxcpm_engine as tts_engine  # VoxCPM - 新的TTS引擎
from backend.app.db.init_db import init_db
from backend.app.routers import tts, voice, auth, credits

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    
    # Initialize Database
    try:
        await init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
    
    # Initialize TTS Engine
    try:
        print("Attempting to initialize TTS Engine...")
        tts_engine.initialize()
        print("TTS Engine initialized, starting queue processor...")
        # Start the queue processor
        asyncio.create_task(tts_engine.process_queue())
        print("Queue processor started")
    except Exception as e:
        print(f"Failed to initialize TTS Engine: {e}")
        import traceback
        traceback.print_exc()
    
    yield
    
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    redirect_slashes=False
)

# CORS
allowed_origins = settings.ALLOWED_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Mount Static Files
# 1. Generated Audio
app.mount("/static/generated", StaticFiles(directory=settings.GENERATED_AUDIO_DIR), name="generated")
# 2. Voice Assets (for previews)
app.mount("/static/voices", StaticFiles(directory=settings.VOICE_ASSETS_DIR), name="voices")

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(credits.router, prefix="/credits", tags=["credits"])
app.include_router(tts.router, prefix="/tts", tags=["tts"])
app.include_router(voice.router, prefix="/voices", tags=["voices"])

# Monitor router - try to load, skip if dependencies missing
try:
    from backend.app.routers import monitor
    app.include_router(monitor.router, prefix="/monitor", tags=["monitor"])
    print("✅ Monitor router loaded")
except Exception as e:
    print(f"⚠️  Monitor router not loaded: {e}")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def read_root():
    return JSONResponse(content={"message": "Mosheng AI Backend is running"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)
