"""
Test Azure Speech-to-Text directly with microphone
Run this to verify Azure STT is working with your API key
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
print("Azure Speech-to-Text Test")
print("=" * 50)
print(f"Region: {AZURE_SPEECH_REGION}")
print(f"Key: {AZURE_SPEECH_KEY[:15]}...")
print()

# Create speech config
speech_config = speechsdk.SpeechConfig(
    subscription=AZURE_SPEECH_KEY,
    region=AZURE_SPEECH_REGION
)
speech_config.speech_recognition_language = "en-US"

# Use default microphone
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

# Create recognizer
recognizer = speechsdk.SpeechRecognizer(
    speech_config=speech_config,
    audio_config=audio_config
)

print("🎤 Speak something into your microphone...")
print("   (Listening for up to 15 seconds)")
print()

# Recognize once (single utterance)
result = recognizer.recognize_once()

# Check result
if result.reason == speechsdk.ResultReason.RecognizedSpeech:
    print(f"✅ RECOGNIZED: '{result.text}'")
    print("\n✅ Azure STT is working correctly!")
elif result.reason == speechsdk.ResultReason.NoMatch:
    print("❌ No speech could be recognized")
    print("   Try speaking more clearly or check your microphone")
elif result.reason == speechsdk.ResultReason.Canceled:
    cancellation = result.cancellation_details
    print(f"❌ CANCELED: {cancellation.reason}")
    if cancellation.reason == speechsdk.CancellationReason.Error:
        print(f"   Error Code: {cancellation.error_code}")
        print(f"   Error Details: {cancellation.error_details}")
        print("\n   Check your Azure Speech key and region!")
