"""
Chat components for Streamlit UI
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
import io

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
                            color: white; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
                    {content}
                </div>
                """, unsafe_allow_html=True)
                if timestamp:
                    st.caption(f"👤 사용자 • {ChatComponents._format_timestamp(timestamp)}")
        else:
            with st.chat_message("assistant"):
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; 
                            border-left: 4px solid #8B5CF6; margin: 0.5rem 0;">
                    {content}
                </div>
                """, unsafe_allow_html=True)
                
                # Display source information if available
                if context and len(context) > 0:
                    st.markdown("---")
                    st.markdown("📚 **참조 출처:**")
                    
                    for i, source in enumerate(context, 1):
                        filename = source.get("filename", "Unknown")
                        page = source.get("page_number", 1)
                        collection = source.get("collection", "documents")
                        similarity = source.get("similarity", 0)
                        
                        with st.expander(f"{i}. {filename} (페이지 {page}, 컬렉션: {collection})", expanded=False):
                            st.write(f"**파일명:** {filename}")
                            st.write(f"**페이지:** {page}")
                            st.write(f"**컬렉션:** {collection}")
                            st.write(f"**유사도:** {similarity:.2f}")
                            if source.get("source_url"):
                                st.write(f"**URL:** {source['source_url']}")
                            if source.get("upload_date"):
                                st.write(f"**업로드 날짜:** {source['upload_date']}")
                            
                            # Show content preview
                            content_preview = source.get("content", "")[:200]
                            if len(source.get("content", "")) > 200:
                                content_preview += "..."
                            st.write(f"**내용 미리보기:** {content_preview}")
                
                if timestamp:
                    st.caption(f"🤖 {ChatComponents._format_timestamp(timestamp)}")

    @staticmethod
    def render_chat_history(messages: List[Dict[str, Any]]):
        """Render the entire chat history"""
        if not messages:
            st.info("채팅을 시작해보세요! 👋")
            return

        for message in messages:
            ChatComponents.render_message(message)

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
                
                # Debug: Show collections info
                st.write(f"🔍 Debug - Collections: {collections}")
                st.write(f"🔍 Debug - Current Collection: {current_collection}")
                
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
