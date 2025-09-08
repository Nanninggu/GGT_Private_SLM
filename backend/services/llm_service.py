"""
LLM Service for Exaone 3.5 2.4 integration
"""
import time
from typing import List, Optional
from backend.models.chat import ChatMessage, ModelResponse, MessageRole
from backend.config.settings import settings

class ExaoneLLMService:
    """Service for interacting with Exaone 3.5 2.4 model"""

    def __init__(self):
        self.model_name = settings.MODEL_NAME
        self.model_path = settings.MODEL_PATH
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        # TODO: Initialize actual Exaone model here
        # self.model = load_exaone_model(self.model_path)

    def generate_response(self, messages: List[ChatMessage]) -> ModelResponse:
        """Generate response using Exaone model"""
        start_time = time.time()

        # Convert messages to model format
        formatted_messages = self._format_messages(messages)

        # TODO: Replace with actual Exaone model inference
        # response = self.model.generate(
        #     formatted_messages,
        #     max_tokens=self.max_tokens,
        #     temperature=self.temperature
        # )

        # Placeholder response (replace with actual model call)
        response_content = f"안녕하세요! Exaone 3.5 2.4 모델을 사용한 응답입니다. 질문: {messages[-1].content if messages else ''}"
        tokens_used = len(response_content.split())

        response_time = time.time() - start_time

        return ModelResponse(
            content=response_content,
            tokens_used=tokens_used,
            response_time=response_time,
            model_name=self.model_name
        )

    def _format_messages(self, messages: List[ChatMessage]) -> str:
        """Format messages for model input"""
        formatted = ""
        for msg in messages:
            role = "사용자" if msg.role == MessageRole.USER else "어시스턴트"
            formatted += f"{role}: {msg.content}\n"
        return formatted

    def validate_model(self) -> bool:
        """Validate that the model is loaded and working"""
        try:
            # TODO: Add actual model validation
            return True
        except Exception as e:
            print(f"Model validation failed: {e}")
            return False
