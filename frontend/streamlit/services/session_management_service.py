"""
사용자별 세션 관리 서비스
st.session_state를 활용한 체계적인 세션 관리
"""
import streamlit as st
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sys

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SessionManagementService:
    """사용자별 세션 관리 서비스"""
    
    def __init__(self):
        self.session_data_dir = "./data/sessions"
        self.user_data_dir = "./data/users"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        os.makedirs(self.session_data_dir, exist_ok=True)
        os.makedirs(self.user_data_dir, exist_ok=True)
    
    def _ensure_user_sessions_initialized(self):
        """user_sessions가 초기화되었는지 확인하고 필요시 초기화"""
        if "user_sessions" not in st.session_state:
            st.session_state.user_sessions = {}
    
    def initialize_user_session(self, user_id: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 세션 초기화"""
        # 사용자별 세션 상태 초기화
        if "user_sessions" not in st.session_state:
            st.session_state.user_sessions = {}
        
        if "current_user_id" not in st.session_state:
            st.session_state.current_user_id = user_id
        
        if "user_info" not in st.session_state:
            st.session_state.user_info = user_info
        
        # 사용자별 세션 데이터 로드
        user_session_data = self._load_user_session_data(user_id)
        
        # 현재 사용자의 세션 정보 설정
        st.session_state.user_sessions[user_id] = {
            "user_id": user_id,
            "user_info": user_info,
            "current_session_id": user_session_data.get("current_session_id", self._generate_default_session_id(user_id)),
            "sessions": user_session_data.get("sessions", {}),
            "preferences": user_session_data.get("preferences", {}),
            "last_activity": datetime.now().isoformat(),
            "login_time": datetime.now().isoformat()
        }
        
        # 현재 세션 ID 설정
        st.session_state.session_id = st.session_state.user_sessions[user_id]["current_session_id"]
        
        # 메시지 히스토리 초기화 (기존 사용자 세션이 있는 경우 보존)
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # 사용자별 메시지 히스토리 로드 시도
        self._load_user_messages(user_id)
        
        # 사용자별 설정 초기화
        self._initialize_user_preferences(user_id)
        
        return st.session_state.user_sessions[user_id]
    
    def _load_user_messages(self, user_id: str):
        """사용자별 메시지 히스토리 로드"""
        try:
            # 현재 사용자의 세션 ID 가져오기
            current_session_id = st.session_state.user_sessions[user_id]["current_session_id"]
            
            # 파일 시스템에서 로드 시도
            if self._load_session_from_file(current_session_id):
                if st.session_state.get("debug_mode", False):
                    st.write(f"🔍 Debug - Loaded user {user_id} messages from file: {len(st.session_state.messages)} messages")
                return True
            
            # 백엔드에서 로드 시도
            from controllers.chat_controller import ChatController
            chat_controller = ChatController()
            
            if chat_controller.check_backend_connection():
                response = chat_controller.api_service.get_chat_history(current_session_id)
                if response.get("success"):
                    messages = []
                    for msg in response["messages"]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"],
                            "timestamp": msg["timestamp"],
                            "context": [],
                            "metadata": {}
                        })
                    
                    st.session_state.messages = messages
                    if st.session_state.get("debug_mode", False):
                        st.write(f"🔍 Debug - Loaded user {user_id} messages from backend: {len(messages)} messages")
                    return True
            
            if st.session_state.get("debug_mode", False):
                st.write(f"🔍 Debug - No messages found for user {user_id}")
            return False
            
        except Exception as e:
            if st.session_state.get("debug_mode", False):
                st.write(f"🔍 Debug - Error loading user {user_id} messages: {str(e)}")
            return False
    
    def _load_session_from_file(self, session_id: str) -> bool:
        """파일 시스템에서 세션 로드"""
        try:
            import json
            import os
            
            file_path = os.path.join("./data", f"session_{session_id}.json")
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Convert file messages to frontend format
            messages = []
            for msg in session_data.get("messages", []):
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                    "timestamp": msg["timestamp"],
                    "context": [],
                    "metadata": msg.get("metadata", {})
                })
            
            st.session_state.messages = messages
            st.session_state.session_id = session_id
            return True
            
        except Exception as e:
            if st.session_state.get("debug_mode", False):
                st.write(f"🔍 Debug - Error loading session from file: {str(e)}")
            return False
    
    def _generate_default_session_id(self, user_id: str) -> str:
        """사용자별 기본 세션 ID 생성"""
        return f"user_{user_id}_default_session"
    
    def _load_user_session_data(self, user_id: str) -> Dict[str, Any]:
        """사용자별 세션 데이터 로드"""
        try:
            file_path = os.path.join(self.user_data_dir, f"user_{user_id}_sessions.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            st.warning(f"사용자 세션 데이터 로드 실패: {str(e)}")
        
        return {
            "current_session_id": self._generate_default_session_id(user_id),
            "sessions": {},
            "preferences": {}
        }
    
    def _save_user_session_data(self, user_id: str):
        """사용자별 세션 데이터 저장"""
        try:
            if user_id in st.session_state.user_sessions:
                user_data = st.session_state.user_sessions[user_id].copy()
                # 민감한 정보 제거
                if "user_info" in user_data:
                    user_data["user_info"] = {
                        "id": user_data["user_info"].get("id"),
                        "username": user_data["user_info"].get("username"),
                        "email": user_data["user_info"].get("email")
                    }
                
                file_path = os.path.join(self.user_data_dir, f"user_{user_id}_sessions.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(user_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.warning(f"사용자 세션 데이터 저장 실패: {str(e)}")
    
    def _initialize_user_preferences(self, user_id: str):
        """사용자별 기본 설정 초기화"""
        self._ensure_user_sessions_initialized()
        
        if user_id not in st.session_state.user_sessions:
            return
        
        user_session = st.session_state.user_sessions[user_id]
        preferences = user_session.get("preferences", {})
        
        # 기본 설정값들
        default_preferences = {
            "theme": "light",
            "language": "ko",
            "rag_mode": "LangChain RAG",
            "model_type": "fast",
            "streaming_enabled": True,
            "selected_collections": [],
            "collection_aliases": {},
            "collection_groups": {},
            "ui_preferences": {
                "sidebar_expanded": True,
                "show_timestamps": True,
                "show_confidence_scores": True,
                "auto_save": True
            }
        }
        
        # 기존 설정과 기본 설정 병합
        for key, value in default_preferences.items():
            if key not in preferences:
                preferences[key] = value
        
        user_session["preferences"] = preferences
        st.session_state.user_sessions[user_id] = user_session
    
    def create_new_session(self, user_id: str, session_title: str = None) -> str:
        """새 채팅 세션 생성"""
        self._ensure_user_sessions_initialized()
        
        if user_id not in st.session_state.user_sessions:
            st.error("사용자 세션이 초기화되지 않았습니다.")
            return None
        
        # 새 세션 ID 생성
        new_session_id = str(uuid.uuid4())
        
        # 세션 제목 설정
        if not session_title:
            timestamp = datetime.now().strftime("%m/%d %H:%M")
            session_title = f"새 대화 ({timestamp})"
        
        # 새 세션 정보 생성
        new_session = {
            "session_id": new_session_id,
            "title": session_title,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0,
            "messages": [],
            "metadata": {
                "user_id": user_id,
                "is_active": True,
                "tags": [],
                "favorite": False
            }
        }
        
        # 사용자 세션에 추가
        user_session = st.session_state.user_sessions[user_id]
        user_session["sessions"][new_session_id] = new_session
        user_session["current_session_id"] = new_session_id
        user_session["last_activity"] = datetime.now().isoformat()
        
        # 현재 세션 상태 업데이트
        st.session_state.session_id = new_session_id
        st.session_state.messages = []
        st.session_state.is_new_session = True
        
        # 세션 데이터 저장
        self._save_user_session_data(user_id)
        
        return new_session_id
    
    def switch_to_session(self, user_id: str, session_id: str) -> bool:
        """다른 세션으로 전환"""
        self._ensure_user_sessions_initialized()
        
        if user_id not in st.session_state.user_sessions:
            st.error("사용자 세션이 초기화되지 않았습니다.")
            return False
        
        user_session = st.session_state.user_sessions[user_id]
        
        if session_id not in user_session["sessions"]:
            st.error("세션을 찾을 수 없습니다.")
            return False
        
        # 현재 세션 저장
        self.save_current_session(user_id)
        
        # 새 세션으로 전환
        target_session = user_session["sessions"][session_id]
        user_session["current_session_id"] = session_id
        user_session["last_activity"] = datetime.now().isoformat()
        
        # 세션 상태 업데이트
        st.session_state.session_id = session_id
        st.session_state.messages = target_session.get("messages", [])
        st.session_state.is_new_session = False
        
        # 세션 데이터 저장
        self._save_user_session_data(user_id)
        
        return True
    
    def save_current_session(self, user_id: str) -> bool:
        """현재 세션 저장"""
        self._ensure_user_sessions_initialized()
        
        if user_id not in st.session_state.user_sessions:
            return False
        
        user_session = st.session_state.user_sessions[user_id]
        current_session_id = st.session_state.get("session_id")
        
        if current_session_id in user_session["sessions"]:
            # 기존 세션 업데이트
            user_session["sessions"][current_session_id]["messages"] = st.session_state.get("messages", [])
            user_session["sessions"][current_session_id]["last_activity"] = datetime.now().isoformat()
            user_session["sessions"][current_session_id]["message_count"] = len(st.session_state.get("messages", []))
        else:
            # 새 세션 생성
            new_session = {
                "session_id": current_session_id,
                "title": st.session_state.get("session_title", f"세션 {current_session_id[:8]}..."),
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "message_count": len(st.session_state.get("messages", [])),
                "messages": st.session_state.get("messages", []),
                "metadata": {
                    "user_id": user_id,
                    "is_active": True,
                    "tags": [],
                    "favorite": False
                }
            }
            user_session["sessions"][current_session_id] = new_session
        
        # 세션 데이터 저장
        self._save_user_session_data(user_id)
        
        return True
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자의 모든 세션 목록 반환 (기본 세션 제외)"""
        self._ensure_user_sessions_initialized()
        
        if user_id not in st.session_state.user_sessions:
            return []
        
        user_session = st.session_state.user_sessions[user_id]
        sessions = []
        
        for session_id, session_data in user_session["sessions"].items():
            # 기본 세션은 목록에서 제외
            if session_id == "default" or session_id.endswith("_default_session"):
                continue
                
            sessions.append({
                "session_id": session_id,
                "title": session_data.get("title", "제목 없음"),
                "created_at": session_data.get("created_at"),
                "last_activity": session_data.get("last_activity"),
                "message_count": session_data.get("message_count", 0),
                "is_current": session_id == user_session["current_session_id"],
                "metadata": session_data.get("metadata", {})
            })
        
        # 최근 활동 순으로 정렬
        sessions.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
        
        return sessions
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """세션 삭제"""
        if user_id not in st.session_state.user_sessions:
            return False
        
        user_session = st.session_state.user_sessions[user_id]
        
        # 기본 세션은 삭제 불가
        default_session_id = self._generate_default_session_id(user_id)
        if session_id == default_session_id:
            st.error("기본 세션은 삭제할 수 없습니다.")
            return False
        
        # 세션 삭제
        if session_id in user_session["sessions"]:
            del user_session["sessions"][session_id]
            
            # 현재 세션이 삭제된 세션이면 기본 세션으로 전환
            if user_session["current_session_id"] == session_id:
                user_session["current_session_id"] = default_session_id
                st.session_state.session_id = default_session_id
                st.session_state.messages = []
                st.session_state.is_new_session = True
            
            # 세션 데이터 저장
            self._save_user_session_data(user_id)
            return True
        
        return False
    
    def update_session_title(self, user_id: str, session_id: str, new_title: str) -> bool:
        """세션 제목 업데이트"""
        if user_id not in st.session_state.user_sessions:
            return False
        
        user_session = st.session_state.user_sessions[user_id]
        
        if session_id in user_session["sessions"]:
            user_session["sessions"][session_id]["title"] = new_title
            user_session["last_activity"] = datetime.now().isoformat()
            
            # 세션 데이터 저장
            self._save_user_session_data(user_id)
            return True
        
        return False
    
    def get_session_info(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 정보 조회"""
        if user_id not in st.session_state.user_sessions:
            return None
        
        user_session = st.session_state.user_sessions[user_id]
        
        if session_id in user_session["sessions"]:
            return user_session["sessions"][session_id]
        
        return None
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """사용자 설정 업데이트"""
        if user_id not in st.session_state.user_sessions:
            return False
        
        user_session = st.session_state.user_sessions[user_id]
        user_session["preferences"].update(preferences)
        user_session["last_activity"] = datetime.now().isoformat()
        
        # 세션 데이터 저장
        self._save_user_session_data(user_id)
        
        return True
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """사용자 설정 조회"""
        if user_id not in st.session_state.user_sessions:
            return {}
        
        return st.session_state.user_sessions[user_id].get("preferences", {})
    
    def clear_user_sessions(self, user_id: str, keep_default: bool = True) -> bool:
        """사용자의 모든 세션 삭제"""
        if user_id not in st.session_state.user_sessions:
            return False
        
        user_session = st.session_state.user_sessions[user_id]
        default_session_id = self._generate_default_session_id(user_id)
        
        # 기본 세션 제외하고 모든 세션 삭제
        sessions_to_delete = []
        for session_id in list(user_session["sessions"].keys()):
            if not keep_default or session_id != default_session_id:
                sessions_to_delete.append(session_id)
        
        for session_id in sessions_to_delete:
            del user_session["sessions"][session_id]
        
        # 기본 세션으로 전환
        user_session["current_session_id"] = default_session_id
        st.session_state.session_id = default_session_id
        st.session_state.messages = []
        st.session_state.is_new_session = True
        
        # 세션 데이터 저장
        self._save_user_session_data(user_id)
        
        return True
    
    def logout_user(self, user_id: str) -> bool:
        """사용자 로그아웃 처리"""
        if user_id not in st.session_state.user_sessions:
            return False
        
        # 현재 세션 저장
        self.save_current_session(user_id)
        
        # 사용자 세션 제거
        del st.session_state.user_sessions[user_id]
        
        # 전역 세션 상태 초기화
        for key in list(st.session_state.keys()):
            if key not in ["user_sessions"]:  # user_sessions는 유지
                del st.session_state[key]
        
        return True
    
    def get_session_statistics(self, user_id: str) -> Dict[str, Any]:
        """사용자 세션 통계 조회 (기본 세션 제외)"""
        if user_id not in st.session_state.user_sessions:
            return {}
        
        user_session = st.session_state.user_sessions[user_id]
        sessions = user_session["sessions"]
        
        # 기본 세션 제외한 세션들만 통계에 포함
        filtered_sessions = {
            session_id: session_data for session_id, session_data in sessions.items()
            if session_id != "default" and not session_id.endswith("_default_session")
        }
        
        total_sessions = len(filtered_sessions)
        total_messages = sum(session.get("message_count", 0) for session in filtered_sessions.values())
        
        # 최근 활동 통계
        recent_sessions = [
            session for session in filtered_sessions.values()
            if session.get("last_activity") and 
            datetime.fromisoformat(session["last_activity"]) > datetime.now() - timedelta(days=7)
        ]
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "recent_sessions_7days": len(recent_sessions),
            "current_session_id": user_session["current_session_id"],
            "last_activity": user_session["last_activity"],
            "login_time": user_session["login_time"]
        }
    
    def search_sessions(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """세션 검색 (기본 세션 제외)"""
        if user_id not in st.session_state.user_sessions:
            return []
        
        user_session = st.session_state.user_sessions[user_id]
        sessions = user_session["sessions"]
        
        query_lower = query.lower()
        matching_sessions = []
        
        for session_id, session_data in sessions.items():
            # 기본 세션은 검색 결과에서 제외
            if session_id == "default" or session_id.endswith("_default_session"):
                continue
                
            # 제목에서 검색
            title = session_data.get("title", "").lower()
            if query_lower in title:
                matching_sessions.append({
                    "session_id": session_id,
                    "title": session_data.get("title", "제목 없음"),
                    "created_at": session_data.get("created_at"),
                    "last_activity": session_data.get("last_activity"),
                    "message_count": session_data.get("message_count", 0),
                    "is_current": session_id == user_session["current_session_id"],
                    "match_type": "title"
                })
                continue
            
            # 메시지 내용에서 검색
            messages = session_data.get("messages", [])
            for message in messages:
                content = message.get("content", "").lower()
                if query_lower in content:
                    matching_sessions.append({
                        "session_id": session_id,
                        "title": session_data.get("title", "제목 없음"),
                        "created_at": session_data.get("created_at"),
                        "last_activity": session_data.get("last_activity"),
                        "message_count": session_data.get("message_count", 0),
                        "is_current": session_id == user_session["current_session_id"],
                        "match_type": "content"
                    })
                    break
        
        # 최근 활동 순으로 정렬
        matching_sessions.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
        
        return matching_sessions

# 전역 인스턴스
session_manager = SessionManagementService()
