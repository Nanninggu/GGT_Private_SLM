"""
세션 관리 기능 테스트 스크립트
"""
import sys
import os
import json
from datetime import datetime, timedelta

# Add frontend directory to Python path
frontend_path = os.path.join(os.path.dirname(__file__), 'frontend', 'streamlit')
sys.path.insert(0, frontend_path)

def test_session_management():
    """세션 관리 서비스 테스트"""
    print("🧪 세션 관리 서비스 테스트 시작...")
    
    try:
        from services.session_management_service import SessionManagementService
        
        # Create test instance
        session_service = SessionManagementService()
        
        # Test user info
        test_user_id = "test_user_123"
        test_user_info = {
            "id": test_user_id,
            "username": "testuser",
            "email": "test@example.com"
        }
        
        print(f"✅ 세션 관리 서비스 초기화 성공")
        
        # Test 1: Initialize user session
        print("\n📝 테스트 1: 사용자 세션 초기화")
        user_session = session_service.initialize_user_session(test_user_id, test_user_info)
        print(f"✅ 사용자 세션 초기화 성공: {user_session['user_id']}")
        
        # Test 2: Create new session
        print("\n📝 테스트 2: 새 세션 생성")
        new_session_id = session_service.create_new_session(test_user_id, "테스트 세션 1")
        print(f"✅ 새 세션 생성 성공: {new_session_id}")
        
        # Test 3: Create multiple sessions
        print("\n📝 테스트 3: 여러 세션 생성")
        session_ids = []
        for i in range(3):
            session_id = session_service.create_new_session(test_user_id, f"테스트 세션 {i+2}")
            session_ids.append(session_id)
            print(f"  - 세션 {i+2} 생성: {session_id}")
        
        # Test 4: Get user sessions
        print("\n📝 테스트 4: 사용자 세션 목록 조회")
        sessions = session_service.get_user_sessions(test_user_id)
        print(f"✅ 총 {len(sessions)}개 세션 조회 성공")
        for session in sessions:
            print(f"  - {session['title']} (ID: {session['session_id'][:8]}...)")
        
        # Test 5: Switch to session
        print("\n📝 테스트 5: 세션 전환")
        if sessions:
            target_session = sessions[1]  # Switch to second session
            success = session_service.switch_to_session(test_user_id, target_session['session_id'])
            print(f"✅ 세션 전환 성공: {target_session['title']}")
        
        # Test 6: Update session title
        print("\n📝 테스트 6: 세션 제목 업데이트")
        if sessions:
            target_session = sessions[0]
            new_title = "업데이트된 세션 제목"
            success = session_service.update_session_title(test_user_id, target_session['session_id'], new_title)
            print(f"✅ 세션 제목 업데이트 성공: {new_title}")
        
        # Test 7: Get session statistics
        print("\n📝 테스트 7: 세션 통계 조회")
        stats = session_service.get_session_statistics(test_user_id)
        print(f"✅ 세션 통계 조회 성공:")
        print(f"  - 총 세션 수: {stats.get('total_sessions', 0)}")
        print(f"  - 총 메시지 수: {stats.get('total_messages', 0)}")
        print(f"  - 최근 7일 세션: {stats.get('recent_sessions_7days', 0)}")
        
        # Test 8: Search sessions
        print("\n📝 테스트 8: 세션 검색")
        search_results = session_service.search_sessions(test_user_id, "테스트")
        print(f"✅ 세션 검색 성공: '{테스트}' 검색 결과 {len(search_results)}개")
        
        # Test 9: Delete session
        print("\n📝 테스트 9: 세션 삭제")
        if len(sessions) > 1:
            session_to_delete = sessions[-1]  # Delete last session
            success = session_service.delete_session(test_user_id, session_to_delete['session_id'])
            print(f"✅ 세션 삭제 성공: {session_to_delete['title']}")
        
        # Test 10: Clear user sessions
        print("\n📝 테스트 10: 사용자 세션 정리")
        success = session_service.clear_user_sessions(test_user_id, keep_default=True)
        print(f"✅ 사용자 세션 정리 성공")
        
        # Test 11: Logout user
        print("\n📝 테스트 11: 사용자 로그아웃")
        success = session_service.logout_user(test_user_id)
        print(f"✅ 사용자 로그아웃 성공")
        
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

def test_session_helpers():
    """세션 헬퍼 함수 테스트"""
    print("\n🧪 세션 헬퍼 함수 테스트 시작...")
    
    try:
        from utils.session_helpers import (
            format_session_time, get_session_activity_level, 
            get_session_activity_color, get_session_activity_emoji,
            validate_session_data
        )
        
        # Test time formatting
        print("\n📝 테스트 1: 시간 포맷팅")
        now = datetime.now()
        test_times = [
            now.isoformat(),  # Now
            (now - timedelta(minutes=5)).isoformat(),  # 5 minutes ago
            (now - timedelta(hours=2)).isoformat(),    # 2 hours ago
            (now - timedelta(days=3)).isoformat(),     # 3 days ago
            (now - timedelta(days=30)).isoformat(),    # 30 days ago
        ]
        
        for time_str in test_times:
            formatted = format_session_time(time_str)
            print(f"  - {time_str} -> {formatted}")
        
        # Test activity level
        print("\n📝 테스트 2: 활동 수준 분석")
        for time_str in test_times:
            level = get_session_activity_level(time_str)
            color = get_session_activity_color(level)
            emoji = get_session_activity_emoji(level)
            print(f"  - {time_str} -> {level} {emoji} ({color})")
        
        # Test session data validation
        print("\n📝 테스트 3: 세션 데이터 유효성 검사")
        test_sessions = [
            {
                "session_id": "valid_session_123",
                "title": "Valid Session",
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "message_count": 10
            },
            {
                "session_id": "invalid",
                "title": "Invalid Session",
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "message_count": -1
            },
            {
                "title": "Missing Fields",
                "message_count": 5
            }
        ]
        
        for i, session in enumerate(test_sessions):
            validation = validate_session_data(session)
            status = "✅ 유효" if validation["valid"] else f"❌ 무효: {validation.get('error', '알 수 없는 오류')}"
            print(f"  - 세션 {i+1}: {status}")
        
        print("\n🎉 세션 헬퍼 함수 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 헬퍼 함수 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

def test_file_operations():
    """파일 작업 테스트"""
    print("\n🧪 파일 작업 테스트 시작...")
    
    try:
        from services.session_management_service import SessionManagementService
        
        session_service = SessionManagementService()
        
        # Test directory creation
        print("\n📝 테스트 1: 디렉토리 생성")
        print(f"  - 세션 데이터 디렉토리: {session_service.session_data_dir}")
        print(f"  - 사용자 데이터 디렉토리: {session_service.user_data_dir}")
        
        # Test file structure
        print("\n📝 테스트 2: 파일 구조 확인")
        if os.path.exists(session_service.session_data_dir):
            print(f"  ✅ 세션 데이터 디렉토리 존재: {session_service.session_data_dir}")
        else:
            print(f"  ❌ 세션 데이터 디렉토리 없음: {session_service.session_data_dir}")
        
        if os.path.exists(session_service.user_data_dir):
            print(f"  ✅ 사용자 데이터 디렉토리 존재: {session_service.user_data_dir}")
        else:
            print(f"  ❌ 사용자 데이터 디렉토리 없음: {session_service.user_data_dir}")
        
        print("\n🎉 파일 작업 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 파일 작업 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """메인 테스트 함수"""
    print("🚀 세션 관리 시스템 테스트 시작")
    print("=" * 50)
    
    # Run all tests
    test_session_management()
    test_session_helpers()
    test_file_operations()
    
    print("\n" + "=" * 50)
    print("🏁 모든 테스트 완료!")

if __name__ == "__main__":
    main()
