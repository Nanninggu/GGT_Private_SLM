#!/usr/bin/env python3
"""
관리자 계정 비밀번호 업데이트 스크립트
사용법: python update_admin_password.py
"""
import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.repositories.user_repository import UserRepository
from backend.services.auth_service import AuthService

async def update_admin_password():
    """관리자 계정 비밀번호 업데이트"""
    try:
        # 서비스 초기화
        user_repo = UserRepository()
        auth_service = AuthService()
        
        # 데이터베이스 초기화
        print("데이터베이스 초기화 중...")
        await user_repo.db_service.initialize()
        
        # 관리자 계정 정보
        admin_username = "admin"
        new_password = "admin123"
        
        print(f"관리자 계정 비밀번호 업데이트 중: {admin_username}")
        
        # 관리자 계정 찾기
        admin_user = await user_repo.get_user_by_username(admin_username)
        if not admin_user:
            print(f"❌ 관리자 계정을 찾을 수 없습니다: {admin_username}")
            return False
        
        print(f"✅ 관리자 계정을 찾았습니다: {admin_user.id}")
        print(f"   현재 역할: {admin_user.role.value}")
        print(f"   활성 상태: {admin_user.is_active}")
        
        # 비밀번호 업데이트
        admin_user.password_hash = auth_service.hash_password(new_password)
        admin_user.updated_at = datetime.now()
        
        if await user_repo.update_user(admin_user):
            print("✅ 관리자 계정 비밀번호가 성공적으로 업데이트되었습니다!")
            print(f"   사용자명: {admin_username}")
            print(f"   새 비밀번호: {new_password}")
            print("\n🔐 로그인 정보:")
            print(f"   사용자명: {admin_username}")
            print(f"   비밀번호: {new_password}")
            return True
        else:
            print("❌ 관리자 계정 비밀번호 업데이트에 실패했습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """메인 함수"""
    print("=" * 50)
    print("🔧 GGT Private SLM - 관리자 비밀번호 업데이트")
    print("=" * 50)
    
    success = await update_admin_password()
    
    if success:
        print("\n✅ 관리자 비밀번호 업데이트가 완료되었습니다!")
        print("이제 admin/admin123으로 로그인할 수 있습니다.")
    else:
        print("\n❌ 관리자 비밀번호 업데이트에 실패했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
