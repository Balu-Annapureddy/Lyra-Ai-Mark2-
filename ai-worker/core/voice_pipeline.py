"""
Voice Pipeline
Robust voice handling with async buffering and error fallback
"""

import asyncio
import queue
import threading
import time
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from core.structured_logger import get_structured_logger
from core.metrics_manager import get_metrics_manager
from core.task_queue import get_task_queue, Priority
from core.managers.fallback_manager import get_fallback_manager

class VoicePipelineStatus(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"

@dataclass
class AudioFrame:
    data: bytes
    timestamp: float
    sequence: int

class VoicePipeline:
    """
    Manages voice interaction pipeline.
    
    Features:
    - Async audio buffering
    - VAD integration hooks
    - Error fallback for STT/TTS
    - Latency tracking
    """
    
    def __init__(self, buffer_size_ms: int = 2000):
        self.struct_logger = get_structured_logger("VoicePipeline")
        self.metrics = get_metrics_manager()
        self.task_queue = get_task_queue()
        self.fallback_manager = get_fallback_manager()
        
        self.status = VoicePipelineStatus.IDLE
        self._audio_buffer = queue.Queue()
        self._buffer_size_ms = buffer_size_ms
        self._running = False
        self._process_thread: Optional[threading.Thread] = None
        
        # Hooks
        self.vad_hook: Optional[Callable[[bytes], bool]] = None
        self.stt_provider: Optional[Callable] = None
        self.tts_provider: Optional[Callable] = None
        
        self.struct_logger.info("initialized", "Voice pipeline initialized")

    def start(self):
        """Start the pipeline processing loop"""
        if self._running:
            return
            
        self._running = True
        self._process_thread = threading.Thread(target=self._process_loop, daemon=True, name="VoicePipeline")
        self._process_thread.start()
        self.status = VoicePipelineStatus.LISTENING
        self.struct_logger.info("started", "Voice pipeline started")

    def stop(self):
        """Stop the pipeline"""
        self._running = False
        if self._process_thread:
            self._process_thread.join(timeout=1.0)
        self.status = VoicePipelineStatus.IDLE
        self.struct_logger.info("stopped", "Voice pipeline stopped")

    def push_audio(self, audio_data: bytes):
        """Push audio frame to buffer"""
        if not self._running:
            return
            
        frame = AudioFrame(audio_data, time.time(), 0) # Sequence not tracked for now
        self._audio_buffer.put(frame)
        
        # VAD Check (Simplified)
        if self.vad_hook and self.vad_hook(audio_data):
            self.struct_logger.debug("vad_active", "Voice activity detected")

    def _process_loop(self):
        """Main processing loop"""
        buffer = []
        
        while self._running:
            try:
                # Accumulate audio
                try:
                    frame = self._audio_buffer.get(timeout=0.1)
                    buffer.append(frame.data)
                except queue.Empty:
                    if buffer:
                        # Process accumulated buffer
                        self._process_audio_chunk(b"".join(buffer))
                        buffer = []
                    continue
                    
            except Exception as e:
                self.struct_logger.error("pipeline_error", f"Error in voice loop: {e}")
                self.status = VoicePipelineStatus.ERROR

    def _process_audio_chunk(self, audio_data: bytes):
        """Process a chunk of audio (STT -> LLM -> TTS)"""
        if not audio_data:
            return
            
        self.status = VoicePipelineStatus.PROCESSING
        start_time = time.time()
        
        # Submit to task queue as CRITICAL
        success = self.task_queue.submit(
            Priority.CRITICAL,
            f"voice_process_{int(start_time)}",
            self._handle_voice_interaction,
            audio_data
        )
        
        if not success:
            self.struct_logger.warning("queue_rejected", "Voice task rejected by queue")
            self.metrics.increment_counter("voice_dropped", 1)

    def _handle_voice_interaction(self, audio_data: bytes):
        """Orchestrate STT -> LLM -> TTS with fallbacks"""
        try:
            # 1. STT
            text = self.fallback_manager.execute_with_fallback(
                self._run_stt,
                ["primary_stt", "fallback_stt"], # Example chain
                audio_data=audio_data
            )
            
            if not text:
                return

            self.struct_logger.info("stt_result", f"Recognized: {text}")
            
            # 2. LLM (Placeholder)
            response_text = f"Echo: {text}" 
            
            # 3. TTS
            audio_out = self.fallback_manager.execute_with_fallback(
                self._run_tts,
                ["primary_tts", "fallback_tts"],
                text=response_text
            )
            
            # Play audio (Placeholder)
            self.status = VoicePipelineStatus.SPEAKING
            self.struct_logger.info("tts_complete", "Playing response audio")
            
        except Exception as e:
            self.struct_logger.error("interaction_failed", f"Voice interaction failed: {e}")
        finally:
            self.status = VoicePipelineStatus.LISTENING

    def _run_stt(self, audio_data: bytes, model_id: str) -> str:
        """Run STT with specific model"""
        # Placeholder implementation
        if model_id == "primary_stt":
            # Simulate occasional failure
            # if random.random() < 0.1: raise Exception("STT Timeout")
            return "Hello world"
        return "Hello world (fallback)"

    def _run_tts(self, text: str, model_id: str) -> bytes:
        """Run TTS with specific model"""
        return b"audio_data"

# Singleton
_voice_pipeline: Optional[VoicePipeline] = None

def get_voice_pipeline() -> VoicePipeline:
    global _voice_pipeline
    if _voice_pipeline is None:
        _voice_pipeline = VoicePipeline()
    return _voice_pipeline
