import azure.cognitiveservices.speech as speechsdk
from typing import AsyncGenerator, Optional
import asyncio
from config.settings import settings

class AzureTTS:
    def __init__(self, voice_name: str = "en-US-JennyNeural"):
        """
        Initialize Azure Text-to-Speech
        
        Args:
            voice_name: Azure Neural Voice name
        """
        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION
        )
        
        # Use raw PCM for lowest latency
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm
        )
        
        # Set voice
        self.speech_config.speech_synthesis_voice_name = voice_name
        
        # Create synthesizer without audio output (we'll handle the stream)
        self.synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=None
        )
    
    async def synthesize_text(self, text: str) -> Optional[bytes]:
        """
        Synthesize text to audio bytes
        
        Returns:
            Raw PCM audio bytes or None if failed
        """
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.synthesizer.speak_text_async(text).get()
        )
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        else:
            print(f"TTS failed: {result.reason}")
            return None
    
    async def synthesize_stream(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesis for chunks of text
        Optimized for sentence-level streaming
        """
        buffer = ""
        
        async for chunk in text_stream:
            buffer += chunk
            
            # Check for sentence boundaries
            if any(p in chunk for p in ['.', '!', '?', '\n']):
                # Synthesize complete sentence
                if buffer.strip():
                    audio_data = await self.synthesize_text(buffer)
                    if audio_data:
                        yield audio_data
                buffer = ""
        
        # Handle remaining text
        if buffer.strip():
            audio_data = await self.synthesize_text(buffer)
            if audio_data:
                yield audio_data