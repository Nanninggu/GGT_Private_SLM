"""
User repository for database operations
"""
import json
import os
import uuid
from datetime import datetime
from typing import Optional, List
from backend.models.user import User, UserRole

class UserRepository:
    """Repository for user data operations"""
    
    def __init__(self, data_dir: str = "backend/data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self._ensure_data_directory()
        self._ensure_users_file()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _ensure_users_file(self):
        """Ensure users.json file exists"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def _load_users(self) -> List[dict]:
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_users(self, users: List[dict]):
        """Save users to JSON file"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2, default=str)
    
    def create_user(self, user: User) -> bool:
        """Create a new user"""
        try:
            users = self._load_users()
            
            # Check if username or email already exists
            for existing_user in users:
                if existing_user.get('username') == user.username:
                    return False
                if existing_user.get('email') == user.email:
                    return False
            
            # Add new user
            user_dict = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'role': user.role.value,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else datetime.now().isoformat(),
                'updated_at': user.updated_at.isoformat() if user.updated_at else datetime.now().isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            
            users.append(user_dict)
            self._save_users(users)
            return True
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            users = self._load_users()
            for user_dict in users:
                if user_dict.get('username') == username:
                    return self._dict_to_user(user_dict)
            return None
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            users = self._load_users()
            for user_dict in users:
                if user_dict.get('email') == email:
                    return self._dict_to_user(user_dict)
            return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            users = self._load_users()
            for user_dict in users:
                if user_dict.get('id') == user_id:
                    return self._dict_to_user(user_dict)
            return None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def update_user(self, user: User) -> bool:
        """Update user information"""
        try:
            users = self._load_users()
            for i, user_dict in enumerate(users):
                if user_dict.get('id') == user.id:
                    users[i] = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'password_hash': user.password_hash,
                        'role': user.role.value,
                        'is_active': user.is_active,
                        'created_at': user.created_at.isoformat() if user.created_at else datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat(),
                        'last_login': user.last_login.isoformat() if user.last_login else None
                    }
                    self._save_users(users)
                    return True
            return False
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user by ID"""
        try:
            users = self._load_users()
            users = [user for user in users if user.get('id') != user_id]
            self._save_users(users)
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        try:
            users = self._load_users()
            return [self._dict_to_user(user_dict) for user_dict in users]
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def _dict_to_user(self, user_dict: dict) -> User:
        """Convert dictionary to User object"""
        return User(
            id=user_dict.get('id'),
            username=user_dict.get('username'),
            email=user_dict.get('email'),
            password_hash=user_dict.get('password_hash'),
            role=UserRole(user_dict.get('role', 'user')),
            is_active=user_dict.get('is_active', True),
            created_at=datetime.fromisoformat(user_dict.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(user_dict.get('updated_at', datetime.now().isoformat())),
            last_login=datetime.fromisoformat(user_dict.get('last_login')) if user_dict.get('last_login') else None
        )
