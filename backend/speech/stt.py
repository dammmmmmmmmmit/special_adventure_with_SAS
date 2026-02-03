import azure.cognitiveservices.speech as speechsdk
from typing import Callable, Optional
import asyncio
import threading
from config.settings import settings

class AzureSTT:
    def __init__(self, on_recognized: Callable, on_recognizing: Optional[Callable] = None):
        """
        Initialize Azure Speech-to-Text with callbacks
        
        Args:
            on_recognized: Callback for final recognized text
            on_recognizing: Optional callback for partial results
        """
        print(f"[STT] Initializing with region: {settings.AZURE_SPEECH_REGION}")
        print(f"[STT] Key starts with: {settings.AZURE_SPEECH_KEY[:10]}...")
        
        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION
        )
        
        # Set speech recognition language
        self.speech_config.speech_recognition_language = "en-US"
        
        # Enable detailed logging
        self.speech_config.set_property(
            speechsdk.PropertyId.Speech_LogFilename, 
            "azure_stt.log"
        )
        
        # Setup audio stream with explicit format (16kHz, 16-bit, mono PCM)
        audio_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=16000,
            bits_per_sample=16,
            channels=1
        )
        self.push_stream = speechsdk.audio.PushAudioInputStream(stream_format=audio_format)
        self.audio_config = speechsdk.audio.AudioConfig(stream=self.push_stream)
        
        # Create recognizer
        self.recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=self.audio_config
        )
        
        # Store callbacks and event loop
        self.on_recognized_callback = on_recognized
        self.on_recognizing_callback = on_recognizing
        self.loop = None
        
        # Connect callbacks
        self.recognizer.recognized.connect(self._handle_recognized)
        self.recognizer.recognizing.connect(self._handle_recognizing)
        self.recognizer.canceled.connect(self._handle_canceled)
        self.recognizer.session_started.connect(self._handle_session_started)
        self.recognizer.session_stopped.connect(self._handle_session_stopped)
        
        # For session management
        self.is_running = False
        self.bytes_pushed = 0
    
    def _handle_session_started(self, evt):
        """Handle session start"""
        print(f"[STT] Session started: {evt.session_id}")
    
    def _handle_session_stopped(self, evt):
        """Handle session stop"""
        print(f"[STT] Session stopped: {evt.session_id}")
    
    def _handle_canceled(self, evt):
        """Handle cancellation/errors"""
        cancellation = evt.result.cancellation_details
        print(f"[STT] CANCELED: Reason={cancellation.reason}")
        if cancellation.reason == speechsdk.CancellationReason.Error:
            print(f"[STT] ERROR: Code={cancellation.error_code}")
            print(f"[STT] ERROR: Details={cancellation.error_details}")
            print("[STT] Did you set the speech resource key and region values correctly?")
    
    def _handle_recognized(self, evt):
        """Handle final recognition results"""
        print(f"[STT] Recognition event: reason={evt.result.reason}")
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            text = evt.result.text
            print(f"[STT] RECOGNIZED: '{text}'")
            if text and self.on_recognized_callback:
                # Schedule the async callback on the event loop
                if self.loop and self.loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.on_recognized_callback(text), 
                        self.loop
                    )
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            print(f"[STT] No speech could be recognized")
    
    def _handle_recognizing(self, evt):
        """Handle partial recognition results"""
        text = evt.result.text
        if text:
            print(f"[STT] Recognizing: '{text}'")
            if self.on_recognizing_callback:
                if self.loop and self.loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.on_recognizing_callback(text), 
                        self.loop
                    )
    
    def start(self):
        """Start continuous recognition"""
        if not self.is_running:
            # Get the current event loop
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                self.loop = asyncio.get_event_loop()
            
            print("[STT] Starting continuous recognition...")
            self.recognizer.start_continuous_recognition()
            self.is_running = True
            print("[STT] Recognition started, waiting for audio...")
    
    def stop(self):
        """Stop recognition"""
        if self.is_running:
            print(f"[STT] Stopping... (pushed {self.bytes_pushed} bytes total)")
            self.recognizer.stop_continuous_recognition()
            self.push_stream.close()
            self.is_running = False
    
    def push_audio(self, audio_bytes: bytes):
        """Push audio data to the recognizer"""
        if self.is_running:
            self.bytes_pushed += len(audio_bytes)
            self.push_stream.write(audio_bytes)