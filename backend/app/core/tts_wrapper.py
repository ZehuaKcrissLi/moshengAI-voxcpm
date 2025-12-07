import sys
import os
import torch
import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

from backend.app.core.config import settings

# Add IndexTTS to sys.path
sys.path.append(settings.INDEX_TTS_ROOT)

logger = logging.getLogger(__name__)

class TTSEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TTSEngine, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.queue = asyncio.Queue()
            cls._instance.executor = ThreadPoolExecutor(max_workers=1) # Serialize GPU access
        return cls._instance

    def initialize(self):
        """
        Initialize the TTS model. This should be called once at startup.
        """
        if self.model is not None:
            logger.info("TTS Model already initialized.")
            return

        logger.info("Initializing TTS Model...")
        try:
            # Import here to avoid import errors if paths aren't set yet
            # We also need to ensure we are in the right directory for relative paths inside the library if any
            # But since we pass absolute paths, it should be fine.
            # However, infer_v2 sets env vars and imports relative to its location sometimes.
            
            # The infer_v2.py imports 'indextts', so adding INDEX_TTS_ROOT to path helps.
            from indextts.infer_v2 import IndexTTS2
            
            self.model = IndexTTS2(
                cfg_path=settings.TTS_CONFIG_PATH,
                model_dir=settings.TTS_MODEL_DIR,
                use_fp16=True, # Enable FP16 for speed
                device="cuda" if torch.cuda.is_available() else "cpu",
                use_cuda_kernel=False # Disable custom kernel to avoid compilation issues for now
            )
            logger.info("TTS Model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize TTS Model: {e}")
            raise e

    async def process_queue(self):
        """
        Background worker to process TTS tasks from the queue.
        """
        logger.info("TTS Worker started.")
        while True:
            task_data = await self.queue.get()
            task_id, text, voice_path, future = task_data
            
            try:
                logger.info(f"Processing task {task_id}...")
                # Run inference in a separate thread to avoid blocking the event loop
                # Since the model uses GPU, we should ensure thread safety if needed, 
                # but we are using a single worker loop here so it's effectively serial.
                output_filename = f"{task_id}.wav"
                output_path = os.path.join(settings.GENERATED_AUDIO_DIR, output_filename)
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self.executor,
                    self._run_inference,
                    text,
                    voice_path,
                    output_path
                )
                
                # Set the result on the future
                future.set_result(f"/static/generated/{output_filename}")
                logger.info(f"Task {task_id} completed.")
                
            except Exception as e:
                logger.error(f"Error processing task {task_id}: {e}")
                future.set_exception(e)
            finally:
                self.queue.task_done()

    def _run_inference(self, text: str, voice_path: str, output_path: str):
        """
        Internal synchronous inference method.
        """
        if self.model is None:
            raise RuntimeError("TTS Model not initialized")
            
        # Call the infer method of IndexTTS2
        # Based on infer_v2.py: infer(self, spk_audio_prompt, text, output_path, ...)
        self.model.infer(
            spk_audio_prompt=voice_path,
            text=text,
            output_path=output_path,
            verbose=False
        )
        return output_path

    async def submit_task(self, text: str, voice_path: str) -> str:
        """
        Submit a TTS task to the queue.
        Returns the task_id.
        """
        task_id = str(uuid.uuid4())
        future = asyncio.get_running_loop().create_future()
        
        # We'll store the future in a separate tracking dict in a real app, 
        # but for this pattern, we return task_id and let the caller poll or wait.
        # However, since we need polling, we should probably store the state in DB/Memory.
        # For now, let's just put it in the queue.
        
        # Wait, the requirement is polling. 
        # So we need a way to track status. The Queue just holds pending work.
        # We need a separate store for status.
        
        # Refactoring for Polling:
        # The submit_task shouldn't wait for result.
        # It should just enqueue.
        # But the worker needs to update some state.
        # For MVP, I will pass a callback or update a global dict?
        # Better: The caller (Router) handles DB updates. 
        # But here I'm just wrapping the engine.
        
        # Let's pass a 'task_id' to the queue and let the worker handle the file creation.
        # The router will handle DB status updates. 
        
        # Actually, to keep this wrapper simple, I will let it accept a callback or 
        # just do the inference. The worker loop logic implies this class handles execution.
        
        # Let's stick to the plan: 
        # The worker loop here is fine. I will modify it to take a 'task_id' and update a simple in-memory dict for now
        # if DB is not ready, but the plan says "Implement Background Worker... Update Task status in DB".
        # So this wrapper should probably just expose `infer_blocking` and let the FastAPI generic worker handle the queue/DB?
        # OR, this wrapper encapsulates the Queue.
        
        # Let's go with: Wrapper encapsulates Queue and Model.
        # It exposes `generate_async(text, voice_path, task_id)` 
        # And we can pass a completion callback.
        
        await self.queue.put((task_id, text, voice_path, future))
        return task_id, future

tts_engine = TTSEngine()

