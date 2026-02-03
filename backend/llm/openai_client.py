from openai import AsyncOpenAI
from typing import AsyncGenerator, List, Dict, Optional
import json
from config.settings import settings

class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        
        # System prompt for voice assistant
        self.system_prompt = """You are a helpful voice assistant. 
        Keep your responses concise and conversational. 
        Avoid using markdown, bullet points, or special formatting.
        Speak naturally as if in a conversation."""
    
    async def generate_response(
        self, 
        user_input: str,
        context: Optional[Dict] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Generate LLM response with streaming
        
        Args:
            user_input: User's transcribed speech
            context: Optional context from database/previous turns
            stream: Whether to stream the response
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add context if available
        if context:
            context_str = f"Context: {json.dumps(context)}"
            messages.append({"role": "system", "content": context_str})
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
                temperature=0.7,
                max_tokens=150  # Keep responses concise for voice
            )
            
            if stream:
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield response.choices[0].message.content
                
        except Exception as e:
            print(f"LLM Error: {e}")
            yield "I'm sorry, I encountered an error processing your request."
    
    async def extract_intent(self, text: str) -> Dict:
        """
        Extract intent from user input using a smaller, faster model
        """
        # For production, use a fine-tuned classification model
        # For now, use simple keyword matching or a fast LLM call
        
        intent_prompt = f"""Extract the intent from this text in JSON format:
        Text: "{text}"
        
        Return only JSON with fields: intent, entities, confidence"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Faster model for intent
                messages=[{"role": "user", "content": intent_prompt}],
                temperature=0,
                max_tokens=100
            )
            
            return json.loads(response.choices[0].message.content)
        except:
            return {"intent": "unknown", "entities": [], "confidence": 0.5}