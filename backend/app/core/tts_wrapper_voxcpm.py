"""
VoxCPM TTS引擎封装
替代IndexTTS，提供更好的兼容性和性能
"""
import sys
import os
import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class VoxCPMEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VoxCPMEngine, cls).__new__(cls)
            cls._instance.model = None
            # queue 延迟到初始化时绑定当前事件循环，避免跨事件循环挂起
            cls._instance.queue = None
            cls._instance.executor = ThreadPoolExecutor(max_workers=1)
        return cls._instance

    def initialize(self):
        """初始化VoxCPM模型"""
        if self.model is not None:
            print("VoxCPM Model already initialized.")
            logger.info("VoxCPM Model already initialized.")
            return

        print("Initializing VoxCPM Model...")
        logger.info("Initializing VoxCPM Model...")
        try:
            from voxcpm import VoxCPM
            
            print("Loading VoxCPM1.5 from HuggingFace...")
            # 加载VoxCPM1.5模型
            # 注意：optimize=False 避免在ThreadPoolExecutor中使用torch.compile时的线程安全问题
            self.model = VoxCPM.from_pretrained(
                hf_model_id="openbmb/VoxCPM1.5",
                load_denoiser=True,  # 加载降噪器
                optimize=False  # 禁用优化以避免线程安全问题
            )
            
            print(f"✅ VoxCPM Model initialized successfully!")
            print(f"   采样率: {self.model.tts_model.sample_rate}")
            print(f"   设备: {self.model.tts_model.device}")
            print(f"   模型对象: {self.model}")
            
            logger.info(f"✅ VoxCPM Model initialized successfully!")
            logger.info(f"   采样率: {self.model.tts_model.sample_rate}")
            logger.info(f"   设备: {self.model.tts_model.device}")
            
            # 绑定queue到当前事件循环，防止旧loop导致get/put阻塞
            self.queue = asyncio.Queue()
            print("Queue created and bound to current event loop.")
            logger.info("Queue created and bound to current event loop.")
            
        except Exception as e:
            print(f"❌ Failed to initialize VoxCPM Model: {e}")
            logger.error(f"Failed to initialize VoxCPM Model: {e}")
            import traceback
            traceback.print_exc()
            raise e

    async def process_queue(self):
        """后台worker处理TTS任务队列"""
        print("="*60)
        print("🚀 VoxCPM Worker started!")
        print("="*60)
        print(f"[Worker] queue id: {id(self.queue)}")
        logger.info("VoxCPM Worker started.")
        
        while True:
            print(f"⏳ Waiting for task from queue... (model: {self.model is not None}) queue id: {id(self.queue)} size: {self.queue.qsize() if self.queue else 'None'}")
            task_data = await self.queue.get()
            task_id, text, voice_path, future = task_data
            
            print(f"📝 Got task {task_id}: {text[:50]}")
            
            try:
                print(f"🎵 Processing task {task_id}...")
                logger.info(f"Processing task {task_id}...")
                
                output_filename = f"{task_id}.wav"
                output_path = os.path.join(settings.GENERATED_AUDIO_DIR, output_filename)
                
                print(f"   输出路径: {output_path}")
                print(f"   音色文件: {voice_path}")
                
                # 在单独线程中运行推理
                loop = asyncio.get_event_loop()
                print(f"   开始推理...")
                await loop.run_in_executor(
                    self.executor,
                    self._run_inference,
                    text,
                    voice_path,
                    output_path
                )
                
                print(f"   推理完成，设置结果...")
                # 设置结果
                future.set_result(f"/static/generated/{output_filename}")
                print(f"✅ Task {task_id} completed successfully!")
                logger.info(f"✅ Task {task_id} completed successfully")
                
            except Exception as e:
                print(f"❌ Error processing task {task_id}: {e}")
                logger.error(f"❌ Error processing task {task_id}: {e}")
                import traceback
                traceback.print_exc()
                future.set_exception(e)
            finally:
                self.queue.task_done()

    def _run_inference(self, text: str, voice_path: str, output_path: str):
        """同步推理方法（线程池内防御性检查）"""
        if self.model is None:
            logger.warning("Model not initialized in executor thread, re-initializing...")
            try:
                from voxcpm import VoxCPM
                self.model = VoxCPM.from_pretrained(
                    hf_model_id="openbmb/VoxCPM1.5",
                    load_denoiser=True,
                    optimize=False  # 禁用优化以避免线程安全问题
                )
                logger.info(f"Model re-initialized inside executor thread. device={self.model.tts_model.device}")
            except Exception as reinit_err:
                logger.exception("Failed to reinitialize model inside executor")
                raise RuntimeError("VoxCPM Model not initialized") from reinit_err
        if self.model is None:
            raise RuntimeError("VoxCPM Model not initialized")
        
        try:
            import soundfile as sf
            
            # 处理voice_path（可能为空字符串或None）
            prompt_wav_path = None
            prompt_text = None
            
            if voice_path and os.path.exists(voice_path):
                prompt_wav_path = voice_path
                # 读取voice的transcript（如果有）
                txt_path = os.path.splitext(voice_path)[0] + ".txt"
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    prompt_text = f.read().strip()
            
            logger.info(f"Generating audio for: {text[:50]}...")
            logger.info(f"Voice reference: {prompt_wav_path or 'None'}")
            logger.info(f"Prompt text: {prompt_text[:50] if prompt_text else 'None'}")
            print(f"🎤 [Inference] Starting VoxCPM generation...")
            print(f"   Text length: {len(text)}")
            print(f"   Model device: {self.model.tts_model.device}")
            
            # 调用VoxCPM生成
            print(f"   Calling model.generate()...")
            wav = self.model.generate(
                text=text,
                prompt_wav_path=prompt_wav_path,  # 参考音色（可能为None）
                prompt_text=prompt_text,          # 参考文本（可能为None）
                cfg_value=2.0,                   # 引导强度
                inference_timesteps=10,           # 推理步数（越高质量越好但越慢）
                normalize=False,                  # 不使用外部文本标准化
                denoise=False,                    # 不使用去噪（保持原始采样率）
                retry_badcase=True,               # 自动重试失败case
                retry_badcase_max_times=3,
                retry_badcase_ratio_threshold=6.0
            )
            print(f"✅ [Inference] Model.generate() completed, output shape: {wav.shape}")
            
            # 保存音频
            sf.write(output_path, wav, self.model.tts_model.sample_rate)
            logger.info(f"✅ Audio saved to: {output_path}")
            
            return output_path
            
        except Exception as e:
            error_msg = str(e) if e else "Unknown error"
            logger.error(f"VoxCPM inference failed: {error_msg}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            print(f"❌ VoxCPM inference error: {error_msg}")
            traceback.print_exc()
            raise e

    async def submit_task(self, text: str, voice_path: str):
        """提交TTS任务到队列"""
        task_id = str(uuid.uuid4())
        future = asyncio.get_running_loop().create_future()
        
        print(f"📤 Submitting task {task_id} to queue")
        print(f"   Text: {text[:50]}")
        print(f"   Voice: {voice_path}")
        print(f"   Queue size before: {self.queue.qsize()}")
        
        await self.queue.put((task_id, text, voice_path, future))
        
        print(f"   Queue size after: {self.queue.qsize()}")
        print(f"✅ Task submitted to queue")
        
        return task_id, future

# 全局实例
voxcpm_engine = VoxCPMEngine()

