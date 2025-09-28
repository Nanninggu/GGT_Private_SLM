"""
인증 상태 영구 저장을 위한 유틸리티
"""
import streamlit as st
import json
import base64
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class AuthPersistence:
    """인증 상태를 영구적으로 저장하고 복원하는 클래스"""
    
    @staticmethod
    def _get_auth_file_path():
        """인증 파일 경로 반환"""
        return os.path.join(os.path.expanduser("~"), ".streamlit_auth.json")
    
    @staticmethod
    def save_auth_state(auth_token: str, refresh_token: str, user_info: Dict[str, Any], login_time: str):
        """인증 상태를 로컬 파일에 저장"""
        try:
            auth_data = {
                "auth_token": auth_token,
                "refresh_token": refresh_token,
                "user_info": user_info,
                "login_time": login_time,
                "saved_at": datetime.now().isoformat()
            }
            
            # 로컬 파일에 저장
            auth_file = AuthPersistence._get_auth_file_path()
            with open(auth_file, 'w', encoding='utf-8') as f:
                json.dump(auth_data, f, ensure_ascii=False, indent=2)
            
            # session_state에도 저장 (현재 세션용)
            st.session_state.auth_token = auth_token
            st.session_state.refresh_token = refresh_token
            st.session_state.user_info = user_info
            st.session_state.login_time = login_time
            
            return True
        except Exception as e:
            print(f"인증 상태 저장 실패: {e}")
            return False
    
    @staticmethod
    def load_auth_state() -> Optional[Dict[str, Any]]:
        """저장된 인증 상태를 로컬 파일에서 복원"""
        try:
            auth_file = AuthPersistence._get_auth_file_path()
            
            if not os.path.exists(auth_file):
                return None
            
            with open(auth_file, 'r', encoding='utf-8') as f:
                auth_data = json.load(f)
            
            # 저장된 시간 확인 (24시간 이내만 유효)
            saved_at = datetime.fromisoformat(auth_data.get("saved_at", ""))
            if datetime.now() - saved_at > timedelta(hours=24):
                AuthPersistence.clear_auth_state()
                return None
            
            return auth_data
            
        except Exception as e:
            print(f"인증 상태 로드 실패: {e}")
            return None
    
    @staticmethod
    def clear_auth_state():
        """인증 상태를 완전히 삭제"""
        try:
            # 로컬 파일에서 인증 데이터 제거
            auth_file = AuthPersistence._get_auth_file_path()
            if os.path.exists(auth_file):
                os.remove(auth_file)
            
            # session_state에서도 제거
            if "auth_token" in st.session_state:
                del st.session_state.auth_token
            if "refresh_token" in st.session_state:
                del st.session_state.refresh_token
            if "user_info" in st.session_state:
                del st.session_state.user_info
            if "login_time" in st.session_state:
                del st.session_state.login_time
                
            return True
        except Exception as e:
            print(f"인증 상태 삭제 실패: {e}")
            return False
    
    @staticmethod
    def restore_auth_to_session(auth_data: Dict[str, Any]) -> bool:
        """복원된 인증 데이터를 session_state에 설정"""
        try:
            st.session_state.auth_token = auth_data.get("auth_token")
            st.session_state.refresh_token = auth_data.get("refresh_token")
            st.session_state.user_info = auth_data.get("user_info")
            st.session_state.login_time = auth_data.get("login_time")
            return True
        except Exception as e:
            print(f"인증 상태 복원 실패: {e}")
            return False
    
    @staticmethod
    def is_token_expired(login_time: str, max_hours: int = 7) -> bool:
        """토큰이 만료되었는지 확인"""
        try:
            login_datetime = datetime.fromisoformat(login_time)
            return datetime.now() - login_datetime > timedelta(hours=max_hours)
        except:
            return True
