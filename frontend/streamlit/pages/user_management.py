"""
User Management Page for HAI Portal
"""
import streamlit as st
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api_service import APIService
from config import ADMIN_USER_ID
from utils.helpers import UIHelpers

def check_admin_permission():
    """Check if current user has admin permission"""
    user_info = st.session_state.get("user_info")
    if not user_info:
        st.error("사용자 정보가 없습니다. 다시 로그인해주세요.")
        return False
    
    # Check if user ID is admin (only admin ID has admin permission)
    user_id = user_info.get("id", "")
    return user_id == ADMIN_USER_ID

def render_user_list():
    """Render user list with management options"""
    st.subheader("👥 사용자 목록")
    
    try:
        api_service = APIService()
        response = api_service.get_all_users()
        
        # Check if API call was successful
        if not response.get("success"):
            st.error(f"사용자 목록을 불러오는 중 오류가 발생했습니다: {response.get('error', '알 수 없는 오류')}")
            return
        
        users = response.get("users", [])
        
        if not users:
            st.info("등록된 사용자가 없습니다.")
            return
        
        # Create user data table
        user_data = []
        for user in users:
            user_data.append({
                "ID": user.get("id", "")[:8] + "...",
                "사용자명": user.get("username", ""),
                "이메일": user.get("email", ""),
                "역할": user.get("role", "user"),
                "상태": "활성" if user.get("is_active", True) else "비활성",
                "가입일": user.get("created_at", ""),
                "최근 로그인": user.get("last_login", "없음")
            })
        
        # Display users in a table
        st.dataframe(
            user_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "사용자명": st.column_config.TextColumn("사용자명", width="medium"),
                "이메일": st.column_config.TextColumn("이메일", width="large"),
                "역할": st.column_config.TextColumn("역할", width="small"),
                "상태": st.column_config.TextColumn("상태", width="small"),
                "가입일": st.column_config.TextColumn("가입일", width="medium"),
                "최근 로그인": st.column_config.TextColumn("최근 로그인", width="medium")
            }
        )
        
        # User management actions
        st.markdown("---")
        st.subheader("🔧 사용자 관리")
        
        # Get user list for selection
        user_options = {f"{user['username']} ({user['email']})": user['id'] for user in users}
        
        if user_options:
            selected_user_display = st.selectbox(
                "관리할 사용자 선택:",
                options=list(user_options.keys()),
                key="user_selection"
            )
            
            if selected_user_display:
                selected_user_id = user_options[selected_user_display]
                selected_user = next(user for user in users if user['id'] == selected_user_id)
                
                # User action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("👁️ 상세 정보", key="view_user_details"):
                        st.session_state.selected_user_for_details = selected_user
                        st.rerun()
                
                with col2:
                    if st.button("✏️ 정보 수정", key="edit_user_info"):
                        st.session_state.selected_user_for_edit = selected_user
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ 사용자 삭제", key="delete_user", type="secondary"):
                        st.session_state.selected_user_for_delete = selected_user
                        st.rerun()
    
    except Exception as e:
        st.error(f"사용자 목록을 불러오는 중 오류가 발생했습니다: {str(e)}")

def render_user_details(user: Dict[str, Any]):
    """Render detailed user information"""
    st.subheader(f"👤 {user.get('username', 'Unknown')} 상세 정보")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**기본 정보**")
        st.write(f"**ID:** {user.get('id', 'N/A')}")
        st.write(f"**사용자명:** {user.get('username', 'N/A')}")
        st.write(f"**이메일:** {user.get('email', 'N/A')}")
        st.write(f"**역할:** {user.get('role', 'N/A')}")
        st.write(f"**상태:** {'활성' if user.get('is_active', True) else '비활성'}")
    
    with col2:
        st.markdown("**시간 정보**")
        st.write(f"**가입일:** {user.get('created_at', 'N/A')}")
        st.write(f"**수정일:** {user.get('updated_at', 'N/A')}")
        st.write(f"**최근 로그인:** {user.get('last_login', 'N/A')}")
    
    if st.button("← 목록으로 돌아가기", key="back_to_list"):
        st.session_state.selected_user_for_details = None
        st.rerun()

def render_user_edit_form(user: Dict[str, Any]):
    """Render user edit form"""
    st.subheader(f"✏️ {user.get('username', 'Unknown')} 정보 수정")
    
    with st.form("edit_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input(
                "사용자명",
                value=user.get('username', ''),
                key="edit_username"
            )
            new_email = st.text_input(
                "이메일",
                value=user.get('email', ''),
                key="edit_email"
            )
        
        with col2:
            new_role = st.selectbox(
                "역할",
                options=["admin", "user", "guest"],
                index=["admin", "user", "guest"].index(user.get('role', 'user')),
                key="edit_role"
            )
            new_status = st.selectbox(
                "상태",
                options=["활성", "비활성"],
                index=0 if user.get('is_active', True) else 1,
                key="edit_status"
            )
        
        # Form buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submit_button = st.form_submit_button("💾 저장", type="primary")
        
        with col2:
            cancel_button = st.form_submit_button("❌ 취소")
        
        with col3:
            reset_button = st.form_submit_button("🔄 초기화")
        
        if submit_button:
            # Validate input
            if not new_username or len(new_username) < 3:
                st.error("사용자명은 최소 3자 이상이어야 합니다.")
                return
            
            if not new_email or '@' not in new_email:
                st.error("유효한 이메일 주소를 입력해주세요.")
                return
            
            # Prepare update data
            update_data = {
                "id": user.get('id'),
                "username": new_username,
                "email": new_email,
                "role": new_role,
                "is_active": new_status == "활성"
            }
            
            try:
                api_service = APIService()
                result = api_service.update_user(user.get('id'), update_data)
                
                if result.get("success"):
                    st.success("사용자 정보가 성공적으로 업데이트되었습니다.")
                    st.session_state.selected_user_for_edit = None
                    st.rerun()
                else:
                    st.error(f"업데이트 실패: {result.get('message', '알 수 없는 오류')}")
            except Exception as e:
                st.error(f"업데이트 중 오류가 발생했습니다: {str(e)}")
        
        elif cancel_button:
            st.session_state.selected_user_for_edit = None
            st.rerun()
        
        elif reset_button:
            st.rerun()

def render_user_delete_confirmation(user: Dict[str, Any]):
    """Render user deletion confirmation"""
    st.subheader(f"🗑️ 사용자 삭제 확인")
    
    st.warning(f"⚠️ **경고**: '{user.get('username', 'Unknown')}' 사용자를 삭제하시겠습니까?")
    st.write("이 작업은 되돌릴 수 없습니다.")
    
    # Show user details
    st.markdown("**삭제될 사용자 정보:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**사용자명:** {user.get('username', 'N/A')}")
        st.write(f"**이메일:** {user.get('email', 'N/A')}")
    
    with col2:
        st.write(f"**역할:** {user.get('role', 'N/A')}")
        st.write(f"**상태:** {'활성' if user.get('is_active', True) else '비활성'}")
    
    # Confirmation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ 삭제 확인", key="confirm_delete", type="primary"):
            try:
                api_service = APIService()
                user_id = user.get('id')
                
                # Debug information
                st.write(f"🔍 디버그 - 삭제할 사용자 ID: {user_id}")
                
                result = api_service.delete_user(user_id)
                
                # Debug information
                st.write(f"🔍 디버그 - API 응답: {result}")
                
                if result.get("success"):
                    st.success("사용자가 성공적으로 삭제되었습니다.")
                    st.session_state.selected_user_for_delete = None
                    st.rerun()
                else:
                    error_msg = result.get('message') or result.get('error', '알 수 없는 오류')
                    st.error(f"삭제 실패: {error_msg}")
            except Exception as e:
                st.error(f"삭제 중 오류가 발생했습니다: {str(e)}")
                st.write(f"🔍 디버그 - 예외 상세: {type(e).__name__}: {str(e)}")
    
    with col2:
        if st.button("❌ 취소", key="cancel_delete"):
            st.session_state.selected_user_for_delete = None
            st.rerun()
    
    with col3:
        if st.button("← 목록으로", key="back_to_list_from_delete"):
            st.session_state.selected_user_for_delete = None
            st.rerun()

def render_user_creation_form():
    """Render new user creation form"""
    st.subheader("➕ 새 사용자 추가")
    
    # Check if user was just created and clear form
    if st.session_state.get("user_created"):
        st.session_state.user_created = False
        st.success("사용자가 성공적으로 생성되었습니다!")
        # Increment form counter to create new form
        st.session_state.form_counter = st.session_state.get("form_counter", 0) + 1
        # Clear all form inputs
        for key in list(st.session_state.keys()):
            if key.startswith("create_"):
                del st.session_state[key]
    
    # Generate unique form key to avoid conflicts
    form_key = f"create_user_form_{st.session_state.get('form_counter', 0)}"
    
    with st.form(form_key):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input(
                "사용자명 *",
                placeholder="최소 3자 이상",
                key=f"create_username_{form_key}"
            )
            email = st.text_input(
                "이메일 *",
                placeholder="user@example.com",
                key=f"create_email_{form_key}"
            )
        
        with col2:
            password = st.text_input(
                "비밀번호 *",
                type="password",
                placeholder="최소 6자 이상",
                key=f"create_password_{form_key}"
            )
            confirm_password = st.text_input(
                "비밀번호 확인 *",
                type="password",
                placeholder="비밀번호를 다시 입력하세요",
                key=f"create_confirm_password_{form_key}"
            )
        
        role = st.selectbox(
            "역할",
            options=["user", "admin", "guest"],
            index=0,
            key=f"create_role_{form_key}"
        )
        
        is_active = st.checkbox(
            "활성 상태",
            value=True,
            key=f"create_is_active_{form_key}"
        )
        
        # Form buttons
        col1, col2 = st.columns(2)
        
        with col1:
            submit_button = st.form_submit_button("➕ 사용자 생성", type="primary")
        
        with col2:
            cancel_button = st.form_submit_button("❌ 취소")
        
        if submit_button:
            # Clean and validate input
            username = username.strip()  # Remove leading/trailing whitespace
            email = email.strip()
            
            # Debug information
            st.write(f"🔍 디버그 - 사용자명: '{username}' (길이: {len(username)})")
            st.write(f"🔍 디버그 - 이메일: '{email}'")
            
            if not username or len(username) < 3:
                st.error(f"사용자명은 최소 3자 이상이어야 합니다. (현재: '{username}', 길이: {len(username)})")
                return
            
            if ' ' in username:
                st.error("사용자명에는 공백을 포함할 수 없습니다.")
                return
            
            if not email or '@' not in email:
                st.error("유효한 이메일 주소를 입력해주세요.")
                return
            
            if not password or len(password) < 6:
                st.error("비밀번호는 최소 6자 이상이어야 합니다.")
                return
            
            if password != confirm_password:
                st.error("비밀번호가 일치하지 않습니다.")
                return
            
            # Prepare user data
            user_data = {
                "username": username,
                "email": email,
                "password": password,
                "role": role,
                "is_active": is_active
            }
            
            try:
                api_service = APIService()
                result = api_service.create_user(user_data)
                
                if isinstance(result, dict) and result.get("success"):
                    st.success("새 사용자가 성공적으로 생성되었습니다.")
                    # Clear form by rerunning without form submission
                    st.session_state.user_created = True
                    # Increment form counter to create new form
                    st.session_state.form_counter = st.session_state.get("form_counter", 0) + 1
                    # Clear all form inputs
                    for key in list(st.session_state.keys()):
                        if key.startswith("create_"):
                            del st.session_state[key]
                    st.rerun()
                else:
                    # Handle different error cases
                    if isinstance(result, dict):
                        error_msg = result.get('message') or result.get('detail') or result.get('error', '알 수 없는 오류')
                        st.error(f"생성 실패: {error_msg}")
                    else:
                        st.error(f"생성 실패: {str(result)}")
            except Exception as e:
                st.error(f"생성 중 오류가 발생했습니다: {str(e)}")
        
        elif cancel_button:
            st.rerun()

def main():
    """Main user management page function"""
    # Load enterprise theme
    UIHelpers.load_enterprise_theme()
    
    # Hide Streamlit default header elements
    UIHelpers.hide_streamlit_header()
    
    # Check authentication
    if not st.session_state.get("auth_token"):
        st.warning("로그인이 필요합니다.")
        if st.button("로그인 페이지로 이동"):
            st.session_state.current_page = "login"
            st.rerun()
        return
    
    # Check admin permission
    if not check_admin_permission():
        st.error("❌ 관리자 권한이 필요합니다.")
        st.info("이 페이지는 관리자만 접근할 수 있습니다.")
        if st.button("← 메인 페이지로 돌아가기"):
            st.session_state.current_page = "main"
            st.rerun()
        return
    
    # Modern Enterprise page header - Clean White Design
    st.markdown("""
    <div class="page-header">
        <div class="page-title">👥 사용자 관리</div>
        <div class="page-subtitle">HAI Portal 사용자 관리 시스템</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation tabs
    tab1, tab2 = st.tabs(["📋 사용자 목록", "➕ 새 사용자 추가"])
    
    with tab1:
        # Check if we're viewing specific user details
        if st.session_state.get("selected_user_for_details"):
            render_user_details(st.session_state.selected_user_for_details)
        elif st.session_state.get("selected_user_for_edit"):
            render_user_edit_form(st.session_state.selected_user_for_edit)
        elif st.session_state.get("selected_user_for_delete"):
            render_user_delete_confirmation(st.session_state.selected_user_for_delete)
        else:
            render_user_list()
    
    with tab2:
        render_user_creation_form()

if __name__ == "__main__":
    main()
