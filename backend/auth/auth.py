import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from config.settings import settings

class TokenValidator:
    def __init__(self):
        self.secret = settings.JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def create_token(self, user_id: str, expiry_hours: int = 24) -> str:
        """Create a new JWT token"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=expiry_hours),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

class VoiceBiometric:
    """Voice fingerprinting for passive authentication"""
    
    def __init__(self):
        self.voice_profiles = {}  # In production, use a database
    
    async def verify_voice(self, audio_data: bytes, user_id: str) -> float:
        """
        Verify voice against stored profile
        Returns confidence score (0.0 to 1.0)
        """
        # TODO: Implement actual voice biometric verification
        # Using Azure Speaker Recognition or similar service
        # For now, return mock confidence
        return 0.95
    
    async def enroll_voice(self, audio_data: bytes, user_id: str):
        """Enroll a new voice profile"""
        # TODO: Implement voice enrollment
        self.voice_profiles[user_id] = audio_data