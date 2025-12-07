import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.tts_wrapper import tts_engine
from backend.app.routers import tts, voice

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    
    # Initialize TTS Engine
    try:
        tts_engine.initialize()
        # Start the queue processor
        asyncio.create_task(tts_engine.process_queue())
    except Exception as e:
        print(f"Failed to initialize TTS Engine: {e}")
        # We might want to exit or continue with error
    
    yield
    
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
# 1. Generated Audio
app.mount("/static/generated", StaticFiles(directory=settings.GENERATED_AUDIO_DIR), name="generated")
# 2. Voice Assets (for previews)
app.mount("/static/voices", StaticFiles(directory=settings.VOICE_ASSETS_DIR), name="voices")

# Routers
app.include_router(tts.router, prefix="/tts", tags=["tts"])
app.include_router(voice.router, prefix="/voices", tags=["voices"])
# app.include_router(auth.router, prefix="/auth", tags=["auth"]) # Later

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def read_root():
    return JSONResponse(content={"message": "Mosheng AI Backend is running"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)
