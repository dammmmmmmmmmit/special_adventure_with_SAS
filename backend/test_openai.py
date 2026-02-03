"""
Test OpenAI API directly
Run this to verify OpenAI is working with your API key
"""
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env from parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

print("=" * 50)
print("OpenAI API Test")
print("=" * 50)
print(f"Model: {OPENAI_MODEL}")
print(f"Key: {OPENAI_API_KEY[:20]}...")
print()

async def test_openai():
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    print("📤 Sending test message to OpenAI...")
    print()
    
    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Keep your response brief."},
                {"role": "user", "content": "Say 'Hello! OpenAI is working!' and nothing else."}
            ],
            max_tokens=50
        )
        
        reply = response.choices[0].message.content
        print(f"✅ Response: {reply}")
        print("\n✅ OpenAI API is working correctly!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n   Check your OpenAI API key!")

# Run the test
asyncio.run(test_openai())
