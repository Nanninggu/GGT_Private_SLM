#!/usr/bin/env python3
"""
Migrate users from JSON file to database
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.repositories.user_repository import UserRepository
from backend.models.user import User, UserRole
from backend.services.database_service import db_service

async def migrate_users():
    """Migrate users from JSON to database"""
    try:
        # Initialize database service
        await db_service.initialize()
        
        # Initialize user repository
        user_repo = UserRepository()
        
        # Load users from JSON file
        json_file = "backend/data/users.json"
        if not os.path.exists(json_file):
            print(f"JSON file not found: {json_file}")
            return
        
        with open(json_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        print(f"Found {len(users_data)} users in JSON file")
        
        # Migrate each user
        migrated_count = 0
        for user_data in users_data:
            try:
                # Create User object
                user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    role=UserRole(user_data['role']),
                    is_active=user_data['is_active'],
                    created_at=datetime.fromisoformat(user_data['created_at']) if user_data.get('created_at') else None,
                    updated_at=datetime.fromisoformat(user_data['updated_at']) if user_data.get('updated_at') else None,
                    last_login=datetime.fromisoformat(user_data['last_login']) if user_data.get('last_login') else None
                )
                
                # Check if user already exists
                existing_user = await user_repo.get_user_by_id(user.id)
                if existing_user:
                    print(f"User {user.username} already exists, skipping...")
                    continue
                
                # Create user in database
                success = await user_repo.create_user(user)
                if success:
                    print(f"Migrated user: {user.username} ({user.email})")
                    migrated_count += 1
                else:
                    print(f"Failed to migrate user: {user.username}")
                    
            except Exception as e:
                print(f"Error migrating user {user_data.get('username', 'unknown')}: {e}")
        
        print(f"Migration completed. {migrated_count} users migrated successfully.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        # Close database connections
        await db_service.close()

if __name__ == "__main__":
    asyncio.run(migrate_users())
