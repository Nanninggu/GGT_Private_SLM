"""
Personalization service for user-specific response customization
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ResponseStyle(Enum):
    """Response style preferences"""
    STANDARD = "standard"      # Standard, balanced tone
    FORMAL = "formal"          # Formal, professional tone
    CASUAL = "casual"          # Casual, friendly tone
    TECHNICAL = "technical"    # Technical, detailed explanations
    SIMPLE = "simple"          # Simple, easy-to-understand
    CONCISE = "concise"        # Brief, to-the-point
    DETAILED = "detailed"      # Comprehensive, thorough

class DetailLevel(Enum):
    """Detail level preferences"""
    MINIMAL = "minimal"         # Very brief responses
    STANDARD = "standard"       # Normal detail level
    COMPREHENSIVE = "comprehensive"  # Very detailed responses

@dataclass
class UserPreferences:
    """User personalization preferences"""
    user_id: str
    response_style: ResponseStyle = ResponseStyle.STANDARD
    detail_level: DetailLevel = DetailLevel.STANDARD
    preferred_language: str = "ko"  # Korean
    include_examples: bool = True
    include_sources: bool = True
    include_metadata: bool = True
    max_response_length: int = 1000
    preferred_format: str = "structured"  # structured, conversational, list
    technical_level: str = "intermediate"  # beginner, intermediate, advanced
    domain_expertise: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class PersonalizationService:
    """Service for managing user personalization and response customization"""
    
    def __init__(self):
        self.user_preferences = {}  # In-memory storage (replace with database in production)
        self.default_preferences = self._create_default_preferences()
    
    def _create_default_preferences(self) -> UserPreferences:
        """Create default user preferences"""
        return UserPreferences(
            user_id="default",
            response_style=ResponseStyle.STANDARD,
            detail_level=DetailLevel.STANDARD,
            preferred_language="ko",
            include_examples=True,
            include_sources=True,
            include_metadata=True,
            max_response_length=1000,
            preferred_format="structured",
            technical_level="intermediate",
            domain_expertise=[]
        )
    
    def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences, create default if not exists"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreferences(
                user_id=user_id,
                response_style=ResponseStyle.STANDARD,
                detail_level=DetailLevel.STANDARD,
                preferred_language="ko",
                include_examples=True,
                include_sources=True,
                include_metadata=True,
                max_response_length=1000,
                preferred_format="structured",
                technical_level="intermediate",
                domain_expertise=[]
            )
        
        return self.user_preferences[user_id]
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = UserPreferences(user_id=user_id)
            
            user_prefs = self.user_preferences[user_id]
            
            # Update preferences
            if "response_style" in preferences:
                user_prefs.response_style = ResponseStyle(preferences["response_style"])
            
            if "detail_level" in preferences:
                user_prefs.detail_level = DetailLevel(preferences["detail_level"])
            
            if "preferred_language" in preferences:
                user_prefs.preferred_language = preferences["preferred_language"]
            
            if "include_examples" in preferences:
                user_prefs.include_examples = bool(preferences["include_examples"])
            
            if "include_sources" in preferences:
                user_prefs.include_sources = bool(preferences["include_sources"])
            
            if "include_metadata" in preferences:
                user_prefs.include_metadata = bool(preferences["include_metadata"])
            
            if "max_response_length" in preferences:
                user_prefs.max_response_length = int(preferences["max_response_length"])
            
            if "preferred_format" in preferences:
                user_prefs.preferred_format = preferences["preferred_format"]
            
            if "technical_level" in preferences:
                user_prefs.technical_level = preferences["technical_level"]
            
            if "domain_expertise" in preferences:
                user_prefs.domain_expertise = list(preferences["domain_expertise"])
            
            user_prefs.updated_at = datetime.now()
            
            logger.info(f"Updated preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
            return False
    
    def customize_prompt(self, base_prompt: str, user_id: str, query: str) -> str:
        """Customize prompt based on user preferences"""
        try:
            preferences = self.get_user_preferences(user_id)
            
            # Add personalization instructions
            personalization_instructions = self._build_personalization_instructions(preferences)
            
            # Customize based on response style
            style_instructions = self._get_style_instructions(preferences.response_style)
            
            # Customize based on detail level
            detail_instructions = self._get_detail_instructions(preferences.detail_level)
            
            # Customize based on technical level
            technical_instructions = self._get_technical_instructions(preferences.technical_level)
            
            # Customize based on preferred format
            format_instructions = self._get_format_instructions(preferences.preferred_format)
            
            # Combine all customizations
            customized_prompt = f"""{base_prompt}

**개인화 설정**:
{personalization_instructions}

**응답 스타일**: {style_instructions}

**상세도**: {detail_instructions}

**기술 수준**: {technical_instructions}

**응답 형식**: {format_instructions}

**사용자 질문**: {query}

위의 개인화 설정에 따라 사용자에게 맞춤화된 응답을 제공하세요."""
            
            return customized_prompt
            
        except Exception as e:
            logger.error(f"Failed to customize prompt: {e}")
            return base_prompt
    
    def _build_personalization_instructions(self, preferences: UserPreferences) -> str:
        """Build personalization instructions based on user preferences"""
        instructions = []
        
        # Language preference
        if preferences.preferred_language == "ko":
            instructions.append("• 반드시 한국어로 답변하세요")
        
        # Response length
        if preferences.max_response_length <= 500:
            instructions.append("• 간결하고 핵심적인 답변을 제공하세요")
        elif preferences.max_response_length >= 1500:
            instructions.append("• 상세하고 포괄적인 답변을 제공하세요")
        
        # Examples preference
        if preferences.include_examples:
            instructions.append("• 구체적인 예시나 사례를 포함하세요")
        
        # Sources preference
        if preferences.include_sources:
            instructions.append("• 참조 정보와 출처를 명시하세요")
        
        # Metadata preference
        if preferences.include_metadata:
            instructions.append("• 신뢰도 점수와 관련 메타데이터를 포함하세요")
        
        # Domain expertise
        if preferences.domain_expertise:
            expertise_str = ", ".join(preferences.domain_expertise)
            instructions.append(f"• 다음 분야의 전문성을 고려하세요: {expertise_str}")
        
        return "\n".join(instructions)
    
    def _get_style_instructions(self, response_style: ResponseStyle) -> str:
        """Get style-specific instructions"""
        style_instructions = {
            ResponseStyle.STANDARD: "균형 잡힌 표준적인 톤으로 답변하세요. 적절한 수준의 전문성과 친근함을 유지하세요.",
            ResponseStyle.FORMAL: "정중하고 전문적인 톤으로 답변하세요. 격식 있는 언어를 사용하세요.",
            ResponseStyle.CASUAL: "친근하고 편안한 톤으로 답변하세요. 일상적인 언어를 사용하세요.",
            ResponseStyle.TECHNICAL: "기술적이고 전문적인 용어를 사용하여 정확한 설명을 제공하세요.",
            ResponseStyle.SIMPLE: "누구나 이해할 수 있도록 간단하고 명확한 언어를 사용하세요.",
            ResponseStyle.CONCISE: "핵심만 간결하게 전달하세요. 불필요한 설명은 생략하세요.",
            ResponseStyle.DETAILED: "포괄적이고 상세한 설명을 제공하세요. 모든 관련 정보를 포함하세요."
        }
        
        return style_instructions.get(response_style, "표준적인 톤으로 답변하세요.")
    
    def _get_detail_instructions(self, detail_level: DetailLevel) -> str:
        """Get detail level instructions"""
        detail_instructions = {
            DetailLevel.MINIMAL: "핵심 정보만 간단히 전달하세요. (100-200자)",
            DetailLevel.STANDARD: "적절한 수준의 상세함으로 답변하세요. (300-800자)",
            DetailLevel.COMPREHENSIVE: "모든 관련 정보를 포함하여 상세히 답변하세요. (800자 이상)"
        }
        
        return detail_instructions.get(detail_level, "적절한 수준의 상세함으로 답변하세요.")
    
    def _get_technical_instructions(self, technical_level: str) -> str:
        """Get technical level instructions"""
        technical_instructions = {
            "beginner": "초보자도 이해할 수 있도록 기본 개념부터 설명하세요. 전문 용어는 풀어서 설명하세요.",
            "intermediate": "중급 수준의 설명을 제공하세요. 기본 개념은 간략히 하고 핵심 내용에 집중하세요.",
            "advanced": "고급 수준의 전문적인 설명을 제공하세요. 전문 용어와 기술적 세부사항을 포함하세요."
        }
        
        return technical_instructions.get(technical_level, "중급 수준의 설명을 제공하세요.")
    
    def _get_format_instructions(self, preferred_format: str) -> str:
        """Get format-specific instructions"""
        format_instructions = {
            "structured": "섹션별로 구조화된 답변을 제공하세요. 이모티콘과 불릿 포인트를 활용하세요.",
            "conversational": "대화하듯이 자연스러운 답변을 제공하세요. 질문을 던지거나 상호작용을 유도하세요.",
            "list": "주요 포인트를 나열하여 정리하세요. 번호나 불릿 포인트를 사용하세요."
        }
        
        return format_instructions.get(preferred_format, "구조화된 답변을 제공하세요.")
    
    def customize_response_format(self, response: str, user_id: str) -> str:
        """Customize response format based on user preferences"""
        try:
            preferences = self.get_user_preferences(user_id)
            
            # Apply length limit
            if len(response) > preferences.max_response_length:
                response = response[:preferences.max_response_length] + "..."
            
            # Apply format customization
            if preferences.preferred_format == "list":
                response = self._convert_to_list_format(response)
            elif preferences.preferred_format == "conversational":
                response = self._convert_to_conversational_format(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to customize response format: {e}")
            return response
    
    def _convert_to_list_format(self, response: str) -> str:
        """Convert response to list format"""
        # Simple conversion - in practice, this would be more sophisticated
        lines = response.split('\n')
        list_items = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('•', '-', '1.', '2.', '3.')):
                list_items.append(f"• {line}")
            else:
                list_items.append(line)
        
        return '\n'.join(list_items)
    
    def _convert_to_conversational_format(self, response: str) -> str:
        """Convert response to conversational format"""
        # Add conversational elements
        conversational_starters = [
            "좋은 질문이네요!",
            "흥미로운 주제입니다.",
            "이에 대해 말씀드리면,",
            "제가 아는 바로는,"
        ]
        
        import random
        starter = random.choice(conversational_starters)
        
        return f"{starter} {response}"
    
    def get_personalization_summary(self, user_id: str) -> Dict[str, Any]:
        """Get personalization summary for user"""
        try:
            preferences = self.get_user_preferences(user_id)
            
            return {
                "user_id": user_id,
                "response_style": preferences.response_style.value,
                "detail_level": preferences.detail_level.value,
                "preferred_language": preferences.preferred_language,
                "include_examples": preferences.include_examples,
                "include_sources": preferences.include_sources,
                "include_metadata": preferences.include_metadata,
                "max_response_length": preferences.max_response_length,
                "preferred_format": preferences.preferred_format,
                "technical_level": preferences.technical_level,
                "domain_expertise": preferences.domain_expertise,
                "created_at": preferences.created_at.isoformat(),
                "updated_at": preferences.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get personalization summary: {e}")
            return {"error": str(e)}
    
    def reset_user_preferences(self, user_id: str) -> bool:
        """Reset user preferences to default"""
        try:
            self.user_preferences[user_id] = UserPreferences(
                user_id=user_id,
                response_style=ResponseStyle.STANDARD,
                detail_level=DetailLevel.STANDARD,
                preferred_language="ko",
                include_examples=True,
                include_sources=True,
                include_metadata=True,
                max_response_length=1000,
                preferred_format="structured",
                technical_level="intermediate",
                domain_expertise=[]
            )
            
            logger.info(f"Reset preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset user preferences: {e}")
            return False

# Global personalization service instance
personalization_service = PersonalizationService()
