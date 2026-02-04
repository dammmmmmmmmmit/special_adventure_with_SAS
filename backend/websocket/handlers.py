import json
import asyncio
from typing import Dict, Any
from speech.stt import AzureSTT
from speech.tts import AzureTTS
from llm.openai_client import LLMClient
from auth.auth import TokenValidator, VoiceBiometric

class AudioMessageHandler:
    def __init__(self, websocket):
        self.websocket = websocket
        self.stt = None
        self.tts = AzureTTS()
        self.llm = LLMClient()
        self.token_validator = TokenValidator()
        self.voice_biometric = VoiceBiometric()
        
        self.user_context = {}
        self.is_processing = False
        self.audio_chunks_received = 0
        
    async def handle_connection(self):
        """Main handler for WebSocket connection"""
        try:
            print("[HANDLER] Starting connection handler...")
            
            # Authenticate user
            auth_success = await self.authenticate()
            if not auth_success:
                print("[HANDLER] Authentication failed!")
                await self.websocket.send(json.dumps({
                    "type": "error",
                    "message": "Authentication failed"
                }))
                return
            
            print(f"[HANDLER] Authentication successful! User: {self.user_context}")
            
            # Initialize STT with callbacks
            print("[HANDLER] Initializing Azure Speech-to-Text...")
            try:
                self.stt = AzureSTT(
                    on_recognized=self.on_text_recognized,
                    on_recognizing=self.on_text_recognizing
                )
                self.stt.start()
                print("[HANDLER] STT started successfully!")
            except Exception as e:
                print(f"[HANDLER] STT initialization failed: {e}")
                await self.websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Speech service failed: {str(e)}"
                }))
                return
            
            # Send ready signal
            await self.websocket.send(json.dumps({"type": "ready"}))
            print("[HANDLER] Sent 'ready' signal to client. Waiting for audio...")
            
            # Process messages
            async for message in self.websocket:
                await self.process_message(message)
                
        except Exception as e:
            print(f"[HANDLER] Connection error: {e}")
        finally:
            print("[HANDLER] Cleaning up connection...")
            if self.stt:
                self.stt.stop()
    
    async def authenticate(self) -> bool:
        """Authenticate the user via token or voice"""
        print("[AUTH] Waiting for authentication message...")
        first_msg = await self.websocket.recv()
        data = json.loads(first_msg)
        print(f"[AUTH] Received: {data}")
        
        if data.get("type") == "auth":
            token = data.get("token")
            
            # For demo/testing: accept demo tokens
            if token == "demo-token":
                self.user_context = {"user_id": "demo-user", "name": "Demo User"}
                print("[AUTH] Demo token accepted!")
                return True
            
            # For production: validate JWT tokens
            user_data = self.token_validator.validate_token(token)
            
            if user_data:
                self.user_context = user_data
                return True
        
        print("[AUTH] Authentication failed - no valid token")
        return False
    
    async def process_message(self, message: str):
        """Process incoming WebSocket messages"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "audio":
                self.audio_chunks_received += 1
                # Convert Int16 audio data to bytes
                # The frontend sends Int16 values as a JSON array
                raw_data = data.get("data", [])
                
                # Convert Int16 array to bytes (little-endian)
                import struct
                audio_bytes = struct.pack(f'<{len(raw_data)}h', *raw_data)
                
                # Log every 10th chunk to avoid spam
                if self.audio_chunks_received % 10 == 0:
                    print(f"[AUDIO] Received {self.audio_chunks_received} audio chunks ({len(audio_bytes)} bytes each)")
                
                # Push to STT
                if self.stt:
                    self.stt.push_audio(audio_bytes)
            
            elif msg_type == "stop":
                print("[HANDLER] Received stop command")
                if self.stt:
                    self.stt.stop()
                    
        except json.JSONDecodeError:
            print("[HANDLER] Invalid message format received")
    
    async def on_text_recognizing(self, text: str):
        """Handle partial recognition results"""
        print(f"[STT PARTIAL] '{text}'")
        # Send partial transcription to client for UI feedback
        await self.websocket.send(json.dumps({
            "type": "partial_transcript",
            "text": text
        }))
    
    async def on_text_recognized(self, text: str):
        """Handle final recognition results"""
        print(f"[STT FINAL] '{text}'")
        
        if self.is_processing:
            print("[STT] Already processing, skipping...")
            return
        
        self.is_processing = True
        
        try:
            # Send final transcript
            await self.websocket.send(json.dumps({
                "type": "final_transcript",
                "text": text
            }))
            
            # Extract intent
            print("[LLM] Extracting intent...")
            intent = await self.llm.extract_intent(text)
            print(f"[LLM] Intent: {intent}")
            
            # Generate and stream response
            print("[LLM] Generating response...")
            async for audio_chunk in self.generate_and_synthesize(text, intent):
                print(f"[TTS] Sending audio chunk ({len(audio_chunk)} bytes)")
                await self.websocket.send(json.dumps({
                    "type": "audio",
                    "data": list(audio_chunk)
                }))
        
        except Exception as e:
            print(f"[ERROR] Processing failed: {e}")
        finally:
            self.is_processing = False
    
    async def generate_and_synthesize(self, text: str, intent: Dict):
        """Generate LLM response and synthesize to audio"""
        # Stream LLM response
        llm_stream = self.llm.generate_response(
            text,
            context={"intent": intent, **self.user_context}
        )
        
        # Stream TTS synthesis
        async for audio_data in self.tts.synthesize_stream(llm_stream):
            yield audio_data