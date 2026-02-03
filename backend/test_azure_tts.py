"""
Test Azure Text-to-Speech directly
Run this to verify Azure TTS is working with your API key
"""
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env from parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

print("=" * 50)
print("Azure Text-to-Speech Test")
print("=" * 50)
print(f"Region: {AZURE_SPEECH_REGION}")
print(f"Key: {AZURE_SPEECH_KEY[:15]}...")
print()

# Create speech config
speech_config = speechsdk.SpeechConfig(
    subscription=AZURE_SPEECH_KEY,
    region=AZURE_SPEECH_REGION
)
speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"

# Use default speaker
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

# Create synthesizer
synthesizer = speechsdk.SpeechSynthesizer(
    speech_config=speech_config,
    audio_config=audio_config
)

text = "Hello! Azure Text to Speech is working correctly."
print(f"🔊 Speaking: '{text}'")
print()

# Synthesize
result = synthesizer.speak_text(text)

if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("✅ Azure TTS is working correctly!")
elif result.reason == speechsdk.ResultReason.Canceled:
    cancellation = result.cancellation_details
    print(f"❌ CANCELED: {cancellation.reason}")
    if cancellation.reason == speechsdk.CancellationReason.Error:
        print(f"   Error Code: {cancellation.error_code}")
        print(f"   Error Details: {cancellation.error_details}")
