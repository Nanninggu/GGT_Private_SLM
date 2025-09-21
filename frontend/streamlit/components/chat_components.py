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
from services.api_service import APIService
from config import ADMIN_USER_ID

class ChatComponents:
    """Reusable chat UI components"""

    @staticmethod
    def render_model_selection():
        """Render model selection UI"""
        # Initialize model type in session state
        if "selected_model_type" not in st.session_state:
            st.session_state.selected_model_type = "fast"
        
        # Model configurations (백엔드 settings.py와 일치)
        model_configs = {
            "fast": {
                "name": "⚡ 빠른 응답",
                "description": "exaone3.5:2.4b-instruct-q4_K_M (1.6GB, Q4_K_M)",
                "use_case": "일반적인 질문, 초고속 응답이 필요한 경우",
                "color": "#10B981"
            },
            "quality": {
                "name": "🎯 고품질 응답",
                "description": "exaone3.5:2.4b-instruct-q8_0 (2.8GB, Q8_0)",
                "use_case": "정확한 답변이 필요한 경우, 창의적 작업",
                "color": "#3B82F6"
            },
            "complex": {
                "name": "🧠 복잡한 작업",
                "description": "exaone3.5:7.8b (4.8GB, 7.8B 파라미터)",
                "use_case": "복잡한 추론, 창의적 글쓰기, 전문적 분석",
                "color": "#8B5CF6"
            }
        }
        
        # Create model selection UI
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border: 1px solid #e9ecef;">
            <h4 style="margin: 0 0 1rem 0; color: #495057;">🤖 AI 모델 선택</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Model selection tabs
        selected_model = st.radio(
            "모델 유형을 선택하세요:",
            options=list(model_configs.keys()),
            format_func=lambda x: model_configs[x]["name"],
            horizontal=True,
            key="model_selection_radio"
        )
        
        # Update session state
        st.session_state.selected_model_type = selected_model
        
        # Display selected model info
        selected_config = model_configs[selected_model]
        
        # Display selected model info (full width)
        st.markdown(f"""
        <div style="background: {selected_config['color']}15; padding: 1.5rem; border-radius: 8px; 
                    border-left: 4px solid {selected_config['color']}; margin: 0.5rem 0;">
            <h5 style="margin: 0 0 0.5rem 0; color: {selected_config['color']};">{selected_config['name']}</h5>
            <p style="margin: 0 0 0.5rem 0; color: #6c757d; font-size: 0.9rem;">{selected_config['description']}</p>
            <p style="margin: 0; color: #495057; font-size: 0.85rem;">{selected_config['use_case']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add info about model switching
        st.info("💡 **팁**: 모델을 변경하면 다음 메시지부터 새로운 모델이 적용됩니다. 현재 대화의 맥락은 유지됩니다.")

    @staticmethod
    def render_message(message: Dict[str, Any]):
        """Render a single chat message with HAI Portal styling"""
        role = message["role"]
        content = message["content"]
        timestamp = message.get("timestamp", "")
        context = message.get("context", [])
        metadata = message.get("metadata", {})
        message_id = message.get("id", str(hash(content + str(timestamp))))

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
                    # PDF and Markdown export buttons
                    col2_1, col2_2 = st.columns(2)
                    
                    with col2_1:
                        if st.button("📄", key=f"download_user_message_pdf_{message_id}", help="PDF 저장", use_container_width=True, type="primary"):
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
                    
                    with col2_2:
                        if st.button("📝", key=f"download_user_message_md_{message_id}", help="마크다운 저장", use_container_width=True, type="secondary"):
                            try:
                                from services.api_service import APIService
                                api_service = APIService()
                                
                                # Export single message to markdown
                                result = api_service.export_single_message_markdown(message, True)
                                
                                if result.get("success"):
                                    filename = f"user_message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                                    
                                    st.download_button(
                                        label="📥 마크다운 다운로드",
                                        data=result.get("content", ""),
                                        file_name=filename,
                                        mime="text/markdown"
                                    )
                                else:
                                    st.error(f"마크다운 생성 오류: {result.get('error', '알 수 없는 오류')}")
                            except Exception as e:
                                st.error(f"마크다운 생성 오류: {str(e)}")
        else:
            with st.chat_message("assistant"):
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; 
                            border-left: 4px solid #8B5CF6; margin: 1rem 0 2rem 0; 
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    {content}
                </div>
                """, unsafe_allow_html=True)
                
                # Display model information
                model_info = message.get("model_info", {})
                if model_info:
                    model_type = model_info.get("model_type", "fast")
                    model_name = model_info.get("model", "exaone3.5:2.4b")
                    
                    # Model type to display name mapping
                    model_display_names = {
                        "fast": "⚡ 빠른 응답",
                        "quality": "🎯 고품질 응답", 
                        "complex": "🧠 복잡한 작업"
                    }
                    
                    display_name = model_display_names.get(model_type, "⚡ 빠른 응답")
                    
                    st.markdown(f"""
                    <div style="background: #e3f2fd; padding: 0.5rem 1rem; border-radius: 5px; 
                                margin: 0.5rem 0; border-left: 3px solid #2196f3; font-size: 0.9rem;">
                        <strong>{display_name}</strong> • {model_name}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Display sources and accuracy information
                sources = message.get("sources", [])
                accuracy = message.get("accuracy", {})
                
                if sources or accuracy:
                    ChatComponents._render_sources_and_accuracy(sources, accuracy)
                elif metadata:
                    # If metadata exists but no sources/accuracy, show a default score
                    st.info("신뢰도 정보를 계산하는 중입니다...")
                else:
                    # No metadata available - show RAG mode from metadata or session state
                    rag_mode = metadata.get("rag_mode") if metadata else st.session_state.get("rag_mode", "LangChain RAG")
                    if rag_mode == "기본 RAG":
                        st.info("기본 RAG 모드로 응답합니다.")
                    else:
                        st.info("LangChain RAG 모드로 응답합니다.")
                
                # AI message with PDF and Markdown icons
                col1, col2 = st.columns([1, 0.08])
                with col1:
                    if timestamp:
                        st.caption(f"🤖 {ChatComponents._format_timestamp(timestamp)}")
                with col2:
                    # PDF and Markdown export buttons
                    col2_1, col2_2 = st.columns(2)
                    
                    with col2_1:
                        if st.button("📄", key=f"download_message_pdf_{message_id}", help="PDF 저장", use_container_width=True, type="primary"):
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
                    
                    with col2_2:
                        if st.button("📝", key=f"download_message_md_{message_id}", help="마크다운 저장", use_container_width=True, type="secondary"):
                            try:
                                from services.api_service import APIService
                                api_service = APIService()
                                
                                # Export single message to markdown
                                result = api_service.export_single_message_markdown(message, True)
                                
                                if result.get("success"):
                                    filename = f"message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                                    
                                    st.download_button(
                                        label="📥 마크다운 다운로드",
                                        data=result.get("content", ""),
                                        file_name=filename,
                                        mime="text/markdown"
                                    )
                                else:
                                    st.error(f"마크다운 생성 오류: {result.get('error', '알 수 없는 오류')}")
                            except Exception as e:
                                st.error(f"마크다운 생성 오류: {str(e)}")

    @staticmethod
    def _render_sources_and_accuracy(sources: List[Dict[str, Any]], accuracy: Dict[str, Any]):
        """Render sources and accuracy information with visual indicators"""
        # Render accuracy information
        if accuracy:
            confidence_score = accuracy.get("confidence_score", 0.0)
            context_count = accuracy.get("context_count", 0)
            avg_similarity = accuracy.get("avg_similarity", 0.0)
            fallback_used = accuracy.get("fallback_used", False)
            
            # Convert scores to percentage
            confidence_percent = round(confidence_score * 100, 1)
            similarity_percent = round(avg_similarity * 100, 1)
            
            # Determine color and emoji based on confidence
            if confidence_score >= 0.8:
                color = "#10B981"  # Green
                emoji = "🟢"
                status = "매우 높음"
            elif confidence_score >= 0.6:
                color = "#F59E0B"  # Yellow
                emoji = "🟡"
                status = "높음"
            elif confidence_score >= 0.4:
                color = "#F97316"  # Orange
                emoji = "🟠"
                status = "보통"
            else:
                color = "#EF4444"  # Red
                emoji = "🔴"
                status = "낮음"
            
            # Show fallback warning if used
            if fallback_used:
                st.warning("⚠️ 관련 문서를 찾을 수 없어 일반 지식으로 답변했습니다.")
            
            # Render accuracy information
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin: 1rem 0 1rem 0; padding: 1rem; 
                        background: #f8f9fa; border-radius: 8px; border-left: 3px solid {color};
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <span style="font-size: 1.2rem; margin-right: 0.75rem;">{emoji}</span>
                <div style="flex: 1;">
                    <strong style="color: {color}; font-size: 1.1rem;">답변 신뢰도: {confidence_percent}%</strong>
                    <small style="color: #666; margin-left: 0.5rem; font-size: 0.9rem;">({status})</small>
                    <br>
                    <small style="color: #666; font-size: 0.9rem;">
                        컨텍스트 문서: {context_count}개 | 평균 유사도: {similarity_percent}%
                    </small>
                </div>
                <div style="background: {color}; height: 10px; border-radius: 5px; 
                            width: {confidence_percent}%; min-width: 30px; margin-left: 1rem;"></div>
            </div>
            """, unsafe_allow_html=True)
        
        # Render sources information
        if sources:
            st.markdown("**📚 참조 문서:**")
            
            for i, source in enumerate(sources, 1):
                filename = source.get("filename", f"문서 {i}")
                similarity_score = source.get("similarity", source.get("similarity_score", 0.0))
                content_preview = source.get("content_preview", "")
                document_id = source.get("document_id", "")
                
                # Convert similarity to percentage and ensure it's valid
                similarity_percent = round(max(0.0, min(1.0, similarity_score)) * 100, 1)
                
                # Determine color based on similarity (ensure valid range)
                normalized_score = max(0.0, min(1.0, similarity_score))
                if normalized_score >= 0.8:
                    source_color = "#10B981"  # Green
                elif normalized_score >= 0.6:
                    source_color = "#F59E0B"  # Yellow
                elif normalized_score >= 0.4:
                    source_color = "#F97316"  # Orange
                else:
                    source_color = "#EF4444"  # Red
                
                # Create expandable source information
                with st.expander(f"📄 {filename} (유사도: {similarity_percent}%)", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**파일명:** {filename}")
                        if document_id:
                            st.write(f"**문서 ID:** {document_id}")
                        st.write(f"**유사도 점수:** {similarity_percent}%")
                    
                    with col2:
                        st.markdown(f"""
                        <div style="background: {source_color}; height: 20px; border-radius: 10px; 
                                    width: 100%; display: flex; align-items: center; justify-content: center;
                                    color: white; font-weight: bold; font-size: 0.9rem;">
                            {similarity_percent}%
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if content_preview:
                        st.write("**내용 미리보기:**")
                        st.text_area("", content_preview, height=100, disabled=True, key=f"source_preview_{i}")
        
        # If no sources but accuracy info exists, show a message
        elif accuracy and not sources:
            st.info("📚 참조 문서 정보를 가져오는 중입니다...")

    @staticmethod
    def _render_similarity_score(similarity: float):
        """Render similarity score with visual indicator (legacy method)"""
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
            # Get current session ID first
            current_session = st.session_state.get("session_id", "default")
            
            # HAI Portal branding
            st.markdown("""
            <div style="text-align: center; padding: 1rem 0; border-bottom: 2px solid #8B5CF6;">
                <h1 style="color: #8B5CF6; margin: 0; font-size: 1.8rem;">HAI Portal</h1>
            </div>
            """, unsafe_allow_html=True)
            
            # User info
            user_info = st.session_state.get("user_info")
            if user_info:
                st.markdown(f"""
                <div style="background: #f0f9ff; padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0; border-left: 3px solid #0ea5e9;">
                    <div style="font-weight: 500; color: #0c4a6e;">👤 {user_info.get('username', '사용자')}</div>
                    <div style="font-size: 0.8rem; color: #64748b;">{user_info.get('email', '')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Export section
            st.markdown("### 📄 내보내기")
            
            # Export format selection
            export_format = st.radio(
                "내보내기 형식 선택",
                ["PDF", "마크다운"],
                help="PDF: 시각적으로 보기 좋은 문서\n마크다운: 텍스트 기반 문서 (GitHub, Notion 등에서 사용 가능)"
            )
            
            if export_format == "PDF":
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
            
            else:  # Markdown export
                # Markdown export options
                session_name = st.text_input(
                    "세션 이름",
                    value=st.session_state.get(f"session_name_{current_session}", "채팅 기록"),
                    help="마크다운 파일에 표시될 세션 이름"
                )
                
                include_metadata = st.checkbox(
                    "메타데이터 포함",
                    value=True,
                    help="신뢰도 점수, 참조 문서 등 메타데이터를 마크다운에 포함"
                )
                
                # Generate Markdown button
                if st.button("📝 마크다운 다운로드", key="download_markdown", use_container_width=True):
                    return ("download_markdown", session_name, include_metadata)
            
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
            
            # User management button (admin only)
            user_info = st.session_state.get("user_info")
            if user_info and user_info.get("id") == ADMIN_USER_ID:  # admin user ID
                if st.button("👥 사용자 관리", key="user_management", use_container_width=True):
                    st.session_state.current_page = "user_management"
                    st.rerun()
                    
                    # Show message about creating collections
                    st.markdown("""
                    **컬렉션 생성 방법:**
                    1. 컬렉션 관리 페이지에서 직접 생성
                    2. 파일 업로드 페이지에서 문서를 업로드
                    3. LangChain RAG 모드로 업로드
                    """)
            
            # Logout button
            st.markdown("---")
            if st.button("🚪 로그아웃", key="logout", use_container_width=True, type="secondary"):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                
                # Show success message
                st.success("로그아웃되었습니다.")
                
                # Redirect to login page
                st.switch_page("pages/login.py")

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
