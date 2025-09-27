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
        return """당신은 전문적이고 신뢰할 수 있는 AI 어시스턴트입니다. 제공된 데이터를 바탕으로 정확하고 유용한 답변을 제공합니다.

**핵심 원칙**:
• 정확성: 제공된 데이터에 기반한 정확한 정보만 제공
• 명확성: 이해하기 쉽고 구조화된 답변 작성
• 완전성: 질문에 대한 포괄적이고 완전한 답변 제공
• 신뢰성: 불확실한 정보는 명확히 표시

{context_section}

**답변 구조**:
📋 **핵심 요약**
질문의 핵심에 대한 간결한 요약 (2-3문장)

📖 **상세 설명**
구체적이고 상세한 설명 (데이터 기반)
• 주요 포인트를 단계별로 설명
• 구체적인 예시나 사례 제시
• 관련된 세부사항 포함

🔍 **추가 정보**
질문과 관련된 추가 맥락이나 배경 정보
• 관련 개념이나 용어 설명
• 실무 적용 방법이나 주의사항
• 다른 관점이나 대안 제시

📚 **참조 정보**
• 참고한 문서: {source_files}
• 신뢰도 점수: {confidence_score}%
• 데이터 출처: {data_sources}

⚠️ **주의사항**
데이터의 한계나 추가 확인이 필요한 사항

{context_data}

**답변 가이드라인**:
• 반드시 한국어로 답변하되 자연스럽게 작성
• 제공된 데이터를 최대한 활용하여 답변
• 데이터에 없는 내용은 "확인된 정보가 없습니다"로 명시
• 각 섹션을 명확하게 구분하여 가독성 향상
• 전문적이면서도 이해하기 쉬운 언어 사용"""
    
    def build_system_prompt(self, context: Optional[str] = None) -> str:
        """Build system prompt with context"""
        try:
            # Check if context is sufficient
            has_enough_context = context and context.strip() and len(context.strip()) > 200
            
            if has_enough_context:
                context_section = self._build_rich_context_section()
                context_data = f"**제공된 데이터베이스 정보**:\n{context}\n\n"
            else:
                context_section = self._build_limited_context_section()
                context_data = "**제공된 정보가 제한적이므로, 가능한 범위 내에서 최대한 유용한 답변을 제공하겠습니다.**\n\n"
            
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
        return """**데이터 활용**: 제공된 컨텍스트를 최대한 활용하여 답변
**스타일**: 명확하고 구조화된 답변 작성
**보완**: 데이터 부족시 '데이터에서 확인하기 어렵습니다'로 마무리

"""
    
    def _build_limited_context_section(self) -> str:
        """Build context section for limited data"""
        return """**제한된 정보**: 제공된 데이터를 최대한 활용하여 답변

"""
    
    def _build_fallback_prompt(self) -> str:
        """Build fallback prompt when context building fails"""
        return """당신은 지식 풍부한 AI 도우미입니다.

**역할**: 사용자의 질문에 대해 정확하고 유용한 한국어 답변을 제공합니다.

**언어 규칙**:
• 반드시 한국어로만 답변하세요
• 모든 응답은 한국어 문법과 표현을 사용하세요
• 전문 용어가 필요한 경우 괄호 안에 영어를 병기할 수 있습니다

**답변 가이드라인**:
• 질문과 관련된 정보를 종합적으로 활용
• 명확하고 이해하기 쉬운 설명을 제공
• 예시나 사례를 들어 설명
• 질문과 직접 관련된 내용 위주로 답변

**답변 형식**:

**핵심 요약**
질문한 내용에 대해 주요 포인트를 정리하여 설명

**상세 설명**
구체적이고 상세한 설명을 제공

**추가 정보**
관련된 추가 정보나 맥락, 실제 적용 사례 등

**정보 출처**
참고한 지식이나 정보의 출처를 명시

**참고사항**
주의사항이나 추가 정보 필요성

답변은 명확하고 구조화된 형태로 작성하되, 과도한 이모티콘 사용은 피하세요."""
    
    def build_basic_chat_prompt(self, user_question: str) -> str:
        """Build prompt for basic chat without RAG context"""
        try:
            base_prompt = self._build_fallback_prompt()
            full_prompt = f"{base_prompt}\n\n**사용자 질문**: {user_question}\n\n**지시사항**:\n• 위의 형식에 따라 완전한 답변을 작성하세요\n• 각 섹션을 명확하게 구분하여 작성하세요\n• 응답을 중간에 끊지 말고 완전히 마무리하세요\n• 과도한 이모티콘 사용은 피하고 깔끔하게 작성하세요\n\n답변:"
            
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
            
            # Extract metadata for prompt
            source_files = []
            confidence_scores = []
            data_sources = []
            
            for doc in context_documents:
                metadata = doc.get("metadata", {})
                filename = metadata.get("filename", metadata.get("file_name", "Unknown"))
                similarity = doc.get("similarity", 0.0)
                source = metadata.get("source", "데이터베이스")
                
                source_files.append(filename)
                confidence_scores.append(similarity)
                data_sources.append(source)
            
            # Calculate average confidence
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            confidence_percent = round(avg_confidence * 100, 1)
            
            # Build enhanced system prompt
            system_prompt = self.build_system_prompt(context)
            
            # Replace placeholders in system prompt
            system_prompt = system_prompt.replace("{source_files}", ", ".join(set(source_files)))
            system_prompt = system_prompt.replace("{confidence_score}", str(confidence_percent))
            system_prompt = system_prompt.replace("{data_sources}", ", ".join(set(data_sources)))
            
            # Build complete prompt with enhanced instructions
            full_prompt = f"""{system_prompt}

**사용자 질문**: {user_question}

**답변 요구사항**:
1. 위의 구조에 따라 완전하고 체계적인 답변을 작성하세요
2. 제공된 컨텍스트를 최대한 활용하여 정확한 정보를 제공하세요
3. 각 섹션을 명확하게 구분하고 이모티콘을 적절히 사용하세요
4. 답변의 품질과 완성도를 높이기 위해 충분한 내용을 포함하세요
5. 불확실한 정보는 명확히 표시하고 추가 확인이 필요함을 알려주세요

**답변**:"""
            
            logger.info(f"Built enhanced RAG prompt with {len(context_documents)} documents, avg confidence: {confidence_percent}%")
            return full_prompt
            
        except Exception as e:
            logger.error(f"Failed to build RAG prompt: {e}")
            # Fallback to simple prompt
            return f"질문: {user_question}\n\n답변:"

    def generate_session_title(self, first_question: str) -> str:
        """Generate a session title based on the first question"""
        try:
            # Clean and truncate the question
            cleaned_question = first_question.strip()
            
            # Remove common question words and clean up
            question_words = ["질문", "문의", "궁금", "알고싶", "알려주", "도움", "help", "question"]
            for word in question_words:
                cleaned_question = cleaned_question.replace(word, "").strip()
            
            # Remove special characters and extra spaces
            import re
            cleaned_question = re.sub(r'[^\w\s가-힣]', '', cleaned_question)
            cleaned_question = re.sub(r'\s+', ' ', cleaned_question).strip()
            
            # Truncate to reasonable length (max 30 characters)
            if len(cleaned_question) > 30:
                cleaned_question = cleaned_question[:30] + "..."
            
            # If question is too short or empty, use default
            if len(cleaned_question) < 3:
                from datetime import datetime
                timestamp = datetime.now().strftime("%m/%d %H:%M")
                return f"새 대화 ({timestamp})"
            
            # Add prefix to make it clear it's a chat title
            return f"💬 {cleaned_question}"
            
        except Exception as e:
            logger.error(f"Failed to generate session title: {e}")
            from datetime import datetime
            timestamp = datetime.now().strftime("%m/%d %H:%M")
            return f"새 대화 ({timestamp})"

# Global prompt service instance
prompt_service = PromptService()

