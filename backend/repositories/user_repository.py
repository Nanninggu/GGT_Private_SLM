"""
User repository for database operations
"""
import json
import os
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import text
from backend.models.user import User, UserRole
from backend.services.database_service import db_service

class UserRepository:
    """Repository for user data operations"""
    
    def __init__(self):
        self.db_service = db_service
    
    def _dict_to_user(self, user_dict: dict) -> User:
        """Convert dictionary to User object"""
        return User(
            id=user_dict['id'],
            username=user_dict['username'],
            email=user_dict['email'],
            password_hash=user_dict['password_hash'],
            role=UserRole(user_dict['role']),
            is_active=user_dict['is_active'],
            created_at=datetime.fromisoformat(user_dict['created_at']) if user_dict.get('created_at') else None,
            updated_at=datetime.fromisoformat(user_dict['updated_at']) if user_dict.get('updated_at') else None,
            last_login=datetime.fromisoformat(user_dict['last_login']) if user_dict.get('last_login') else None
        )
    
    async def create_user(self, user: User) -> bool:
        """Create a new user"""
        try:
            async with self.db_service.get_session() as session:
                # Check if username or email already exists
                result = await session.execute(text("""
                    SELECT id FROM users 
                    WHERE username = :username OR email = :email
                """), {"username": user.username, "email": user.email})
                
                if result.fetchone():
                    return False
                
                # Insert new user
                await session.execute(text("""
                    INSERT INTO users (id, username, email, password_hash, role, is_active, created_at, updated_at, last_login)
                    VALUES (:id, :username, :email, :password_hash, :role, :is_active, :created_at, :updated_at, :last_login)
                """), {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "password_hash": user.password_hash,
                    "role": user.role.value,
                    "is_active": user.is_active,
                    "created_at": user.created_at or datetime.now(),
                    "updated_at": user.updated_at or datetime.now(),
                    "last_login": user.last_login
                })
                
                await session.commit()
                return True
                
        except Exception as e:
            print(f"Error creating user: {e}", exc_info=True)
            return False
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            async with self.db_service.get_session() as session:
                result = await session.execute(text("""
                    SELECT id, username, email, password_hash, role, is_active, 
                           created_at, updated_at, last_login
                    FROM users WHERE username = :username
                """), {"username": username})
                
                row = result.fetchone()
                if row:
                    return User(
                        id=str(row[0]),
                        username=row[1],
                        email=row[2],
                        password_hash=row[3],
                        role=UserRole(row[4]),
                        is_active=row[5],
                        created_at=row[6],
                        updated_at=row[7],
                        last_login=row[8]
                    )
                return None
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            async with self.db_service.get_session() as session:
                result = await session.execute(text("""
                    SELECT id, username, email, password_hash, role, is_active, 
                           created_at, updated_at, last_login
                    FROM users WHERE email = :email
                """), {"email": email})
                
                row = result.fetchone()
                if row:
                    return User(
                        id=str(row[0]),
                        username=row[1],
                        email=row[2],
                        password_hash=row[3],
                        role=UserRole(row[4]),
                        is_active=row[5],
                        created_at=row[6],
                        updated_at=row[7],
                        last_login=row[8]
                    )
                return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            async with self.db_service.get_session() as session:
                result = await session.execute(text("""
                    SELECT id, username, email, password_hash, role, is_active, 
                           created_at, updated_at, last_login
                    FROM users WHERE id = :user_id
                """), {"user_id": user_id})
                
                row = result.fetchone()
                if row:
                    return User(
                        id=str(row[0]),
                        username=row[1],
                        email=row[2],
                        password_hash=row[3],
                        role=UserRole(row[4]),
                        is_active=row[5],
                        created_at=row[6],
                        updated_at=row[7],
                        last_login=row[8]
                    )
                return None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    async def update_user(self, user: User) -> bool:
        """Update user information"""
        try:
            async with self.db_service.get_session() as session:
                await session.execute(text("""
                    UPDATE users 
                    SET username = :username, email = :email, password_hash = :password_hash,
                        role = :role, is_active = :is_active, updated_at = :updated_at,
                        last_login = :last_login
                    WHERE id = :id
                """), {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "password_hash": user.password_hash,
                    "role": user.role.value,
                    "is_active": user.is_active,
                    "updated_at": datetime.now(),
                    "last_login": user.last_login
                })
                
                await session.commit()
                return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user by ID"""
        try:
            async with self.db_service.get_session() as session:
                await session.execute(text("""
                    DELETE FROM users WHERE id = :user_id
                """), {"user_id": user_id})
                
                await session.commit()
                return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    async def get_all_users(self) -> List[User]:
        """Get all users"""
        try:
            async with self.db_service.get_session() as session:
                result = await session.execute(text("""
                    SELECT id, username, email, password_hash, role, is_active, 
                           created_at, updated_at, last_login
                    FROM users ORDER BY created_at DESC
                """))
                
                users = []
                for row in result:
                    users.append(User(
                        id=str(row[0]),
                        username=row[1],
                        email=row[2],
                        password_hash=row[3],
                        role=UserRole(row[4]),
                        is_active=row[5],
                        created_at=row[6],
                        updated_at=row[7],
                        last_login=row[8]
                    ))
                return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
