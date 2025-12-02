"""
Text-to-Speech Service
Offline: pyttsx3
Cloud fallback: Google/OpenAI (stub)
"""

import os
import io
import logging
import tempfile
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TTSService:
    """
    Text-to-Speech service with offline and cloud support
    """
    
    def __init__(self):
        self.engine = None
        self.is_initialized = False
        self.voices = {}
    
    async def initialize(self):
        """Initialize TTS service"""
        try:
            # Initialize pyttsx3
            await self._init_pyttsx3()
            self.is_initialized = True
            logger.info("✅ TTS Service initialized (pyttsx3)")
        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")
            self.is_initialized = False
    
    async def _init_pyttsx3(self):
        """Initialize pyttsx3 for offline TTS"""
        try:
            import pyttsx3
            
            self.engine = pyttsx3.init()
            
            # Configure voice properties
            self.engine.setProperty('rate', 175)  # Speed
            self.engine.setProperty('volume', 0.9)  # Volume
            
            # Get available voices
            voices = self.engine.getProperty('voices')
            
            # Categorize voices
            for voice in voices:
                voice_name = voice.name.lower()
                if 'female' in voice_name or 'zira' in voice_name:
                    self.voices['female'] = voice.id
                elif 'male' in voice_name or 'david' in voice_name:
                    self.voices['male'] = voice.id
            
            # Set default voice
            if self.voices:
                self.engine.setProperty('voice', list(self.voices.values())[0])
            
            logger.info(f"Available voices: {list(self.voices.keys())}")
            
        except ImportError:
            logger.error("pyttsx3 not installed. Install with: pip install pyttsx3")
            raise
        except Exception as e:
            logger.error(f"pyttsx3 initialization error: {e}")
            raise
    
    def is_ready(self) -> bool:
        """Check if service is ready"""
        return self.is_initialized and self.engine is not None
    
    async def synthesize(
        self,
        text: str,
        voice: str = "default"
    ) -> bytes:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            voice: Voice to use (male/female/default)
        
        Returns:
            Audio data as bytes (WAV format)
        """
        if not self.is_ready():
            logger.warning("TTS not ready, using cloud fallback")
            return await self._synthesize_cloud(text, voice)
        
        try:
            return await self._synthesize_pyttsx3(text, voice)
        except Exception as e:
            logger.error(f"pyttsx3 synthesis failed: {e}")
            return await self._synthesize_cloud(text, voice)
    
    async def _synthesize_pyttsx3(self, text: str, voice: str) -> bytes:
        """
        Synthesize using pyttsx3 (offline)
        """
        try:
            # Set voice if specified
            if voice in self.voices:
                self.engine.setProperty('voice', self.voices[voice])
            
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Save to file
            self.engine.save_to_file(text, temp_path)
            self.engine.runAndWait()
            
            # Read file
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up
            os.unlink(temp_path)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"pyttsx3 synthesis error: {e}")
            raise
    
    async def _synthesize_cloud(self, text: str, voice: str) -> bytes:
        """
        Synthesize using cloud API (stub)
        
        TODO: Implement Google TTS or OpenAI TTS API
        """
        logger.info("Cloud TTS called (stub)")
        
        # TODO: Implement cloud API
        # Example with Google Cloud TTS:
        # from google.cloud import texttospeech
        # client = texttospeech.TextToSpeechClient()
        # synthesis_input = texttospeech.SynthesisInput(text=text)
        # voice = texttospeech.VoiceSelectionParams(
        #     language_code="en-US",
        #     name="en-US-Neural2-F"
        # )
        # audio_config = texttospeech.AudioConfig(
        #     audio_encoding=texttospeech.AudioEncoding.LINEAR16
        # )
        # response = client.synthesize_speech(
        #     input=synthesis_input,
        #     voice=voice,
        #     audio_config=audio_config
        # )
        # return response.audio_content
        
        # Return empty audio for stub
        return b''
    
    def set_voice(self, voice: str):
        """
        Set voice for synthesis
        
        Args:
            voice: Voice name (male/female)
        """
        if self.engine and voice in self.voices:
            self.engine.setProperty('voice', self.voices[voice])
            logger.info(f"Voice set to: {voice}")
    
    def set_rate(self, rate: int):
        """
        Set speech rate
        
        Args:
            rate: Words per minute (100-300)
        """
        if self.engine:
            self.engine.setProperty('rate', rate)
            logger.info(f"Speech rate set to: {rate}")
    
    def set_volume(self, volume: float):
        """
        Set volume
        
        Args:
            volume: Volume level (0.0-1.0)
        """
        if self.engine:
            self.engine.setProperty('volume', volume)
            logger.info(f"Volume set to: {volume}")
