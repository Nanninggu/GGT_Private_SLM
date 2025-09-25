"""
User feedback service for response quality improvement
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of user feedback"""
    RATING = "rating"           # 1-5 star rating
    THUMBS_UP = "thumbs_up"     # Thumbs up/down
    HELPFUL = "helpful"         # Helpful/Not helpful
    ACCURATE = "accurate"       # Accurate/Inaccurate
    COMPLETE = "complete"       # Complete/Incomplete
    CLEAR = "clear"            # Clear/Unclear
    RELEVANT = "relevant"      # Relevant/Irrelevant

@dataclass
class UserFeedback:
    """User feedback model"""
    id: str
    user_id: str
    session_id: str
    message_id: str
    feedback_type: FeedbackType
    rating: Optional[int] = None  # 1-5 for rating type
    is_positive: Optional[bool] = None  # True/False for boolean feedback
    comment: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeedbackAnalytics:
    """Feedback analytics model"""
    total_feedback: int
    positive_feedback: int
    negative_feedback: int
    average_rating: float
    feedback_by_type: Dict[str, int]
    recent_trends: Dict[str, float]
    quality_issues: List[str]
    improvement_suggestions: List[str]

class FeedbackService:
    """Service for managing user feedback and analytics"""
    
    def __init__(self):
        self.feedback_storage = {}  # In-memory storage (fallback)
        self.analytics_cache = {}
        self.db_config = self._get_db_config()
    
    def _get_db_config(self):
        """Get database configuration"""
        try:
            from config.settings import Settings
            settings = Settings()
            return {
                'host': '127.0.0.1',
                'port': 5433,
                'database': 'postgres',
                'user': 'postgres',
                'password': 'test1234'
            }
        except Exception as e:
            logger.warning(f"Could not get database config: {e}")
            return {
                'host': '127.0.0.1',
                'port': 5433,
                'database': 'postgres',
                'user': 'postgres',
                'password': 'test1234'
            }
    
    def _get_db_connection(self):
        """Get database connection"""
        if not self.db_config:
            return None
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return None
    
    def submit_feedback(self, 
                       user_id: str, 
                       session_id: str, 
                       message_id: str,
                       feedback_type: FeedbackType,
                       rating: Optional[int] = None,
                       is_positive: Optional[bool] = None,
                       comment: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Submit user feedback"""
        try:
            # Validate feedback data
            if feedback_type == FeedbackType.RATING and (rating is None or not 1 <= rating <= 5):
                return {"success": False, "error": "Rating must be between 1 and 5"}
            
            if feedback_type != FeedbackType.RATING and is_positive is None:
                return {"success": False, "error": "is_positive must be provided for non-rating feedback"}
            
            # Try to save to database first
            conn = self._get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        # Insert feedback into database
                        cursor.execute("""
                            INSERT INTO feedback (user_id, session_id, message_id, feedback_type, rating, is_positive, comment, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            user_id,
                            session_id,
                            message_id,
                            feedback_type.value,
                            rating,
                            is_positive,
                            comment,
                            datetime.now()
                        ))
                        
                        feedback_id = cursor.fetchone()[0]
                        conn.commit()
                        
                        logger.info(f"Feedback saved to database: {feedback_id} by user {user_id}")
                        
                        # Clear analytics cache to force refresh
                        self.analytics_cache.clear()
                        
                        return {
                            "success": True,
                            "feedback_id": feedback_id,
                            "message": "피드백이 성공적으로 제출되었습니다"
                        }
                        
                except Exception as e:
                    logger.error(f"Failed to save feedback to database: {e}")
                    conn.rollback()
                finally:
                    conn.close()
            
            # Fallback to in-memory storage
            feedback_id = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            feedback = UserFeedback(
                id=feedback_id,
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                feedback_type=feedback_type,
                rating=rating,
                is_positive=is_positive,
                comment=comment,
                metadata=metadata or {}
            )
            
            # Store feedback in memory
            self.feedback_storage[feedback_id] = feedback
            
            # Clear analytics cache to force refresh
            self.analytics_cache.clear()
            
            logger.info(f"Feedback submitted (in-memory): {feedback_type.value} by user {user_id}")
            
            return {
                "success": True,
                "feedback_id": feedback_id,
                "message": "피드백이 성공적으로 제출되었습니다 (로컬 저장)"
            }
            
        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}")
            return {"success": False, "error": str(e)}
    
    def get_feedback_analytics(self, user_id: Optional[str] = None, days: int = 30) -> FeedbackAnalytics:
        """Get feedback analytics"""
        try:
            cache_key = f"analytics_{user_id}_{days}"
            if cache_key in self.analytics_cache:
                return self.analytics_cache[cache_key]
            
            # Filter feedback by user and date range
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            filtered_feedback = [
                f for f in self.feedback_storage.values()
                if (user_id is None or f.user_id == user_id) and f.timestamp.timestamp() >= cutoff_date
            ]
            
            if not filtered_feedback:
                return FeedbackAnalytics(
                    total_feedback=0,
                    positive_feedback=0,
                    negative_feedback=0,
                    average_rating=0.0,
                    feedback_by_type={},
                    recent_trends={},
                    quality_issues=[],
                    improvement_suggestions=[]
                )
            
            # Calculate basic metrics
            total_feedback = len(filtered_feedback)
            positive_feedback = sum(1 for f in filtered_feedback if self._is_positive_feedback(f))
            negative_feedback = total_feedback - positive_feedback
            
            # Calculate average rating
            rating_feedback = [f for f in filtered_feedback if f.feedback_type == FeedbackType.RATING and f.rating]
            average_rating = sum(f.rating for f in rating_feedback) / len(rating_feedback) if rating_feedback else 0.0
            
            # Calculate feedback by type
            feedback_by_type = {}
            for feedback_type in FeedbackType:
                count = sum(1 for f in filtered_feedback if f.feedback_type == feedback_type)
                feedback_by_type[feedback_type.value] = count
            
            # Calculate recent trends (last 7 days vs previous 7 days)
            recent_trends = self._calculate_recent_trends(filtered_feedback)
            
            # Identify quality issues
            quality_issues = self._identify_quality_issues(filtered_feedback)
            
            # Generate improvement suggestions
            improvement_suggestions = self._generate_improvement_suggestions(
                positive_feedback, negative_feedback, average_rating, quality_issues
            )
            
            analytics = FeedbackAnalytics(
                total_feedback=total_feedback,
                positive_feedback=positive_feedback,
                negative_feedback=negative_feedback,
                average_rating=average_rating,
                feedback_by_type=feedback_by_type,
                recent_trends=recent_trends,
                quality_issues=quality_issues,
                improvement_suggestions=improvement_suggestions
            )
            
            # Cache the results
            self.analytics_cache[cache_key] = analytics
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get feedback analytics: {e}")
            return FeedbackAnalytics(
                total_feedback=0,
                positive_feedback=0,
                negative_feedback=0,
                average_rating=0.0,
                feedback_by_type={},
                recent_trends={},
                quality_issues=["분석 중 오류 발생"],
                improvement_suggestions=["시스템 관리자에게 문의하세요"]
            )
    
    def _is_positive_feedback(self, feedback: UserFeedback) -> bool:
        """Determine if feedback is positive"""
        if feedback.feedback_type == FeedbackType.RATING:
            return feedback.rating and feedback.rating >= 4
        else:
            return feedback.is_positive is True
    
    def _calculate_recent_trends(self, feedback: List[UserFeedback]) -> Dict[str, float]:
        """Calculate recent trends in feedback"""
        try:
            # Split feedback into last 7 days and previous 7 days
            now = datetime.now().timestamp()
            last_7_days = now - (7 * 24 * 60 * 60)
            previous_7_days = now - (14 * 24 * 60 * 60)
            
            recent_feedback = [f for f in feedback if f.timestamp.timestamp() >= last_7_days]
            previous_feedback = [f for f in feedback if previous_7_days <= f.timestamp.timestamp() < last_7_days]
            
            # Calculate positive feedback rates
            recent_positive_rate = self._calculate_positive_rate(recent_feedback)
            previous_positive_rate = self._calculate_positive_rate(previous_feedback)
            
            # Calculate trend
            trend = recent_positive_rate - previous_positive_rate if previous_positive_rate > 0 else 0.0
            
            return {
                "recent_positive_rate": recent_positive_rate,
                "previous_positive_rate": previous_positive_rate,
                "trend": trend,
                "trend_direction": "improving" if trend > 0.05 else "declining" if trend < -0.05 else "stable"
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate recent trends: {e}")
            return {}
    
    def _calculate_positive_rate(self, feedback: List[UserFeedback]) -> float:
        """Calculate positive feedback rate"""
        if not feedback:
            return 0.0
        
        positive_count = sum(1 for f in feedback if self._is_positive_feedback(f))
        return positive_count / len(feedback)
    
    def _identify_quality_issues(self, feedback: List[UserFeedback]) -> List[str]:
        """Identify quality issues from feedback"""
        issues = []
        
        # Check for low ratings
        rating_feedback = [f for f in feedback if f.feedback_type == FeedbackType.RATING and f.rating]
        if rating_feedback:
            avg_rating = sum(f.rating for f in rating_feedback) / len(rating_feedback)
            if avg_rating < 3.0:
                issues.append("전반적인 응답 품질이 낮습니다")
            elif avg_rating < 4.0:
                issues.append("응답 품질 개선이 필요합니다")
        
        # Check for specific feedback types
        negative_helpful = sum(1 for f in feedback if f.feedback_type == FeedbackType.HELPFUL and not f.is_positive)
        if negative_helpful > len(feedback) * 0.3:
            issues.append("응답이 도움이 되지 않는다는 피드백이 많습니다")
        
        negative_accurate = sum(1 for f in feedback if f.feedback_type == FeedbackType.ACCURATE and not f.is_positive)
        if negative_accurate > len(feedback) * 0.2:
            issues.append("응답의 정확성에 대한 우려가 있습니다")
        
        negative_clear = sum(1 for f in feedback if f.feedback_type == FeedbackType.CLEAR and not f.is_positive)
        if negative_clear > len(feedback) * 0.25:
            issues.append("응답의 명확성이 부족합니다")
        
        return issues
    
    def _generate_improvement_suggestions(self, 
                                        positive_feedback: int, 
                                        negative_feedback: int, 
                                        average_rating: float,
                                        quality_issues: List[str]) -> List[str]:
        """Generate improvement suggestions based on feedback"""
        suggestions = []
        
        # Overall satisfaction
        total_feedback = positive_feedback + negative_feedback
        if total_feedback > 0:
            satisfaction_rate = positive_feedback / total_feedback
            if satisfaction_rate < 0.6:
                suggestions.append("전반적인 응답 품질을 개선하기 위해 프롬프트 엔지니어링을 강화하세요")
            elif satisfaction_rate < 0.8:
                suggestions.append("사용자 만족도를 높이기 위해 응답의 완성도를 높이세요")
        
        # Rating-based suggestions
        if average_rating < 3.0:
            suggestions.append("응답의 정확성과 관련성을 크게 개선해야 합니다")
        elif average_rating < 4.0:
            suggestions.append("응답의 구조화와 명확성을 개선하세요")
        
        # Issue-specific suggestions
        if "도움이 되지 않는다" in str(quality_issues):
            suggestions.append("사용자의 질문에 더 직접적으로 답변하고 실용적인 정보를 제공하세요")
        
        if "정확성" in str(quality_issues):
            suggestions.append("제공된 데이터를 더 신중하게 검토하고 불확실한 정보는 명시하세요")
        
        if "명확성" in str(quality_issues):
            suggestions.append("더 간결하고 이해하기 쉬운 언어를 사용하고 구조를 명확히 하세요")
        
        return suggestions
    
    def get_user_feedback_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's feedback history"""
        try:
            user_feedback = [
                f for f in self.feedback_storage.values()
                if f.user_id == user_id
            ]
            
            # Sort by timestamp (newest first)
            user_feedback.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Limit results
            user_feedback = user_feedback[:limit]
            
            # Convert to dictionary format
            return [
                {
                    "id": f.id,
                    "session_id": f.session_id,
                    "message_id": f.message_id,
                    "feedback_type": f.feedback_type.value,
                    "rating": f.rating,
                    "is_positive": f.is_positive,
                    "comment": f.comment,
                    "timestamp": f.timestamp.isoformat(),
                    "metadata": f.metadata
                }
                for f in user_feedback
            ]
            
        except Exception as e:
            logger.error(f"Failed to get user feedback history: {e}")
            return []
    
    def get_feedback_summary(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a summary of feedback data"""
        try:
            analytics = self.get_feedback_analytics(user_id)
            
            return {
                "total_feedback": analytics.total_feedback,
                "satisfaction_rate": analytics.positive_feedback / max(1, analytics.total_feedback),
                "average_rating": analytics.average_rating,
                "quality_level": self._get_quality_level(analytics.average_rating),
                "main_issues": analytics.quality_issues[:3],  # Top 3 issues
                "top_suggestions": analytics.improvement_suggestions[:3],  # Top 3 suggestions
                "trend": analytics.recent_trends.get("trend_direction", "stable")
            }
            
        except Exception as e:
            logger.error(f"Failed to get feedback summary: {e}")
            return {"error": str(e)}
    
    def _get_quality_level(self, average_rating: float) -> str:
        """Get quality level based on average rating"""
        if average_rating >= 4.5:
            return "excellent"
        elif average_rating >= 4.0:
            return "good"
        elif average_rating >= 3.0:
            return "fair"
        else:
            return "poor"

# Global feedback service instance
feedback_service = FeedbackService()
