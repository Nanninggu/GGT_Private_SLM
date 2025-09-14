"""
Chat controller for managing chat functionality in Streamlit
"""
import streamlit as st
from typing import Dict, Any, List, Optional
import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api_service import APIService
import uuid
from datetime import datetime

class ChatController:
    """Controller for chat-related functionality"""

    def __init__(self):
        self.api_service = APIService()
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize Streamlit session state"""
        if "session_id" not in st.session_state:
            st.session_state.session_id = "default"  # Use "default" as initial session
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "backend_connected" not in st.session_state:
            st.session_state.backend_connected = False

    def check_backend_connection(self) -> bool:
        """Check if backend is connected"""
        connected = self.api_service.health_check()
        st.session_state.backend_connected = connected
        return connected

    def send_message(self, message: str) -> Optional[Dict[str, Any]]:
        """Send a message and return response with context"""
        if not message.strip():
            st.error("메시지를 입력해주세요.")
            return None

        # Check backend connection
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return None

        # Send message to backend
        with st.spinner("응답을 생성하고 있습니다..."):
            response = self.api_service.send_message(message, st.session_state.session_id, use_rag=True)

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
        if st.session_state.backend_connected:
            self.api_service.clear_session(st.session_state.session_id)

        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.success("채팅이 초기화되었습니다.")

    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get current chat history"""
        return st.session_state.messages

    def load_session_history(self, session_id: str):
        """Load chat history from backend"""
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
            # Don't show success message for automatic loading
            if session_id != st.session_state.get("last_loaded_session", ""):
                st.success(f"채팅 기록을 불러왔습니다. ({len(messages)}개 메시지)")
        else:
            st.error(f"채팅 기록을 불러올 수 없습니다: {response.get('error', '알 수 없는 오류')}")
    
    def switch_to_session(self, session_id: str):
        """Switch to a different session and load its history"""
        if session_id != st.session_state.get("session_id", ""):
            # Clear new session flag when switching to existing session
            st.session_state.is_new_session = False
            self.load_session_history(session_id)
            st.session_state.last_loaded_session = session_id  # Update last loaded session
            st.rerun()

    def get_available_sessions(self) -> List[str]:
        """Get list of available sessions"""
        if not self.check_backend_connection():
            return []

        response = self.api_service.get_sessions()
        if response["success"]:
            return response["sessions"]
        return []

    def check_session_exists(self, session_id: str) -> bool:
        """Check if a specific session exists without loading all sessions"""
        if not self.check_backend_connection():
            return False

        response = self.api_service.check_session_exists(session_id)
        if response["success"]:
            return response["exists"]
        return False

    def clear_all_sessions(self) -> Dict[str, Any]:
        """Clear all sessions except default"""
        if not self.check_backend_connection():
            return {"success": False, "error": "백엔드 서버에 연결할 수 없습니다."}

        response = self.api_service.clear_all_sessions()
        if response["success"]:
            # Clear current session if it was deleted
            current_session = st.session_state.get("session_id", "")
            if current_session != "default" and current_session in response.get("cleared_sessions", []):
                st.session_state.session_id = "default"
                st.session_state.messages = []
                st.session_state.last_loaded_session = "default"
        
        return response
    
    def send_message_langchain(self, message: str, use_rag: bool = True) -> Optional[Dict[str, Any]]:
        """Send a message using LangChain RAG"""
        if not message.strip():
            st.error("메시지를 입력해주세요.")
            return None

        # Check backend connection
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return None

        # Send message to backend using LangChain
        with st.spinner("LangChain RAG로 응답을 생성하고 있습니다..."):
            response = self.api_service.send_message_langchain(message, st.session_state.session_id, use_rag)

        if response["success"]:
            return {
                "content": response["assistant_message"]["content"],
                "context": response.get("context", []),
                "metadata": response.get("metadata", {})
            }
        else:
            st.error(f"LangChain RAG 오류가 발생했습니다: {response.get('error', '알 수 없는 오류')}")
            return None
    
    def send_message_stream(self, message: str, use_rag: bool = True) -> Optional[str]:
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
            rag_mode = st.session_state.get("rag_mode", "기본 RAG")
            use_langchain = (rag_mode == "LangChain RAG")
            
            # Show initial status with enhanced styling
            with status_container.container():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%); 
                            color: white; padding: 0.75rem; border-radius: 8px; 
                            text-align: center; margin: 0.5rem 0;">
                    🤖 AI가 응답을 생성하고 있습니다...
                </div>
                """, unsafe_allow_html=True)
            
            for chunk in self.api_service.send_message_stream(message, st.session_state.session_id, use_langchain):
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
                    
                    if context_sources:
                        with context_container.container():
                            # Enhanced context display with similarity scores
                            st.markdown("### 📚 참고 문서")
                            
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
        """Create a new collection"""
        if not self.check_backend_connection():
            return {"success": False, "error": "백엔드 서버에 연결할 수 없습니다."}
        
        if not collection_name or collection_name.strip() == "":
            return {"success": False, "error": "컬렉션 이름을 입력해주세요."}
        
        response = self.api_service.create_collection(collection_name, description)
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
            st.error(f"컬렉션 삭제에 실패했습니다: {response.get('error', '알 수 없는 오류')}")
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