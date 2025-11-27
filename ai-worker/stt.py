"""
Speech-to-Text Service
Offline: Vosk
Cloud fallback: Google/OpenAI (stub)
"""

import os
import json
import logging
import wave
import io
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class STTService:
    """
    Speech-to-Text service with offline and cloud support
    """
    
    def __init__(self):
        self.vosk_model = None
        self.recognizer = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize STT service"""
        try:
            # Try to initialize Vosk
            await self._init_vosk()
            self.is_initialized = True
            logger.info("✅ STT Service initialized (Vosk)")
        except Exception as e:
            logger.warning(f"Vosk initialization failed: {e}. Will use cloud fallback.")
            self.is_initialized = True  # Still mark as initialized for cloud fallback
    
    async def _init_vosk(self):
        """
        Initialize Vosk for offline STT
        
        TODO: Download Vosk model if not present
        Models: https://alphacephei.com/vosk/models
        Recommended: vosk-model-small-en-us-0.15 (~40MB)
        """
        try:
            from vosk import Model, KaldiRecognizer
            
            # Check for Vosk model
            model_path = os.path.join(os.path.dirname(__file__), "models", "vosk-model-small-en-us")
            
            if os.path.exists(model_path):
                self.vosk_model = Model(model_path)
                logger.info(f"Loaded Vosk model from {model_path}")
            else:
                logger.warning(f"Vosk model not found at {model_path}")
                logger.info("Download from: https://alphacephei.com/vosk/models")
                logger.info("Extract to: ai-worker/models/vosk-model-small-en-us/")
                self.vosk_model = None
        except ImportError:
            logger.warning("Vosk not installed. Install with: pip install vosk")
            self.vosk_model = None
    
    def is_ready(self) -> bool:
        """Check if service is ready"""
        return self.is_initialized
    
    async def transcribe(self, audio_data: bytes) -> Dict:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Raw audio bytes (WAV format preferred)
        
        Returns:
            dict with text, confidence, and engine used
        """
        # Try Vosk first (offline)
        if self.vosk_model:
            try:
                result = await self._transcribe_vosk(audio_data)
                return result
            except Exception as e:
                logger.error(f"Vosk transcription failed: {e}")
        
        # Fallback to cloud (stub)
        logger.info("Using cloud STT fallback")
        return await self._transcribe_cloud(audio_data)
    
    async def _transcribe_vosk(self, audio_data: bytes) -> Dict:
        """
        Transcribe using Vosk (offline)
        """
        from vosk import KaldiRecognizer
        
        try:
            # Parse WAV file
            with io.BytesIO(audio_data) as audio_file:
                with wave.open(audio_file, 'rb') as wf:
                    # Check format
                    if wf.getnchannels() != 1:
                        raise ValueError("Audio must be mono")
                    if wf.getsampwidth() != 2:
                        raise ValueError("Audio must be 16-bit")
                    
                    sample_rate = wf.getframerate()
                    
                    # Create recognizer
                    rec = KaldiRecognizer(self.vosk_model, sample_rate)
                    rec.SetWords(True)
                    
                    # Process audio
                    while True:
                        data = wf.readframes(4000)
                        if len(data) == 0:
                            break
                        rec.AcceptWaveform(data)
                    
                    # Get final result
                    result = json.loads(rec.FinalResult())
                    
                    return {
                        "text": result.get("text", ""),
                        "confidence": 0.9,  # Vosk doesn't provide confidence
                        "engine": "vosk"
                    }
        except Exception as e:
            logger.error(f"Vosk transcription error: {e}")
            raise
    
    async def _transcribe_cloud(self, audio_data: bytes) -> Dict:
        """
        Transcribe using cloud API (stub)
        
        TODO: Implement Google Speech-to-Text or OpenAI Whisper API
        """
        logger.info("Cloud STT called (stub)")
        
        # TODO: Implement cloud API
        # Example with OpenAI Whisper API:
        # import openai
        # response = openai.Audio.transcribe("whisper-1", audio_data)
        # return {"text": response.text, "confidence": 1.0, "engine": "whisper-api"}
        
        # Stub response
        return {
            "text": "This is a stub transcription. Please configure Vosk or cloud API.",
            "confidence": 1.0,
            "engine": "stub"
        }
    
    async def transcribe_stream(self, audio_stream):
        """
        Transcribe streaming audio (for real-time use)
        
        TODO: Implement streaming transcription
        """
        # TODO: Implement streaming with Vosk
        pass
