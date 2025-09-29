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
    
    async def chat_completion(self, messages: List[Dict[str, str]], model: str = None, model_type: str = "fast") -> Dict[str, Any]:
        """Generate chat completion using Ollama with model selection"""
        try:
            # Get model configuration based on model_type
            if model_type in settings.MODEL_CONFIGS:
                model_config = settings.MODEL_CONFIGS[model_type]
                model = model or model_config["model"]
                options = {
                    "num_ctx": model_config["num_ctx"],
                    "num_predict": model_config["num_predict"],
                    "temperature": model_config["temperature"],
                    "top_p": model_config["top_p"],
                    "top_k": model_config["top_k"],
                    "repeat_penalty": model_config["repeat_penalty"],
                    # 메모리 사용량 최적화
                    "num_gpu": 1,  # GPU 사용량 제한
                    "num_thread": 4,  # CPU 스레드 수 제한
                    "low_vram": True,  # 낮은 VRAM 모드
                    "f16_kv": True,  # 16비트 정밀도 사용
                }
            else:
                # Fallback to default settings
                model = model or settings.MODEL_NAME
                options = {
                    "num_ctx": settings.OLLAMA_CHAT_NUM_CTX,
                    "num_predict": settings.OLLAMA_CHAT_NUM_PREDICT,
                    "temperature": settings.OLLAMA_CHAT_TEMPERATURE,
                    "top_p": settings.OLLAMA_CHAT_TOP_P,
                    "top_k": settings.OLLAMA_CHAT_TOP_K,
                    "repeat_penalty": settings.OLLAMA_CHAT_REPEAT_PENALTY,
                    # 메모리 사용량 최적화
                    "num_gpu": 1,  # GPU 사용량 제한
                    "num_thread": 4,  # CPU 스레드 수 제한
                    "low_vram": True,  # 낮은 VRAM 모드
                    "f16_kv": True,  # 16비트 정밀도 사용
                }
            
            # Check if model is available before making the request
            if not await self.check_model_availability(model):
                logger.error(f"Model {model} is not available")
                raise Exception(f"Model {model} is not available. Please check if the model is installed in Ollama.")
            
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)
            
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "options": options
                }
            )
            
            # Better error handling for HTTP 500
            if response.status_code == 500:
                error_text = response.text
                logger.error(f"Ollama HTTP 500 error for model {model}: {error_text}")
                raise Exception(f"Ollama server error (500): {error_text}")
            
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
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500:
                logger.error(f"Ollama server crashed (500): {e.response.text}")
                raise Exception(f"Ollama 서버가 크래시했습니다. 모델 '{model}'이 메모리 부족이나 다른 문제로 인해 종료되었습니다. 더 작은 모델을 사용하거나 시스템 메모리를 확인해주세요.")
            else:
                logger.error(f"Ollama HTTP error {e.response.status_code}: {e.response.text}")
                raise Exception(f"Ollama 서버 오류 ({e.response.status_code}): {e.response.text}")
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Ollama server: {e}")
            raise Exception("Ollama 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        except Exception as e:
            logger.error(f"Failed to generate chat completion: {e}")
            if "aborted (core dumped)" in str(e):
                raise Exception(f"Ollama 모델 '{model}'이 메모리 부족으로 크래시했습니다. 더 작은 모델을 사용하거나 시스템 메모리를 확인해주세요.")
            raise
    
    async def generate(self, prompt: str, model: str = None, model_type: str = "fast") -> str:
        """Generate text completion using Ollama with model selection"""
        try:
            # Get model configuration based on model_type
            if model_type in settings.MODEL_CONFIGS:
                model_config = settings.MODEL_CONFIGS[model_type]
                model = model or model_config["model"]
                options = {
                    "num_ctx": model_config["num_ctx"],
                    "num_predict": model_config["num_predict"],
                    "temperature": model_config["temperature"],
                    "top_p": model_config["top_p"],
                    "top_k": model_config["top_k"],
                    "repeat_penalty": model_config["repeat_penalty"]
                }
            else:
                # Fallback to default settings
                model = model or settings.MODEL_NAME
                options = {
                    "num_ctx": settings.OLLAMA_CHAT_NUM_CTX,
                    "num_predict": settings.OLLAMA_CHAT_NUM_PREDICT,
                    "temperature": settings.OLLAMA_CHAT_TEMPERATURE,
                    "top_p": settings.OLLAMA_CHAT_TOP_P,
                    "top_k": settings.OLLAMA_CHAT_TOP_K,
                    "repeat_penalty": settings.OLLAMA_CHAT_REPEAT_PENALTY,
                    # 메모리 사용량 최적화
                    "num_gpu": 1,  # GPU 사용량 제한
                    "num_thread": 4,  # CPU 스레드 수 제한
                    "low_vram": True,  # 낮은 VRAM 모드
                    "f16_kv": True,  # 16비트 정밀도 사용
                }
            
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": options
                }
            )
            
            # Better error handling for HTTP 500
            if response.status_code == 500:
                error_text = response.text
                logger.error(f"Ollama HTTP 500 error for model {model}: {error_text}")
                raise Exception(f"Ollama server error (500): {error_text}")
            
            response.raise_for_status()
            data = response.json()
            
            return data.get("response", "")
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500:
                logger.error(f"Ollama server crashed (500): {e.response.text}")
                raise Exception(f"Ollama 서버가 크래시했습니다. 모델 '{model}'이 메모리 부족이나 다른 문제로 인해 종료되었습니다. 더 작은 모델을 사용하거나 시스템 메모리를 확인해주세요.")
            else:
                logger.error(f"Ollama HTTP error {e.response.status_code}: {e.response.text}")
                raise Exception(f"Ollama 서버 오류 ({e.response.status_code}): {e.response.text}")
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Ollama server: {e}")
            raise Exception("Ollama 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            if "aborted (core dumped)" in str(e):
                raise Exception(f"Ollama 모델 '{model}'이 메모리 부족으로 크래시했습니다. 더 작은 모델을 사용하거나 시스템 메모리를 확인해주세요.")
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
    
    async def check_model_availability(self, model: str) -> bool:
        """Check if a specific model is available"""
        try:
            models = await self.list_models()
            model_names = [m.get("name", "") for m in models]
            return model in model_names
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
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
    
    async def generate_stream(self, prompt: str, model: str = None, model_type: str = "fast") -> AsyncGenerator[str, None]:
        """Generate streaming text completion using Ollama with model selection"""
        try:
            # Get model configuration based on model_type
            if model_type in settings.MODEL_CONFIGS:
                model_config = settings.MODEL_CONFIGS[model_type]
                model = model or model_config["model"]
                options = {
                    "num_ctx": model_config["num_ctx"],
                    "num_predict": model_config["num_predict"],
                    "temperature": model_config["temperature"],
                    "top_p": model_config["top_p"],
                    "top_k": model_config["top_k"],
                    "repeat_penalty": model_config["repeat_penalty"]
                }
            else:
                # Fallback to default settings
                model = model or settings.MODEL_NAME
                options = {
                    "num_ctx": settings.OLLAMA_CHAT_NUM_CTX,
                    "num_predict": settings.OLLAMA_CHAT_NUM_PREDICT,
                    "temperature": settings.OLLAMA_CHAT_TEMPERATURE,
                    "top_p": settings.OLLAMA_CHAT_TOP_P,
                    "top_k": settings.OLLAMA_CHAT_TOP_K,
                    "repeat_penalty": settings.OLLAMA_CHAT_REPEAT_PENALTY,
                    # 메모리 사용량 최적화
                    "num_gpu": 1,  # GPU 사용량 제한
                    "num_thread": 4,  # CPU 스레드 수 제한
                    "low_vram": True,  # 낮은 VRAM 모드
                    "f16_kv": True,  # 16비트 정밀도 사용
                }
            
            async with self.client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True,
                    "options": options
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
                            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500:
                logger.error(f"Ollama server crashed (500): {e.response.text}")
                yield f"❌ Ollama 서버가 크래시했습니다. 모델 '{model}'이 메모리 부족이나 다른 문제로 인해 종료되었습니다. 더 작은 모델을 사용하거나 시스템 메모리를 확인해주세요."
            else:
                logger.error(f"Ollama HTTP error {e.response.status_code}: {e.response.text}")
                yield f"❌ Ollama 서버 오류 ({e.response.status_code}): {e.response.text}"
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Ollama server: {e}")
            yield f"❌ Ollama 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
        except Exception as e:
            logger.error(f"Failed to generate streaming text: {e}")
            if "aborted (core dumped)" in str(e):
                yield f"❌ Ollama 모델 '{model}'이 메모리 부족으로 크래시했습니다. 더 작은 모델을 사용하거나 시스템 메모리를 확인해주세요."
            else:
                yield f"❌ 오류가 발생했습니다: {str(e)}"
    
    async def chat_completion_stream(self, messages: List[Dict[str, str]], model: str = None, model_type: str = "fast") -> AsyncGenerator[str, None]:
        """Generate streaming chat completion using Ollama with model selection"""
        try:
            # Get model configuration based on model_type
            if model_type in settings.MODEL_CONFIGS:
                model_config = settings.MODEL_CONFIGS[model_type]
                model = model or model_config["model"]
            else:
                model = model or settings.MODEL_NAME
            
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)
            
            async for chunk in self.generate_stream(prompt, model, model_type):
                yield chunk
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500:
                logger.error(f"Ollama server crashed (500): {e.response.text}")
                yield f"❌ Ollama 서버가 크래시했습니다. 모델 '{model}'이 메모리 부족이나 다른 문제로 인해 종료되었습니다. 더 작은 모델을 사용하거나 시스템 메모리를 확인해주세요."
            else:
                logger.error(f"Ollama HTTP error {e.response.status_code}: {e.response.text}")
                yield f"❌ Ollama 서버 오류 ({e.response.status_code}): {e.response.text}"
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Ollama server: {e}")
            yield f"❌ Ollama 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
        except Exception as e:
            logger.error(f"Failed to generate streaming chat completion: {e}")
            if "aborted (core dumped)" in str(e):
                yield f"❌ Ollama 모델 '{model}'이 메모리 부족으로 크래시했습니다. 더 작은 모델을 사용하거나 시스템 메모리를 확인해주세요."
            else:
                yield f"❌ 오류가 발생했습니다: {str(e)}"
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available models with their configurations"""
        try:
            models = await self.list_models()
            available_models = []
            
            for model_info in models:
                model_name = model_info.get("name", "")
                if "exaone3.5" in model_name:
                    # Determine model type based on name
                    if "q8_0" in model_name:
                        model_type = "quality"
                    elif "7.8b" in model_name:
                        model_type = "complex"
                    else:
                        model_type = "fast"
                    
                    # Get configuration
                    if model_type in settings.MODEL_CONFIGS:
                        config = settings.MODEL_CONFIGS[model_type]
                        available_models.append({
                            "name": model_name,
                            "type": model_type,
                            "description": config["description"],
                            "use_case": config["use_case"],
                            "size": model_info.get("size", "Unknown"),
                            "modified": model_info.get("modified", "Unknown")
                        })
            
            return available_models
            
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    async def get_model_config(self, model_type: str) -> Dict[str, Any]:
        """Get configuration for a specific model type"""
        if model_type in settings.MODEL_CONFIGS:
            return settings.MODEL_CONFIGS[model_type]
        else:
            return {
                "model": settings.MODEL_NAME,
                "description": "기본 모델",
                "use_case": "일반적인 사용"
            }
    
    async def close(self):
        """Close Ollama service"""
        if self.client:
            await self.client.aclose()
            logger.info("Ollama service closed")

# Global Ollama service instance
ollama_service = OllamaService()
