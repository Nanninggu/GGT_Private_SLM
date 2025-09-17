"""
User model for authentication
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from enum import Enum

class UserRole(Enum):
    """User roles"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

@dataclass
class User:
    """User model"""
    id: str
    username: str
    email: str
    password_hash: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    last_login: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class LoginRequest:
    """Login request model"""
    username: str
    password: str

@dataclass
class RegisterRequest:
    """Register request model"""
    username: str
    email: str
    password: str
    confirm_password: str

@dataclass
class AuthResponse:
    """Authentication response model"""
    success: bool
    message: str
    user: Optional[User] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None

@dataclass
class TokenData:
    """Token data model"""
    username: str
    user_id: str
    role: str
    exp: int
