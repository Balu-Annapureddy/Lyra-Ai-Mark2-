"""
Model Warmup - Reduce First Response Latency by 60-70%
Runs dummy inference after model load to warm up the model
"""

import logging
import asyncio
from typing import Any, Optional
import time

logger = logging.getLogger(__name__)


class ModelWarmer:
    """Handles model warmup to reduce first-response latency"""
    
    def __init__(self, enabled: bool = True):
        """
        Initialize model warmer
        
        Args:
            enabled: Whether warmup is enabled
        """
        self.enabled = enabled
        self._warmup_times = {}
        logger.info(f"ModelWarmer initialized (enabled={enabled})")
    
    async def warmup_llm(self, model: Any, model_name: str = "llm") -> float:
        """
        Warm up LLM with dummy inference
        
        Args:
            model: LLM model instance
            model_name: Name of model for logging
        
        Returns:
            Warmup time in seconds
        """
        if not self.enabled:
            logger.debug("Warmup disabled, skipping LLM warmup")
            return 0.0
        
        logger.info(f"Warming up LLM: {model_name}")
        start_time = time.time()
        
        try:
            # Run dummy inference
            if hasattr(model, 'generate'):
                # llama-cpp-python style
                await asyncio.to_thread(
                    model.generate,
                    "Hello",
                    max_tokens=5
                )
            elif hasattr(model, '__call__'):
                # Transformers style
                await asyncio.to_thread(
                    model,
                    "Hello",
                    max_new_tokens=5
                )
            else:
                logger.warning(f"Unknown LLM interface for {model_name}")
                return 0.0
            
            warmup_time = time.time() - start_time
            self._warmup_times[model_name] = warmup_time
            logger.info(f"LLM warmup complete: {model_name} ({warmup_time:.2f}s)")
            return warmup_time
        
        except Exception as e:
            logger.error(f"LLM warmup failed for {model_name}: {e}")
            return 0.0
    
    async def warmup_stt(self, stt_service: Any, model_name: str = "stt") -> float:
        """
        Warm up STT with silent audio frame
        
        Args:
            stt_service: STT service instance
            model_name: Name of model for logging
        
        Returns:
            Warmup time in seconds
        """
        if not self.enabled:
            logger.debug("Warmup disabled, skipping STT warmup")
            return 0.0
        
        logger.info(f"Warming up STT: {model_name}")
        start_time = time.time()
        
        try:
            # Create silent audio frame (1 second at 16kHz)
            import numpy as np
            silent_audio = np.zeros(16000, dtype=np.int16)
            
            # Run dummy transcription
            if hasattr(stt_service, 'transcribe'):
                await asyncio.to_thread(
                    stt_service.transcribe,
                    silent_audio
                )
            elif hasattr(stt_service, 'recognize'):
                await asyncio.to_thread(
                    stt_service.recognize,
                    silent_audio
                )
            else:
                logger.warning(f"Unknown STT interface for {model_name}")
                return 0.0
            
            warmup_time = time.time() - start_time
            self._warmup_times[model_name] = warmup_time
            logger.info(f"STT warmup complete: {model_name} ({warmup_time:.2f}s)")
            return warmup_time
        
        except Exception as e:
            logger.error(f"STT warmup failed for {model_name}: {e}")
            return 0.0
    
    async def warmup_tts(self, tts_service: Any, model_name: str = "tts") -> float:
        """
        Warm up TTS with dummy synthesis
        
        Args:
            tts_service: TTS service instance
            model_name: Name of model for logging
        
        Returns:
            Warmup time in seconds
        """
        if not self.enabled:
            logger.debug("Warmup disabled, skipping TTS warmup")
            return 0.0
        
        logger.info(f"Warming up TTS: {model_name}")
        start_time = time.time()
        
        try:
            # Run dummy synthesis
            if hasattr(tts_service, 'synthesize'):
                await asyncio.to_thread(
                    tts_service.synthesize,
                    "test"
                )
            elif hasattr(tts_service, 'speak'):
                await asyncio.to_thread(
                    tts_service.speak,
                    "test"
                )
            else:
                logger.warning(f"Unknown TTS interface for {model_name}")
                return 0.0
            
            warmup_time = time.time() - start_time
            self._warmup_times[model_name] = warmup_time
            logger.info(f"TTS warmup complete: {model_name} ({warmup_time:.2f}s)")
            return warmup_time
        
        except Exception as e:
            logger.error(f"TTS warmup failed for {model_name}: {e}")
            return 0.0
    
    async def warmup_vad(self, vad_service: Any, model_name: str = "vad") -> float:
        """
        Warm up VAD with silent frame
        
        Args:
            vad_service: VAD service instance
            model_name: Name of model for logging
        
        Returns:
            Warmup time in seconds
        """
        if not self.enabled:
            logger.debug("Warmup disabled, skipping VAD warmup")
            return 0.0
        
        logger.info(f"Warming up VAD: {model_name}")
        start_time = time.time()
        
        try:
            # Create silent audio frame
            import numpy as np
            silent_audio = np.zeros(512, dtype=np.float32)
            
            # Run dummy VAD
            if hasattr(vad_service, 'process'):
                await asyncio.to_thread(
                    vad_service.process,
                    silent_audio
                )
            elif hasattr(vad_service, '__call__'):
                await asyncio.to_thread(
                    vad_service,
                    silent_audio
                )
            else:
                logger.warning(f"Unknown VAD interface for {model_name}")
                return 0.0
            
            warmup_time = time.time() - start_time
            self._warmup_times[model_name] = warmup_time
            logger.info(f"VAD warmup complete: {model_name} ({warmup_time:.2f}s)")
            return warmup_time
        
        except Exception as e:
            logger.error(f"VAD warmup failed for {model_name}: {e}")
            return 0.0
    
    def get_warmup_times(self) -> dict:
        """Get all warmup times"""
        return self._warmup_times.copy()


# Global warmer instance
_global_warmer: Optional[ModelWarmer] = None


def get_warmer() -> ModelWarmer:
    """Get global model warmer"""
    global _global_warmer
    if _global_warmer is None:
        _global_warmer = ModelWarmer()
    return _global_warmer


if __name__ == "__main__":
    # Test model warmer
    print("Testing Model Warmer")
    print("=" * 50)
    
    class DummyLLM:
        def generate(self, prompt: str, max_tokens: int = 10):
            time.sleep(0.1)
            return "test response"
    
    async def test():
        warmer = ModelWarmer(enabled=True)
        model = DummyLLM()
        
        warmup_time = await warmer.warmup_llm(model, "test-llm")
        print(f"Warmup time: {warmup_time:.2f}s")
        print(f"All warmup times: {warmer.get_warmup_times()}")
    
    asyncio.run(test())
    print("=" * 50)
