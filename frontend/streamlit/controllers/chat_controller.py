"""
Chat controller for managing chat functionality in Streamlit
"""
import streamlit as st
from typing import Dict, Any, List, Optional
import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.api_service import APIService
except ImportError:
    APIService = None
import uuid
from datetime import datetime

class ChatController:
    """Controller for chat-related functionality"""

    def __init__(self):
        try:
            self.api_service = APIService(base_url="http://localhost:9502")
        except:
            self.api_service = None
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize Streamlit session state"""
        if "session_id" not in st.session_state:
            # Get user-specific default session ID
            user_info = st.session_state.get("user_info") or {}
            current_user_id = user_info.get("id", "default")
            if current_user_id == "default":
                st.session_state.session_id = "default"
            else:
                st.session_state.session_id = f"user_{current_user_id}_default_session"
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "backend_connected" not in st.session_state:
            st.session_state.backend_connected = False
        if "last_loaded_session" not in st.session_state:
            st.session_state.last_loaded_session = None

    def check_backend_connection(self) -> bool:
        """Check if backend is connected"""
        if self.api_service:
            connected = self.api_service.health_check()
            st.session_state.backend_connected = connected
            return connected
        else:
            st.session_state.backend_connected = False
            return False

    def send_message(self, message: str, model_type: str = "fast") -> Optional[Dict[str, Any]]:
        """Send a message and return response with context"""
        if not message.strip():
            st.error("메시지를 입력해주세요.")
            return None

        # Check backend connection
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return None

        # Send message to backend with RAG mode
        if not self.api_service:
            st.error("API 서비스가 사용할 수 없습니다.")
            return None
            
        rag_mode = st.session_state.get("rag_mode", "LangChain RAG")
        collection_names = st.session_state.get("selected_collections", None)
        response = self.api_service.send_message(message, st.session_state.session_id, use_rag=True, rag_mode=rag_mode, model_type=model_type, collection_names=collection_names)

        if response["success"]:
            return {
                "content": response["assistant_message"]["content"],
                "context": response.get("context", []),
                "metadata": response.get("metadata", {})
            }
        else:
            st.error(f"오류가 발생했습니다: {response.get('error', '알 수 없는 오류')}")
            return None

    def clear_chat(self):
        """Clear current chat session"""
        if st.session_state.backend_connected and self.api_service:
            self.api_service.clear_session(st.session_state.session_id)

        # Switch to user-specific default session
        user_info = st.session_state.get("user_info") or {}
        current_user_id = user_info.get("id", "default")
        if current_user_id == "default":
            new_session_id = "default"
        else:
            new_session_id = f"user_{current_user_id}_default_session"
            
        st.session_state.messages = []
        st.session_state.session_id = new_session_id
        st.success("채팅이 초기화되었습니다.")
    
    def save_current_session(self):
        """Save current session to backend"""
        if not st.session_state.backend_connected or not self.api_service:
            return False
        
        try:
            current_messages = st.session_state.get("messages", [])
            current_session_id = st.session_state.get("session_id", "default")
            
            if current_messages:
                # Use the new save_session method for better reliability
                result = self.api_service.save_session(current_session_id, current_messages)
                if result.get("success", False):
                    # Also save to file system as backup
                    self._save_session_to_file(current_session_id, current_messages)
                    return True
                else:
                    # If backend save fails, still try file save
                    file_success = self._save_session_to_file(current_session_id, current_messages)
                    return file_success
            return False
        except Exception as e:
            # Try file save as fallback
            try:
                current_session_id = st.session_state.get("session_id", "default")
                current_messages = st.session_state.get("messages", [])
                if current_messages:
                    return self._save_session_to_file(current_session_id, current_messages)
            except:
                pass
            return False

    def _save_session_to_file(self, session_id: str, messages: List[Dict[str, Any]]) -> bool:
        """Save session to file system directly"""
        try:
            import json
            import os
            from datetime import datetime
            
            # Create data directory if it doesn't exist
            data_dir = "./data"
            os.makedirs(data_dir, exist_ok=True)
            
            # Prepare session data
            session_data = {
                "id": session_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "messages": messages
            }
            
            # Save to file
            file_path = os.path.join(data_dir, f"session_{session_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            st.error(f"파일 저장 중 오류가 발생했습니다: {str(e)}")
            return False

    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get current chat history"""
        return st.session_state.messages

    def load_session_history(self, session_id: str):
        """Load chat history from backend and file system"""
        if st.session_state.get("debug_mode", False):
            st.write(f"🔍 Debug - Loading session history for: {session_id}")
        
        # Try to load from file system first
        if self._load_session_from_file(session_id):
            if st.session_state.get("debug_mode", False):
                st.write(f"🔍 Debug - Loaded from file system: {len(st.session_state.messages)} messages")
            return
        
        if st.session_state.get("debug_mode", False):
            st.write(f"🔍 Debug - File loading failed, trying backend")
        
        # If file loading fails, try backend
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다.")
            return

        response = self.api_service.get_chat_history(session_id)
        if response["success"]:
            # Convert backend messages to frontend format
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
            st.session_state.session_id = session_id
            
            if st.session_state.get("debug_mode", False):
                st.write(f"🔍 Debug - Loaded from backend: {len(messages)} messages")
            
            # Don't show success message for automatic loading
            if session_id != st.session_state.get("last_loaded_session", ""):
                st.success(f"채팅 기록을 불러왔습니다. ({len(messages)}개 메시지)")
        else:
            if st.session_state.get("debug_mode", False):
                st.write(f"🔍 Debug - Backend loading failed: {response.get('error', '알 수 없는 오류')}")
            st.error(f"채팅 기록을 불러올 수 없습니다: {response.get('error', '알 수 없는 오류')}")

    def _load_session_from_file(self, session_id: str) -> bool:
        """Load session from file system"""
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
            
            if session_id != st.session_state.get("last_loaded_session", ""):
                st.success(f"채팅 기록을 불러왔습니다. ({len(messages)}개 메시지)")
            
            return True
        except Exception as e:
            st.error(f"파일에서 채팅 기록을 불러올 수 없습니다: {str(e)}")
            return False
    
    def switch_to_session(self, session_id: str):
        """Switch to a different session and load its history"""
        if session_id != st.session_state.get("session_id", ""):
            # Clear new session flag when switching to existing session
            st.session_state.is_new_session = False
            self.load_session_history(session_id)
            st.session_state.last_loaded_session = session_id  # Update last loaded session
            # Note: st.rerun() is called by the component that calls this method

    def get_available_sessions(self) -> List[str]:
        """Get list of available sessions from file system and backend"""
        all_sessions = []
        
        # Get sessions from file system
        file_sessions = self._get_sessions_from_file()
        if file_sessions:
            all_sessions.extend(file_sessions)
        
        # Get sessions from backend if available
        if self.check_backend_connection() and self.api_service:
            response = self.api_service.get_sessions()
            if response.get("success") and response.get("sessions"):
                all_sessions.extend(response["sessions"])
        
        # Remove duplicates while preserving order
        if all_sessions:
            seen = set()
            unique_sessions = []
            for session in all_sessions:
                if session not in seen:
                    seen.add(session)
                    unique_sessions.append(session)
            return unique_sessions
        
        return []
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get list of sessions for a specific user"""
        if not self.check_backend_connection() or not self.api_service:
            # Fallback to file system with user filtering
            return self._get_user_sessions_from_file(user_id)
        
        try:
            response = self.api_service.get_user_sessions(user_id)
            if response.get("success") and response.get("sessions"):
                # Extract session IDs from the response
                sessions = []
                for session in response["sessions"]:
                    if isinstance(session, dict):
                        sessions.append(session.get("session_id", ""))
                    else:
                        sessions.append(str(session))
                return [s for s in sessions if s]  # Filter out empty strings
            else:
                # Fallback to file system if backend fails
                return self._get_user_sessions_from_file(user_id)
        except Exception as e:
            st.warning(f"사용자 세션 조회 실패, 파일 시스템으로 대체: {str(e)}")
            return self._get_user_sessions_from_file(user_id)
    
    def _get_user_sessions_from_file(self, user_id: str) -> List[str]:
        """Get user-specific sessions from file system"""
        try:
            import os
            
            data_dir = "./data"
            if not os.path.exists(data_dir):
                return []
            
            user_sessions = []
            for filename in os.listdir(data_dir):
                if filename.startswith("session_") and filename.endswith(".json"):
                    session_id = filename[8:-5]  # Remove "session_" prefix and ".json" suffix
                    # Check if session belongs to the user (based on session ID pattern)
                    if session_id.startswith(f"user_{user_id}_"):
                        user_sessions.append(session_id)
            
            # Sort by modification time (newest first)
            user_sessions.sort(key=lambda x: os.path.getmtime(os.path.join(data_dir, f"session_{x}.json")), reverse=True)
            return user_sessions
        except Exception as e:
            st.error(f"파일에서 사용자 세션 목록을 불러올 수 없습니다: {str(e)}")
            return []

    def _get_sessions_from_file(self) -> List[str]:
        """Get sessions from file system"""
        try:
            import os
            
            data_dir = "./data"
            if not os.path.exists(data_dir):
                return []
            
            sessions = []
            for filename in os.listdir(data_dir):
                if filename.startswith("session_") and filename.endswith(".json"):
                    session_id = filename[8:-5]  # Remove "session_" prefix and ".json" suffix
                    sessions.append(session_id)
            
            # Sort by modification time (newest first)
            sessions.sort(key=lambda x: os.path.getmtime(os.path.join(data_dir, f"session_{x}.json")), reverse=True)
            return sessions
        except Exception as e:
            st.error(f"파일에서 세션 목록을 불러올 수 없습니다: {str(e)}")
            return []

    def check_session_exists(self, session_id: str) -> bool:
        """Check if a specific session exists without loading all sessions"""
        if not self.check_backend_connection() or not self.api_service:
            return False

        response = self.api_service.check_session_exists(session_id)
        if response["success"]:
            return response["exists"]
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        try:
            user_info = st.session_state.get("user_info") or {}
            current_user_id = user_info.get("id", "default")
            user_default_session = f"user_{current_user_id}_default_session" if current_user_id != "default" else "default"
            
            if session_id == user_default_session:
                st.error("기본 세션은 삭제할 수 없습니다.")
                return False
            
            # If we're deleting the current session, switch to user default first
            if st.session_state.get("session_id") == session_id:
                st.session_state.session_id = user_default_session
                st.session_state.messages = []
                st.session_state.last_loaded_session = None
                st.session_state.is_new_session = True
            
            # Delete from file system first
            file_success = self._delete_session_from_file(session_id)
            
            # Try to delete from backend if available
            backend_success = True
            if self.api_service and self.check_backend_connection():
                try:
                    response = self.api_service.delete_session(session_id)
                    if not response.get("success", False):
                        backend_success = False
                        st.warning(f"백엔드에서 세션 삭제에 실패했습니다: {response.get('error', '알 수 없는 오류')}")
                except Exception as e:
                    backend_success = False
                    st.warning(f"백엔드 삭제 중 오류가 발생했습니다: {str(e)}")
            
            # Clear any related session state
            for key in list(st.session_state.keys()):
                if key.startswith("confirm_delete_") or key.startswith("show_"):
                    del st.session_state[key]
            
            if file_success:
                return True
            else:
                return False
            
        except Exception as e:
            st.error(f"세션 삭제 중 오류가 발생했습니다: {str(e)}")
            return False

    def _delete_session_from_file(self, session_id: str) -> bool:
        """Delete session from file system"""
        try:
            import os
            
            file_path = os.path.join("./data", f"session_{session_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            st.error(f"파일에서 세션 삭제 중 오류가 발생했습니다: {str(e)}")
            return False

    def _clear_all_sessions_from_file(self) -> List[str]:
        """Clear all sessions from file system except default"""
        try:
            import os
            
            data_dir = "./data"
            if not os.path.exists(data_dir):
                return []
            
            cleared_sessions = []
            for filename in os.listdir(data_dir):
                if filename.startswith("session_") and filename.endswith(".json"):
                    session_id = filename[8:-5]  # Remove "session_" prefix and ".json" suffix
                    if session_id != "default":
                        file_path = os.path.join(data_dir, filename)
                        os.remove(file_path)
                        cleared_sessions.append(session_id)
            
            return cleared_sessions
        except Exception as e:
            st.error(f"파일에서 전체 세션 삭제 중 오류가 발생했습니다: {str(e)}")
            return []

    def clear_all_sessions(self) -> Dict[str, Any]:
        """Clear all sessions except user default"""
        try:
            # Clear current session immediately
            user_info = st.session_state.get("user_info") or {}
            current_user_id = user_info.get("id", "default")
            user_default_session = f"user_{current_user_id}_default_session" if current_user_id != "default" else "default"
            
            st.session_state.session_id = user_default_session
            st.session_state.messages = []
            st.session_state.last_loaded_session = user_default_session
            st.session_state.is_new_session = True
            
            # Clear any confirmation states
            for key in list(st.session_state.keys()):
                if key.startswith("confirm_delete_") or key.startswith("show_"):
                    del st.session_state[key]
            
            # Clear all sessions from file system
            cleared_sessions = self._clear_all_sessions_from_file()
            
            # Try to clear backend sessions if available
            if self.api_service and self.check_backend_connection():
                try:
                    response = self.api_service.clear_all_sessions()
                    if response.get("success", False):
                        return {
                            "success": True,
                            "message": f"모든 채팅이 삭제되었습니다. ({len(cleared_sessions)}개 세션)",
                            "cleared_sessions": cleared_sessions
                        }
                    else:
                        return {
                            "success": True,
                            "message": f"모든 채팅이 삭제되었습니다. ({len(cleared_sessions)}개 세션)",
                            "warning": "백엔드 삭제 실패"
                        }
                except Exception as e:
                    return {
                        "success": True,
                        "message": f"모든 채팅이 삭제되었습니다. ({len(cleared_sessions)}개 세션)",
                        "warning": f"백엔드 연결 실패: {str(e)}"
                    }
            else:
                return {
                    "success": True,
                    "message": f"모든 채팅이 삭제되었습니다. ({len(cleared_sessions)}개 세션)"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"전체 삭제 중 오류 발생: {str(e)}"
            }
    
    def send_message_langchain(self, message: str, model_type: str = "fast", use_rag: bool = True) -> Optional[Dict[str, Any]]:
        """Send a message using LangChain RAG"""
        if not message.strip():
            st.error("메시지를 입력해주세요.")
            return None

        # Check backend connection
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return None

        # Send message to backend using LangChain
        rag_mode = st.session_state.get("rag_mode", "LangChain RAG")
        collection_names = st.session_state.get("selected_collections", None)
        response = self.api_service.send_message_langchain(message, st.session_state.session_id, use_rag, rag_mode, model_type, collection_names)

        if response["success"]:
            return {
                "content": response["assistant_message"]["content"],
                "context": response.get("context", []),
                "metadata": response.get("metadata", {})
            }
        else:
            st.error(f"LangChain RAG 오류가 발생했습니다: {response.get('error', '알 수 없는 오류')}")
            return None
    
    def send_message_stream(self, message: str, model_type: str = "fast", use_rag: bool = True) -> Optional[str]:
        """Send message with streaming response"""
        if not message.strip():
            st.error("메시지를 입력해주세요.")
            return None

        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return None

        # Create message container for streaming
        message_container = st.empty()
        context_container = st.empty()
        status_container = st.empty()
        full_response = ""
        context_sources = []
        
        try:
            # Get streaming response
            rag_mode = st.session_state.get("rag_mode", "LangChain RAG")
            use_langchain = (rag_mode == "LangChain RAG")
            
            # Show initial status with enhanced styling
            with status_container.container():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%); 
                            color: white; padding: 1rem; border-radius: 10px; 
                            text-align: center; margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                        <div style="animation: pulse 1.5s ease-in-out infinite; font-size: 1.2rem;">🤖</div>
                        <span style="font-size: 1.1rem; font-weight: 500;">AI가 응답을 생성하고 있습니다...</span>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem; opacity: 0.8;">
                        벡터 검색 및 답변 생성 중
                    </div>
                </div>
                <style>
                @keyframes pulse {
                    0%, 100% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.1); opacity: 0.7; }
                }
                </style>
                """, unsafe_allow_html=True)
            
            collection_names = st.session_state.get("selected_collections", None)
            for chunk in self.api_service.send_message_stream(message, st.session_state.session_id, use_langchain, rag_mode, model_type, collection_names):
                if "error" in chunk:
                    if chunk.get("retrying", False):
                        # Show retry status
                        with status_container.container():
                            st.warning(f"🔄 {chunk['error']}")
                    else:
                        # Show final error
                        with status_container.container():
                            st.error(f"❌ {chunk['error']}")
                        return None
                
                if chunk.get("type") == "context":
                    context_sources = chunk.get("sources", [])
                    similarity_scores = chunk.get("similarity_scores", [])
                    context_count = chunk.get("context_count", 0)
                    source_collections = chunk.get("source_collections", [])
                    collections_used = chunk.get("collections_used", [])
                    multi_collection = chunk.get("multi_collection", False)
                    
                    if context_sources:
                        with context_container.container():
                            # Enhanced context display with similarity scores
                            st.markdown("### 📚 참고 문서")
                            
                            # Show collection information
                            if multi_collection and collections_used:
                                st.info(f"🔍 검색된 컬렉션: {', '.join(collections_used)}")
                            elif source_collections:
                                st.info(f"🔍 검색된 컬렉션: {', '.join(source_collections)}")
                            
                            # Create a more detailed context display
                            for i, (source, similarity) in enumerate(zip(context_sources, similarity_scores), 1):
                                similarity_percent = similarity * 100 if similarity else 0
                                st.markdown(f"""
                                <div style="background: #e3f2fd; padding: 0.5rem; border-radius: 5px; 
                                            margin: 0.25rem 0; border-left: 3px solid #2196F3;">
                                    <strong>{i}. {source}</strong> 
                                    <span style="color: #666; font-size: 0.9em;">(유사도: {similarity_percent:.1f}%)</span>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            if context_count > 0:
                                if multi_collection:
                                    st.caption(f"총 {context_count}개의 관련 문서를 {len(collections_used)}개 컬렉션에서 참조했습니다.")
                                else:
                                    st.caption(f"총 {context_count}개의 관련 문서를 참조했습니다.")
                        
                        # Clear status when context is received
                        status_container.empty()
                
                if chunk.get("content"):
                    full_response += chunk["content"]
                    with message_container.container():
                        # Enhanced typing effect with better styling
                        st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; 
                                    border-left: 4px solid #8B5CF6; margin: 0.5rem 0; 
                                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                    line-height: 1.6;">
                            {full_response}<span style="animation: blink 1s infinite;">▌</span>
                        </div>
                        <style>
                        @keyframes blink {{
                            0%, 50% {{ opacity: 1; }}
                            51%, 100% {{ opacity: 0; }}
                        }}
                        </style>
                        """, unsafe_allow_html=True)
                    
                    # Show streaming status
                    with status_container.container():
                        st.markdown("""
                        <div style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); 
                                    color: white; padding: 0.75rem; border-radius: 8px; 
                                    text-align: center; margin: 0.5rem 0;">
                            <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                                <div style="animation: pulse 1s ease-in-out infinite; font-size: 1rem;">✨</div>
                                <span style="font-size: 0.9rem;">답변을 생성하고 있습니다...</span>
                            </div>
                        </div>
                        <style>
                        @keyframes pulse {
                            0%, 100% { transform: scale(1); opacity: 1; }
                            50% { transform: scale(1.1); opacity: 0.7; }
                        }
                        </style>
                        """, unsafe_allow_html=True)
                
                if chunk.get("finished", False):
                    # Clear status and show completion
                    status_container.empty()
                    break
            
            # Final response without cursor and with enhanced styling
            with message_container.container():
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; 
                            border-left: 4px solid #8B5CF6; margin: 0.5rem 0; 
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            line-height: 1.6;">
                    {full_response}
                </div>
                """, unsafe_allow_html=True)
            
            # Show completion status with enhanced styling
            with status_container.container():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); 
                            color: white; padding: 0.75rem; border-radius: 8px; 
                            text-align: center; margin: 0.5rem 0;">
                    ✅ 응답이 완료되었습니다.
                </div>
                """, unsafe_allow_html=True)
            
            return full_response
            
        except Exception as e:
            with status_container.container():
                st.error(f"❌ 스트리밍 메시지 전송 중 오류가 발생했습니다: {str(e)}")
            return None
    
    # Collection Management Methods
    def get_collections(self) -> List[Dict[str, Any]]:
        """Get list of available collections"""
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다.")
            return []
        
        response = self.api_service.get_collections()
        if response.get("success", False):
            return response.get("collections", [])
        else:
            st.error(f"컬렉션 목록을 가져올 수 없습니다: {response.get('error', '알 수 없는 오류')}")
            return []
    
    def get_collections_response(self) -> Dict[str, Any]:
        """Get full collections response including metadata"""
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다.")
            return {"success": False, "error": "Backend connection failed"}
        
        response = self.api_service.get_collections()
        if response.get("success", False):
            return response
        else:
            st.error(f"컬렉션 목록을 가져올 수 없습니다: {response.get('error', '알 수 없는 오류')}")
            return response
    
    def get_current_collection(self) -> Optional[str]:
        """Get currently active collection"""
        if not self.check_backend_connection():
            return None
        
        response = self.api_service.get_current_collection()
        if response.get("success", False):
            return response.get("current_collection")
        else:
            st.error(f"현재 컬렉션을 가져올 수 없습니다: {response.get('error', '알 수 없는 오류')}")
            return None
    
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a collection"""
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다.")
            return None
        
        response = self.api_service.get_collection_info(collection_name)
        if response.get("success", False):
            return response.get("collection")
        else:
            st.error(f"컬렉션 정보를 가져올 수 없습니다: {response.get('error', '알 수 없는 오류')}")
            return None
    
    def create_collection(self, collection_name: str, description: str = "") -> Dict[str, Any]:
        """Create a new personal collection"""
        if not self.check_backend_connection():
            return {"success": False, "error": "백엔드 서버에 연결할 수 없습니다."}
        
        if not collection_name or collection_name.strip() == "":
            return {"success": False, "error": "컬렉션 이름을 입력해주세요."}
        
        response = self.api_service.create_collection(collection_name, description)
        return response
    
    def create_shared_collection(self, collection_name: str, description: str = "") -> Dict[str, Any]:
        """Create a new shared collection"""
        if not self.check_backend_connection():
            return {"success": False, "error": "백엔드 서버에 연결할 수 없습니다."}
        
        if not collection_name or collection_name.strip() == "":
            return {"success": False, "error": "컬렉션 이름을 입력해주세요."}
        
        response = self.api_service.create_shared_collection(collection_name, description)
        return response
    
    def change_collection_type(self, collection_name: str, new_type: str) -> Dict[str, Any]:
        """Change collection type between personal and shared"""
        if not self.check_backend_connection():
            return {"success": False, "error": "백엔드 서버에 연결할 수 없습니다."}
        
        if not collection_name or collection_name.strip() == "":
            return {"success": False, "error": "컬렉션 이름을 입력해주세요."}
        
        if new_type not in ["personal", "shared"]:
            return {"success": False, "error": "타입은 'personal' 또는 'shared'여야 합니다."}
        
        response = self.api_service.change_collection_type(collection_name, new_type)
        return response
    
    def switch_collection(self, collection_name: str) -> Dict[str, Any]:
        """Switch active collection"""
        if not self.check_backend_connection():
            return {"success": False, "error": "백엔드 서버에 연결할 수 없습니다."}
        
        if not collection_name or collection_name.strip() == "":
            return {"success": False, "error": "컬렉션 이름을 선택해주세요."}
        
        response = self.api_service.switch_collection(collection_name)
        return response
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection and all its documents"""
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다.")
            return False
        
        if collection_name == "documents":
            st.error("기본 'documents' 컬렉션은 삭제할 수 없습니다.")
            return False
        
        response = self.api_service.delete_collection(collection_name)
        if response.get("success", False):
            st.success(f"컬렉션 '{collection_name}'이 삭제되었습니다.")
            return True
        else:
            error_message = response.get('error', '알 수 없는 오류')
            # Check if it's a "collection does not exist" error
            if "does not exist" in error_message or "COLLECTION_NOT_FOUND" in str(response):
                st.warning(f"컬렉션 '{collection_name}'이 존재하지 않습니다.")
                return True  # Return True since this is expected behavior, not an error
            elif "UNAUTHORIZED" in str(response) or "not authorized" in error_message.lower():
                st.error(f"컬렉션 '{collection_name}'을 삭제할 권한이 없습니다. 컬렉션을 생성한 사용자만 삭제할 수 있습니다.")
                return False
            else:
                st.error(f"컬렉션 삭제에 실패했습니다: {error_message}")
                return False
    
    def rename_collection(self, old_name: str, new_name: str) -> Dict[str, Any]:
        """Rename a collection"""
        if not self.check_backend_connection():
            return {"success": False, "error": "백엔드 서버에 연결할 수 없습니다."}
        
        if old_name == "documents":
            return {"success": False, "error": "기본 'documents' 컬렉션은 이름을 변경할 수 없습니다."}
        
        if not new_name or new_name.strip() == "":
            return {"success": False, "error": "새 컬렉션 이름을 입력해주세요."}
        
        response = self.api_service.rename_collection(old_name, new_name)
        return response
    
    def export_chat_markdown(self, session_id: str, session_name: str = "채팅 기록", include_metadata: bool = True) -> Dict[str, Any]:
        """Export chat session to markdown format"""
        if not self.check_backend_connection():
            return {"success": False, "error": "백엔드 서버에 연결할 수 없습니다."}
        
        response = self.api_service.export_chat_markdown(session_id, session_name, include_metadata)
        return response
    
    def export_single_message_markdown(self, message: Dict[str, Any], include_metadata: bool = True) -> Dict[str, Any]:
        """Export a single message to markdown format"""
        if not self.check_backend_connection():
            return {"success": False, "error": "백엔드 서버에 연결할 수 없습니다."}
        
        response = self.api_service.export_single_message_markdown(message, include_metadata)
        return response
    
    def get_markdown_export_stats(self) -> Dict[str, Any]:
        """Get statistics about exported markdown files"""
        if not self.check_backend_connection():
            return {"success": False, "error": "백엔드 서버에 연결할 수 없습니다."}
        
        response = self.api_service.get_markdown_export_stats()
        return response