"""
사용자별 세션 관리 페이지
"""
import streamlit as st
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.session_management_service import session_manager
except ImportError:
    session_manager = None

def main():
    """세션 관리 페이지 메인 함수"""
    
    # Hide Streamlit default header elements
    from utils.helpers import UIHelpers
    UIHelpers.hide_streamlit_header()
    
    # Apply Material Design 3 Theme
    from utils.helpers import DesignThemeManager
    theme_manager = DesignThemeManager()
    
    # Load theme from file if not already loaded
    if "theme_loaded" not in st.session_state:
        try:
            import json
            with open("data/theme_settings.json", "r", encoding="utf-8") as f:
                theme_settings = json.load(f)
                st.session_state.selected_theme = theme_settings.get("selected_theme", "gemini")
                st.session_state.theme_loaded = True
        except:
            st.session_state.selected_theme = "gemini"
            st.session_state.theme_loaded = True
    
    # Get theme from session state or default to gemini
    selected_theme = st.session_state.get("selected_theme", "gemini")
    theme_manager.apply_theme(selected_theme)
    
    # Check authentication
    if not st.session_state.get("auth_token"):
        st.warning("로그인이 필요합니다.")
        if st.button("로그인 페이지로 이동"):
            st.session_state.current_page = "login"
            st.rerun()
        return
    
    user_info = st.session_state.get("user_info", {})
    user_id = user_info.get("id", "default")
    
    if not session_manager or user_id == "default":
        st.error("세션 관리 서비스를 사용할 수 없습니다.")
        return
    
    # Page header
    st.markdown("""
    <div class="page-header">
        <div class="page-title">🔧 세션 관리</div>
        <div class="page-subtitle">사용자별 채팅 세션을 관리하세요</div>
    </div>
    """, unsafe_allow_html=True)
    
    # User info display
    st.markdown(f"""
    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #6c757d;">
        <h4 style="margin: 0 0 0.5rem 0; color: #495057;">👤 사용자 정보</h4>
        <p style="margin: 0; color: #6c757d;">
            <strong>사용자명:</strong> {user_info.get('username', 'Unknown')}<br>
            <strong>이메일:</strong> {user_info.get('email', 'Unknown')}<br>
            <strong>사용자 ID:</strong> {user_id}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Session statistics
    stats = session_manager.get_session_statistics(user_id)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 세션 수", stats.get("total_sessions", 0))
    
    with col2:
        st.metric("총 메시지 수", stats.get("total_messages", 0))
    
    with col3:
        st.metric("최근 7일 세션", stats.get("recent_sessions_7days", 0))
    
    with col4:
        last_activity = stats.get("last_activity", "")
        if last_activity:
            try:
                dt = datetime.fromisoformat(last_activity)
                formatted_time = dt.strftime("%m/%d %H:%M")
                st.metric("마지막 활동", formatted_time)
            except:
                st.metric("마지막 활동", "알 수 없음")
        else:
            st.metric("마지막 활동", "없음")
    
    st.markdown("---")
    
    # Session search and filter
    st.subheader("🔍 세션 검색 및 필터")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("세션 검색", placeholder="제목이나 내용으로 검색...", key="session_search")
    
    with col2:
        if st.button("🔍 검색", use_container_width=True):
            st.session_state.session_search_query = search_query
    
    # Clear search
    if st.session_state.get("session_search_query"):
        if st.button("❌ 검색 초기화"):
            st.session_state.session_search_query = None
            st.rerun()
    
    # Get sessions based on search
    if st.session_state.get("session_search_query"):
        sessions = session_manager.search_sessions(user_id, st.session_state.session_search_query)
        st.info(f"'{st.session_state.session_search_query}' 검색 결과: {len(sessions)}개 세션")
    else:
        sessions = session_manager.get_user_sessions(user_id)
    
    st.markdown("---")
    
    # Session list
    st.subheader(f"📋 세션 목록 ({len(sessions)}개)")
    
    if not sessions:
        st.info("저장된 세션이 없습니다. 새 채팅을 시작해보세요!")
        return
    
    # Session management actions
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📊 통계 보기", use_container_width=True):
            st.session_state.show_session_stats = True
    
    with col3:
        if st.button("⚙️ 설정", use_container_width=True):
            st.session_state.show_session_settings = True
    
    # Session statistics modal
    if st.session_state.get("show_session_stats", False):
        with st.expander("📊 세션 통계", expanded=True):
            st.markdown("### 📈 상세 통계")
            
            # Message count distribution
            message_counts = [session.get("message_count", 0) for session in sessions]
            if message_counts:
                avg_messages = sum(message_counts) / len(message_counts)
                max_messages = max(message_counts)
                min_messages = min(message_counts)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("평균 메시지 수", f"{avg_messages:.1f}")
                with col2:
                    st.metric("최대 메시지 수", max_messages)
                with col3:
                    st.metric("최소 메시지 수", min_messages)
            
            # Recent activity
            recent_sessions = [
                session for session in sessions
                if session.get("last_activity") and 
                datetime.fromisoformat(session["last_activity"]) > datetime.now() - timedelta(days=7)
            ]
            
            st.markdown("### 📅 최근 활동")
            st.write(f"**최근 7일간 활성 세션:** {len(recent_sessions)}개")
            
            if recent_sessions:
                st.write("**최근 활성 세션들:**")
                for session in recent_sessions[:5]:  # Show top 5
                    st.write(f"• {session.get('title', '제목 없음')} ({session.get('message_count', 0)}개 메시지)")
            
            if st.button("닫기", key="close_stats"):
                st.session_state.show_session_stats = False
                st.rerun()
    
    # Session settings modal
    if st.session_state.get("show_session_settings", False):
        with st.expander("⚙️ 세션 설정", expanded=True):
            st.markdown("### 🔧 세션 관리 설정")
            
            # Auto-save settings
            auto_save = st.checkbox("자동 저장 활성화", value=True, help="세션 변경 시 자동으로 저장합니다.")
            
            # Session cleanup settings
            st.markdown("### 🗑️ 세션 정리")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("오래된 세션 정리", help="30일 이상 비활성 세션을 정리합니다."):
                    # Implement old session cleanup
                    st.info("오래된 세션 정리 기능은 구현 중입니다.")
            
            with col2:
                if st.button("빈 세션 정리", help="메시지가 없는 세션을 정리합니다."):
                    # Implement empty session cleanup
                    st.info("빈 세션 정리 기능은 구현 중입니다.")
            
            # Export settings
            st.markdown("### 📤 내보내기 설정")
            
            if st.button("모든 세션 내보내기", help="모든 세션을 JSON 파일로 내보냅니다."):
                # Implement session export
                st.info("세션 내보내기 기능은 구현 중입니다.")
            
            if st.button("닫기", key="close_settings"):
                st.session_state.show_session_settings = False
                st.rerun()
    
    # Display sessions
    for i, session in enumerate(sessions):
        session_id = session.get("session_id")
        session_title = session.get("title", "제목 없음")
        message_count = session.get("message_count", 0)
        last_activity = session.get("last_activity", "")
        is_current = session.get("is_current", False)
        
        # Format last activity
        if last_activity:
            try:
                dt = datetime.fromisoformat(last_activity)
                formatted_time = dt.strftime("%m/%d %H:%M")
            except:
                formatted_time = "알 수 없음"
        else:
            formatted_time = "없음"
        
        # Session card
        with st.container():
            # Current session indicator
            if is_current:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                            padding: 1rem; border-radius: 10px; margin: 0.5rem 0; 
                            border-left: 4px solid #2196f3; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.2rem;">▶️</span>
                        <h4 style="margin: 0; color: #1976d2;">현재 세션</h4>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Session info
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{session_title}**")
                st.caption(f"메시지: {message_count}개 • 마지막 활동: {formatted_time}")
            
            with col2:
                if st.button("🔄 전환", key=f"switch_{session_id}", help="이 세션으로 전환"):
                    if session_manager.switch_to_session(user_id, session_id):
                        st.success("세션으로 전환되었습니다!")
                        st.rerun()
                    else:
                        st.error("세션 전환에 실패했습니다.")
            
            with col3:
                if st.button("✏️ 편집", key=f"edit_{session_id}", help="세션 제목 편집"):
                    st.session_state[f"editing_{session_id}"] = True
                    st.rerun()
            
            with col4:
                if not is_current:  # Don't allow deletion of current session
                    if st.button("🗑️ 삭제", key=f"delete_{session_id}", help="세션 삭제"):
                        st.session_state[f"confirm_delete_{session_id}"] = True
                        st.rerun()
            
            # Edit session title
            if st.session_state.get(f"editing_{session_id}", False):
                with st.expander("세션 제목 편집", expanded=True):
                    new_title = st.text_input(
                        "새 제목",
                        value=session_title,
                        key=f"edit_title_{session_id}"
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("💾 저장", key=f"save_title_{session_id}"):
                            if new_title.strip():
                                if session_manager.update_session_title(user_id, session_id, new_title.strip()):
                                    st.success("제목이 저장되었습니다!")
                                    del st.session_state[f"editing_{session_id}"]
                                    st.rerun()
                                else:
                                    st.error("제목 저장에 실패했습니다.")
                            else:
                                st.error("제목을 입력해주세요.")
                    
                    with col2:
                        if st.button("❌ 취소", key=f"cancel_edit_{session_id}"):
                            del st.session_state[f"editing_{session_id}"]
                            st.rerun()
            
            # Delete confirmation
            if st.session_state.get(f"confirm_delete_{session_id}", False):
                st.warning(f"'{session_title}' 세션을 삭제하시겠습니까?")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ 삭제 확인", key=f"confirm_delete_{session_id}"):
                        if session_manager.delete_session(user_id, session_id):
                            st.success("세션이 삭제되었습니다!")
                            del st.session_state[f"confirm_delete_{session_id}"]
                            st.rerun()
                        else:
                            st.error("세션 삭제에 실패했습니다.")
                
                with col2:
                    if st.button("❌ 취소", key=f"cancel_delete_{session_id}"):
                        del st.session_state[f"confirm_delete_{session_id}"]
                        st.rerun()
            
            st.markdown("---")
    
    # Bulk actions
    st.markdown("### 🔧 일괄 작업")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ 모든 세션 삭제", help="현재 세션을 제외한 모든 세션을 삭제합니다."):
            st.session_state.show_bulk_delete_confirm = True
    
    with col2:
        if st.button("📤 세션 내보내기", help="모든 세션을 JSON 파일로 내보냅니다."):
            st.info("세션 내보내기 기능은 구현 중입니다.")
    
    with col3:
        if st.button("🔄 세션 새로고침", help="세션 목록을 새로고침합니다."):
            st.rerun()
    
    # Bulk delete confirmation
    if st.session_state.get("show_bulk_delete_confirm", False):
        st.warning("⚠️ 모든 세션을 삭제하시겠습니까? (현재 세션 제외)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 삭제 확인", key="confirm_bulk_delete"):
                if session_manager.clear_user_sessions(user_id, keep_default=True):
                    st.success("모든 세션이 삭제되었습니다!")
                    del st.session_state["show_bulk_delete_confirm"]
                    st.rerun()
                else:
                    st.error("세션 삭제에 실패했습니다.")
        
        with col2:
            if st.button("❌ 취소", key="cancel_bulk_delete"):
                del st.session_state["show_bulk_delete_confirm"]
                st.rerun()

if __name__ == "__main__":
    main()
