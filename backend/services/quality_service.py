"""
Response quality assessment service
"""
import re
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Quality metrics for response assessment"""
    completeness_score: float  # 0-1, 답변의 완전성
    accuracy_score: float      # 0-1, 답변의 정확성
    relevance_score: float     # 0-1, 질문과의 관련성
    clarity_score: float       # 0-1, 답변의 명확성
    structure_score: float     # 0-1, 구조화 정도
    overall_score: float       # 0-1, 전체 품질 점수
    issues: List[str]         # 발견된 문제점들
    suggestions: List[str]     # 개선 제안사항

class QualityService:
    """Service for assessing response quality"""
    
    def __init__(self):
        self.quality_thresholds = {
            "excellent": 0.85,
            "good": 0.70,
            "fair": 0.55,
            "poor": 0.40
        }
    
    def assess_response_quality(self, 
                              user_question: str, 
                              response: str, 
                              context_documents: List[Dict[str, Any]] = None,
                              sources: List[Dict[str, Any]] = None) -> QualityMetrics:
        """Assess the quality of a response"""
        try:
            # Calculate individual quality scores
            completeness = self._assess_completeness(user_question, response)
            accuracy = self._assess_accuracy(response, context_documents, sources)
            relevance = self._assess_relevance(user_question, response)
            clarity = self._assess_clarity(response)
            structure = self._assess_structure(response)
            
            # Calculate overall score (weighted average)
            overall = (
                completeness * 0.25 +
                accuracy * 0.25 +
                relevance * 0.20 +
                clarity * 0.15 +
                structure * 0.15
            )
            
            # Identify issues and suggestions
            issues = self._identify_issues(completeness, accuracy, relevance, clarity, structure)
            suggestions = self._generate_suggestions(issues, overall)
            
            return QualityMetrics(
                completeness_score=completeness,
                accuracy_score=accuracy,
                relevance_score=relevance,
                clarity_score=clarity,
                structure_score=structure,
                overall_score=overall,
                issues=issues,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Failed to assess response quality: {e}")
            return QualityMetrics(
                completeness_score=0.0,
                accuracy_score=0.0,
                relevance_score=0.0,
                clarity_score=0.0,
                structure_score=0.0,
                overall_score=0.0,
                issues=["품질 평가 중 오류 발생"],
                suggestions=["시스템 관리자에게 문의하세요"]
            )
    
    def _assess_completeness(self, question: str, response: str) -> float:
        """Assess how completely the response answers the question"""
        try:
            # Check for key question words
            question_words = ["무엇", "어떻게", "왜", "언제", "어디서", "누가", "어느", "몇"]
            question_has_keywords = any(word in question for word in question_words)
            
            # Check response length (minimum threshold)
            min_length = 50
            length_score = min(1.0, len(response) / 200)  # Normalize to 200 chars
            
            # Check for structured sections
            section_indicators = ["핵심", "요약", "설명", "정보", "참조", "주의"]
            structure_indicators = sum(1 for indicator in section_indicators if indicator in response)
            structure_score = min(1.0, structure_indicators / 3)  # Normalize to 3 sections
            
            # Check for completeness indicators
            completeness_indicators = ["완전", "포괄", "상세", "구체", "예시"]
            completeness_indicators_count = sum(1 for indicator in completeness_indicators if indicator in response)
            completeness_score = min(1.0, completeness_indicators_count / 2)
            
            # Calculate final score
            if question_has_keywords:
                return (length_score * 0.4 + structure_score * 0.4 + completeness_score * 0.2)
            else:
                return (length_score * 0.6 + structure_score * 0.4)
                
        except Exception as e:
            logger.error(f"Failed to assess completeness: {e}")
            return 0.5
    
    def _assess_accuracy(self, response: str, context_docs: List[Dict[str, Any]] = None, sources: List[Dict[str, Any]] = None) -> float:
        """Assess the accuracy of the response based on context and sources"""
        try:
            if not context_docs and not sources:
                return 0.5  # No context to verify against
            
            # Check for source citations
            source_indicators = ["참조", "출처", "문서", "파일", "근거"]
            has_sources = any(indicator in response for indicator in source_indicators)
            source_score = 1.0 if has_sources else 0.3
            
            # Check for uncertainty indicators (good for accuracy)
            uncertainty_indicators = ["확인", "검증", "추정", "가능성", "제한"]
            has_uncertainty = any(indicator in response for indicator in uncertainty_indicators)
            uncertainty_score = 0.8 if has_uncertainty else 0.6
            
            # Check for data-driven language
            data_indicators = ["데이터", "통계", "분석", "결과", "연구", "조사"]
            has_data_language = any(indicator in response for indicator in data_indicators)
            data_score = 1.0 if has_data_language else 0.7
            
            # Calculate average accuracy score
            return (source_score * 0.4 + uncertainty_score * 0.3 + data_score * 0.3)
            
        except Exception as e:
            logger.error(f"Failed to assess accuracy: {e}")
            return 0.5
    
    def _assess_relevance(self, question: str, response: str) -> float:
        """Assess how relevant the response is to the question"""
        try:
            # Extract key terms from question
            question_terms = re.findall(r'\b\w+\b', question.lower())
            response_terms = re.findall(r'\b\w+\b', response.lower())
            
            # Calculate term overlap
            common_terms = set(question_terms) & set(response_terms)
            if len(question_terms) > 0:
                term_overlap = len(common_terms) / len(question_terms)
            else:
                term_overlap = 0.0
            
            # Check for direct question addressing
            question_patterns = [
                r"질문.*답변",
                r"문의.*응답",
                r"요청.*제공",
                r"궁금.*설명"
            ]
            direct_addressing = any(re.search(pattern, response) for pattern in question_patterns)
            addressing_score = 1.0 if direct_addressing else 0.7
            
            # Check for topic consistency
            topic_indicators = ["관련", "해당", "이에", "따라서", "따라"]
            topic_consistency = sum(1 for indicator in topic_indicators if indicator in response)
            topic_score = min(1.0, topic_consistency / 2)
            
            return (term_overlap * 0.5 + addressing_score * 0.3 + topic_score * 0.2)
            
        except Exception as e:
            logger.error(f"Failed to assess relevance: {e}")
            return 0.5
    
    def _assess_clarity(self, response: str) -> float:
        """Assess the clarity and readability of the response"""
        try:
            # Check for clear structure indicators
            structure_indicators = ["•", "1.", "2.", "3.", "-", "→", "▶"]
            structure_count = sum(response.count(indicator) for indicator in structure_indicators)
            structure_score = min(1.0, structure_count / 5)
            
            # Check for explanation patterns
            explanation_patterns = [
                r"즉,", r"다시 말해", r"구체적으로", r"예를 들어",
                r"예시로", r"설명하면", r"정리하면"
            ]
            explanation_count = sum(len(re.findall(pattern, response)) for pattern in explanation_patterns)
            explanation_score = min(1.0, explanation_count / 3)
            
            # Check for Korean language quality
            korean_indicators = ["입니다", "습니다", "합니다", "됩니다", "됩니다"]
            korean_count = sum(response.count(indicator) for indicator in korean_indicators)
            korean_score = min(1.0, korean_count / 10)
            
            # Check for appropriate length
            length_score = 1.0 if 100 <= len(response) <= 1000 else 0.7
            
            return (structure_score * 0.3 + explanation_score * 0.3 + korean_score * 0.2 + length_score * 0.2)
            
        except Exception as e:
            logger.error(f"Failed to assess clarity: {e}")
            return 0.5
    
    def _assess_structure(self, response: str) -> float:
        """Assess the structural quality of the response"""
        try:
            # Check for required sections
            required_sections = ["핵심", "요약", "설명", "정보"]
            section_count = sum(1 for section in required_sections if section in response)
            section_score = min(1.0, section_count / 2)
            
            # Check for emoji usage (good for structure)
            emoji_pattern = r'[📋📖🔍📚⚠️💡🎯🚀]'
            emoji_count = len(re.findall(emoji_pattern, response))
            emoji_score = min(1.0, emoji_count / 3)
            
            # Check for paragraph breaks
            paragraph_breaks = response.count('\n\n')
            paragraph_score = min(1.0, paragraph_breaks / 3)
            
            # Check for bullet points or numbering
            bullet_patterns = [r'^\s*[•\-\*]\s', r'^\s*\d+\.\s']
            bullet_count = sum(len(re.findall(pattern, response, re.MULTILINE)) for pattern in bullet_patterns)
            bullet_score = min(1.0, bullet_count / 3)
            
            return (section_score * 0.3 + emoji_score * 0.2 + paragraph_score * 0.3 + bullet_score * 0.2)
            
        except Exception as e:
            logger.error(f"Failed to assess structure: {e}")
            return 0.5
    
    def _identify_issues(self, completeness: float, accuracy: float, relevance: float, clarity: float, structure: float) -> List[str]:
        """Identify specific issues with the response"""
        issues = []
        
        if completeness < 0.6:
            issues.append("답변이 불완전하거나 질문에 대한 충분한 정보를 제공하지 않습니다")
        
        if accuracy < 0.6:
            issues.append("답변의 정확성이나 신뢰성이 부족합니다")
        
        if relevance < 0.6:
            issues.append("질문과의 관련성이 낮거나 주제에서 벗어났습니다")
        
        if clarity < 0.6:
            issues.append("답변이 명확하지 않거나 이해하기 어렵습니다")
        
        if structure < 0.6:
            issues.append("답변의 구조가 체계적이지 않습니다")
        
        return issues
    
    def _generate_suggestions(self, issues: List[str], overall_score: float) -> List[str]:
        """Generate improvement suggestions based on identified issues"""
        suggestions = []
        
        if overall_score < 0.5:
            suggestions.append("전체적인 답변 품질을 개선하기 위해 더 상세하고 구조화된 응답을 작성하세요")
        
        if "불완전" in str(issues):
            suggestions.append("질문의 모든 측면을 다루고 충분한 예시와 설명을 포함하세요")
        
        if "정확성" in str(issues):
            suggestions.append("제공된 데이터를 더 신중하게 검토하고 불확실한 정보는 명시하세요")
        
        if "관련성" in str(issues):
            suggestions.append("질문의 핵심 키워드를 더 많이 활용하고 직접적으로 답변하세요")
        
        if "명확" in str(issues):
            suggestions.append("더 간결하고 이해하기 쉬운 언어를 사용하고 구조를 명확히 하세요")
        
        if "구조" in str(issues):
            suggestions.append("섹션을 명확히 구분하고 이모티콘과 불릿 포인트를 활용하세요")
        
        return suggestions
    
    def get_quality_level(self, overall_score: float) -> str:
        """Get quality level based on overall score"""
        if overall_score >= self.quality_thresholds["excellent"]:
            return "excellent"
        elif overall_score >= self.quality_thresholds["good"]:
            return "good"
        elif overall_score >= self.quality_thresholds["fair"]:
            return "fair"
        else:
            return "poor"
    
    def get_quality_color(self, overall_score: float) -> str:
        """Get color code for quality level"""
        level = self.get_quality_level(overall_score)
        colors = {
            "excellent": "#10B981",  # Green
            "good": "#3B82F6",       # Blue
            "fair": "#F59E0B",       # Yellow
            "poor": "#EF4444"        # Red
        }
        return colors.get(level, "#6B7280")
    
    def get_quality_emoji(self, overall_score: float) -> str:
        """Get emoji for quality level"""
        level = self.get_quality_level(overall_score)
        emojis = {
            "excellent": "🟢",
            "good": "🔵",
            "fair": "🟡",
            "poor": "🔴"
        }
        return emojis.get(level, "⚪")

# Global quality service instance
quality_service = QualityService()
