#!/usr/bin/env python3
"""
성능 최적화 테스트 스크립트
최적화 적용 후 성능 향상을 측정합니다.
"""
import asyncio
import time
import sys
import os
import logging

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.vector_service import vector_service
from backend.services.rag_service import rag_service
from backend.services.cache_service import cache_service
from backend.services.ollama_service import ollama_service
from backend.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_vector_search_performance():
    """벡터 검색 성능 테스트"""
    logger.info("🔍 벡터 검색 성능 테스트 시작...")
    
    test_queries = [
        "인공지능이란 무엇인가?",
        "머신러닝과 딥러닝의 차이점",
        "자연어 처리 기술",
        "컴퓨터 비전 응용 분야",
        "데이터 사이언스 방법론"
    ]
    
    total_time = 0
    successful_searches = 0
    
    for i, query in enumerate(test_queries, 1):
        try:
            start_time = time.time()
            results = await vector_service.search_similar_optimized(query, top_k=3)
            end_time = time.time()
            
            search_time = end_time - start_time
            total_time += search_time
            successful_searches += 1
            
            logger.info(f"쿼리 {i}: {search_time:.3f}초, 결과 {len(results)}개")
            
        except Exception as e:
            logger.error(f"쿼리 {i} 실패: {e}")
    
    if successful_searches > 0:
        avg_time = total_time / successful_searches
        logger.info(f"✅ 벡터 검색 평균 시간: {avg_time:.3f}초")
        return avg_time
    else:
        logger.error("❌ 모든 벡터 검색 실패")
        return None

async def test_rag_performance():
    """RAG 성능 테스트"""
    logger.info("🤖 RAG 성능 테스트 시작...")
    
    test_queries = [
        "인공지능의 역사를 설명해주세요",
        "머신러닝 알고리즘의 종류는?",
        "자연어 처리의 주요 기술들",
        "딥러닝의 장단점",
        "AI 윤리와 사회적 영향"
    ]
    
    total_time = 0
    successful_queries = 0
    
    for i, query in enumerate(test_queries, 1):
        try:
            start_time = time.time()
            result = await rag_service.rag_query(query, model_type="fast")
            end_time = time.time()
            
            query_time = end_time - start_time
            total_time += query_time
            successful_queries += 1
            
            response_length = len(result.get("response", ""))
            context_count = result.get("metadata", {}).get("context_count", 0)
            
            logger.info(f"RAG 쿼리 {i}: {query_time:.3f}초, 응답 {response_length}자, 컨텍스트 {context_count}개")
            
        except Exception as e:
            logger.error(f"RAG 쿼리 {i} 실패: {e}")
    
    if successful_queries > 0:
        avg_time = total_time / successful_queries
        logger.info(f"✅ RAG 평균 시간: {avg_time:.3f}초")
        return avg_time
    else:
        logger.error("❌ 모든 RAG 쿼리 실패")
        return None

async def test_cache_performance():
    """캐시 성능 테스트"""
    logger.info("💾 캐시 성능 테스트 시작...")
    
    # 캐시 통계 확인
    cache_stats = cache_service.get_cache_stats()
    logger.info(f"캐시 통계: {cache_stats}")
    
    # 캐시 히트율 확인
    embedding_hit_rate = cache_stats.get("embedding_hit_rate", 0)
    search_hit_rate = cache_stats.get("search_hit_rate", 0)
    chat_hit_rate = cache_stats.get("chat_hit_rate", 0)
    
    logger.info(f"임베딩 캐시 히트율: {embedding_hit_rate}%")
    logger.info(f"검색 캐시 히트율: {search_hit_rate}%")
    logger.info(f"채팅 캐시 히트율: {chat_hit_rate}%")
    
    return {
        "embedding_hit_rate": embedding_hit_rate,
        "search_hit_rate": search_hit_rate,
        "chat_hit_rate": chat_hit_rate
    }

async def test_optimization_settings():
    """최적화 설정 확인"""
    logger.info("⚙️ 최적화 설정 확인...")
    
    # 벡터 DB 설정
    logger.info(f"벡터 DB ef_search: {settings.VECTOR_DB_EF_SEARCH}")
    logger.info(f"벡터 DB top_k: {settings.VECTOR_DB_TOP_K}")
    logger.info(f"벡터 DB similarity_threshold: {settings.VECTOR_DB_SIMILARITY_THRESHOLD}")
    
    # RAG 설정
    logger.info(f"RAG context_max_docs: {settings.RAG_CONTEXT_MAX_DOCS}")
    logger.info(f"RAG vector_search_top_k: {settings.RAG_VECTOR_SEARCH_TOP_K}")
    logger.info(f"RAG context_max_length: {settings.RAG_CONTEXT_MAX_LENGTH}")
    
    # LLM 설정
    fast_config = settings.MODEL_CONFIGS.get("fast", {})
    logger.info(f"LLM num_ctx: {fast_config.get('num_ctx', 'N/A')}")
    logger.info(f"LLM num_predict: {fast_config.get('num_predict', 'N/A')}")
    
    # 캐시 설정
    logger.info(f"캐시 TTL: {cache_service.cache_ttl}초")
    logger.info(f"채팅 캐시 TTL: {cache_service.chat_cache_ttl}초")

async def main():
    """메인 테스트 함수"""
    logger.info("🚀 성능 최적화 테스트 시작")
    logger.info("=" * 50)
    
    try:
        # 서비스 초기화
        logger.info("서비스 초기화 중...")
        await vector_service.initialize()
        await rag_service.initialize()
        await ollama_service.initialize()
        
        # 최적화 설정 확인
        await test_optimization_settings()
        logger.info("=" * 50)
        
        # 벡터 검색 성능 테스트
        vector_avg_time = await test_vector_search_performance()
        logger.info("=" * 50)
        
        # RAG 성능 테스트
        rag_avg_time = await test_rag_performance()
        logger.info("=" * 50)
        
        # 캐시 성능 테스트
        cache_stats = await test_cache_performance()
        logger.info("=" * 50)
        
        # 결과 요약
        logger.info("📊 성능 테스트 결과 요약")
        logger.info("=" * 50)
        
        if vector_avg_time:
            logger.info(f"벡터 검색 평균 시간: {vector_avg_time:.3f}초")
        
        if rag_avg_time:
            logger.info(f"RAG 평균 시간: {rag_avg_time:.3f}초")
        
        logger.info(f"임베딩 캐시 히트율: {cache_stats['embedding_hit_rate']}%")
        logger.info(f"검색 캐시 히트율: {cache_stats['search_hit_rate']}%")
        logger.info(f"채팅 캐시 히트율: {cache_stats['chat_hit_rate']}%")
        
        # 성능 평가
        if vector_avg_time and vector_avg_time < 0.5:
            logger.info("✅ 벡터 검색 성능: 우수 (0.5초 미만)")
        elif vector_avg_time and vector_avg_time < 1.0:
            logger.info("⚠️ 벡터 검색 성능: 양호 (1.0초 미만)")
        else:
            logger.info("❌ 벡터 검색 성능: 개선 필요 (1.0초 이상)")
        
        if rag_avg_time and rag_avg_time < 2.0:
            logger.info("✅ RAG 성능: 우수 (2.0초 미만)")
        elif rag_avg_time and rag_avg_time < 5.0:
            logger.info("⚠️ RAG 성능: 양호 (5.0초 미만)")
        else:
            logger.info("❌ RAG 성능: 개선 필요 (5.0초 이상)")
        
        logger.info("🎉 성능 최적화 테스트 완료!")
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
    finally:
        # 서비스 정리
        await vector_service.close()
        await rag_service.close()
        await ollama_service.close()

if __name__ == "__main__":
    asyncio.run(main())
