#!/usr/bin/env python3
"""
임베딩 생성 테스트 스크립트
Ollama 서버와 임베딩 모델이 정상적으로 작동하는지 확인합니다.
"""
import sys
import os
import asyncio
import httpx

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config.settings import settings
from backend.services.vector_service import vector_service

async def test_ollama_connection():
    """Ollama 서버 연결 테스트"""
    print("=" * 60)
    print("1. Ollama 서버 연결 테스트")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=10.0) as client:
            # 서버 상태 확인
            response = await client.get("/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            
            print(f"✓ Ollama 서버 연결 성공: {settings.OLLAMA_BASE_URL}")
            print(f"  설치된 모델 수: {len(models)}")
            
            # 모델 목록 출력
            if models:
                print("\n  설치된 모델:")
                for model in models:
                    model_name = model.get("name", "unknown")
                    print(f"    - {model_name}")
            
            # nomic-embed-text 모델 확인
            embedding_model = settings.OLLAMA_EMBEDDING_MODEL
            model_names = [m.get("name", "") for m in models]
            model_found = any(embedding_model in name for name in model_names)
            
            if model_found:
                print(f"\n✓ 임베딩 모델 '{embedding_model}' 발견됨")
            else:
                print(f"\n✗ 임베딩 모델 '{embedding_model}'을 찾을 수 없습니다!")
                print(f"  설치 명령: ollama pull {embedding_model}")
                return False
            
            return True
            
    except httpx.RequestError as e:
        print(f"✗ Ollama 서버 연결 실패: {e}")
        print(f"  서버 주소: {settings.OLLAMA_BASE_URL}")
        print(f"  확인 사항: Ollama 서버가 실행 중인지 확인하세요.")
        return False
    except Exception as e:
        print(f"✗ 오류 발생: {e}")
        return False

async def test_embedding_generation():
    """임베딩 생성 테스트"""
    print("\n" + "=" * 60)
    print("2. 임베딩 생성 테스트")
    print("=" * 60)
    
    try:
        # Vector service 초기화
        await vector_service.initialize()
        print("✓ Vector service 초기화 완료")
        
        # 테스트 텍스트
        test_texts = [
            "안녕하세요. 이것은 테스트입니다.",
            "Hello, this is a test.",
            "임베딩 생성이 정상적으로 작동하는지 확인합니다."
        ]
        
        print(f"\n임베딩 모델: {settings.OLLAMA_EMBEDDING_MODEL}")
        print(f"테스트 텍스트 수: {len(test_texts)}\n")
        
        for i, text in enumerate(test_texts, 1):
            print(f"테스트 {i}/{len(test_texts)}: '{text[:30]}...'")
            try:
                embedding = await vector_service.generate_embedding(text)
                
                if embedding:
                    print(f"  ✓ 임베딩 생성 성공")
                    print(f"    - 차원: {len(embedding)}")
                    expected_dimension = settings.OLLAMA_EMBEDDING_DIMENSION
                    print(f"    - 예상 차원: {expected_dimension}")
                    
                    if len(embedding) == expected_dimension:
                        print(f"    - 차원 일치: ✓")
                    else:
                        print(f"    - 차원 불일치: ⚠️ (예상: {expected_dimension}, 실제: {len(embedding)})")
                    
                    # 임베딩 값 샘플 출력
                    print(f"    - 샘플 값: [{embedding[0]:.6f}, {embedding[1]:.6f}, {embedding[2]:.6f}, ...]")
                else:
                    print(f"  ✗ 임베딩 생성 실패: 결과가 None입니다")
                    return False
                    
            except Exception as e:
                print(f"  ✗ 임베딩 생성 실패: {e}")
                print(f"    오류 타입: {type(e).__name__}")
                return False
            
            print()
        
        print("✓ 모든 임베딩 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"✗ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_document_addition():
    """문서 추가 테스트 (실제 업로드 시뮬레이션)"""
    print("\n" + "=" * 60)
    print("3. 문서 추가 테스트 (업로드 시뮬레이션)")
    print("=" * 60)
    
    try:
        test_content = """
        이것은 테스트 문서입니다.
        임베딩 생성과 문서 저장이 정상적으로 작동하는지 확인합니다.
        여러 문장으로 구성된 문서를 테스트합니다.
        """
        
        print(f"테스트 문서 길이: {len(test_content)} 문자")
        print("문서를 벡터 데이터베이스에 추가 중...\n")
        
        metadata = {
            "filename": "test_embedding.txt",
            "file_type": "text/plain",
            "test": True
        }
        
        doc_id = await vector_service.add_document(
            content=test_content,
            metadata=metadata,
            collection_name="documents",
            user_id=None
        )
        
        print(f"✓ 문서 추가 성공!")
        print(f"  - 문서 ID: {doc_id}")
        print(f"  - 컬렉션: documents")
        
        # 데이터베이스에서 확인
        from backend.services.database_service import db_service
        async with db_service.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("""
                    SELECT id, 
                           CASE WHEN embedding IS NOT NULL THEN true ELSE false END as has_embedding,
                           LENGTH(content) as content_length
                    FROM documents 
                    WHERE id = :doc_id
                """),
                {"doc_id": doc_id}
            )
            row = result.fetchone()
            
            if row:
                print(f"\n  데이터베이스 확인:")
                print(f"    - 문서 ID: {row.id}")
                print(f"    - 임베딩 존재: {'✓ 예' if row.has_embedding else '✗ 아니오'}")
                print(f"    - 내용 길이: {row.content_length} 문자")
                
                if not row.has_embedding:
                    print(f"\n  ⚠️ 경고: 문서는 저장되었지만 임베딩이 없습니다!")
                    print(f"     이는 벡터화 실패를 의미합니다.")
                    return False
            else:
                print(f"\n  ✗ 문서를 데이터베이스에서 찾을 수 없습니다.")
                return False
        
        print(f"\n✓ 문서 추가 및 벡터화 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"✗ 문서 추가 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 60)
    print("임베딩 생성 테스트 시작")
    print("=" * 60)
    print(f"Ollama 서버: {settings.OLLAMA_BASE_URL}")
    print(f"임베딩 모델: {settings.OLLAMA_EMBEDDING_MODEL}")
    print(f"임베딩 타임아웃: {settings.OLLAMA_EMBEDDING_TIMEOUT}초")
    print()
    
    results = []
    
    # 1. Ollama 연결 테스트
    result1 = await test_ollama_connection()
    results.append(("Ollama 서버 연결", result1))
    
    if not result1:
        print("\n⚠️ Ollama 서버 연결 실패로 인해 테스트를 중단합니다.")
        return
    
    # 2. 임베딩 생성 테스트
    result2 = await test_embedding_generation()
    results.append(("임베딩 생성", result2))
    
    if not result2:
        print("\n⚠️ 임베딩 생성 실패로 인해 문서 추가 테스트를 건너뜁니다.")
    else:
        # 3. 문서 추가 테스트
        result3 = await test_document_addition()
        results.append(("문서 추가 및 벡터화", result3))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ 통과" if result else "✗ 실패"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 모든 테스트 통과!")
        print("임베딩 기능이 정상적으로 작동합니다.")
    else:
        print("✗ 일부 테스트 실패")
        print("위의 오류 메시지를 확인하고 문제를 해결하세요.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

