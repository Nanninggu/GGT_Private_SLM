"""
브라우저 로컬 스토리지를 사용한 인증 상태 저장
"""
import streamlit as st
import json
from typing import Dict, Any, Optional

class BrowserStorage:
    """브라우저 로컬 스토리지를 사용한 데이터 저장"""
    
    @staticmethod
    def save_to_local_storage(key: str, data: Dict[str, Any]) -> bool:
        """브라우저 로컬 스토리지에 데이터 저장"""
        try:
            # JavaScript 코드로 로컬 스토리지에 저장
            js_code = f"""
            <script>
            localStorage.setItem('{key}', JSON.stringify({json.dumps(data)}));
            </script>
            """
            st.components.v1.html(js_code, height=0)
            return True
        except Exception as e:
            print(f"로컬 스토리지 저장 실패: {e}")
            return False
    
    @staticmethod
    def load_from_local_storage(key: str) -> Optional[Dict[str, Any]]:
        """브라우저 로컬 스토리지에서 데이터 로드"""
        try:
            # JavaScript 코드로 로컬 스토리지에서 읽기
            js_code = f"""
            <script>
            const data = localStorage.getItem('{key}');
            if (data) {{
                window.parent.postMessage({{type: 'localStorageData', key: '{key}', data: data}}, '*');
            }}
            </script>
            """
            st.components.v1.html(js_code, height=0)
            
            # Streamlit에서는 직접적으로 로컬 스토리지 값을 읽을 수 없으므로
            # 대신 session_state를 사용하여 임시 저장
            return st.session_state.get(f"localStorage_{key}")
        except Exception as e:
            print(f"로컬 스토리지 로드 실패: {e}")
            return None
    
    @staticmethod
    def remove_from_local_storage(key: str) -> bool:
        """브라우저 로컬 스토리지에서 데이터 삭제"""
        try:
            js_code = f"""
            <script>
            localStorage.removeItem('{key}');
            </script>
            """
            st.components.v1.html(js_code, height=0)
            return True
        except Exception as e:
            print(f"로컬 스토리지 삭제 실패: {e}")
            return False
