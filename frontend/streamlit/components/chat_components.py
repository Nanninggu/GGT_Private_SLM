"""
Chat components for Streamlit UI
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
import io
import sys
import os

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_service import PDFService

class ChatComponents:
    """Reusable chat UI components"""

    @staticmethod
    def render_message(message: Dict[str, Any]):
        """Render a single chat message with HAI Portal styling"""
        role = message["role"]
        content = message["content"]
        timestamp = message.get("timestamp", "")
        context = message.get("context", [])
        metadata = message.get("metadata", {})

        if role == "user":
            with st.chat_message("user"):
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%); 
                            color: white; padding: 1.5rem; border-radius: 10px; 
                            margin: 1rem 0 2rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    {content}
                </div>
                """, unsafe_allow_html=True)
                # User message with PDF icon
                col1, col2 = st.columns([1, 0.08])
                with col1:
                    if timestamp:
                        st.caption(f"👤 사용자 • {ChatComponents._format_timestamp(timestamp)}")
                with col2:
                    if st.button("📄", key=f"download_user_message_{hash(content)}", help="PDF 저장", use_container_width=True, type="primary"):
                        try:
                            pdf_service = PDFService()
                            single_message = [message]
                            pdf_content = pdf_service.generate_chat_pdf(
                                single_message,
                                "single_message",
                                "개별 메시지",
                                True
                            )
                            
                            filename = f"user_message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            
                            st.download_button(
                                label="📥 메시지 PDF 다운로드",
                                data=pdf_content,
                                file_name=filename,
                                mime="application/pdf"
                            )
                        except Exception as e:
                            st.error(f"PDF 생성 오류: {str(e)}")
        else:
            with st.chat_message("assistant"):
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; 
                            border-left: 4px solid #8B5CF6; margin: 1rem 0 2rem 0; 
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    {content}
                </div>
                """, unsafe_allow_html=True)
                
                # Display similarity score if available
                if metadata and "similarity" in metadata:
                    similarity = metadata.get("similarity", 0)
                    ChatComponents._render_similarity_score(similarity)
                elif metadata:
                    # If metadata exists but no similarity, show a default score
                    st.info("신뢰도 정보를 계산하는 중입니다...")
                else:
                    # No metadata available
                    st.info("기본 모드로 응답합니다.")
                
                # AI message with PDF icon
                col1, col2 = st.columns([1, 0.08])
                with col1:
                    if timestamp:
                        st.caption(f"🤖 {ChatComponents._format_timestamp(timestamp)}")
                with col2:
                    if st.button("📄", key=f"download_message_{hash(content)}", help="PDF 저장", use_container_width=True, type="primary"):
                        try:
                            pdf_service = PDFService()
                            single_message = [message]
                            pdf_content = pdf_service.generate_chat_pdf(
                                single_message,
                                "single_message",
                                "개별 메시지",
                                True
                            )
                            
                            filename = f"message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            
                            st.download_button(
                                label="📥 메시지 PDF 다운로드",
                                data=pdf_content,
                                file_name=filename,
                                mime="application/pdf"
                            )
                        except Exception as e:
                            st.error(f"PDF 생성 오류: {str(e)}")

    @staticmethod
    def _render_similarity_score(similarity: float):
        """Render similarity score with visual indicator"""
        # Convert similarity to percentage
        similarity_percent = round(similarity * 100, 1)
        
        # Determine color and emoji based on similarity
        if similarity >= 0.8:
            color = "#10B981"  # Green
            emoji = "🟢"
            status = "매우 높음"
        elif similarity >= 0.6:
            color = "#F59E0B"  # Yellow
            emoji = "🟡"
            status = "높음"
        elif similarity >= 0.4:
            color = "#F97316"  # Orange
            emoji = "🟠"
            status = "보통"
        else:
            color = "#EF4444"  # Red
            emoji = "🔴"
            status = "낮음"
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 1rem 0 1.5rem 0; padding: 1rem; 
                    background: #f8f9fa; border-radius: 8px; border-left: 3px solid {color};
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <span style="font-size: 1.2rem; margin-right: 0.75rem;">{emoji}</span>
            <div style="flex: 1;">
                <strong style="color: {color}; font-size: 1.1rem;">답변 신뢰도: {similarity_percent}%</strong>
                <small style="color: #666; margin-left: 0.5rem; font-size: 0.9rem;">({status})</small>
            </div>
            <div style="background: {color}; height: 10px; border-radius: 5px; 
                        width: {similarity_percent}%; min-width: 30px; margin-left: 1rem;"></div>
        </div>
        """, unsafe_allow_html=True)


    @staticmethod
    def render_chat_history(messages: List[Dict[str, Any]]):
        """Render the entire chat history"""
        if not messages:
            st.info("채팅을 시작해보세요! 👋")
            return

        for message in messages:
            ChatComponents.render_message(message)

    @staticmethod
    def _inject_accessibility_scripts():
        """Inject CSS and JavaScript for accessibility features"""
        st.markdown("""
        <style>
        /* Accessibility styles for similarity score display */
        .similarity-score {
            transition: all 0.3s ease;
        }
        
        .similarity-score:hover {
            background-color: #f0f8ff !important;
            border-color: #8B5CF6 !important;
        }
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
            .similarity-score {
                border-width: 2px;
            }
        }
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            .similarity-score {
                transition: none;
            }
        }
        
        /* PDF icon button styles - compact and clean */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 50% !important;
            width: 32px !important;
            height: 32px !important;
            min-height: 32px !important;
            padding: 0 !important;
            font-size: 12px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 !important;
        }
        
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 8px rgba(139, 92, 246, 0.4) !important;
            background: linear-gradient(135deg, #7C3AED 0%, #9333EA 100%) !important;
        }
        
        .stButton > button[kind="primary"]:active {
            transform: translateY(0) !important;
            box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3) !important;
        }
        
        /* Ensure PDF icon buttons are properly sized */
        .stButton {
            margin: 0 !important;
            padding: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_sidebar():
        """Render sidebar with HAI Portal navigation"""
        with st.sidebar:
            # HAI Portal branding
            st.markdown("""
            <div style="text-align: center; padding: 1rem 0; border-bottom: 2px solid #8B5CF6;">
                <h1 style="color: #8B5CF6; margin: 0; font-size: 1.8rem;">HAI Portal</h1>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # HAI-Chat section (current)
            st.markdown("### 💬 HAI-Chat")
            st.markdown('<div style="background: #e3f2fd; padding: 0.5rem; border-radius: 5px; margin: 0.5rem 0;">현재 선택된 서비스</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Settings and logout
            st.markdown("### ⚙️ 설정")
            if st.button("🔧 설정", key="nav_settings", use_container_width=True):
                st.info("설정 페이지는 준비 중입니다.")
            
            if st.button("🚪 로그아웃", key="nav_logout", use_container_width=True):
                st.info("로그아웃 기능은 준비 중입니다.")
            
            st.markdown("---")
            
            # Chat controls
            st.markdown("### 💬 채팅 제어")
            if st.button("🗑️ 채팅 초기화", key="clear_chat", use_container_width=True):
                return "clear_chat"
            
            # PDF Export section
            st.markdown("---")
            st.markdown("### 📄 PDF 내보내기")
            
            # PDF export options
            pdf_type = st.radio(
                "PDF 유형 선택",
                ["전체 채팅 기록", "요약 보고서"],
                help="전체 채팅 기록: 모든 메시지를 포함한 상세 PDF\n요약 보고서: 통계와 주요 내용을 포함한 요약 PDF"
            )
            
            # PDF generation options
            include_metadata = st.checkbox(
                "메타데이터 포함",
                value=True,
                help="신뢰도 점수, 참조 문서 등 메타데이터를 PDF에 포함"
            )
            
            # Generate PDF button
            if st.button("📥 PDF 다운로드", key="download_pdf", use_container_width=True):
                return ("download_pdf", pdf_type, include_metadata)
            
            # Response Mode selection
            st.subheader("응답 모드")
            
            # Streaming option with enhanced UI
            streaming_enabled = st.checkbox(
                "🚀 실시간 스트리밍",
                value=st.session_state.get("streaming_enabled", True),
                key="streaming_checkbox",
                help="ChatGPT처럼 실시간으로 텍스트가 타이핑되는 효과"
            )
            st.session_state.streaming_enabled = streaming_enabled
            
            if streaming_enabled:
                st.markdown("""
                <div style="background: #e8f5e8; padding: 0.5rem; border-radius: 5px; 
                            border-left: 3px solid #10B981; margin: 0.5rem 0;">
                    ✨ <strong>실시간 스트리밍 활성화</strong><br>
                    <small>ChatGPT 스타일의 부드러운 타이핑 효과</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: #f0f0f0; padding: 0.5rem; border-radius: 5px; 
                            border-left: 3px solid #6B7280; margin: 0.5rem 0;">
                    📝 <strong>일반 응답 모드</strong><br>
                    <small>전체 응답을 한 번에 표시</small>
                </div>
                """, unsafe_allow_html=True)
            
            # RAG Mode selection
            st.subheader("RAG 모드")
            
            # Get current rag_mode and convert to index
            current_rag_mode = st.session_state.get("rag_mode", "기본 RAG")
            rag_options = ["기본 RAG", "LangChain RAG"]
            current_index = rag_options.index(current_rag_mode) if current_rag_mode in rag_options else 0
            
            rag_mode = st.selectbox(
                "RAG 시스템 선택",
                rag_options,
                index=current_index,
                key="rag_mode_select"
            )
            st.session_state.rag_mode = rag_mode
            
            if rag_mode == "LangChain RAG":
                st.info("🧠 LangChain 기반 RAG\n- 대화 메모리 지원\n- 고급 문서 검색\n- 체인 기반 처리")
            else:
                st.info("⚡ 기본 RAG\n- 빠른 응답\n- 간단한 검색")
            
            # Collection Selection (only for LangChain RAG)
            if rag_mode == "LangChain RAG":
                st.markdown("---")
                st.subheader("📚 Vector DB 컬렉션")
                
                # Import here to avoid circular imports
                from controllers.chat_controller import ChatController
                chat_controller = ChatController()
                
                # Get collections
                collections = chat_controller.get_collections()
                current_collection = chat_controller.get_current_collection()
                
                # Display collections as a formatted list
                if collections:
                    st.markdown("**📋 사용 가능한 컬렉션:**")
                    for collection in collections:
                        collection_name = collection.get('name', 'Unknown')
                        document_count = collection.get('document_count', 0)
                        description = collection.get('metadata', {}).get('description', '')
                        
                        # Create a formatted list item
                        list_item = f"• **{collection_name}** ({document_count}개 문서)"
                        if description:
                            list_item += f" - {description}"
                        
                        st.markdown(list_item)
                    
                    # Show current collection
                    if current_collection:
                        st.markdown(f"**현재 선택된 컬렉션:** {current_collection}")
                else:
                    st.info("컬렉션을 불러오는 중...")
                
                # If no collections returned, create default collection
                if not collections:
                    collections = [{
                        "id": "default",
                        "name": "documents",
                        "metadata": {},
                        "created_at": None,
                        "document_count": 0
                    }]
                
                # Always show collection selection UI
                if collections:
                    # Create collection options
                    collection_options = [f"{col['name']} ({col.get('document_count', 0)}개 문서)" for col in collections]
                    
                    # Find current collection index
                    current_collection_index = 0
                    for i, col in enumerate(collections):
                        if col['name'] == current_collection:
                            current_collection_index = i
                            break
                    
                    # Collection selector
                    selected_index = st.selectbox(
                        "사용할 컬렉션 선택",
                        range(len(collection_options)),
                        format_func=lambda x: collection_options[x],
                        index=current_collection_index,
                        key="collection_select"
                    )
                    
                    if selected_index is not None:
                        selected_collection = collections[selected_index]['name']
                        
                        # Show collection info
                        if st.button("ℹ️ 컬렉션 정보 보기", key="show_collection_info"):
                            collection_info = chat_controller.get_collection_info(selected_collection)
                            if collection_info:
                                st.json(collection_info)
                        
                        # Switch collection if different
                        if selected_collection != current_collection:
                            if st.button("🔄 컬렉션 전환", key="switch_collection"):
                                if chat_controller.switch_collection(selected_collection):
                                    st.rerun()
                    
                    # Show current collection info
                    if current_collection:
                        st.info(f"현재 활성 컬렉션: **{current_collection}**")
                else:
                    # Show default collection when no collections are available
                    st.info("기본 컬렉션을 사용합니다.")
                    
                    # Show current collection info
                    if current_collection:
                        st.info(f"현재 활성 컬렉션: **{current_collection}**")
                    
                    # Refresh button
                    if st.button("🔄 컬렉션 목록 새로고침", key="refresh_collections"):
                        st.rerun()
                    
                    # Collection management button
                    if st.button("🗂️ 컬렉션 관리", key="collection_management", use_container_width=True):
                        st.switch_page("pages/collection_management.py")
                    
                    # Show message about creating collections
                    st.markdown("""
                    **컬렉션 생성 방법:**
                    1. 컬렉션 관리 페이지에서 직접 생성
                    2. 파일 업로드 페이지에서 문서를 업로드
                    3. LangChain RAG 모드로 업로드
                    """)

            # Session management
            st.subheader("세션 관리")
            
            # Current session display
            current_session = st.session_state.get("session_id", "default")
            st.text_input("현재 세션 ID", value=current_session, disabled=True)
            
            # Session list
            st.markdown("### 📋 채팅 히스토리")
            
            # Import here to avoid circular imports
            from services.api_service import APIService
            api_service = APIService()
            
            # Get all sessions (skip if we just created a new session)
            if not st.session_state.get("is_new_session", False):
                sessions_response = api_service.get_sessions()
                if sessions_response.get("success"):
                    sessions = sessions_response.get("sessions", [])
                    # Cache the sessions for future use
                    st.session_state.cached_sessions = sessions
                else:
                    sessions = []
            else:
                # For new sessions, use cached sessions or empty list
                sessions = st.session_state.get("cached_sessions", [])
                # Reset the new session flag after using cached sessions
                st.session_state.is_new_session = False
                
                if sessions:
                    # Session selector
                    session_options = []
                    session_map = {}
                    
                    for session_id in sessions:
                        # Create display name for session
                        if session_id == "default":
                            display_name = f"기본 세션 ({session_id})"
                        else:
                            # Check if session has a custom name
                            session_name = st.session_state.get(f"session_name_{session_id}", "")
                            if session_name:
                                # Try to get session info to show message count
                                history_response = api_service.get_chat_history(session_id, limit=1)
                                if history_response.get("success"):
                                    message_count = len(history_response.get("messages", []))
                                    display_name = f"{session_name} ({message_count}개 메시지)"
                                else:
                                    display_name = f"{session_name} (메시지 없음)"
                            else:
                                # Try to get session info to show message count
                                history_response = api_service.get_chat_history(session_id, limit=1)
                                if history_response.get("success"):
                                    message_count = len(history_response.get("messages", []))
                                    display_name = f"세션 {session_id[:8]}... ({message_count}개 메시지)"
                                else:
                                    display_name = f"세션 {session_id[:8]}..."
                        
                        session_options.append(display_name)
                        session_map[display_name] = session_id
                    
                    # Add current session if not in list
                    if current_session not in sessions:
                        session_options.insert(0, f"현재 세션 ({current_session})")
                        session_map[f"현재 세션 ({current_session})"] = current_session
                    
                    # Find current session index
                    current_index = 0
                    for i, option in enumerate(session_options):
                        if session_map[option] == current_session:
                            current_index = i
                            break
                    
                    # Session selector
                    selected_display = st.selectbox(
                        "세션 선택",
                        session_options,
                        index=current_index,
                        key="session_selector"
                    )
                    
                    if selected_display and session_map[selected_display] != current_session:
                        if st.button("🔄 세션 전환", key="switch_session"):
                            # Use ChatController to switch session and load history
                            from controllers.chat_controller import ChatController
                            chat_controller = ChatController()
                            chat_controller.switch_to_session(session_map[selected_display])
                    
                    # Session name editing
                    st.markdown("#### ✏️ 세션 이름 편집")
                    current_session_name = st.session_state.get(f"session_name_{current_session}", "")
                    new_session_name = st.text_input(
                        "세션 이름",
                        value=current_session_name,
                        placeholder="세션 이름을 입력하세요...",
                        key=f"session_name_input_{current_session}"
                    )
                    
                    if new_session_name != current_session_name:
                        if st.button("💾 이름 저장", key="save_session_name"):
                            st.session_state[f"session_name_{current_session}"] = new_session_name
                            st.success("세션 이름이 저장되었습니다.")
                            st.rerun()
                    
                    # Session actions
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("➕ 새 세션", key="new_session"):
                            import uuid
                            new_session_id = str(uuid.uuid4())
                            
                            # Set all session state at once to avoid infinite loop
                            st.session_state.session_id = new_session_id
                            st.session_state.messages = []  # Clear messages for new session
                            st.session_state.last_loaded_session = new_session_id  # Update last loaded session
                            st.session_state.is_new_session = True  # Mark as new session to skip existence check
                            
                            # Add new session to cached sessions to avoid re-fetching
                            if "cached_sessions" not in st.session_state:
                                st.session_state.cached_sessions = []
                            if new_session_id not in st.session_state.cached_sessions:
                                st.session_state.cached_sessions.append(new_session_id)
                            
                            st.success("새 세션이 생성되었습니다.")
                            st.rerun()
                    
                    with col2:
                        if st.button("🗑️ 세션 삭제", key="delete_session"):
                            if current_session != "default":  # Don't allow deleting default session
                                delete_response = api_service.clear_session(current_session)
                                if delete_response.get("success"):
                                    # Also remove session name from session state
                                    if f"session_name_{current_session}" in st.session_state:
                                        del st.session_state[f"session_name_{current_session}"]
                                    st.success("세션이 삭제되었습니다.")
                                    st.session_state.session_id = "default"
                                    st.rerun()
                                else:
                                    st.error("세션 삭제에 실패했습니다.")
                            else:
                                st.warning("기본 세션은 삭제할 수 없습니다.")
                    
                    with col3:
                        if st.button("🔄 새로고침", key="refresh_session_list"):
                            st.rerun()
                    
                    # All sessions delete section
                    st.markdown("---")
                    st.markdown("#### ⚠️ 위험한 작업")
                    
                    # Check if deletion is in progress
                    if st.session_state.get("deleting_all_sessions", False):
                        st.info("🔄 모든 세션을 삭제하는 중입니다...")
                        return None
                    
                    # Check if sessions were just deleted
                    if st.session_state.get("sessions_deleted", False):
                        st.success("✅ 모든 세션이 성공적으로 삭제되었습니다!")
                        st.session_state.sessions_deleted = False  # Clear the flag
                        return None
                    
                    # Show session count
                    non_default_sessions = [s for s in sessions if s != "default"]
                    if non_default_sessions:
                        st.warning(f"⚠️ **{len(non_default_sessions)}개의 세션**이 삭제 대상입니다.")
                        
                        # Confirmation checkbox
                        confirm_delete = st.checkbox(
                            "모든 세션 삭제를 확인합니다 (기본 세션 제외)",
                            key="confirm_delete_all",
                            help="이 작업은 되돌릴 수 없습니다!"
                        )
                        
                        if confirm_delete:
                            # Additional confirmation with session list
                            st.markdown("**삭제될 세션 목록:**")
                            for session_id in non_default_sessions:
                                session_name = st.session_state.get(f"session_name_{session_id}", "")
                                if session_name:
                                    st.write(f"• {session_name} ({session_id[:8]}...)")
                                else:
                                    st.write(f"• 세션 {session_id[:8]}...")
                            
                            # Final delete button
                            if st.button("💥 모든 세션 삭제", key="delete_all_sessions", type="primary"):
                                # Set deletion in progress flag
                                st.session_state.deleting_all_sessions = True
                                
                                # Use ChatController to delete all sessions
                                from controllers.chat_controller import ChatController
                                chat_controller = ChatController()
                                
                                with st.spinner("모든 세션을 삭제하는 중..."):
                                    result = chat_controller.clear_all_sessions()
                                
                                if result.get("success"):
                                    cleared_count = len(result.get("cleared_sessions", []))
                                    
                                    # Clear session names from session state
                                    for session_id in result.get("cleared_sessions", []):
                                        if f"session_name_{session_id}" in st.session_state:
                                            del st.session_state[f"session_name_{session_id}"]
                                    
                                    # Switch to default session and clear messages
                                    st.session_state.session_id = "default"
                                    st.session_state.messages = []
                                    st.session_state.last_loaded_session = "default"
                                    
                                    # Clear deletion flag
                                    st.session_state.deleting_all_sessions = False
                                    
                                    # Show success message
                                    st.success(f"✅ {cleared_count}개의 세션이 삭제되었습니다.")
                                    
                                    # Force a complete page refresh to avoid infinite loop
                                    st.session_state.force_refresh = True
                                    st.rerun()
                                else:
                                    st.session_state.deleting_all_sessions = False
                                    st.error(f"❌ 세션 삭제에 실패했습니다: {result.get('error', '알 수 없는 오류')}")
                    else:
                        st.info("삭제할 세션이 없습니다. (기본 세션만 존재)")
                    
                    # Show session info
                    if current_session:
                        history_response = api_service.get_chat_history(current_session)
                        if history_response.get("success"):
                            message_count = len(history_response.get("messages", []))
                            st.info(f"📊 현재 세션: {message_count}개 메시지")
                            
                            # History search and filter
                            if message_count > 0:
                                st.markdown("#### 🔍 히스토리 검색")
                                search_term = st.text_input(
                                    "메시지 검색",
                                    placeholder="검색어를 입력하세요...",
                                    key="history_search"
                                )
                                
                                # Filter messages by search term
                                messages = history_response.get("messages", [])
                                if search_term:
                                    filtered_messages = [
                                        msg for msg in messages 
                                        if search_term.lower() in msg.get("content", "").lower()
                                    ]
                                    st.info(f"'{search_term}' 검색 결과: {len(filtered_messages)}개 메시지")
                                else:
                                    filtered_messages = messages
                                
                                # Show recent messages preview
                                if filtered_messages:
                                    st.markdown("#### 📝 최근 메시지 미리보기")
                                    preview_count = min(3, len(filtered_messages))
                                    for i, msg in enumerate(filtered_messages[-preview_count:]):
                                        role = msg.get("role", "unknown")
                                        content = msg.get("content", "")
                                        timestamp = msg.get("timestamp", "")
                                        
                                        # Truncate content for preview
                                        preview_content = content[:100] + "..." if len(content) > 100 else content
                                        
                                        if role == "user":
                                            st.markdown(f"**👤 사용자:** {preview_content}")
                                        else:
                                            st.markdown(f"**🤖 AI:** {preview_content}")
                                        
                                        if timestamp:
                                            try:
                                                from datetime import datetime
                                                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                                st.caption(f"시간: {dt.strftime('%H:%M:%S')}")
                                            except:
                                                st.caption(f"시간: {timestamp}")
                                        
                                        if i < preview_count - 1:
                                            st.markdown("---")
                                
                                # History actions
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("📖 전체 히스토리 보기", key="show_full_history"):
                                        st.session_state.show_full_history = not st.session_state.get("show_full_history", False)
                                        st.rerun()
                                
                                with col2:
                                    if st.button("💾 히스토리 내보내기", key="export_history"):
                                        # Create export data
                                        export_data = {
                                            "session_id": current_session,
                                            "session_name": st.session_state.get(f"session_name_{current_session}", ""),
                                            "exported_at": datetime.now().isoformat(),
                                            "message_count": len(filtered_messages),
                                            "messages": filtered_messages
                                        }
                                        
                                        # Convert to JSON
                                        import json
                                        json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
                                        
                                        # Create download button
                                        st.download_button(
                                            label="📥 JSON 파일로 다운로드",
                                            data=json_data,
                                            file_name=f"chat_history_{current_session}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                            mime="application/json"
                                        )
                                
                                # Show full history if requested
                                if st.session_state.get("show_full_history", False):
                                    st.markdown("#### 📚 전체 채팅 히스토리")
                                    for msg in reversed(filtered_messages):  # Show newest first
                                        ChatComponents.render_message({
                                            "role": msg.get("role", "unknown"),
                                            "content": msg.get("content", ""),
                                            "timestamp": msg.get("timestamp", ""),
                                            "context": [],
                                            "metadata": {}
                                        })
                        else:
                            st.info("📊 현재 세션: 메시지 없음")
                    else:
                        st.info("저장된 세션이 없습니다.")
                        if st.button("➕ 새 세션 생성", key="create_first_session"):
                            import uuid
                            new_session_id = str(uuid.uuid4())
                            st.session_state.session_id = new_session_id
                            st.rerun()
                else:
                    st.error("세션 목록을 불러올 수 없습니다.")
                    if st.button("🔄 새로고침", key="refresh_sessions"):
                        st.rerun()

            # Connection status
            st.subheader("연결 상태")
            if st.session_state.get("backend_connected", False):
                st.success("✅ 백엔드 연결됨")
            else:
                st.error("❌ 백엔드 연결 실패")

            if st.button("🔄 연결 확인", key="check_connection"):
                return "check_connection"

        return None

    @staticmethod
    def render_chat_input():
        """Render chat input component"""
        return st.chat_input("메시지를 입력하세요...")

    @staticmethod
    def _format_timestamp(timestamp_str: str) -> str:
        """Format timestamp for display"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%H:%M:%S")
        except:
            return timestamp_str

class StatusComponents:
    """Components for displaying status information"""

    @staticmethod
    def show_connection_status(connected: bool):
        """Show connection status"""
        if connected:
            st.success("🟢 백엔드 서버에 연결되었습니다.")
        else:
            st.error("🔴 백엔드 서버에 연결할 수 없습니다. 서버를 시작해주세요.")

    @staticmethod
    def show_loading():
        """Show loading indicator"""
        return st.spinner("처리 중...")

    @staticmethod
    def show_error(message: str):
        """Show error message"""
        st.error(f"❌ 오류: {message}")

    @staticmethod
    def show_success(message: str):
        """Show success message"""
        st.success(f"✅ {message}")

    @staticmethod
    def show_ai_typing():
        """Show AI typing indicator with animation"""
        st.markdown("""
        <div style="display: flex; align-items: center; margin: 1rem 0; padding: 1rem; 
                    background: #f8f9fa; border-radius: 10px; border-left: 4px solid #8B5CF6;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="margin-right: 1rem;">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
            <div style="flex: 1;">
                <strong style="color: #8B5CF6;">🤖 AI가 답변을 생성하고 있습니다...</strong>
                <br>
                <small style="color: #666;">잠시만 기다려주세요</small>
            </div>
        </div>
        
        <style>
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .typing-indicator span {
            height: 8px;
            width: 8px;
            border-radius: 50%;
            background-color: #8B5CF6;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-indicator span:nth-child(1) {
            animation-delay: -0.32s;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: -0.16s;
        }
        
        @keyframes typing {
            0%, 80%, 100% {
                transform: scale(0.8);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }
        </style>
        """, unsafe_allow_html=True)

class FileUploadComponents:
    """Components for file upload functionality"""

    @staticmethod
    def render_file_uploader(rag_mode: str = "기본 RAG", multiple: bool = False) -> Optional[st.runtime.uploaded_file_manager.UploadedFile]:
        """Render file uploader widget"""
        st.subheader("📁 파일 업로드")
        st.write("문서를 업로드하여 RAG 시스템에 추가할 수 있습니다.")
        
        # Supported file types
        supported_types = ["txt", "md", "pdf", "docx", "csv", "json"]
        
        if multiple:
            uploaded_files = st.file_uploader(
                "파일들을 선택하세요 (여러 개 선택 가능)",
                type=supported_types,
                accept_multiple_files=True,
                help=f"지원되는 파일 형식: {', '.join(supported_types)}",
                key=f"file_uploader_multiple_{rag_mode}"
            )
            
            if uploaded_files:
                st.write(f"**선택된 파일 수:** {len(uploaded_files)}개")
                
                # Display file info for each file
                for i, uploaded_file in enumerate(uploaded_files):
                    with st.expander(f"📄 {uploaded_file.name}", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**파일명:** {uploaded_file.name}")
                        with col2:
                            st.write(f"**크기:** {len(uploaded_file.getvalue())} bytes")
                        with col3:
                            st.write(f"**타입:** {uploaded_file.type}")
                        
                        # Show file content preview for text files
                        if uploaded_file.type.startswith('text/'):
                            st.write("**파일 내용 미리보기:**")
                            content = uploaded_file.getvalue().decode('utf-8')
                            preview = content[:300] + "..." if len(content) > 300 else content
                            st.text_area("", preview, height=80, disabled=True, key=f"preview_{i}")
            
            return uploaded_files
        else:
            uploaded_file = st.file_uploader(
                "파일을 선택하세요",
                type=supported_types,
                help=f"지원되는 파일 형식: {', '.join(supported_types)}",
                key=f"file_uploader_{rag_mode}"
            )
            
            if uploaded_file is not None:
                # Display file info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**파일명:** {uploaded_file.name}")
                with col2:
                    st.write(f"**크기:** {len(uploaded_file.getvalue())} bytes")
                with col3:
                    st.write(f"**타입:** {uploaded_file.type}")
                
                # Show file content preview for text files
                if uploaded_file.type.startswith('text/'):
                    st.write("**파일 내용 미리보기:**")
                    content = uploaded_file.getvalue().decode('utf-8')
                    preview = content[:500] + "..." if len(content) > 500 else content
                    st.text_area("", preview, height=100, disabled=True)
            
            return uploaded_file

    @staticmethod
    def render_upload_progress():
        """Render upload progress indicator"""
        return st.progress(0)

    @staticmethod
    def show_upload_success(filename: str, doc_id: str = None, doc_ids: List[str] = None):
        """Show upload success message"""
        if doc_id:
            st.success(f"✅ 파일 '{filename}'이 성공적으로 업로드되었습니다! (문서 ID: {doc_id})")
        elif doc_ids:
            st.success(f"✅ 파일 '{filename}'이 성공적으로 업로드되었습니다! (문서 ID: {', '.join(doc_ids)})")
        else:
            st.success(f"✅ 파일 '{filename}'이 성공적으로 업로드되었습니다!")

    @staticmethod
    def show_upload_error(error_message: str):
        """Show upload error message"""
        st.error(f"❌ 업로드 실패: {error_message}")

    @staticmethod
    def render_rag_mode_selector() -> str:
        """Render RAG mode selector for file upload"""
        st.write("**RAG 모드 선택:**")
        rag_mode = st.radio(
            "업로드할 RAG 시스템을 선택하세요:",
            ["기본 RAG", "LangChain RAG"],
            help="기본 RAG: 단순한 벡터 검색\nLangChain RAG: 고급 체인 처리 및 메모리"
        )
        return rag_mode

    @staticmethod
    def render_upload_button():
        """Render upload button"""
        return st.button("🚀 파일 업로드 및 벡터화", type="primary", use_container_width=True)

    @staticmethod
    def show_success(message: str):
        """Show success message"""
        st.success(f"✅ {message}")
