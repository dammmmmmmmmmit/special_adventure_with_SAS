import asyncio
import websockets
from config.settings import settings
from websocket.handlers import AudioMessageHandler

async def handle_client(websocket):
    """Handle new WebSocket connection"""
    print(f"New connection from {websocket.remote_address}")
    
    handler = AudioMessageHandler(websocket)
    await handler.handle_connection()
    
    print(f"Connection closed from {websocket.remote_address}")

async def main():
    """Start the WebSocket server"""
    print(f"Starting voice agent server on ws://{settings.WS_HOST}:{settings.WS_PORT}")
    
    async with websockets.serve(
        handle_client,
        settings.WS_HOST,
        settings.WS_PORT,
        max_size=10 * 1024 * 1024,  # 10MB max message size for audio
        ping_interval=20,
        ping_timeout=10
    ):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped")