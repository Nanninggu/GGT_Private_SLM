"""
Accuracy measurement controller for RAG system evaluation
"""
import asyncio
from typing import Dict, Any, List

from backend.services.accuracy_service import accuracy_service


class AccuracyController:
    """Controller for accuracy measurement endpoints"""

    def __init__(self):
        self.accuracy_service = accuracy_service

    async def measure_single_query(self, query: str, expected_answer: str = None) -> Dict[str, Any]:
        """Measure accuracy for a single query"""
        try:
            if not query.strip():
                return {
                    "success": False,
                    "error": "Query cannot be empty"
                }

            result = await self.accuracy_service.measure_query_accuracy(query, expected_answer)
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            import traceback
            print(f"Error in measure_single_query: {e}")
            print(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    async def run_test_suite(self, test_queries: List[Dict[str, str]]) -> Dict[str, Any]:
        """Run a comprehensive accuracy test suite"""
        try:
            if not test_queries:
                return {
                    "success": False,
                    "error": "Test queries cannot be empty"
                }

            result = await self.accuracy_service.run_accuracy_test_suite(test_queries)
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            result = await self.accuracy_service.get_system_health_metrics()
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_sample_test_queries(self) -> Dict[str, Any]:
        """Get sample test queries for accuracy testing"""
        try:
            sample_queries = [
                {
                    "query": "인공지능이란 무엇인가요?",
                    "expected_answer": "인공지능은 인간의 지능을 모방하여 학습, 추론, 문제해결 등의 능력을 가진 컴퓨터 시스템입니다."
                },
                {
                    "query": "RAG 시스템의 장점은 무엇인가요?",
                    "expected_answer": "RAG 시스템은 검색 증강 생성으로, 최신 정보를 활용하고 정확한 답변을 제공할 수 있습니다."
                },
                {
                    "query": "벡터 데이터베이스는 어떻게 작동하나요?",
                    "expected_answer": "벡터 데이터베이스는 문서를 벡터로 변환하여 유사도 검색을 통해 관련 문서를 찾습니다."
                },
                {
                    "query": "시스템의 성능을 측정하는 방법은?",
                    "expected_answer": "시스템 성능은 응답 시간, 정확도, 유사도 점수 등을 통해 측정할 수 있습니다."
                },
                {
                    "query": "한국어 자연어 처리는 어떻게 이루어지나요?",
                    "expected_answer": "한국어 자연어 처리는 형태소 분석, 구문 분석, 의미 분석 등의 단계를 거쳐 이루어집니다."
                }
            ]
            
            return {
                "success": True,
                "sample_queries": sample_queries
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
