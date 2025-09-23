"""
Authentication service for JWT token management
"""
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from backend.models.user import User, LoginRequest, RegisterRequest, AuthResponse, TokenData, UserRole
from backend.repositories.user_repository import UserRepository
from backend.config.settings import settings

class AuthService:
    """Service for authentication and authorization"""
    
    def __init__(self):
        self.user_repository = UserRepository()
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            salt, password_hash = hashed_password.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except ValueError:
            return False
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            'sub': user.username,
            'user_id': user.id,
            'role': user.role.value,
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            'sub': user.username,
            'user_id': user.id,
            'role': user.role.value,
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token type is correct (access token)
            if payload.get('type') != 'access':
                return None
                
            return TokenData(
                username=payload.get('sub'),
                user_id=payload.get('user_id'),
                role=payload.get('role'),
                exp=payload.get('exp')
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def register_user(self, request: RegisterRequest) -> AuthResponse:
        """Register a new user"""
        try:
            # Validate input
            if not request.username or len(request.username) < 3:
                return AuthResponse(
                    success=False,
                    message="사용자명은 최소 3자 이상이어야 합니다."
                )
            
            if not request.email or '@' not in request.email:
                return AuthResponse(
                    success=False,
                    message="유효한 이메일 주소를 입력해주세요."
                )
            
            if not request.password or len(request.password) < 6:
                return AuthResponse(
                    success=False,
                    message="비밀번호는 최소 6자 이상이어야 합니다."
                )
            
            if request.password != request.confirm_password:
                return AuthResponse(
                    success=False,
                    message="비밀번호가 일치하지 않습니다."
                )
            
            # Check if user already exists
            if self.user_repository.get_user_by_username(request.username):
                return AuthResponse(
                    success=False,
                    message="이미 존재하는 사용자명입니다."
                )
            
            if self.user_repository.get_user_by_email(request.email):
                return AuthResponse(
                    success=False,
                    message="이미 존재하는 이메일입니다."
                )
            
            # Create new user
            import uuid
            user = User(
                id=str(uuid.uuid4()),
                username=request.username,
                email=request.email,
                password_hash=self.hash_password(request.password),
                role=UserRole.USER,
                is_active=True
            )
            
            # Save user
            if self.user_repository.create_user(user):
                # Create tokens
                access_token = self.create_access_token(user)
                refresh_token = self.create_refresh_token(user)
                
                return AuthResponse(
                    success=True,
                    message="회원가입이 완료되었습니다.",
                    user=user,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=self.access_token_expire_minutes * 60
                )
            else:
                return AuthResponse(
                    success=False,
                    message="회원가입 중 오류가 발생했습니다."
                )
                
        except Exception as e:
            return AuthResponse(
                success=False,
                message=f"회원가입 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def login_user(self, request: LoginRequest) -> AuthResponse:
        """Login user"""
        try:
            print(f"Login attempt for username: {request.username}")
            # Ensure database is initialized
            await self.user_repository.db_service.initialize()
            # Get user by username
            user = await self.user_repository.get_user_by_username(request.username)
            if not user:
                print(f"User not found: {request.username}")
                return AuthResponse(
                    success=False,
                    message="사용자명 또는 비밀번호가 올바르지 않습니다."
                )
            print(f"User found: {user.username}, active: {user.is_active}")
            
            # Check if user is active
            if not user.is_active:
                return AuthResponse(
                    success=False,
                    message="비활성화된 계정입니다."
                )
            
            # Verify password
            password_valid = self.verify_password(request.password, user.password_hash)
            print(f"Password valid: {password_valid}")
            if not password_valid:
                return AuthResponse(
                    success=False,
                    message="사용자명 또는 비밀번호가 올바르지 않습니다."
                )
            
            # Update last login
            user.last_login = datetime.now()
            await self.user_repository.update_user(user)
            
            # Create tokens
            access_token = self.create_access_token(user)
            refresh_token = self.create_refresh_token(user)
            print(f"Tokens created successfully")
            
            return AuthResponse(
                success=True,
                message="로그인에 성공했습니다.",
                user=user,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire_minutes * 60
            )
            
        except Exception as e:
            return AuthResponse(
                success=False,
                message=f"로그인 중 오류가 발생했습니다: {str(e)}"
            )
    
    def refresh_access_token(self, refresh_token: str) -> AuthResponse:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token specifically
            try:
                payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
                
                # Check if token type is refresh token
                if payload.get('type') != 'refresh':
                    return AuthResponse(
                        success=False,
                        message="유효하지 않은 리프레시 토큰입니다."
                    )
                    
                token_data = TokenData(
                    username=payload.get('sub'),
                    user_id=payload.get('user_id'),
                    role=payload.get('role'),
                    exp=payload.get('exp')
                )
            except jwt.ExpiredSignatureError:
                return AuthResponse(
                    success=False,
                    message="리프레시 토큰이 만료되었습니다."
                )
            except jwt.InvalidTokenError:
                return AuthResponse(
                    success=False,
                    message="유효하지 않은 리프레시 토큰입니다."
                )
            
            # Get user
            user = self.user_repository.get_user_by_id(token_data.user_id)
            if not user or not user.is_active:
                return AuthResponse(
                    success=False,
                    message="사용자를 찾을 수 없거나 비활성화된 계정입니다."
                )
            
            # Create new access token and refresh token
            access_token = self.create_access_token(user)
            new_refresh_token = self.create_refresh_token(user)
            
            return AuthResponse(
                success=True,
                message="토큰이 갱신되었습니다.",
                user=user,
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_in=self.access_token_expire_minutes * 60
            )
            
        except Exception as e:
            return AuthResponse(
                success=False,
                message=f"토큰 갱신 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token"""
        try:
            token_data = self.verify_token(token)
            if not token_data:
                return None
            
            # Ensure database is initialized
            await self.user_repository.db_service.initialize()
            user = await self.user_repository.get_user_by_id(token_data.user_id)
            if not user or not user.is_active:
                return None
            
            return user
        except Exception:
            return None
    
    def logout_user(self, user_id: str) -> bool:
        """Logout user (in a real implementation, you might want to blacklist the token)"""
        # For now, we'll just return True
        # In a production system, you might want to maintain a blacklist of tokens
        return True

# Global auth service instance
auth_service = AuthService()
