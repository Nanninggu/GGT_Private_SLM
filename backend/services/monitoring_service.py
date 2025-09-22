"""
Real-time monitoring service for response quality and system performance
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json

logger = logging.getLogger(__name__)

@dataclass
class QualityAlert:
    """Quality alert model"""
    id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False

@dataclass
class PerformanceMetrics:
    """Performance metrics model"""
    timestamp: datetime
    response_time: float
    quality_score: float
    user_satisfaction: float
    error_rate: float
    throughput: int  # requests per minute
    active_users: int

class MonitoringService:
    """Service for real-time monitoring and alerting"""
    
    def __init__(self):
        self.quality_thresholds = {
            "excellent": 0.85,
            "good": 0.70,
            "fair": 0.55,
            "poor": 0.40
        }
        
        self.alert_thresholds = {
            "quality_degradation": 0.6,  # Alert if quality drops below 60%
            "response_time": 5.0,        # Alert if response time exceeds 5 seconds
            "error_rate": 0.1,           # Alert if error rate exceeds 10%
            "user_satisfaction": 0.5     # Alert if satisfaction drops below 50%
        }
        
        # In-memory storage for metrics (replace with time-series DB in production)
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 data points
        self.active_alerts = {}
        self.alert_history = deque(maxlen=500)
        
        # Initialize monitoring task (will be started when needed)
        self._monitoring_task = None
        self._monitoring_started = False
    
    def _start_monitoring(self):
        """Start background monitoring task"""
        if not self._monitoring_started:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    self._monitoring_task = asyncio.create_task(self._monitoring_loop())
                else:
                    # If no event loop is running, start one
                    asyncio.run(self._monitoring_loop())
                self._monitoring_started = True
            except RuntimeError:
                # No event loop available, will start when needed
                self._monitoring_started = False
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await self._check_quality_alerts()
                await self._check_performance_alerts()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    def record_metrics(self, 
                      response_time: float,
                      quality_score: float,
                      user_satisfaction: float = None,
                      error_occurred: bool = False,
                      active_users: int = 1):
        """Record performance metrics"""
        try:
            # Calculate error rate
            recent_metrics = list(self.metrics_history)[-10:]  # Last 10 metrics
            error_count = sum(1 for m in recent_metrics if m.error_rate > 0)
            error_rate = error_count / max(1, len(recent_metrics))
            
            # Calculate throughput (requests per minute)
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)
            recent_requests = [m for m in self.metrics_history if m.timestamp >= one_minute_ago]
            throughput = len(recent_requests)
            
            # Create metrics record
            metrics = PerformanceMetrics(
                timestamp=now,
                response_time=response_time,
                quality_score=quality_score,
                user_satisfaction=user_satisfaction or 0.5,  # Default if not provided
                error_rate=error_rate,
                throughput=throughput,
                active_users=active_users
            )
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            logger.debug(f"Recorded metrics: response_time={response_time:.2f}s, quality={quality_score:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
    
    async def _check_quality_alerts(self):
        """Check for quality-related alerts"""
        try:
            if len(self.metrics_history) < 5:  # Need at least 5 data points
                return
            
            recent_metrics = list(self.metrics_history)[-5:]  # Last 5 metrics
            avg_quality = sum(m.quality_score for m in recent_metrics) / len(recent_metrics)
            avg_satisfaction = sum(m.user_satisfaction for m in recent_metrics) / len(recent_metrics)
            
            # Check quality degradation
            if avg_quality < self.alert_thresholds["quality_degradation"]:
                await self._create_alert(
                    "quality_degradation",
                    "high",
                    f"응답 품질이 저하되었습니다. 평균 품질: {avg_quality:.2f}",
                    {"avg_quality": avg_quality, "threshold": self.alert_thresholds["quality_degradation"]}
                )
            
            # Check user satisfaction
            if avg_satisfaction < self.alert_thresholds["user_satisfaction"]:
                await self._create_alert(
                    "user_satisfaction",
                    "medium",
                    f"사용자 만족도가 낮습니다. 평균 만족도: {avg_satisfaction:.2f}",
                    {"avg_satisfaction": avg_satisfaction, "threshold": self.alert_thresholds["user_satisfaction"]}
                )
                
        except Exception as e:
            logger.error(f"Failed to check quality alerts: {e}")
    
    async def _check_performance_alerts(self):
        """Check for performance-related alerts"""
        try:
            if len(self.metrics_history) < 3:  # Need at least 3 data points
                return
            
            recent_metrics = list(self.metrics_history)[-3:]  # Last 3 metrics
            avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
            avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
            
            # Check response time
            if avg_response_time > self.alert_thresholds["response_time"]:
                await self._create_alert(
                    "response_time",
                    "medium",
                    f"응답 시간이 느립니다. 평균 응답 시간: {avg_response_time:.2f}초",
                    {"avg_response_time": avg_response_time, "threshold": self.alert_thresholds["response_time"]}
                )
            
            # Check error rate
            if avg_error_rate > self.alert_thresholds["error_rate"]:
                await self._create_alert(
                    "error_rate",
                    "high",
                    f"오류율이 높습니다. 평균 오류율: {avg_error_rate:.2%}",
                    {"avg_error_rate": avg_error_rate, "threshold": self.alert_thresholds["error_rate"]}
                )
                
        except Exception as e:
            logger.error(f"Failed to check performance alerts: {e}")
    
    async def _create_alert(self, alert_type: str, severity: str, message: str, metadata: Dict[str, Any]):
        """Create a new alert"""
        try:
            alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{alert_type}"
            
            # Check if similar alert already exists
            if alert_type in self.active_alerts:
                existing_alert = self.active_alerts[alert_type]
                if not existing_alert.resolved and (datetime.now() - existing_alert.timestamp).seconds < 300:  # 5 minutes
                    return  # Don't create duplicate alerts
            
            alert = QualityAlert(
                id=alert_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                timestamp=datetime.now(),
                metadata=metadata
            )
            
            self.active_alerts[alert_type] = alert
            self.alert_history.append(alert)
            
            logger.warning(f"Alert created: {alert_type} - {message}")
            
            # Send notification (in production, this would send to monitoring system)
            await self._send_notification(alert)
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
    
    async def _send_notification(self, alert: QualityAlert):
        """Send alert notification"""
        try:
            # In production, this would send to Slack, email, PagerDuty, etc.
            notification = {
                "alert_id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
            
            logger.info(f"Notification sent: {json.dumps(notification, ensure_ascii=False)}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def get_dashboard_data(self, hours: int = 24) -> Dict[str, Any]:
        """Get dashboard data for monitoring"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return self._get_empty_dashboard()
            
            # Calculate summary statistics
            avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
            avg_quality_score = sum(m.quality_score for m in recent_metrics) / len(recent_metrics)
            avg_user_satisfaction = sum(m.user_satisfaction for m in recent_metrics) / len(recent_metrics)
            avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
            total_requests = len(recent_metrics)
            
            # Calculate trends
            trends = self._calculate_trends(recent_metrics)
            
            # Get active alerts
            active_alerts = [alert for alert in self.active_alerts.values() if not alert.resolved]
            
            # Get quality distribution
            quality_distribution = self._calculate_quality_distribution(recent_metrics)
            
            return {
                "summary": {
                    "total_requests": total_requests,
                    "avg_response_time": round(avg_response_time, 2),
                    "avg_quality_score": round(avg_quality_score, 2),
                    "avg_user_satisfaction": round(avg_user_satisfaction, 2),
                    "avg_error_rate": round(avg_error_rate, 3),
                    "active_alerts": len(active_alerts)
                },
                "trends": trends,
                "quality_distribution": quality_distribution,
                "active_alerts": [
                    {
                        "id": alert.id,
                        "type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "metadata": alert.metadata
                    }
                    for alert in active_alerts
                ],
                "time_range": {
                    "start": cutoff_time.isoformat(),
                    "end": datetime.now().isoformat(),
                    "hours": hours
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return self._get_empty_dashboard()
    
    def _get_empty_dashboard(self) -> Dict[str, Any]:
        """Get empty dashboard data"""
        return {
            "summary": {
                "total_requests": 0,
                "avg_response_time": 0.0,
                "avg_quality_score": 0.0,
                "avg_user_satisfaction": 0.0,
                "avg_error_rate": 0.0,
                "active_alerts": 0
            },
            "trends": {},
            "quality_distribution": {},
            "active_alerts": [],
            "time_range": {
                "start": datetime.now().isoformat(),
                "end": datetime.now().isoformat(),
                "hours": 24
            }
        }
    
    def _calculate_trends(self, metrics: List[PerformanceMetrics]) -> Dict[str, str]:
        """Calculate trends for metrics"""
        try:
            if len(metrics) < 2:
                return {}
            
            # Split metrics into first half and second half
            mid_point = len(metrics) // 2
            first_half = metrics[:mid_point]
            second_half = metrics[mid_point:]
            
            trends = {}
            
            # Response time trend
            first_avg_rt = sum(m.response_time for m in first_half) / len(first_half)
            second_avg_rt = sum(m.response_time for m in second_half) / len(second_half)
            trends["response_time"] = "improving" if second_avg_rt < first_avg_rt else "degrading"
            
            # Quality trend
            first_avg_quality = sum(m.quality_score for m in first_half) / len(first_half)
            second_avg_quality = sum(m.quality_score for m in second_half) / len(second_half)
            trends["quality"] = "improving" if second_avg_quality > first_avg_quality else "degrading"
            
            # User satisfaction trend
            first_avg_satisfaction = sum(m.user_satisfaction for m in first_half) / len(first_half)
            second_avg_satisfaction = sum(m.user_satisfaction for m in second_half) / len(second_half)
            trends["user_satisfaction"] = "improving" if second_avg_satisfaction > first_avg_satisfaction else "degrading"
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to calculate trends: {e}")
            return {}
    
    def _calculate_quality_distribution(self, metrics: List[PerformanceMetrics]) -> Dict[str, int]:
        """Calculate quality score distribution"""
        try:
            distribution = {
                "excellent": 0,  # >= 0.85
                "good": 0,       # 0.70 - 0.84
                "fair": 0,       # 0.55 - 0.69
                "poor": 0        # < 0.55
            }
            
            for metric in metrics:
                score = metric.quality_score
                if score >= 0.85:
                    distribution["excellent"] += 1
                elif score >= 0.70:
                    distribution["good"] += 1
                elif score >= 0.55:
                    distribution["fair"] += 1
                else:
                    distribution["poor"] += 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"Failed to calculate quality distribution: {e}")
            return {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        try:
            for alert in self.active_alerts.values():
                if alert.id == alert_id:
                    alert.resolved = True
                    logger.info(f"Alert resolved: {alert_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False
    
    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get alert history"""
        try:
            alerts = list(self.alert_history)[-limit:]
            return [
                {
                    "id": alert.id,
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "metadata": alert.metadata
                }
                for alert in alerts
            ]
            
        except Exception as e:
            logger.error(f"Failed to get alert history: {e}")
            return []
    
    def update_thresholds(self, new_thresholds: Dict[str, float]) -> bool:
        """Update alert thresholds"""
        try:
            for key, value in new_thresholds.items():
                if key in self.alert_thresholds:
                    self.alert_thresholds[key] = value
            
            logger.info(f"Updated thresholds: {new_thresholds}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update thresholds: {e}")
            return False

# Global monitoring service instance (lazy initialization)
monitoring_service = None

def get_monitoring_service():
    """Get monitoring service instance with lazy initialization"""
    global monitoring_service
    if monitoring_service is None:
        monitoring_service = MonitoringService()
    return monitoring_service
