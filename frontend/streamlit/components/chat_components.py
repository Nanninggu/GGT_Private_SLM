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

try:
    from services.pdf_service import PDFService
except ImportError:
    PDFService = None
try:
    from services.api_service import APIService
except ImportError:
    APIService = None
try:
    from services.session_management_service import session_manager
except ImportError:
    session_manager = None

try:
    from config import ADMIN_USER_ID
except ImportError:
    ADMIN_USER_ID = "admin"

class ChatComponents:
    """Reusable chat UI components"""

    @staticmethod
    def render_model_selection():
        """Render model selection UI"""
        # Initialize model type in session state
        if "selected_model_type" not in st.session_state:
            st.session_state.selected_model_type = "fast"
        
        # Model configurations (백엔드 settings.py와 일치) - Modern Enterprise White theme
        model_configs = {
            "fast": {
                "name": "⚡ 빠른 응답",
                "description": "exaone3.5:2.4b-instruct-q4_K_M (1.6GB, Q4_K_M)",
                "use_case": "일반적인 질문, 초고속 응답이 필요한 경우",
                "color": "#6c757d"
            },
            "quality": {
                "name": "🎯 고품질 응답",
                "description": "exaone3.5:2.4b-instruct-q8_0 (2.8GB, Q8_0)",
                "use_case": "정확한 답변이 필요한 경우, 창의적 작업",
                "color": "#495057"
            },
            "complex": {
                "name": "🧠 복잡한 작업",
                "description": "exaone3.5:7.8b (4.8GB, 7.8B 파라미터)",
                "use_case": "복잡한 추론, 창의적 글쓰기, 전문적 분석",
                "color": "#212529"
            }
        }
        
        # Create modern model selection UI
        st.markdown("""
        <div style="background: #ffffff; padding: 2rem; border-radius: 20px; margin-bottom: 1.5rem; 
                    border: 2px solid #f1f3f4; box-shadow: 0 4px 20px rgba(0,0,0,0.06);
                    position: relative; overflow: hidden;">
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; 
                        background: linear-gradient(90deg, #6c757d 0%, #495057 100%);"></div>
            <h4 style="margin: 0 0 1rem 0; color: #212529; font-weight: 700; font-size: 1.2rem;">🤖 AI 모델 선택</h4>
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
        
        # Display selected model info (full width) - Modern Enterprise card style
        st.markdown(f"""
        <div style="background: #ffffff; padding: 2rem; border-radius: 20px; 
                    border-left: 4px solid {selected_config['color']}; margin: 1rem 0;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.08); border: 2px solid #f1f3f4;
                    position: relative; overflow: hidden;">
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; 
                        background: linear-gradient(90deg, {selected_config['color']} 0%, {selected_config['color']}80 100%);"></div>
            <h5 style="margin: 0 0 0.75rem 0; color: {selected_config['color']}; font-weight: 700; font-size: 1.1rem;">{selected_config['name']}</h5>
            <p style="margin: 0 0 0.75rem 0; color: #6c757d; font-size: 0.95rem; line-height: 1.5;">{selected_config['description']}</p>
            <p style="margin: 0; color: #495057; font-size: 0.9rem; line-height: 1.4;">{selected_config['use_case']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add info about model switching - Modern Enterprise info box
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 16px; margin-top: 1rem; 
                    border: 2px solid #f1f3f4; border-left: 4px solid #6c757d;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
            <p style="margin: 0; color: #495057; font-size: 0.9rem; font-weight: 500;">
                💡 <strong>팁</strong>: 모델을 변경하면 다음 메시지부터 새로운 모델이 적용됩니다. 현재 대화의 맥락은 유지됩니다.
            </p>
        </div>
        """, unsafe_allow_html=True)

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
                # Use Streamlit's built-in styling with custom container
                with st.container():
                    st.markdown(f"**{content}**")
                    if timestamp:
                        st.caption(f"👤 사용자 • {ChatComponents._format_timestamp(timestamp)}")
                
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
                            # Generate and download PDF directly
                            if PDFService:
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
                                        label="📥 PDF 다운로드",
                                        data=pdf_content,
                                        file_name=filename,
                                        mime="application/pdf",
                                        key=f"download_user_pdf_{message_id}"
                                    )
                                except Exception as e:
                                    st.error(f"PDF 생성 오류: {str(e)}")
                            else:
                                st.info("PDF 서비스가 사용할 수 없습니다.")
                    
                    with col2_2:
                        if st.button("📝", key=f"download_user_message_md_{message_id}", help="마크다운 저장", use_container_width=True, type="secondary"):
                            # Generate and download Markdown directly
                            if APIService:
                                try:
                                    api_service = APIService()
                                    
                                    # Export single message to markdown
                                    result = api_service.export_single_message_markdown(message, True)
                                    
                                    if result.get("success"):
                                        filename = f"user_message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                                        
                                        st.download_button(
                                            label="📥 마크다운 다운로드",
                                            data=result.get("content", ""),
                                            file_name=filename,
                                            mime="text/markdown",
                                            key=f"download_user_md_{message_id}"
                                        )
                                    else:
                                        st.error(f"마크다운 생성 오류: {result.get('error', '알 수 없는 오류')}")
                                except Exception as e:
                                    st.error(f"마크다운 생성 오류: {str(e)}")
                            else:
                                st.info("API 서비스가 사용할 수 없습니다.")
                
        else:
            with st.chat_message("assistant"):
                # Use Streamlit's built-in styling with custom container
                with st.container():
                    st.markdown(content)
                    if timestamp:
                        st.caption(f"🤖 AI • {ChatComponents._format_timestamp(timestamp)}")
                
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
                
                # Display quality metrics if available
                quality_metrics = message.get("metadata", {}).get("quality_metrics", {})
                if quality_metrics:
                    ChatComponents._render_quality_metrics(quality_metrics)
                
                # Display feedback UI
                ChatComponents._render_feedback_ui(message_id, message)
                
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
                            # Generate and download PDF directly
                            if PDFService:
                                try:
                                    pdf_service = PDFService()
                                    single_message = [message]
                                    pdf_content = pdf_service.generate_chat_pdf(
                                        single_message,
                                        "single_message",
                                        "개별 메시지",
                                        True
                                    )
                                    
                                    filename = f"assistant_message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                    
                                    st.download_button(
                                        label="📥 PDF 다운로드",
                                        data=pdf_content,
                                        file_name=filename,
                                        mime="application/pdf",
                                        key=f"download_assistant_pdf_{message_id}"
                                    )
                                except Exception as e:
                                    st.error(f"PDF 생성 오류: {str(e)}")
                            else:
                                st.info("PDF 서비스가 사용할 수 없습니다.")
                    
                    with col2_2:
                        if st.button("📝", key=f"download_message_md_{message_id}", help="마크다운 저장", use_container_width=True, type="secondary"):
                            # Generate and download Markdown directly
                            if APIService:
                                try:
                                    api_service = APIService()
                                    
                                    # Export single message to markdown
                                    result = api_service.export_single_message_markdown(message, True)
                                    
                                    if result.get("success"):
                                        filename = f"assistant_message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                                        
                                        st.download_button(
                                            label="📥 마크다운 다운로드",
                                            data=result.get("content", ""),
                                            file_name=filename,
                                            mime="text/markdown",
                                            key=f"download_assistant_md_{message_id}"
                                        )
                                    else:
                                        st.error(f"마크다운 생성 오류: {result.get('error', '알 수 없는 오류')}")
                                except Exception as e:
                                    st.error(f"마크다운 생성 오류: {str(e)}")
                            else:
                                st.info("API 서비스가 사용할 수 없습니다.")
                


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
            
            # Render accuracy information using Streamlit components
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.markdown(f"<div style='text-align: center; font-size: 2rem;'>{emoji}</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**답변 신뢰도: {confidence_percent}%** ({status})")
                st.markdown(f"컨텍스트 문서: {context_count}개 | 평균 유사도: {similarity_percent}%")
            
            with col3:
                # Progress bar for confidence
                st.progress(confidence_score)
                st.caption(f"{confidence_percent}%")
            
            # Color-coded status indicator
            if confidence_score >= 0.8:
                st.success(f"🟢 신뢰도가 매우 높습니다 ({confidence_percent}%)")
            elif confidence_score >= 0.6:
                st.warning(f"🟡 신뢰도가 높습니다 ({confidence_percent}%)")
            elif confidence_score >= 0.4:
                st.warning(f"🟠 신뢰도가 보통입니다 ({confidence_percent}%)")
            else:
                st.error(f"🔴 신뢰도가 낮습니다 ({confidence_percent}%)")
        
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
    def _render_quality_metrics(quality_metrics: Dict[str, Any]):
        """Render quality metrics with visual indicators"""
        overall_score = quality_metrics.get("overall_score", 0.0)
        quality_level = quality_metrics.get("quality_level", "fair")
        issues = quality_metrics.get("issues", [])
        suggestions = quality_metrics.get("suggestions", [])
        
        # Convert score to percentage
        score_percent = round(overall_score * 100, 1)
        
        # Determine color and emoji based on quality level
        quality_colors = {
            "excellent": "#10B981",  # Green
            "good": "#3B82F6",       # Blue
            "fair": "#F59E0B",       # Yellow
            "poor": "#EF4444"        # Red
        }
        
        quality_emojis = {
            "excellent": "🟢",
            "good": "🔵", 
            "fair": "🟡",
            "poor": "🔴"
        }
        
        color = quality_colors.get(quality_level, "#6B7280")
        emoji = quality_emojis.get(quality_level, "⚪")
        
        # Render quality metrics
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0;
                    border-left: 3px solid {color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.75rem;">{emoji}</span>
                <strong style="color: {color}; font-size: 1.1rem;">응답 품질: {score_percent}%</strong>
                <small style="color: #666; margin-left: 0.5rem; font-size: 0.9rem;">({quality_level})</small>
            </div>
            <div style="background: {color}; height: 8px; border-radius: 4px; 
                        width: {score_percent}%; min-width: 20px; margin-bottom: 0.5rem;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show issues and suggestions if available
        if issues or suggestions:
            with st.expander("🔍 품질 분석 상세", expanded=False):
                if issues:
                    st.markdown("**⚠️ 발견된 문제점:**")
                    for issue in issues:
                        st.markdown(f"• {issue}")
                
                if suggestions:
                    st.markdown("**💡 개선 제안:**")
                    for suggestion in suggestions:
                        st.markdown(f"• {suggestion}")

    @staticmethod
    def _render_feedback_ui(message_id: str, message: Dict[str, Any]):
        """Render feedback UI for user interaction"""
        st.markdown("---")
        
        # Feedback section header with better styling
        st.markdown("""
        <div style="margin: 1rem 0 1.5rem 0; padding: 0.75rem 0; border-bottom: 1px solid #e9ecef;">
            <h4 style="margin: 0; color: #495057; font-size: 1rem; font-weight: 600;">
                💬 이 응답이 도움이 되었나요?
            </h4>
        </div>
        
        <style>
        /* Feedback button styling */
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
            border: 1px solid #e9ecef !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        }
        
        /* Star rating button - same style as other buttons */
        .stButton > button[kind="secondary"]:has-text("⭐") {
            background: #f8f9fa !important;
            color: #495057 !important;
            border-color: #dee2e6 !important;
        }
        
        .stButton > button[kind="secondary"]:has-text("⭐"):hover {
            background: #e9ecef !important;
            border-color: #adb5bd !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Main feedback row - only star rating, centered in half screen width with left alignment
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Star rating section - clean and simple
            st.markdown("**별점 평가**")
            
            # Functional buttons row - only star rating
            col2_1, col2_2 = st.columns([1, 1])
            
            with col2_1:
                rating = st.selectbox(
                    "점수 선택",
                    [1, 2, 3, 4, 5],
                    index=4,  # Default to 5 stars
                    key=f"rating_{message_id}",
                    help="1-5점으로 평가해주세요",
                    label_visibility="collapsed"
                )
            
            with col2_2:
                if st.button("⭐ 평가", key=f"submit_rating_{message_id}", use_container_width=True, type="secondary"):
                    ChatComponents._submit_feedback(message_id, "rating", rating=rating)
                    st.success(f"피드백이 제출되었습니다. {rating}점 평가를 주셔서 감사합니다!")

    @staticmethod
    def _submit_feedback(message_id: str, feedback_type: str, is_positive: bool = None, rating: int = None, comment: str = None):
        """Submit feedback to backend and database"""
        try:
            # Get user info from session state
            user_info = st.session_state.get("user_info", {})
            user_id = user_info.get("id", "anonymous")
            session_id = st.session_state.get("session_id", "default")
            
            # Prepare feedback data
            feedback_data = {
                "user_id": user_id,
                "session_id": session_id,
                "message_id": message_id,
                "feedback_type": feedback_type,
                "is_positive": is_positive,
                "rating": rating,
                "comment": comment,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in local session state first (always works)
            if "feedback_history" not in st.session_state:
                st.session_state.feedback_history = []
            
            st.session_state.feedback_history.append({
                "message_id": message_id,
                "feedback_type": feedback_type,
                "rating": rating,
                "is_positive": is_positive,
                "comment": comment,
                "timestamp": datetime.now().isoformat()
            })
            
            # Try to submit to backend via API
            api_success = False
            try:
                from services.api_service import APIService
                api_service = APIService()
                
                # Submit feedback via API
                result = api_service.submit_feedback(feedback_data)
                
                if result and result.get("success"):
                    # Database submission successful
                    st.info("피드백이 데이터베이스에 저장되었습니다.")
                    api_success = True
                else:
                    error_msg = result.get('error', '알 수 없는 오류') if result else '응답을 받을 수 없음'
                    st.warning(f"데이터베이스 저장 실패 (로컬 저장됨): {error_msg}")
                    
            except ImportError as e:
                st.warning(f"API 서비스를 불러올 수 없습니다 (로컬 저장됨): {str(e)}")
            except Exception as e:
                # API service error, but local storage worked
                st.warning(f"데이터베이스 연결 실패 (로컬 저장됨): {str(e)}")
            
            # Show success message based on submission result
            if api_success:
                if feedback_type == "rating" and rating:
                    st.success(f"피드백이 제출되었습니다. {rating}점 평가를 주셔서 감사합니다!")
                else:
                    st.success("피드백이 제출되었습니다. 피드백을 주셔서 감사합니다!")
            else:
                if feedback_type == "rating" and rating:
                    st.success(f"피드백이 로컬에 저장되었습니다. {rating}점 평가를 주셔서 감사합니다!")
                else:
                    st.success("피드백이 로컬에 저장되었습니다. 피드백을 주셔서 감사합니다!")
            
        except Exception as e:
            st.error(f"피드백 제출 중 오류가 발생했습니다: {str(e)}")

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
    def render_session_sidebar():
        """Render session management sidebar with management features"""
        try:
            from controllers.chat_controller import ChatController
            
            # Initialize chat controller
            chat_controller = ChatController()
        except ImportError:
            st.error("채팅 컨트롤러를 불러올 수 없습니다.")
            return None
        
        # Get current user info
        user_info = st.session_state.get("user_info", {})
        user_id = user_info.get("id", "default")
        
        # Use new session management service if available
        if session_manager and user_id != "default":
            user_sessions = session_manager.get_user_sessions(user_id)
            session_count = len(user_sessions)
        else:
            # Fallback to old system
            user_sessions = []
            if chat_controller.api_service:
                response = chat_controller.api_service.get_user_sessions(user_id)
                if response.get("success") and response.get("sessions"):
                    user_sessions = response["sessions"]
            
            # Fallback to file-based sessions if no database sessions
            if not user_sessions:
                sessions = chat_controller.get_available_sessions()
                user_sessions = [{"session_id": session_id, "title": f"세션 {session_id[:8]}...", "created_at": None, "message_count": 0} for session_id in sessions]
            
            session_count = len(user_sessions) if user_sessions else 0
        
        # Chat History Header with improved styling
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; padding: 0.5rem 0;">
            <h3 style="margin: 0; color: #495057; font-size: 1.1rem; font-weight: 600;">💬 채팅 히스토리 ({session_count}개)</h3>
            <div style="display: flex; gap: 0.5rem;">
                <button onclick="window.location.reload()" style="background: none; border: none; color: #6c757d; cursor: pointer; font-size: 1.2rem; padding: 0.25rem;" title="새로고침">🔄</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Search and filter section
        if session_count > 0:
            search_query = st.text_input("🔍 세션 검색", placeholder="세션 제목이나 내용으로 검색...", key="session_search")
            if search_query:
                # Filter sessions based on search query
                filtered_sessions = []
                for session in user_sessions:
                    title = session.get("title", "").lower()
                    if search_query.lower() in title:
                        filtered_sessions.append(session)
                user_sessions = filtered_sessions
        
        # New Chat Button with enhanced styling
        st.markdown("""
        <style>
        div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, #6c757d 0%, #495057 100%) !important;
            color: white !important;
            border: 2px solid #495057 !important;
            border-radius: 20px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 16px rgba(108, 117, 125, 0.3) !important;
            width: 100% !important;
            text-align: center !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.5rem !important;
        }
        
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(108, 117, 125, 0.4) !important;
            background: linear-gradient(135deg, #495057 0%, #343a40 100%) !important;
            border-color: #343a40 !important;
        }
        
        div[data-testid="stButton"] > button[kind="primary"]:active {
            transform: translateY(0) !important;
            box-shadow: 0 4px 16px rgba(108, 117, 125, 0.3) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if st.button("💬 새 채팅", key="new_chat_btn", use_container_width=True, type="primary"):
            # Use new session management service if available
            if session_manager and user_id != "default":
                # Save current session first
                session_manager.save_current_session(user_id)
                
                # Create new session
                new_session_id = session_manager.create_new_session(user_id)
                
                if new_session_id:
                    # Clear any confirmation states
                    for key in list(st.session_state.keys()):
                        if key.startswith("confirm_delete_") or key.startswith("show_"):
                            del st.session_state[key]
                    
                    # Force refresh session list
                    st.session_state.force_refresh = True
                    
                    # Show success message
                    st.success("✨ 새 채팅이 시작되었습니다!")
                    
                    # Use JavaScript to reload the page safely
                    st.markdown("""
                    <script>
                    setTimeout(function() {
                        window.location.reload();
                    }, 500);
                    </script>
                    """, unsafe_allow_html=True)
                else:
                    st.error("새 채팅 생성에 실패했습니다.")
            else:
                # Fallback to old system
                # Save current chat if it has messages
                current_messages = st.session_state.get("messages", [])
                if current_messages:
                    # Save current session before creating new one
                    try:
                        if chat_controller.api_service:
                            chat_controller.api_service.save_session(st.session_state.session_id, current_messages)
                    except:
                        pass  # Continue even if save fails
                
                # Generate new session ID immediately
                import uuid
                new_session_id = str(uuid.uuid4())
                
                # Update session state immediately
                st.session_state.session_id = new_session_id
                st.session_state.messages = []
                st.session_state.last_loaded_session = None
                st.session_state.is_new_session = True
                
                # Generate unique title with timestamp (will be updated when first question is asked)
                timestamp = datetime.now().strftime("%m/%d %H:%M")
                st.session_state.session_title = f"새 대화 ({timestamp})"
                
                # Create session in database
                if chat_controller.api_service:
                    try:
                        response = chat_controller.api_service.create_chat_session(
                            new_session_id,
                            st.session_state.get("user_id", "default"),
                            st.session_state.session_title
                        )
                        if not response.get("success"):
                            st.warning(f"DB에 세션 저장 실패: {response.get('error', '알 수 없는 오류')}")
                    except Exception as e:
                        st.warning(f"DB에 세션 저장 중 오류: {str(e)}")
                
                # Clear any confirmation states
                for key in list(st.session_state.keys()):
                    if key.startswith("confirm_delete_") or key.startswith("show_"):
                        del st.session_state[key]
                
                # Force refresh session list
                st.session_state.force_refresh = True
                
                # Show success message with better styling
                st.success("✨ 새 채팅이 시작되었습니다!")
                
                # Use JavaScript to reload the page safely
                st.markdown("""
                <script>
                setTimeout(function() {
                    window.location.reload();
                }, 500);
                </script>
                """, unsafe_allow_html=True)
        
        # Clear All Chats Button with confirmation
        if st.button("🗑️ 전체 삭제", key="clear_all_chats_btn", use_container_width=True, type="secondary"):
            # Show confirmation dialog
            st.session_state.show_clear_all_confirm = True
        
        # Confirmation dialog for clear all
        if st.session_state.get("show_clear_all_confirm", False):
            st.markdown("""
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; 
                        padding: 1rem; margin: 0.5rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem;">⚠️</span>
                    <strong style="color: #856404;">모든 채팅 기록을 삭제하시겠습니까?</strong>
                </div>
                <div style="color: #856404; font-size: 0.9rem;">
                    이 작업은 되돌릴 수 없습니다. 모든 채팅 세션이 영구적으로 삭제됩니다.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Use buttons without columns in sidebar
            if st.button("✅ 확인", key="confirm_clear_all", type="primary", use_container_width=True):
                try:
                    # Clear current session immediately
                    st.session_state.messages = []
                    st.session_state.session_id = "default"
                    st.session_state.last_loaded_session = None
                    
                    # Clear any confirmation states
                    for key in list(st.session_state.keys()):
                        if key.startswith("confirm_delete_") or key.startswith("show_"):
                            del st.session_state[key]
                    
                    # Try to clear backend sessions
                    backend_success = True
                    try:
                        if chat_controller.api_service and chat_controller.check_backend_connection():
                            result = chat_controller.clear_all_sessions()
                            if not result.get("success", False):
                                backend_success = False
                                st.warning(f"백엔드 삭제 중 일부 오류가 발생했습니다: {result.get('warning', '알 수 없는 오류')}")
                    except Exception as e:
                        backend_success = False
                        st.warning(f"백엔드 삭제 중 오류가 발생했습니다: {str(e)}")
                    
                    # Show success message
                    if backend_success:
                        st.success("모든 채팅이 성공적으로 삭제되었습니다.")
                    else:
                        st.warning("현재 채팅이 초기화되었습니다. 일부 백엔드 데이터는 수동으로 정리해야 할 수 있습니다.")
                    
                    # Force refresh session list
                    st.session_state.force_refresh = True
                    
                    # Clear confirmation state
                    st.session_state.show_clear_all_confirm = False
                except Exception as e:
                    st.error(f"전체 삭제 중 오류가 발생했습니다: {str(e)}")
            
            if st.button("❌ 취소", key="cancel_clear_all", use_container_width=True):
                st.session_state.show_clear_all_confirm = False
        
        
        st.markdown("---")
        
        # Display session list
        current_session = st.session_state.get("session_id", "default")
        
        if not user_sessions:
            st.markdown("""
            <div style="text-align: center; padding: 2rem 1rem; color: #6c757d;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">💭</div>
                <div>아직 채팅 기록이 없습니다</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem;">새 채팅을 시작해보세요!</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Sort sessions by last activity (newest first)
            user_sessions.sort(key=lambda x: x.get("last_activity", x.get("created_at", "")), reverse=True)
            
            # Create scrollable container for sessions
            st.markdown("""
            <div style="max-height: 400px; overflow-y: auto; padding-right: 0.5rem;">
            """, unsafe_allow_html=True)
            
            # Display each session
            for session in user_sessions:
                session_id = session.get("session_id")
                session_title = session.get("title", "알 수 없는 채팅")
                message_count = session.get("message_count", 0)
                last_activity = session.get("last_activity", "")
                is_current = session_id == current_session
                
                # Format last activity
                if last_activity:
                    try:
                        if isinstance(last_activity, str):
                            dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                            last_activity = dt.strftime("%m/%d %H:%M")
                    except:
                        last_activity = "알 수 없음"
                
                # Create session item
                with st.container():
                    # Session name and actions in horizontal layout
                    if session_id != "default":
                        # Create horizontal layout for session name and action buttons
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            # Session button
                            button_type = "primary" if is_current else "secondary"
                            button_text = f"💬 {session_title}"
                            if is_current:
                                button_text = f"▶️ {session_title}"
                            
                            if st.button(
                                button_text,
                                key=f"session_{session_id}",
                                help=f"메시지: {message_count}개\n마지막 활동: {last_activity}",
                                use_container_width=True,
                                type=button_type
                            ):
                                if not is_current:
                                    # Use new session management service if available
                                    if session_manager and user_id != "default":
                                        session_manager.switch_to_session(user_id, session_id)
                                    else:
                                        chat_controller.switch_to_session(session_id)
                        
                        with col2:
                            if st.button("✏️", key=f"edit_{session_id}", help="제목 편집", use_container_width=True):
                                st.session_state[f"editing_title_{session_id}"] = True
                        
                        with col3:
                            if st.button("🗑️", key=f"delete_{session_id}", help="삭제", use_container_width=True):
                                st.session_state[f"confirm_delete_{session_id}"] = True
                    else:
                        # Default session - no action buttons
                        button_type = "primary" if is_current else "secondary"
                        button_text = f"💬 {session_title}"
                        if is_current:
                            button_text = f"▶️ {session_title}"
                        
                        if st.button(
                            button_text,
                            key=f"session_{session_id}",
                            help=f"메시지: {message_count}개\n마지막 활동: {last_activity}",
                            use_container_width=True,
                            type=button_type
                        ):
                            if not is_current:
                                # Use new session management service if available
                                if session_manager and user_id != "default":
                                    session_manager.switch_to_session(user_id, session_id)
                                else:
                                    chat_controller.switch_to_session(session_id)
                    
                    # Show edit form if editing
                    if st.session_state.get(f"editing_title_{session_id}", False):
                        with st.expander("제목 편집", expanded=True):
                            new_title = st.text_input(
                                "새 제목",
                                value=session_title,
                                key=f"edit_title_{session_id}"
                            )
                            
                            # Use horizontal layout for buttons
                            st.markdown("""
                            <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                            """, unsafe_allow_html=True)
                            
                            if st.button("💾", key=f"save_title_{session_id}", help="저장", use_container_width=True):
                                if new_title.strip():
                                    # Use new session management service if available
                                    if session_manager and user_id != "default":
                                        if session_manager.update_session_title(user_id, session_id, new_title.strip()):
                                            st.success("제목이 저장되었습니다!")
                                            del st.session_state[f"editing_title_{session_id}"]
                                        else:
                                            st.error("제목 저장에 실패했습니다.")
                                    else:
                                        # Fallback to old system
                                        if chat_controller.api_service:
                                            response = chat_controller.api_service.update_session_title(
                                                session_id, 
                                                new_title.strip(),
                                                st.session_state.get("user_id", "default")
                                            )
                                            if response.get("success"):
                                                st.success("제목이 저장되었습니다!")
                                                del st.session_state[f"editing_title_{session_id}"]
                                            else:
                                                st.error(f"저장 실패: {response.get('error', '알 수 없는 오류')}")
                                        else:
                                            st.session_state[f"session_title_{session_id}"] = new_title.strip()
                                            st.success("제목이 저장되었습니다! (로컬 저장)")
                                            del st.session_state[f"editing_title_{session_id}"]
                                else:
                                    st.error("제목을 입력해주세요.")
                            
                            if st.button("❌", key=f"cancel_edit_{session_id}", help="취소", use_container_width=True):
                                del st.session_state[f"editing_title_{session_id}"]
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Show delete confirmation if needed
                    if st.session_state.get(f"confirm_delete_{session_id}", False):
                        st.warning("⚠️ 이 세션을 삭제하시겠습니까?")
                        
                        # Use horizontal layout for buttons
                        st.markdown("""
                        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                        """, unsafe_allow_html=True)
                        
                        if st.button("✅", key=f"confirm_yes_{session_id}", help="삭제", use_container_width=True):
                            try:
                                # Use new session management service if available
                                if session_manager and user_id != "default":
                                    if session_manager.delete_session(user_id, session_id):
                                        # Force refresh
                                        st.session_state.force_refresh = True
                                        del st.session_state[f"confirm_delete_{session_id}"]
                                        st.success("세션이 삭제되었습니다!")
                                    else:
                                        st.error("세션 삭제에 실패했습니다.")
                                else:
                                    # Fallback to old system
                                    # Delete from database
                                    if chat_controller.api_service:
                                        chat_controller.api_service.delete_chat_session(session_id)
                                    
                                    # Delete from file system
                                    chat_controller.delete_session(session_id)
                                    
                                    # If current session, switch to default
                                    if is_current:
                                        st.session_state.session_id = "default"
                                        st.session_state.messages = []
                                        st.session_state.last_loaded_session = None
                                    
                                    # Force refresh
                                    st.session_state.force_refresh = True
                                    del st.session_state[f"confirm_delete_{session_id}"]
                                    st.success("세션이 삭제되었습니다!")
                            except Exception as e:
                                st.error(f"삭제 실패: {str(e)}")
                        
                        if st.button("❌", key=f"confirm_no_{session_id}", help="취소", use_container_width=True):
                            del st.session_state[f"confirm_delete_{session_id}"]
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Show session metadata
                    if message_count > 0 or last_activity:
                        st.caption(f"📊 {message_count}개 메시지 • {last_activity}")
                    
                    st.markdown("---")
            
            # Close scrollable container
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        return None
    
    @staticmethod
    def get_session_title(session_id: str) -> str:
        """Get a user-friendly title for a session from database"""
        try:
            from controllers.chat_controller import ChatController
            chat_controller = ChatController()
            
            # Try to get session info from database first
            if chat_controller.api_service:
                response = chat_controller.api_service.get_session_info(session_id)
                if response.get("success") and response.get("session"):
                    session_info = response["session"]
                    return session_info.get("title", "알 수 없는 채팅")
            
            # Fallback to session state if DB is not available
            if f"session_title_{session_id}" in st.session_state:
                return st.session_state[f"session_title_{session_id}"]
            
            if session_id == st.session_state.get("session_id") and st.session_state.get("session_title"):
                return st.session_state.session_title
            
            # Generate a unique title for new sessions
            timestamp = datetime.now().strftime("%m/%d %H:%M")
            return f"새 대화 ({timestamp})"
        except:
            return "알 수 없는 채팅"
    
    @staticmethod
    def get_session_metadata(session_id: str) -> Dict[str, Any]:
        """Get metadata for a session (message count, last activity, etc.)"""
        try:
            from controllers.chat_controller import ChatController
            chat_controller = ChatController()
            
            # Get session stats from API
            if chat_controller.api_service:
                response = chat_controller.api_service.get_session_stats(session_id)
                if response.get("success") and response.get("stats"):
                    stats = response["stats"]
                    message_count = stats.get("message_count", 0)
                    
                    # Format last activity time
                    last_activity = ""
                    last_activity_raw = stats.get("last_activity", "")
                    if last_activity_raw:
                        try:
                            dt = datetime.fromisoformat(last_activity_raw.replace('Z', '+00:00'))
                            last_activity = dt.strftime("%m/%d %H:%M")
                        except:
                            last_activity = "알 수 없음"
                    
                    return {
                        "message_count": message_count,
                        "last_activity": last_activity,
                        "has_messages": message_count > 0
                    }
                else:
                    return {
                        "message_count": 0,
                        "last_activity": "",
                        "has_messages": False
                    }
            else:
                return {
                    "message_count": 0,
                    "last_activity": "",
                    "has_messages": False
                }
        except:
            return {
                "message_count": 0,
                "last_activity": "알 수 없음",
                "has_messages": False
            }

    @staticmethod
    def render_sidebar():
        """Render sidebar with HAI Portal navigation and chat history"""
        with st.sidebar:
            # Get current session ID first
            current_session = st.session_state.get("session_id", "default")
            
            # HAI Portal branding - removed
            
            # Session Management Section
            action = ChatComponents.render_session_sidebar()
            
            # User info - Modern design
            user_info = st.session_state.get("user_info")
            if user_info:
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 12px; margin: 0.5rem 0; 
                            border-left: 3px solid #6c757d; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border: 1px solid #e9ecef;">
                    <div style="font-weight: 600; color: #495057; font-size: 0.95rem;">👤 {user_info.get('username', '사용자')}</div>
                    <div style="font-size: 0.8rem; color: #6c757d; margin-top: 0.25rem;">{user_info.get('email', '')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
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
                        
                        # Create a formatted list item - only show collection name
                        list_item = f"• **{collection_name}**"
                        
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
                    # Create collection options for multiselect
                    collection_options = [f"{col['name']} ({col.get('document_count', 0)}개 문서)" for col in collections]
                    collection_names = [col['name'] for col in collections]
                    
                    # Initialize multi-collection selection in session state
                    if "selected_collections" not in st.session_state:
                        # Default to current collection if it exists, otherwise first collection
                        if current_collection in collection_names:
                            st.session_state.selected_collections = [current_collection]
                        else:
                            st.session_state.selected_collections = [collection_names[0]] if collection_names else []
                    
                    # Multi-collection selector with aliases
                    def format_collection_name(collection_name):
                        collection_info = next((col for col in collections if col['name'] == collection_name), {})
                        doc_count = collection_info.get('document_count', 0)
                        is_shared = collection_info.get('is_shared', False)
                        collection_icon = "🌐" if is_shared else "👤"
                        
                        # Check if there's a custom alias
                        aliases = st.session_state.get("collection_aliases", {})
                        if collection_name in aliases and aliases[collection_name]:
                            return f"{collection_icon} {aliases[collection_name]} ({collection_name}) - {doc_count}개 문서"
                        else:
                            # Use auto-generated alias for long names
                            if len(collection_name) > 20:
                                display_name = collection_name[:17] + "..."
                                return f"{collection_icon} {display_name} ({collection_name}) - {doc_count}개 문서"
                            else:
                                return f"{collection_icon} {collection_name} - {doc_count}개 문서"
                    
                    selected_collections = st.multiselect(
                        "사용할 컬렉션 선택 (여러 개 선택 가능)",
                        options=collection_names,
                        default=st.session_state.selected_collections,
                        format_func=format_collection_name,
                        key="multi_collection_select",
                        help="LangChain RAG 모드에서 여러 컬렉션을 선택하여 질문할 수 있습니다. 긴 이름은 별명으로 관리할 수 있습니다."
                    )
                    
                    # Update session state
                    st.session_state.selected_collections = selected_collections
                    
                    # Clear active group if collections don't match
                    active_group = st.session_state.get("active_group")
                    if active_group and selected_collections != active_group["collections"]:
                        st.session_state.active_group = None
                    
                    if selected_collections:
                        # Show selected collections info with aliases
                        collection_display_names = []
                        aliases = st.session_state.get("collection_aliases", {})
                        
                        for col_name in selected_collections:
                            # Use custom alias if available
                            if col_name in aliases and aliases[col_name]:
                                collection_display_names.append(f"{aliases[col_name]} ({col_name})")
                            else:
                                # Use auto-generated alias for long names
                                if len(col_name) > 15:
                                    alias = col_name[:12] + "..."
                                    collection_display_names.append(f"{alias} ({col_name})")
                                else:
                                    collection_display_names.append(col_name)
                        
                        st.info(f"선택된 컬렉션: {', '.join(collection_display_names)}")
                        
                        # Collection management - Clean dropdown and action buttons
                        st.markdown("---")
                        
                        # Action selection dropdown
                        action_options = ["컬렉션 정보 보기", "컬렉션 활성화", "별명 관리", "그룹으로 묶기"]
                        selected_action = st.selectbox(
                            "📋 컬렉션 관리 작업을 선택하세요:",
                            options=action_options,
                            key="collection_action_select"
                        )
                        
                        # Execute selected action
                        if selected_action == "컬렉션 정보 보기":
                            if st.button("ℹ️ 정보 보기", key="show_collection_info", use_container_width=True):
                                for collection_name in selected_collections:
                                    collection_info = chat_controller.get_collection_info(collection_name)
                                    if collection_info:
                                        st.write(f"**{collection_name}** 정보:")
                                        st.json(collection_info)
                                        st.markdown("---")
                        
                        elif selected_action == "컬렉션 활성화":
                            if len(selected_collections) == 1:
                                # Single collection - direct activation
                                if st.button("🔄 활성화", key="activate_single_collection", use_container_width=True):
                                    collection_name = selected_collections[0]
                                    result = chat_controller.switch_collection(collection_name)
                                    if result.get("success"):
                                        st.session_state.current_collection = collection_name
                                        st.session_state.active_group = None
                                        st.success(f"'{collection_name}' 컬렉션이 활성화되었습니다.")
                                    else:
                                        st.error(f"컬렉션 활성화 실패: {result.get('error', '알 수 없는 오류')}")
                            else:
                                # Multiple collections - dropdown selection
                                selected_for_activation = st.selectbox(
                                    "활성화할 컬렉션 선택:",
                                    options=selected_collections,
                                    format_func=lambda x: aliases.get(x, x) if x in aliases and aliases[x] else x,
                                    key="collection_activation_select"
                                )
                                if st.button("🔄 선택된 컬렉션 활성화", key="activate_selected_collection", use_container_width=True):
                                    result = chat_controller.switch_collection(selected_for_activation)
                                    if result.get("success"):
                                        st.session_state.current_collection = selected_for_activation
                                        st.session_state.active_group = None
                                        st.success(f"'{selected_for_activation}' 컬렉션이 활성화되었습니다.")
                                    else:
                                        st.error(f"컬렉션 활성화 실패: {result.get('error', '알 수 없는 오류')}")
                        
                        elif selected_action == "별명 관리":
                            if st.button("📝 별명 관리", key="manage_aliases", use_container_width=True):
                                st.session_state.show_alias_management = True
                        
                        elif selected_action == "그룹으로 묶기":
                            if len(selected_collections) > 1:
                                if st.button("🔗 그룹으로 묶기", key="create_collection_group", use_container_width=True):
                                    st.session_state.show_group_creation = True
                            else:
                                st.warning("2개 이상의 컬렉션을 선택해야 그룹으로 묶을 수 있습니다.")
                        
                        # Alias management UI
                        if st.session_state.get("show_alias_management", False):
                            st.markdown("---")
                            st.subheader("📝 컬렉션 별명 관리")
                            
                            # Initialize collection aliases in session state
                            if "collection_aliases" not in st.session_state:
                                st.session_state.collection_aliases = {}
                            
                            # Show alias management for selected collections
                            for collection_name in selected_collections:
                                current_alias = st.session_state.collection_aliases.get(collection_name, "")
                                
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    new_alias = st.text_input(
                                        f"별명 (최대 20자)",
                                        value=current_alias,
                                        key=f"alias_{collection_name}",
                                        placeholder=f"예: {collection_name[:10]}...",
                                        max_chars=20
                                    )
                                
                                with col2:
                                    if st.button("저장", key=f"save_alias_{collection_name}"):
                                        if new_alias and len(new_alias.strip()) > 0:
                                            st.session_state.collection_aliases[collection_name] = new_alias.strip()
                                            st.success(f"'{collection_name}'의 별명이 '{new_alias.strip()}'로 설정되었습니다.")
                                        else:
                                            # Remove alias if empty
                                            if collection_name in st.session_state.collection_aliases:
                                                del st.session_state.collection_aliases[collection_name]
                                            st.info(f"'{collection_name}'의 별명이 제거되었습니다.")
                            
                            close_alias_clicked = st.button("닫기", key="close_alias_management")
                            if close_alias_clicked:
                                st.session_state.show_alias_management = False
                        
                        # Collection group creation UI
                        if st.session_state.get("show_group_creation", False):
                            st.markdown("---")
                            st.subheader("🔗 컬렉션 그룹 생성")
                            
                            # Initialize collection groups in session state
                            if "collection_groups" not in st.session_state:
                                st.session_state.collection_groups = {}
                            
                            # Show selected collections for grouping
                            st.write("**그룹에 포함될 컬렉션들:**")
                            for i, collection_name in enumerate(selected_collections, 1):
                                aliases = st.session_state.get("collection_aliases", {})
                                display_name = aliases.get(collection_name, collection_name) if collection_name in aliases and aliases[collection_name] else collection_name
                                st.write(f"{i}. {display_name} ({collection_name})")
                            
                            # Check if editing existing group
                            editing_group_id = st.session_state.get("editing_group")
                            if editing_group_id and editing_group_id in st.session_state.get("collection_groups", {}):
                                # Editing existing group
                                existing_group = st.session_state.collection_groups[editing_group_id]
                                default_name = existing_group["name"]
                                default_description = existing_group.get("description", "")
                                st.info(f"그룹 편집 중: {default_name}")
                            else:
                                # Creating new group
                                default_name = ""
                                default_description = ""
                            
                            # Group name input
                            group_name = st.text_input(
                                "그룹 이름을 입력하세요:",
                                value=default_name,
                                placeholder="예: 내 문서 그룹, 프로젝트 A, 등등",
                                key="group_name_input",
                                max_chars=30
                            )
                            
                            # Group description
                            group_description = st.text_area(
                                "그룹 설명 (선택사항):",
                                value=default_description,
                                placeholder="이 그룹에 대한 간단한 설명을 입력하세요.",
                                key="group_description_input",
                                max_chars=100
                            )
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                if editing_group_id:
                                    # Editing existing group
                                    if st.button("✅ 그룹 수정", key="update_group"):
                                        if group_name and group_name.strip():
                                            st.session_state.collection_groups[editing_group_id].update({
                                                "name": group_name.strip(),
                                                "description": group_description.strip() if group_description else "",
                                                "collections": selected_collections.copy()
                                            })
                                            st.success(f"'{group_name.strip()}' 그룹이 수정되었습니다!")
                                            st.session_state.show_group_creation = False
                                            st.session_state.editing_group = None
                                        else:
                                            st.error("그룹 이름을 입력해주세요.")
                                else:
                                    # Creating new group
                                    if st.button("✅ 그룹 생성", key="create_group"):
                                        if group_name and group_name.strip():
                                            group_id = f"group_{len(st.session_state.collection_groups) + 1}"
                                            st.session_state.collection_groups[group_id] = {
                                                "name": group_name.strip(),
                                                "description": group_description.strip() if group_description else "",
                                                "collections": selected_collections.copy(),
                                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                            }
                                            st.success(f"'{group_name.strip()}' 그룹이 생성되었습니다!")
                                            st.session_state.show_group_creation = False
                                        else:
                                            st.error("그룹 이름을 입력해주세요.")
                            
                            with col2:
                                cancel_group_clicked = st.button("❌ 취소", key="cancel_group_creation")
                                if cancel_group_clicked:
                                    st.session_state.show_group_creation = False
                                    if editing_group_id:
                                        st.session_state.editing_group = None
                            
                            with col3:
                                show_group_list_clicked = st.button("📋 그룹 목록", key="show_group_list")
                                if show_group_list_clicked:
                                    st.session_state.show_group_list = True
                        
                        # Group list and management UI
                        if st.session_state.get("show_group_list", False):
                            st.markdown("---")
                            st.subheader("📋 컬렉션 그룹 관리")
                            
                            groups = st.session_state.get("collection_groups", {})
                            
                            if groups:
                                for group_id, group_info in groups.items():
                                    with st.expander(f"🔗 {group_info['name']} ({len(group_info['collections'])}개 컬렉션)"):
                                        st.write(f"**설명:** {group_info.get('description', '설명 없음')}")
                                        st.write(f"**생성일:** {group_info.get('created_at', 'Unknown')}")
                                        
                                        st.write("**포함된 컬렉션들:**")
                                        for i, collection_name in enumerate(group_info['collections'], 1):
                                            aliases = st.session_state.get("collection_aliases", {})
                                            display_name = aliases.get(collection_name, collection_name) if collection_name in aliases and aliases[collection_name] else collection_name
                                            st.write(f"  {i}. {display_name} ({collection_name})")
                                        
                                        col1, col2, col3 = st.columns(3)
                                        
                                        with col1:
                                            if st.button(f"🔄 그룹 활성화", key=f"activate_group_{group_id}"):
                                                # Set all collections in the group as selected
                                                st.session_state.selected_collections = group_info['collections'].copy()
                                                # Set the first collection as current collection
                                                if group_info['collections']:
                                                    st.session_state.current_collection = group_info['collections'][0]
                                                # Store group information for display
                                                st.session_state.active_group = {
                                                    "id": group_id,
                                                    "name": group_info['name'],
                                                    "description": group_info.get('description', ''),
                                                    "collections": group_info['collections'].copy()
                                                }
                                                st.success(f"'{group_info['name']}' 그룹의 모든 컬렉션이 선택되었습니다!")
                                        
                                        with col2:
                                            if st.button(f"✏️ 그룹 수정", key=f"edit_group_{group_id}"):
                                                st.session_state.editing_group = group_id
                                                st.session_state.show_group_creation = True
                                        
                                        with col3:
                                            if st.button(f"🗑️ 그룹 삭제", key=f"delete_group_{group_id}"):
                                                st.session_state.group_to_delete = group_id
                                        
                                        # Group deletion confirmation
                                        if st.session_state.get("group_to_delete") == group_id:
                                            st.warning(f"'{group_info['name']}' 그룹을 삭제하시겠습니까?")
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                if st.button("✅ 삭제 확인", key=f"confirm_delete_group_{group_id}"):
                                                    del st.session_state.collection_groups[group_id]
                                                    st.success(f"'{group_info['name']}' 그룹이 삭제되었습니다.")
                                                    st.session_state.group_to_delete = None
                                            with col2:
                                                if st.button("❌ 취소", key=f"cancel_delete_group_{group_id}"):
                                                    st.session_state.group_to_delete = None
                            else:
                                st.info("생성된 그룹이 없습니다.")
                            
                            close_group_list_clicked = st.button("닫기", key="close_group_list")
                            if close_group_list_clicked:
                                st.session_state.show_group_list = False
                        
                        # For backward compatibility, set the first selected collection as current
                        if selected_collections:
                            selected_collection = selected_collections[0]
                        else:
                            selected_collection = current_collection
                    else:
                        st.warning("최소 하나의 컬렉션을 선택해주세요.")
                        selected_collection = current_collection
                    
                    # Switch collection if different (for single collection compatibility)
                    if selected_collection != current_collection:
                        if st.button("🔄 컬렉션 전환", key="switch_collection"):
                            result = chat_controller.switch_collection(selected_collection)
                            if result.get("success"):
                                st.session_state.current_collection = selected_collection
                                # Clear active group when switching to individual collection
                                st.session_state.active_group = None
                                st.success(f"'{selected_collection}' 컬렉션으로 전환되었습니다.")
                            else:
                                st.error(f"컬렉션 전환 실패: {result.get('error', '알 수 없는 오류')}")
                    
                    # Show current collection info with alias and group info
                    if current_collection:
                        aliases = st.session_state.get("collection_aliases", {})
                        if current_collection in aliases and aliases[current_collection]:
                            display_name = f"{aliases[current_collection]} ({current_collection})"
                        else:
                            display_name = current_collection
                        
                        # Check if there's an active group
                        active_group = st.session_state.get("active_group")
                        if active_group and st.session_state.get("selected_collections") == active_group["collections"]:
                            st.info(f"현재 활성 그룹: **{active_group['name']}** ({len(active_group['collections'])}개 컬렉션)")
                            if active_group.get('description'):
                                st.caption(f"그룹 설명: {active_group['description']}")
                            
                            # Show collections in the active group
                            with st.expander("🔍 활성 그룹의 컬렉션들", expanded=False):
                                for i, collection_name in enumerate(active_group['collections'], 1):
                                    collection_alias = aliases.get(collection_name, "")
                                    if collection_alias:
                                        st.write(f"{i}. {collection_alias} ({collection_name})")
                                    else:
                                        st.write(f"{i}. {collection_name}")
                        else:
                            st.info(f"현재 활성 컬렉션: **{display_name}**")
                else:
                    # Show default collection when no collections are available
                    st.info("기본 컬렉션을 사용합니다.")
                    
                    # Show current collection info with alias
                    if current_collection:
                        aliases = st.session_state.get("collection_aliases", {})
                        if current_collection in aliases and aliases[current_collection]:
                            display_name = f"{aliases[current_collection]} ({current_collection})"
                        else:
                            display_name = current_collection
                        st.info(f"현재 활성 컬렉션: **{display_name}**")
                    
                    # Refresh button
                    if st.button("🔄 컬렉션 목록 새로고침", key="refresh_collections"):
                        st.session_state.force_refresh = True
                    
            # Menu management button (admin only)
            user_info = st.session_state.get("user_info")
            if user_info and user_info.get("id") == ADMIN_USER_ID:  # admin user ID
                if st.button("📋 메뉴 관리", key="menu_management", use_container_width=True):
                    st.session_state.current_page = "menu_management"
                    st.rerun()
            
            # Logout button
            st.markdown("---")
            if st.button("🚪 로그아웃", key="logout", use_container_width=True, type="secondary"):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                
                # Show success message
                st.success("로그아웃되었습니다.")
                
                # Redirect to login page using session state
                st.session_state.current_page = "login"
                st.rerun()

        return action

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
        
        # Create two columns for horizontal layout
        col1, col2 = st.columns(2)
        
        with col1:
            rag_mode = st.radio(
                "업로드할 RAG 시스템을 선택하세요:",
                ["기본 RAG", "LangChain RAG"],
                help="기본 RAG: 단순한 벡터 검색\nLangChain RAG: 고급 체인 처리 및 메모리",
                horizontal=True
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
