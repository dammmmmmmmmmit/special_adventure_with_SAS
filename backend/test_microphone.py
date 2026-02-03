"""
Microphone Diagnostic Test
This will help diagnose why Azure STT isn't hearing your microphone
"""
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from pathlib import Path
import os
import time

# Load .env from parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

print("=" * 60)
print("🔍 MICROPHONE DIAGNOSTIC TEST")
print("=" * 60)
print()

# Step 1: Check if we can access the microphone at all
print("STEP 1: Testing microphone access...")
print("-" * 40)

try:
    # Try using pyaudio to check microphone
    import pyaudio
    p = pyaudio.PyAudio()
    
    print(f"PyAudio version: {pyaudio.get_portaudio_version_text()}")
    print(f"Default input device: {p.get_default_input_device_info()['name']}")
    
    # List all input devices
    print("\nAvailable input devices:")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print(f"  [{i}] {dev['name']} (channels: {dev['maxInputChannels']})")
    
    # Try to record a short sample
    print("\n🎤 Recording 2 seconds of audio...")
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024
    )
    
    frames = []
    for _ in range(int(16000 / 1024 * 2)):  # 2 seconds
        data = stream.read(1024)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Calculate audio level
    import struct
    all_data = b''.join(frames)
    samples = struct.unpack(f'{len(all_data)//2}h', all_data)
    max_amplitude = max(abs(s) for s in samples)
    avg_amplitude = sum(abs(s) for s in samples) / len(samples)
    
    print(f"✅ Recording successful!")
    print(f"   Max amplitude: {max_amplitude} (should be > 500 if you spoke)")
    print(f"   Avg amplitude: {avg_amplitude:.0f}")
    
    if max_amplitude < 100:
        print("\n⚠️  WARNING: Very low audio level detected!")
        print("   - Check if your microphone is muted")
        print("   - Check microphone volume in Windows Sound Settings")
        print("   - Try speaking louder")
    elif max_amplitude < 500:
        print("\n⚠️  WARNING: Audio level is low")
        print("   - Try speaking closer to the microphone")
        print("   - Increase microphone volume in Windows Settings")
    else:
        print("\n✅ Audio levels look good!")
    
except ImportError:
    print("⚠️  PyAudio not installed. Installing...")
    print("   Run: pip install pyaudio")
    print("   Then run this test again.")
    print()
    print("   If PyAudio fails to install, try:")
    print("   pip install pipwin")
    print("   pipwin install pyaudio")
except Exception as e:
    print(f"❌ Microphone error: {e}")
    print()
    print("   This might indicate a driver or permission issue.")

print()
print("-" * 40)
print("STEP 2: Testing Azure STT with longer timeout...")
print("-" * 40)
print()

# Create speech config
speech_config = speechsdk.SpeechConfig(
    subscription=AZURE_SPEECH_KEY,
    region=AZURE_SPEECH_REGION
)
speech_config.speech_recognition_language = "en-US"

# Set timeout properties
speech_config.set_property(
    speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, 
    "10000"  # 10 seconds
)
speech_config.set_property(
    speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, 
    "3000"  # 3 seconds
)

# Use default microphone
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

# Create recognizer
recognizer = speechsdk.SpeechRecognizer(
    speech_config=speech_config,
    audio_config=audio_config
)

print("🎤 Please say something clearly (e.g., 'Hello, can you hear me?')")
print("   Listening for up to 15 seconds...")
print()

# Set up event handlers
def on_recognizing(evt):
    print(f"   [Partial] {evt.result.text}")

def on_session_started(evt):
    print(f"   [Session started] {evt.session_id}")

def on_session_stopped(evt):
    print(f"   [Session stopped]")

recognizer.recognizing.connect(on_recognizing)
recognizer.session_started.connect(on_session_started)
recognizer.session_stopped.connect(on_session_stopped)

# Recognize
result = recognizer.recognize_once_async().get()

print()
if result.reason == speechsdk.ResultReason.RecognizedSpeech:
    print(f"✅ SUCCESS! Recognized: '{result.text}'")
    print("\n🎉 Your microphone is working with Azure STT!")
elif result.reason == speechsdk.ResultReason.NoMatch:
    details = result.no_match_details
    print(f"❌ No speech recognized")
    print(f"   Reason: {details.reason}")
    print()
    print("   Possible causes:")
    print("   - Microphone volume too low")
    print("   - Background noise too high")
    print("   - Speaking too quietly")
    print("   - Wrong microphone selected in Windows")
elif result.reason == speechsdk.ResultReason.Canceled:
    cancellation = result.cancellation_details
    print(f"❌ Canceled: {cancellation.reason}")
    if cancellation.reason == speechsdk.CancellationReason.Error:
        print(f"   Error: {cancellation.error_details}")

print()
print("=" * 60)
