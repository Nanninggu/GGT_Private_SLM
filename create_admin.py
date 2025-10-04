#!/usr/bin/env python3
"""
관리자 계정 생성 스크립트
사용법: python create_admin.py
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.models.user import User, UserRole
from backend.repositories.user_repository import UserRepository
from backend.services.auth_service import AuthService

async def create_admin_user():
    """관리자 계정 생성"""
    try:
        # 서비스 초기화
        user_repo = UserRepository()
        auth_service = AuthService()
        
        # 데이터베이스 초기화
        print("데이터베이스 초기화 중...")
        await user_repo.db_service.initialize()
        
        # 관리자 계정 정보
        admin_username = "admin"
        admin_email = "admin@example.com"
        admin_password = "admin123"
        
        print(f"관리자 계정 생성 중: {admin_username}")
        
        # 기존 관리자 계정 확인
        existing_user = await user_repo.get_user_by_username(admin_username)
        if existing_user:
            print(f"❌ 관리자 계정이 이미 존재합니다: {admin_username}")
            print(f"   사용자 ID: {existing_user.id}")
            print(f"   역할: {existing_user.role.value}")
            print(f"   활성 상태: {existing_user.is_active}")
            
            # 기존 계정을 관리자로 업그레이드
            if existing_user.role != UserRole.ADMIN:
                print("기존 계정을 관리자로 업그레이드 중...")
                existing_user.role = UserRole.ADMIN
                existing_user.is_active = True
                existing_user.updated_at = datetime.now()
                
                if await user_repo.update_user(existing_user):
                    print("✅ 기존 계정이 관리자로 업그레이드되었습니다.")
                else:
                    print("❌ 계정 업그레이드에 실패했습니다.")
                    return False
            else:
                print("✅ 관리자 계정이 이미 존재하고 활성화되어 있습니다.")
            
            return True
        
        # 새 관리자 계정 생성
        admin_user = User(
            id=str(uuid.uuid4()),
            username=admin_username,
            email=admin_email,
            password_hash=auth_service.hash_password(admin_password),
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 사용자 생성
        if await user_repo.create_user(admin_user):
            print("✅ 관리자 계정이 성공적으로 생성되었습니다!")
            print(f"   사용자명: {admin_username}")
            print(f"   이메일: {admin_email}")
            print(f"   비밀번호: {admin_password}")
            print(f"   사용자 ID: {admin_user.id}")
            print(f"   역할: {admin_user.role.value}")
            print("\n🔐 로그인 정보:")
            print(f"   사용자명: {admin_username}")
            print(f"   비밀번호: {admin_password}")
            return True
        else:
            print("❌ 관리자 계정 생성에 실패했습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """메인 함수"""
    print("=" * 50)
    print("🔧 GGT Private SLM - 관리자 계정 생성")
    print("=" * 50)
    
    success = await create_admin_user()
    
    if success:
        print("\n✅ 관리자 계정 생성이 완료되었습니다!")
        print("이제 admin/admin123으로 로그인할 수 있습니다.")
    else:
        print("\n❌ 관리자 계정 생성에 실패했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
