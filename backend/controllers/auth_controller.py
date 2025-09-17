"""
Authentication controller for handling login/register requests
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from backend.models.user import LoginRequest, RegisterRequest, AuthResponse
from backend.services.auth_service import auth_service

# Security scheme for JWT
security = HTTPBearer()

class AuthController:
    """Controller for authentication operations"""
    
    def __init__(self):
        self.auth_service = auth_service
    
    def register(self, request: RegisterRequest) -> AuthResponse:
        """Register a new user"""
        return self.auth_service.register_user(request)
    
    def login(self, request: LoginRequest) -> AuthResponse:
        """Login user"""
        return self.auth_service.login_user(request)
    
    def refresh_token(self, refresh_token: str) -> AuthResponse:
        """Refresh access token"""
        return self.auth_service.refresh_access_token(refresh_token)
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current authenticated user"""
        token = credentials.credentials
        user = self.auth_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    
    def logout(self, user_id: str) -> bool:
        """Logout user"""
        return self.auth_service.logout_user(user_id)
    
    def verify_token(self, token: str) -> bool:
        """Verify if token is valid"""
        user = self.auth_service.get_current_user(token)
        return user is not None

# Global auth controller instance
auth_controller = AuthController()
