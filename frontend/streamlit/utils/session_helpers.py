"""
세션 관리 헬퍼 함수들
"""
import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

def get_user_session_info(user_id: str) -> Dict[str, Any]:
    """사용자 세션 정보 조회"""
    try:
        from services.session_management_service import session_manager
        
        if not session_manager or user_id == "default":
            return {
                "total_sessions": 0,
                "total_messages": 0,
                "current_session_id": "default",
                "last_activity": None,
                "login_time": None
            }
        
        return session_manager.get_session_statistics(user_id)
    except Exception as e:
        st.warning(f"세션 정보 조회 실패: {str(e)}")
        return {
            "total_sessions": 0,
            "total_messages": 0,
            "current_session_id": "default",
            "last_activity": None,
            "login_time": None
        }

def format_session_time(timestamp_str: str) -> str:
    """세션 시간 포맷팅"""
    if not timestamp_str:
        return "없음"
    
    try:
        dt = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days}일 전"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}시간 전"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}분 전"
        else:
            return "방금 전"
    except:
        return "알 수 없음"

def get_session_activity_level(last_activity: str) -> str:
    """세션 활동 수준 반환"""
    if not last_activity:
        return "inactive"
    
    try:
        dt = datetime.fromisoformat(last_activity)
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 30:
            return "inactive"
        elif diff.days > 7:
            return "low"
        elif diff.days > 1:
            return "medium"
        else:
            return "high"
    except:
        return "unknown"

def get_session_activity_color(activity_level: str) -> str:
    """세션 활동 수준에 따른 색상 반환"""
    colors = {
        "high": "#10B981",    # Green
        "medium": "#F59E0B",  # Yellow
        "low": "#F97316",     # Orange
        "inactive": "#6B7280", # Gray
        "unknown": "#6B7280"   # Gray
    }
    return colors.get(activity_level, "#6B7280")

def get_session_activity_emoji(activity_level: str) -> str:
    """세션 활동 수준에 따른 이모지 반환"""
    emojis = {
        "high": "🟢",
        "medium": "🟡",
        "low": "🟠",
        "inactive": "⚫",
        "unknown": "⚪"
    }
    return emojis.get(activity_level, "⚪")

def create_session_export_data(user_id: str) -> Dict[str, Any]:
    """세션 내보내기 데이터 생성"""
    try:
        from services.session_management_service import session_manager
        
        if not session_manager or user_id == "default":
            return {"error": "세션 관리 서비스를 사용할 수 없습니다."}
        
        sessions = session_manager.get_user_sessions(user_id)
        
        export_data = {
            "user_id": user_id,
            "export_time": datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "sessions": []
        }
        
        for session in sessions:
            session_info = session_manager.get_session_info(user_id, session["session_id"])
            if session_info:
                export_data["sessions"].append(session_info)
        
        return export_data
    except Exception as e:
        return {"error": f"내보내기 데이터 생성 실패: {str(e)}"}

def cleanup_old_sessions(user_id: str, days_threshold: int = 30) -> Dict[str, Any]:
    """오래된 세션 정리"""
    try:
        from services.session_management_service import session_manager
        
        if not session_manager or user_id == "default":
            return {"success": False, "error": "세션 관리 서비스를 사용할 수 없습니다."}
        
        sessions = session_manager.get_user_sessions(user_id)
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        deleted_sessions = []
        
        for session in sessions:
            session_id = session["session_id"]
            last_activity = session.get("last_activity", "")
            
            if last_activity:
                try:
                    activity_date = datetime.fromisoformat(last_activity)
                    if activity_date < cutoff_date:
                        if session_manager.delete_session(user_id, session_id):
                            deleted_sessions.append(session_id)
                except:
                    continue
        
        return {
            "success": True,
            "deleted_count": len(deleted_sessions),
            "deleted_sessions": deleted_sessions
        }
    except Exception as e:
        return {"success": False, "error": f"세션 정리 실패: {str(e)}"}

def cleanup_empty_sessions(user_id: str) -> Dict[str, Any]:
    """빈 세션 정리"""
    try:
        from services.session_management_service import session_manager
        
        if not session_manager or user_id == "default":
            return {"success": False, "error": "세션 관리 서비스를 사용할 수 없습니다."}
        
        sessions = session_manager.get_user_sessions(user_id)
        deleted_sessions = []
        
        for session in sessions:
            session_id = session["session_id"]
            message_count = session.get("message_count", 0)
            
            if message_count == 0:
                if session_manager.delete_session(user_id, session_id):
                    deleted_sessions.append(session_id)
        
        return {
            "success": True,
            "deleted_count": len(deleted_sessions),
            "deleted_sessions": deleted_sessions
        }
    except Exception as e:
        return {"success": False, "error": f"빈 세션 정리 실패: {str(e)}"}

def get_session_usage_stats(user_id: str) -> Dict[str, Any]:
    """세션 사용 통계"""
    try:
        from services.session_management_service import session_manager
        
        if not session_manager or user_id == "default":
            return {"error": "세션 관리 서비스를 사용할 수 없습니다."}
        
        sessions = session_manager.get_user_sessions(user_id)
        
        if not sessions:
            return {
                "total_sessions": 0,
                "total_messages": 0,
                "avg_messages_per_session": 0,
                "most_active_session": None,
                "recent_activity": 0,
                "activity_distribution": {}
            }
        
        # Basic stats
        total_sessions = len(sessions)
        total_messages = sum(session.get("message_count", 0) for session in sessions)
        avg_messages = total_messages / total_sessions if total_sessions > 0 else 0
        
        # Most active session
        most_active = max(sessions, key=lambda x: x.get("message_count", 0))
        
        # Recent activity (last 7 days)
        cutoff_date = datetime.now() - timedelta(days=7)
        recent_sessions = [
            session for session in sessions
            if session.get("last_activity") and 
            datetime.fromisoformat(session["last_activity"]) > cutoff_date
        ]
        
        # Activity distribution
        activity_distribution = {"high": 0, "medium": 0, "low": 0, "inactive": 0}
        for session in sessions:
            activity_level = get_session_activity_level(session.get("last_activity", ""))
            if activity_level in activity_distribution:
                activity_distribution[activity_level] += 1
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "avg_messages_per_session": avg_messages,
            "most_active_session": {
                "title": most_active.get("title", "제목 없음"),
                "message_count": most_active.get("message_count", 0),
                "session_id": most_active.get("session_id")
            },
            "recent_activity": len(recent_sessions),
            "activity_distribution": activity_distribution
        }
    except Exception as e:
        return {"error": f"통계 생성 실패: {str(e)}"}

def validate_session_data(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """세션 데이터 유효성 검사"""
    required_fields = ["session_id", "title", "created_at", "last_activity", "message_count"]
    missing_fields = []
    
    for field in required_fields:
        if field not in session_data:
            missing_fields.append(field)
    
    if missing_fields:
        return {
            "valid": False,
            "error": f"필수 필드 누락: {', '.join(missing_fields)}"
        }
    
    # Validate session_id format
    session_id = session_data.get("session_id", "")
    if not session_id or len(session_id) < 10:
        return {
            "valid": False,
            "error": "유효하지 않은 세션 ID"
        }
    
    # Validate message_count
    message_count = session_data.get("message_count", 0)
    if not isinstance(message_count, int) or message_count < 0:
        return {
            "valid": False,
            "error": "유효하지 않은 메시지 수"
        }
    
    return {"valid": True}

def backup_user_sessions(user_id: str, backup_dir: str = "./backups") -> Dict[str, Any]:
    """사용자 세션 백업"""
    try:
        from services.session_management_service import session_manager
        
        if not session_manager or user_id == "default":
            return {"success": False, "error": "세션 관리 서비스를 사용할 수 없습니다."}
        
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        
        # Get session data
        sessions = session_manager.get_user_sessions(user_id)
        backup_data = {
            "user_id": user_id,
            "backup_time": datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "sessions": []
        }
        
        for session in sessions:
            session_info = session_manager.get_session_info(user_id, session["session_id"])
            if session_info:
                backup_data["sessions"].append(session_info)
        
        # Save backup file
        backup_filename = f"user_{user_id}_sessions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "backup_path": backup_path,
            "backup_filename": backup_filename,
            "total_sessions": len(sessions)
        }
    except Exception as e:
        return {"success": False, "error": f"백업 실패: {str(e)}"}

def restore_user_sessions(user_id: str, backup_path: str) -> Dict[str, Any]:
    """사용자 세션 복원"""
    try:
        from services.session_management_service import session_manager
        
        if not session_manager or user_id == "default":
            return {"success": False, "error": "세션 관리 서비스를 사용할 수 없습니다."}
        
        if not os.path.exists(backup_path):
            return {"success": False, "error": "백업 파일을 찾을 수 없습니다."}
        
        # Load backup data
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Validate backup data
        if backup_data.get("user_id") != user_id:
            return {"success": False, "error": "백업 파일의 사용자 ID가 일치하지 않습니다."}
        
        # Restore sessions
        restored_count = 0
        for session_data in backup_data.get("sessions", []):
            # Validate session data
            validation = validate_session_data(session_data)
            if not validation["valid"]:
                continue
            
            # Create session
            session_id = session_data["session_id"]
            session_title = session_data.get("title", "복원된 세션")
            
            # Check if session already exists
            existing_sessions = session_manager.get_user_sessions(user_id)
            if any(s["session_id"] == session_id for s in existing_sessions):
                continue
            
            # Create new session
            new_session_id = session_manager.create_new_session(user_id, session_title)
            if new_session_id:
                # Update session with backup data
                session_manager.update_session_title(user_id, new_session_id, session_title)
                restored_count += 1
        
        return {
            "success": True,
            "restored_count": restored_count,
            "total_in_backup": len(backup_data.get("sessions", []))
        }
    except Exception as e:
        return {"success": False, "error": f"복원 실패: {str(e)}"}
