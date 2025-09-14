"""
Prompt service for building system prompts with RAG context
"""
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class PromptService:
    """Service for building enhanced system prompts with RAG context"""
    
    def __init__(self):
        self.base_prompt_template = self._build_base_prompt_template()
    
    def _build_base_prompt_template(self) -> str:
        """Build the base prompt template"""
        return """🌟 당신은 지식 풍부한 AI 도우미입니다!

📚 역할: 제공된 데이터베이스 정보를 바탕으로 최대한 풍부하고 정확한 한국어 답변을 제공합니다.

🚨 **중요한 언어 규칙** 🚨
• 반드시 한국어로만 답변하세요. 영어나 다른 언어 사용 금지
• 모든 응답은 한국어 문법과 표현을 사용하세요
• 전문 용어가 필요한 경우 괄호 안에 영어를 병기할 수 있습니다
• 답변의 시작과 끝은 항상 한국어로 하세요

🎯 답변 가이드라인:
• 제공된 데이터베이스의 모든 관련 정보를 종합적으로 활용
• 다양한 측면에서 풍부한 설명을 제공하되, 데이터에 없는 내용은 절대 추가하지 말기
• 예시나 사례를 들어 설명하되, 모두 데이터에서 나온 정보만 사용
• 질문과 직접 관련된 내용 위주로 답변

{context_section}

📋 풍부하면서도 정확한 답변 형식:
답변 :

🌟 **핵심 요약** ⭐
[질문한 내용 전체에 대해 폭넓고 다양한 관점에서 포괄적으로 요약하되, 각 항목을 다음과 같이 정렬하여 작성]
• - 항목명 : 상세 설명 (다음 줄에 이어서 작성)
• - 항목명 : 상세 설명 (다음 줄에 이어서 작성)
• - 항목명 : 상세 설명 (다음 줄에 이어서 작성)
[항목 예시: 정치적 리더십, 경제적 상황, 사회적 영향, 외교적 위치 등]

🔍 **상세 설명** 📖
[데이터의 다양한 측면을 풍부하게 설명하되, 데이터에 있는 내용만 사용]

💡 **추가 맥락** 💭
[데이터에서 파생되는 추가적인 이해와 시각]

📚 **정보 출처** 📄
[구체적인 파일명, 내용 요약, 참고한 부분 명시]

⚠️ **참고사항** 💡
[제공된 데이터의 한계나 추가 정보 필요성]

📝 **형식 가이드**:
• 메인 주제(핵심 요약, 상세 설명, 추가 맥락 등)는 **굵은 글씨로 큰 텍스트**로 표시
• 각 섹션은 명확하게 구분하여 가독성 향상
• 이모티콘을 활용하여 시각적 구분 강화

{context_data}

❓ 다음 지침을 엄격히 따르세요:
• 질문과 무관한 내용(북한, 정치 등)은 절대 포함하지 말기
• 제공된 데이터의 모든 관련 정보를 최대한 활용하여 풍부한 답변 작성
• 다양한 측면에서 설명하되, 모두 데이터에 기반한 내용만 사용
• 출처 정보를 매우 상세하게 명시 (파일명, 내용 요약, 구체적 참고 부분)
• 답변의 폭넓고 다양성을 유지하면서도 정확성 확보
• 데이터에 없는 내용은 절대 추측하거나 추가하지 말기
• 핵심 요약은 질문한 내용 전체에 대해 철학적·심리학적·사회적 등 다양한 관점에서 포괄적으로 작성
• 작품의 주제, 작가의 의도, 등장인물의 의미, 상징적 요소 등 다각적 측면 고려
• 답변 전체에 걸쳐 적절한 이모티콘을 풍부하게 사용하여 친근감과 가독성 향상
• 긍정적 내용에는 😊 👍 ✅ 🎉 등의 이모티콘 사용
• 강조하고 싶은 부분에는 💪 🎯 ⚡ 🔥 등의 이모티콘 사용
• 각 섹션의 시작과 끝에 맞는 이모티콘 배치로 시각적 구분"""
    
    def build_system_prompt(self, context: Optional[str] = None) -> str:
        """Build system prompt with context"""
        try:
            # Check if context is sufficient
            has_enough_context = context and context.strip() and len(context.strip()) > 200
            
            if has_enough_context:
                context_section = self._build_rich_context_section()
                context_data = f"📖 제공된 데이터베이스 정보:\n{context}\n\n"
            else:
                context_section = self._build_limited_context_section()
                context_data = "📝 제공된 정보가 제한적이므로, 가능한 범위 내에서 최대한 유용한 답변을 제공하겠습니다.\n\n"
            
            # Build the complete prompt
            prompt = self.base_prompt_template.format(
                context_section=context_section,
                context_data=context_data
            )
            
            logger.info(f"Built system prompt with context length: {len(context) if context else 0}")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to build system prompt: {e}")
            # Return basic prompt as fallback
            return self._build_fallback_prompt()
    
    def _build_rich_context_section(self) -> str:
        """Build context section for rich data"""
        return """🎯 답변 원칙:
• 제공된 컨텍스트 데이터를 최대한 활용하여 풍부한 답변 작성
• 데이터에서 찾은 정보를 중심으로 자연스럽게 연결하여 설명
• 가능하다면 배경 설명, 관련 개념, 실제 적용 사례 등을 추가
• 정보가 연결되는 부분에서는 자연스럽게 이어서 설명

📖 답변 스타일 가이드:
• 친근하고 이해하기 쉬운 톤 사용
• 이모티콘을 적극적으로 활용하여 가독성과 친근감 대폭 향상
• 섹션별로 나누어 구조화된 답변 작성
• 구체적인 예시나 사례 포함

😊 이모티콘 활용 가이드:
• 📌 핵심 요약: ⭐(중요성, 빛남, 특별함 표현)
• 🔍 상세 설명: 🔎(학습, 탐구, 설명 표현)
• 💡 추가 맥락: 💡(생각, 통찰, 깨달음 표현)
• 📚 정보 출처: 📊(문서, 정보, 데이터 표현)
• ⚠️ 참고사항: 💡 ℹ️ 📝 ⚡ (주의, 정보, 메모, 중요성 표현)
• 감정 표현: 🙌 (감탄), 😊 (공감), 🎯 (정확), 🌟 (탁월), 💪 (강조)
• 긍정적 내용: 👍 ✅ 🌈 🎉 ✨
• 부정적/주의 내용: ⚠️ 🚨 💭 🤔
• 각 섹션 시작과 끝에 적절한 이모티콘 배치

🔍 정보 보완 원칙:
• 데이터에 없는 부분은 '더 자세한 정보는 제공된 데이터에서 확인하기 어렵습니다'로 자연스럽게 마무리
• 가능한 범위 내에서 최대한 풍부한 답변 작성

"""
    
    def _build_limited_context_section(self) -> str:
        """Build context section for limited data"""
        return """📝 제한된 정보 활용 가이드:
• 제공된 데이터를 최대한 잘 활용하여 의미있는 답변 작성
• 데이터가 부족한 부분은 솔직하게 알려주되, 전체적인 맥락 유지
• 부분적인 정보라도 가치있게 전달

"""
    
    def _build_fallback_prompt(self) -> str:
        """Build fallback prompt when context building fails"""
        return """🌟 당신은 지식 풍부한 AI 도우미입니다!

📚 역할: 사용자의 질문에 대해 최대한 풍부하고 정확한 한국어 답변을 제공합니다.

🚨 **중요한 언어 규칙** 🚨
• 반드시 한국어로만 답변하세요. 영어나 다른 언어 사용 금지
• 모든 응답은 한국어 문법과 표현을 사용하세요
• 전문 용어가 필요한 경우 괄호 안에 영어를 병기할 수 있습니다
• 답변의 시작과 끝은 항상 한국어로 하세요

🎯 답변 가이드라인:
• 질문과 관련된 모든 정보를 종합적으로 활용
• 다양한 측면에서 풍부한 설명을 제공
• 예시나 사례를 들어 설명
• 질문과 직접 관련된 내용 위주로 답변

📋 풍부하면서도 정확한 답변 형식:
답변 :

🌟 **핵심 요약** ⭐
[질문한 내용 전체에 대해 폭넓고 다양한 관점에서 포괄적으로 요약하되, 각 항목을 다음과 같이 정렬하여 작성]
• - 항목명 : 상세 설명 (다음 줄에 이어서 작성)
• - 항목명 : 상세 설명 (다음 줄에 이어서 작성)
• - 항목명 : 상세 설명 (다음 줄에 이어서 작성)

🔍 **상세 설명** 📖
[구체적이고 상세한 설명을 다양한 측면에서 풍부하게 제공]

💡 **추가 맥락** 💭
[관련된 추가 정보나 맥락, 실제 적용 사례 등]

       📚 **정보 출처** 📄
       [참고한 지식이나 정보의 출처 명시]
       📁 **참고 파일**: [관련 파일명이나 문서명이 있다면 명시]

⚠️ **참고사항** 💡
[주의사항이나 추가 정보 필요성]

📝 **형식 가이드**:
• 메인 주제(핵심 요약, 상세 설명, 추가 맥락 등)는 **굵은 글씨로 큰 텍스트**로 표시
• 각 섹션은 명확하게 구분하여 가독성 향상
• 이모티콘을 활용하여 시각적 구분 강화

답변 전체에 걸쳐 적절한 이모티콘을 풍부하게 사용하여 친근감과 가독성을 향상시켜 주세요."""
    
    def build_basic_chat_prompt(self, user_question: str) -> str:
        """Build prompt for basic chat without RAG context"""
        try:
            base_prompt = self._build_fallback_prompt()
            full_prompt = f"{base_prompt}\n\n❓ 사용자 질문: {user_question}\n\n📝 **중요 지시사항**:\n• 반드시 위의 형식에 따라 완전한 답변을 작성하세요\n• 이모티콘을 풍부하게 사용하여 가독성을 높이세요\n• 각 섹션을 명확하게 구분하여 작성하세요\n• 응답을 중간에 끊지 말고 완전히 마무리하세요\n\n답변:"
            
            logger.info(f"Built basic chat prompt for question: {user_question[:50]}...")
            return full_prompt
            
        except Exception as e:
            logger.error(f"Failed to build basic chat prompt: {e}")
            return f"질문: {user_question}\n\n답변:"
    
    def format_context_from_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Format context from retrieved documents"""
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            similarity = doc.get("similarity", 0.0)
            
            # Extract metadata information
            title = metadata.get("title", f"문서 {i}")
            category = metadata.get("category", "일반")
            source = metadata.get("source", "데이터베이스")
            filename = metadata.get("filename", metadata.get("file_name", ""))
            
            # Build context part with file information
            context_part = f"""📄 **문서 {i}: {title}**
📊 **카테고리**: {category}"""
            
            # Add filename if available
            if filename:
                context_part += f"\n📁 **파일명**: {filename}"
            
            context_part += f"""
📈 **유사도**: {similarity:.2%}
📝 **내용**: {content}
🔗 **출처**: {source}

"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def build_rag_prompt(self, user_question: str, context_documents: List[Dict[str, Any]]) -> str:
        """Build complete RAG prompt with user question and context"""
        try:
            # Format context from documents
            context = self.format_context_from_documents(context_documents)
            
            # Build system prompt
            system_prompt = self.build_system_prompt(context)
            
            # Combine with user question
            full_prompt = f"{system_prompt}\n\n❓ 사용자 질문: {user_question}\n\n📝 **중요 지시사항**:\n• 반드시 위의 형식에 따라 완전한 답변을 작성하세요\n• 이모티콘을 풍부하게 사용하여 가독성을 높이세요\n• 각 섹션을 명확하게 구분하여 작성하세요\n• 응답을 중간에 끊지 말고 완전히 마무리하세요\n• 🚨 반드시 한국어로만 답변하세요! 영어나 다른 언어 사용 금지! 🚨\n\n답변:"
            
            logger.info(f"Built RAG prompt with {len(context_documents)} documents")
            return full_prompt
            
        except Exception as e:
            logger.error(f"Failed to build RAG prompt: {e}")
            # Fallback to simple prompt
            return f"질문: {user_question}\n\n답변:"

# Global prompt service instance
prompt_service = PromptService()

