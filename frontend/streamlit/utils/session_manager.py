"""
Chat Session Manager for handling session lifecycle
"""
import streamlit as st
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import time

class ChatSessionManager:
    """Manages chat session lifecycle and prevents infinite loops"""
    
    def __init__(self):
        self.current_session_id = None
        self.messages = []
        self.is_creating_new_chat = False
        self.last_creation_time = 0
        self.creation_cooldown = 3.0  # 3초 쿨다운
    
    def initialize_session(self):
        """Initialize session state"""
        if "session_manager_initialized" not in st.session_state:
            st.session_state.session_manager_initialized = True
            st.session_state.is_creating_new_chat = False
            st.session_state.last_chat_creation_time = 0
            st.session_state.session_creation_lock = False
    
    def can_create_new_chat(self) -> bool:
        """Check if new chat can be created (cooldown and lock check)"""
        current_time = time.time()
        last_creation = st.session_state.get("last_chat_creation_time", 0)
        is_locked = st.session_state.get("session_creation_lock", False)
        is_processing = st.session_state.get("is_creating_new_chat", False)
        
        # 쿨다운 체크
        if current_time - last_creation < self.creation_cooldown:
            return False
        
        # 락 체크
        if is_locked or is_processing:
            return False
        
        return True
    
    def lock_creation(self):
        """Lock session creation to prevent duplicates"""
        st.session_state.session_creation_lock = True
        st.session_state.is_creating_new_chat = True
        st.session_state.last_chat_creation_time = time.time()
    
    def unlock_creation(self):
        """Unlock session creation"""
        st.session_state.session_creation_lock = False
        st.session_state.is_creating_new_chat = False
    
    def generate_session_id(self, user_id: str) -> str:
        """Generate unique session ID for user"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        random_suffix = str(uuid.uuid4())[:8]
        return f"user_{user_id}_session_{timestamp}_{random_suffix}"
    
    def generate_title_from_first_message(self, messages: List[Dict[str, Any]]) -> str:
        """Generate title from first user message"""
        if not messages:
            return "새 대화"
        
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "").strip()
                # 제목 정리
                clean_title = content.replace("질문:", "").replace("문의:", "").replace("요청:", "").strip()
                if len(clean_title) > 40:
                    clean_title = clean_title[:40] + "..."
                
                # 타임스탬프 추가
                timestamp = datetime.now().strftime("%m/%d %H:%M")
                return f"{clean_title} ({timestamp})"
        
        return "새 대화"
    
    def save_current_session(self, session_id: str = None, messages: List[Dict[str, Any]] = None, user_id: str = None, *args, **kwargs) -> bool:
        """Save current session with title generation"""
        try:
            # Debug information
            print(f"🔍 save_current_session 호출됨:")
            print(f"  - session_id: {session_id}")
            print(f"  - messages 개수: {len(messages) if messages else 0}")
            print(f"  - user_id: {user_id}")
            
            # If no arguments provided, do nothing (for backward compatibility)
            if session_id is None or messages is None or user_id is None:
                print("⚠️ 인자가 부족하여 저장하지 않음")
                return True
                
            if not messages or not session_id:
                print("⚠️ 메시지나 세션 ID가 없어서 저장하지 않음")
                return True
            
            print(f"💾 이전 대화 저장 시작: {len(messages)}개 메시지")
            
            # 제목 생성
            title = self.generate_title_from_first_message(messages)
            
            # API 서비스를 통한 저장
            from controllers.chat_controller import ChatController
            chat_controller = ChatController()
            
            if chat_controller.api_service:
                # 세션 제목 업데이트
                try:
                    print(f"🔍 세션 제목 업데이트 시도: {title}")
                    result = chat_controller.api_service.update_session_title(session_id, title, user_id)
                    print(f"🔍 제목 업데이트 결과: {result}")
                    if not result.get("success", False):
                        print(f"❌ 세션 제목 업데이트 실패: {result.get('error', '알 수 없는 오류')}")
                except Exception as e:
                    print(f"❌ 세션 제목 업데이트 실패: {e}")
                
                # 메시지 저장
                try:
                    print(f"🔍 메시지 저장 시도: {len(messages)}개 메시지")
                    result = chat_controller.api_service.save_session(session_id, messages)
                    print(f"🔍 메시지 저장 결과: {result}")
                    success = result.get("success", False)
                    if success:
                        print("✅ 메시지 저장 성공")
                    else:
                        print(f"❌ 메시지 저장 실패: {result.get('error', '알 수 없는 오류')}")
                    return success
                except Exception as e:
                    print(f"❌ 메시지 저장 실패: {e}")
                    return False
            
            return True
        except Exception as e:
            print(f"세션 저장 중 오류: {e}")
            return False
    
    def start_new_chat(self, user_id: str) -> Dict[str, Any]:
        """Start new chat session with proper error handling"""
        # 중복 실행 방지
        if not self.can_create_new_chat():
            return {
                "success": False,
                "error": "새 채팅 생성이 진행 중이거나 쿨다운 중입니다.",
                "cooldown_remaining": self.creation_cooldown - (time.time() - st.session_state.get("last_chat_creation_time", 0))
            }
        
        # 락 설정
        self.lock_creation()
        
        try:
            # 1. 현재 대화가 있으면 저장
            current_messages = st.session_state.get("messages", [])
            current_session_id = st.session_state.get("session_id")
            
            print(f"🔍 새 채팅 생성 시작:")
            print(f"  - 현재 메시지 개수: {len(current_messages)}")
            print(f"  - 현재 세션 ID: {current_session_id}")
            print(f"  - 사용자 ID: {user_id}")
            
            if current_messages and current_session_id:
                print("💾 이전 대화 저장 시도...")
                print(f"  - 저장할 메시지 개수: {len(current_messages)}")
                print(f"  - 저장할 세션 ID: {current_session_id}")
                print(f"  - 사용자 ID: {user_id}")
                
                save_result = self.save_current_session(current_session_id, current_messages, user_id)
                print(f"💾 저장 결과: {save_result}")
                
                if not save_result:
                    print("⚠️ 이전 대화 저장에 실패했지만 새 채팅을 계속 진행합니다.")
            else:
                print("ℹ️ 저장할 이전 대화가 없음")
            
            # 2. 새 세션 생성
            new_session_id = self.generate_session_id(user_id)
            
            # 3. 백엔드에 새 세션 생성
            from controllers.chat_controller import ChatController
            chat_controller = ChatController()
            
            if chat_controller.api_service:
                response = chat_controller.api_service.create_chat_session(
                    new_session_id,
                    user_id,
                    "새 대화"
                )
                
                if not response.get("success"):
                    return {
                        "success": False,
                        "error": f"세션 생성 실패: {response.get('error', '알 수 없는 오류')}"
                    }
            
            # 4. 세션 상태 업데이트
            print(f"🔍 세션 상태 업데이트 시작:")
            print(f"  - 이전 세션 ID: {st.session_state.get('session_id', 'None')}")
            print(f"  - 새 세션 ID: {new_session_id}")
            print(f"  - 이전 메시지 개수: {len(st.session_state.get('messages', []))}")
            
            st.session_state.session_id = new_session_id
            st.session_state.messages = []
            st.session_state.last_loaded_session = new_session_id
            st.session_state.is_new_session = True  # 새 세션임을 표시
            st.session_state.session_title = "새 대화"
            
            print(f"✅ 새 세션 생성 완료: {new_session_id}")
            print(f"✅ is_new_session 플래그 설정: {st.session_state.is_new_session}")
            print(f"✅ 메시지 초기화 완료")
            print(f"✅ 세션 제목 설정: {st.session_state.session_title}")
            
            # 5. 확인 상태 초기화
            for key in list(st.session_state.keys()):
                if key.startswith("confirm_delete_") or key.startswith("show_"):
                    del st.session_state[key]
            
            return {
                "success": True,
                "session_id": new_session_id,
                "message": "새 채팅이 시작되었습니다!"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"새 채팅 생성 중 오류: {str(e)}"
            }
        finally:
            # 락 해제
            self.unlock_creation()
    
    def save_session(self):
        """Save current session state to persistent storage"""
        try:
            # This method is for saving general session state, not chat messages
            # The actual implementation would depend on your session storage mechanism
            pass
        except Exception as e:
            print(f"세션 저장 중 오류: {e}")
    
    def get_status_message(self) -> Optional[str]:
        """Get current status message for UI"""
        if st.session_state.get("is_creating_new_chat", False):
            return "새 채팅을 생성 중입니다. 잠시만 기다려주세요..."
        
        if not self.can_create_new_chat():
            remaining = self.creation_cooldown - (time.time() - st.session_state.get("last_chat_creation_time", 0))
            if remaining > 0:
                return f"새 채팅을 {remaining:.1f}초 후에 다시 시도할 수 있습니다."
        
        return None

# 전역 인스턴스
session_manager = ChatSessionManager()