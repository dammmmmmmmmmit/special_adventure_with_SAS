import numpy as np
from typing import Tuple

class AudioProcessor:
    """Audio processing utilities"""
    
    @staticmethod
    def pcm_to_float32(pcm_bytes: bytes, sample_rate: int = 16000) -> np.ndarray:
        """Convert PCM bytes to float32 numpy array"""
        audio_array = np.frombuffer(pcm_bytes, dtype=np.int16)
        return audio_array.astype(np.float32) / 32768.0
    
    @staticmethod
    def float32_to_pcm(audio_array: np.ndarray) -> bytes:
        """Convert float32 numpy array to PCM bytes"""
        pcm_array = (audio_array * 32768).astype(np.int16)
        return pcm_array.tobytes()
    
    @staticmethod
    def resample(audio: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
        """Resample audio to target sample rate"""
        if orig_rate == target_rate:
            return audio
        
        # Simple linear interpolation resampling
        duration = len(audio) / orig_rate
        target_length = int(duration * target_rate)
        
        indices = np.linspace(0, len(audio) - 1, target_length)
        return np.interp(indices, np.arange(len(audio)), audio)
    
    @staticmethod
    def calculate_rms(audio: np.ndarray) -> float:
        """Calculate RMS (loudness) of audio"""
        return np.sqrt(np.mean(audio ** 2))
    
    @staticmethod
    def detect_silence(audio: np.ndarray, threshold: float = 0.01) -> bool:
        """Detect if audio is silence"""
        return AudioProcessor.calculate_rms(audio) < threshold