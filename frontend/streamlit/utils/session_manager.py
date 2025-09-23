"""
Session management utilities for persistent authentication
"""
import streamlit as st
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class SessionManager:
    """Manages persistent session storage using browser local storage"""
    
    def __init__(self):
        self.storage_key = "hai_portal_session"
    
    def save_session(self, auth_token: str, refresh_token: str, user_info: Dict[str, Any]) -> None:
        """Save session data to browser local storage"""
        session_data = {
            "auth_token": auth_token,
            "refresh_token": refresh_token,
            "user_info": user_info,
            "login_time": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=8)).isoformat()
        }
        
        # Use JavaScript to save to localStorage
        st.markdown(f"""
        <script>
        localStorage.setItem('{self.storage_key}', '{json.dumps(session_data)}');
        </script>
        """, unsafe_allow_html=True)
    
    def load_session(self) -> Optional[Dict[str, Any]]:
        """Load session data from browser local storage"""
        try:
            # Use JavaScript to get from localStorage
            session_data = st.markdown(f"""
            <script>
            const sessionData = localStorage.getItem('{self.storage_key}');
            if (sessionData) {{
                window.parent.postMessage({{type: 'session_data', data: sessionData}}, '*');
            }}
            </script>
            """, unsafe_allow_html=True)
            
            # This is a simplified approach - in practice, you'd need to handle the async nature
            # For now, we'll use a different approach with st.session_state
            return None
        except:
            return None
    
    def clear_session(self) -> None:
        """Clear session data from browser local storage"""
        st.markdown(f"""
        <script>
        localStorage.removeItem('{self.storage_key}');
        </script>
        """, unsafe_allow_html=True)
    
    def is_session_valid(self, session_data: Dict[str, Any]) -> bool:
        """Check if session data is still valid"""
        try:
            expires_at = datetime.fromisoformat(session_data.get("expires_at", ""))
            return datetime.now() < expires_at
        except:
            return False
    
    def needs_refresh(self, session_data: Dict[str, Any]) -> bool:
        """Check if session needs refresh (within 1 hour of expiry)"""
        try:
            expires_at = datetime.fromisoformat(session_data.get("expires_at", ""))
            refresh_threshold = expires_at - timedelta(hours=1)
            return datetime.now() > refresh_threshold
        except:
            return True

# Alternative approach using st.session_state with persistence
class PersistentSessionManager:
    """Manages persistent session using st.session_state with file backup"""
    
    def __init__(self):
        self.session_file = "session_backup.json"
    
    def save_session_to_file(self, session_data: Dict[str, Any]) -> None:
        """Save session data to file as backup"""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"Failed to save session: {e}")
    
    def load_session_from_file(self) -> Optional[Dict[str, Any]]:
        """Load session data from file backup"""
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def initialize_session(self) -> None:
        """Initialize session state with persistent data"""
        # Initialize basic session state
        if "auth_token" not in st.session_state:
            st.session_state.auth_token = None
        if "user_info" not in st.session_state:
            st.session_state.user_info = None
        if "refresh_token" not in st.session_state:
            st.session_state.refresh_token = None
        if "login_time" not in st.session_state:
            st.session_state.login_time = None
        
        # Try to load from file backup
        if not st.session_state.auth_token:
            session_data = self.load_session_from_file()
            if session_data and self.is_session_valid(session_data):
                st.session_state.auth_token = session_data.get("auth_token")
                st.session_state.user_info = session_data.get("user_info")
                st.session_state.refresh_token = session_data.get("refresh_token")
                st.session_state.login_time = session_data.get("login_time")
                
                # Check if refresh is needed
                if self.needs_refresh(session_data):
                    self.attempt_token_refresh()
    
    def save_current_session(self) -> None:
        """Save current session state to file"""
        if st.session_state.auth_token:
            session_data = {
                "auth_token": st.session_state.auth_token,
                "user_info": st.session_state.user_info,
                "refresh_token": st.session_state.refresh_token,
                "login_time": st.session_state.login_time,
                "expires_at": (datetime.now() + timedelta(hours=8)).isoformat()
            }
            self.save_session_to_file(session_data)
    
    def clear_session(self) -> None:
        """Clear session data"""
        st.session_state.auth_token = None
        st.session_state.user_info = None
        st.session_state.refresh_token = None
        st.session_state.login_time = None
        
        # Clear file backup
        try:
            import os
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
        except:
            pass
    
    def is_session_valid(self, session_data: Dict[str, Any]) -> bool:
        """Check if session data is still valid"""
        try:
            expires_at = datetime.fromisoformat(session_data.get("expires_at", ""))
            return datetime.now() < expires_at
        except:
            return False
    
    def needs_refresh(self, session_data: Dict[str, Any]) -> bool:
        """Check if session needs refresh (within 1 hour of expiry)"""
        try:
            expires_at = datetime.fromisoformat(session_data.get("expires_at", ""))
            refresh_threshold = expires_at - timedelta(hours=1)
            return datetime.now() > refresh_threshold
        except:
            return True
    
    def attempt_token_refresh(self) -> bool:
        """Attempt to refresh the token"""
        try:
            from services.api_service import APIService
            api_service = APIService()
            result = api_service.refresh_token(st.session_state.refresh_token)
            
            if result.get("success"):
                st.session_state.auth_token = result.get("access_token")
                st.session_state.refresh_token = result.get("refresh_token")
                st.session_state.login_time = datetime.now().isoformat()
                
                if result.get("user"):
                    st.session_state.user_info = result.get("user")
                
                # Save updated session
                self.save_current_session()
                return True
            else:
                # Refresh failed, clear session
                self.clear_session()
                return False
        except:
            self.clear_session()
            return False

# Global session manager instance
session_manager = PersistentSessionManager()
