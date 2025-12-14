import os
import glob
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from backend.app.core.config import settings

router = APIRouter(redirect_slashes=False)

class Voice(BaseModel):
    id: str
    name: str
    category: str
    preview_url: str
    transcript: str = ""

@router.get("", response_model=List[Voice])
@router.get("/", response_model=List[Voice])
async def get_voices():
    """
    Scan the prompt_voice directory and return available voices.
    """
    voices = []
    # Structure is prompt_voice/{category}/{filename}.wav
    # We use glob to find all .wav files
    search_pattern = os.path.join(settings.VOICE_ASSETS_DIR, "**", "*.wav")
    wav_files = glob.glob(search_pattern, recursive=True)
    
    # Sort files for consistent order
    wav_files.sort()

    for wav_path in wav_files:
        # Get relative path parts
        rel_path = os.path.relpath(wav_path, settings.VOICE_ASSETS_DIR)
        parts = rel_path.split(os.sep)
        
        if len(parts) < 2:
            continue # Skip files in root or weird structure
            
        category = parts[0] # e.g. male, female
        filename = parts[-1]
        name = os.path.splitext(filename)[0]
        
        # Look for transcript .txt
        txt_path = os.path.splitext(wav_path)[0] + ".txt"
        transcript = ""
        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    transcript = f.read().strip()
            except Exception:
                pass

        # Construct preview URL (served by static mount)
        # We need to expose prompt_voice as static too or copy them? 
        # Better to expose prompt_voice as /static/voices
        preview_url = f"/static/voices/{category}/{filename}"
        
        voices.append(Voice(
            id=rel_path, # Use relative path as ID
            name=name,
            category=category,
            preview_url=preview_url,
            transcript=transcript
        ))
        
    return voices

