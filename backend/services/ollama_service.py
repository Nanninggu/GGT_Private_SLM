"""
Ollama service for LLM integration
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
import httpx
import json

from backend.config.settings import settings

logger = logging.getLogger(__name__)

class OllamaService:
    """Ollama service for LLM chat and completion"""
    
    def __init__(self):
        self.client = None
        
    async def initialize(self):
        """Initialize Ollama service"""
        try:
            self.client = httpx.AsyncClient(
                base_url=settings.OLLAMA_BASE_URL,
                timeout=settings.OLLAMA_CHAT_TIMEOUT
            )
            logger.info("Ollama service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama service: {e}")
            raise
    
    async def chat_completion(self, messages: List[Dict[str, str]], model: str = None) -> Dict[str, Any]:
        """Generate chat completion using Ollama"""
        try:
            model = model or settings.MODEL_NAME
            
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)
            
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "options": {
                        "num_ctx": settings.OLLAMA_CHAT_NUM_CTX,
                        "num_predict": settings.OLLAMA_CHAT_NUM_PREDICT,
                        "temperature": settings.OLLAMA_CHAT_TEMPERATURE,
                        "top_p": settings.OLLAMA_CHAT_TOP_P,
                        "top_k": settings.OLLAMA_CHAT_TOP_K,
                        "repeat_penalty": settings.OLLAMA_CHAT_REPEAT_PENALTY
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data.get("response", ""),
                "model": data.get("model", model),
                "done": data.get("done", True),
                "total_duration": data.get("total_duration", 0),
                "load_duration": data.get("load_duration", 0),
                "prompt_eval_count": data.get("prompt_eval_count", 0),
                "prompt_eval_duration": data.get("prompt_eval_duration", 0),
                "eval_count": data.get("eval_count", 0),
                "eval_duration": data.get("eval_duration", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate chat completion: {e}")
            raise
    
    async def generate(self, prompt: str, model: str = None) -> str:
        """Generate text completion using Ollama"""
        try:
            model = model or settings.MODEL_NAME
            
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_ctx": settings.OLLAMA_CHAT_NUM_CTX,
                        "num_predict": settings.OLLAMA_CHAT_NUM_PREDICT,
                        "temperature": settings.OLLAMA_CHAT_TEMPERATURE,
                        "top_p": settings.OLLAMA_CHAT_TOP_P,
                        "top_k": settings.OLLAMA_CHAT_TOP_K,
                        "repeat_penalty": settings.OLLAMA_CHAT_REPEAT_PENALTY
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("response", "")
            
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models"""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            
            return data.get("models", [])
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull model from Ollama registry"""
        try:
            response = await self.client.post(
                "/api/pull",
                json={"name": model_name}
            )
            response.raise_for_status()
            
            logger.info(f"Model {model_name} pulled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check Ollama service health"""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to prompt format with Korean response enforcement"""
        prompt_parts = []
        
        # Add Korean response enforcement at the beginning
        korean_system_prompt = settings.KOREAN_SYSTEM_PROMPT
        
        prompt_parts.append(f"System: {korean_system_prompt}")
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                # Skip if it's already the Korean system prompt
                if "중요한 언어 규칙" not in content:
                    prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts) + "\n\nAssistant:"
    
    async def generate_stream(self, prompt: str, model: str = None) -> AsyncGenerator[str, None]:
        """Generate streaming text completion using Ollama"""
        try:
            model = model or settings.MODEL_NAME
            
            async with self.client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "num_ctx": settings.OLLAMA_CHAT_NUM_CTX,
                        "num_predict": settings.OLLAMA_CHAT_NUM_PREDICT,
                        "temperature": settings.OLLAMA_CHAT_TEMPERATURE,
                        "top_p": settings.OLLAMA_CHAT_TOP_P,
                        "top_k": settings.OLLAMA_CHAT_TOP_K,
                        "repeat_penalty": settings.OLLAMA_CHAT_REPEAT_PENALTY
                    }
                }
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Failed to generate streaming text: {e}")
            yield f"❌ 오류가 발생했습니다: {str(e)}"
    
    async def chat_completion_stream(self, messages: List[Dict[str, str]], model: str = None) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion using Ollama"""
        try:
            model = model or settings.MODEL_NAME
            
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)
            
            async for chunk in self.generate_stream(prompt, model):
                yield chunk
                
        except Exception as e:
            logger.error(f"Failed to generate streaming chat completion: {e}")
            yield f"❌ 오류가 발생했습니다: {str(e)}"
    
    async def close(self):
        """Close Ollama service"""
        if self.client:
            await self.client.aclose()
            logger.info("Ollama service closed")

# Global Ollama service instance
ollama_service = OllamaService()
