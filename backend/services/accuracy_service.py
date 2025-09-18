"""
Accuracy measurement service for RAG system evaluation
"""
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import json
import re
from datetime import datetime

from backend.services.rag_service import rag_service
from backend.services.vector_service import vector_service

logger = logging.getLogger(__name__)

class AccuracyService:
    """Service for measuring RAG system accuracy and performance"""
    
    def __init__(self):
        self.rag_service = rag_service
        self.vector_service = vector_service
        
    async def initialize(self):
        """Initialize accuracy service"""
        try:
            # No specific initialization needed for accuracy service
            # It depends on rag_service and vector_service which are initialized separately
            logger.info("Accuracy service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize accuracy service: {e}")
            raise
        
    async def measure_query_accuracy(self, query: str, expected_answer: Optional[str] = None) -> Dict[str, Any]:
        """Measure accuracy for a single query"""
        try:
            start_time = time.time()
            
            # Get RAG response
            rag_result = await self.rag_service.rag_query(query)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Extract metrics
            metrics = {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "response_time": response_time,
                "success": rag_result.get("success", False),
                "response": rag_result.get("response", ""),
                "context_count": rag_result.get("metadata", {}).get("context_count", 0),
                "similarity_scores": rag_result.get("metadata", {}).get("similarity_scores", []),
                "average_similarity": rag_result.get("metadata", {}).get("similarity", 0.0),
                "context_files": rag_result.get("metadata", {}).get("context_files", []),
                "fallback_mode": rag_result.get("metadata", {}).get("fallback_mode", False)
            }
            
            # Calculate additional accuracy metrics
            accuracy_metrics = await self._calculate_accuracy_metrics(query, rag_result, expected_answer)
            metrics.update(accuracy_metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to measure query accuracy: {e}")
            return {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "success": False
            }
    
    async def _calculate_accuracy_metrics(self, query: str, rag_result: Dict[str, Any], expected_answer: Optional[str] = None) -> Dict[str, Any]:
        """Calculate various accuracy metrics"""
        try:
            metrics = {}
            
            # Context relevance score
            context_relevance = self._calculate_context_relevance(query, rag_result.get("context", []))
            metrics["context_relevance"] = context_relevance
            
            # Answer quality score (basic heuristics)
            answer_quality = self._calculate_answer_quality(rag_result.get("response", ""))
            metrics["answer_quality"] = answer_quality
            
            # Overall accuracy score
            overall_accuracy = self._calculate_overall_accuracy(rag_result, context_relevance, answer_quality)
            metrics["overall_accuracy"] = overall_accuracy
            
            # Confidence level
            confidence = self._calculate_confidence(rag_result)
            metrics["confidence"] = confidence
            
            # Expected answer comparison (if provided)
            if expected_answer:
                similarity_to_expected = self._calculate_similarity_to_expected(
                    rag_result.get("response", ""), expected_answer
                )
                metrics["similarity_to_expected"] = similarity_to_expected
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate accuracy metrics: {e}")
            return {
                "context_relevance": 0.0,
                "answer_quality": 0.0,
                "overall_accuracy": 0.0,
                "confidence": 0.0
            }
    
    def _calculate_context_relevance(self, query: str, context: List[Dict[str, Any]]) -> float:
        """Calculate how relevant the retrieved context is to the query"""
        if not context:
            return 0.0
        
        # Use average similarity score as context relevance
        similarity_scores = [doc.get("similarity", 0) for doc in context]
        if similarity_scores:
            return sum(similarity_scores) / len(similarity_scores)
        return 0.0
    
    def _calculate_answer_quality(self, answer: str) -> float:
        """Calculate answer quality based on heuristics"""
        if not answer or len(answer.strip()) < 10:
            return 0.0
        
        quality_score = 0.0
        
        # Length factor (not too short, not too long)
        length = len(answer.strip())
        if 50 <= length <= 1000:
            quality_score += 0.3
        elif 20 <= length < 50 or 1000 < length <= 2000:
            quality_score += 0.2
        else:
            quality_score += 0.1
        
        # Completeness indicators
        if any(indicator in answer.lower() for indicator in ["답변", "설명", "정보", "내용"]):
            quality_score += 0.2
        
        # Structure indicators
        if any(indicator in answer for indicator in ["1.", "2.", "•", "-", "**"]):
            quality_score += 0.2
        
        # Korean language quality
        korean_chars = sum(1 for char in answer if '\uac00' <= char <= '\ud7af')
        total_chars = len([char for char in answer if char.isalpha()])
        if total_chars > 0 and korean_chars / total_chars > 0.5:
            quality_score += 0.3
        
        return min(quality_score, 1.0)
    
    def _calculate_overall_accuracy(self, rag_result: Dict[str, Any], context_relevance: float, answer_quality: float) -> float:
        """Calculate overall accuracy score"""
        if not rag_result.get("success", False):
            return 0.0
        
        # Weighted combination of different factors
        weights = {
            "context_relevance": 0.4,
            "answer_quality": 0.3,
            "similarity": 0.3
        }
        
        similarity = rag_result.get("metadata", {}).get("similarity", 0.0)
        
        overall = (
            context_relevance * weights["context_relevance"] +
            answer_quality * weights["answer_quality"] +
            similarity * weights["similarity"]
        )
        
        return min(overall, 1.0)
    
    def _calculate_confidence(self, rag_result: Dict[str, Any]) -> float:
        """Calculate confidence level based on various factors"""
        if not rag_result.get("success", False):
            return 0.0
        
        confidence = 0.0
        
        # Context availability
        context_count = rag_result.get("metadata", {}).get("context_count", 0)
        if context_count > 0:
            confidence += 0.4
        else:
            confidence += 0.1  # Some confidence even without context
        
        # Similarity scores
        similarity_scores = rag_result.get("metadata", {}).get("similarity_scores", [])
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            confidence += avg_similarity * 0.4
        
        # Response length (longer responses might be more confident)
        response = rag_result.get("response", "")
        if len(response) > 100:
            confidence += 0.2
        elif len(response) > 50:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_similarity_to_expected(self, actual_answer: str, expected_answer: str) -> float:
        """Calculate similarity between actual and expected answers"""
        if not actual_answer or not expected_answer:
            return 0.0
        
        # Simple word overlap similarity
        actual_words = set(actual_answer.lower().split())
        expected_words = set(expected_answer.lower().split())
        
        if not expected_words:
            return 0.0
        
        overlap = len(actual_words.intersection(expected_words))
        similarity = overlap / len(expected_words)
        
        return min(similarity, 1.0)
    
    async def run_accuracy_test_suite(self, test_queries: List[Dict[str, str]]) -> Dict[str, Any]:
        """Run a comprehensive accuracy test suite"""
        try:
            results = []
            total_queries = len(test_queries)
            
            for i, test_case in enumerate(test_queries):
                query = test_case.get("query", "")
                expected = test_case.get("expected_answer", "")
                
                logger.info(f"Running accuracy test {i+1}/{total_queries}: {query[:50]}...")
                
                result = await self.measure_query_accuracy(query, expected)
                results.append(result)
                
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
            
            # Calculate aggregate metrics
            aggregate_metrics = self._calculate_aggregate_metrics(results)
            
            return {
                "test_suite_results": results,
                "aggregate_metrics": aggregate_metrics,
                "total_queries": total_queries,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to run accuracy test suite: {e}")
            return {
                "error": str(e),
                "total_queries": len(test_queries),
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_aggregate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate metrics from test results"""
        if not results:
            return {}
        
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            return {
                "success_rate": 0.0,
                "average_response_time": 0.0,
                "average_accuracy": 0.0,
                "average_confidence": 0.0
            }
        
        # Calculate averages
        success_rate = len(successful_results) / len(results)
        avg_response_time = sum(r.get("response_time", 0) for r in successful_results) / len(successful_results)
        avg_accuracy = sum(r.get("overall_accuracy", 0) for r in successful_results) / len(successful_results)
        avg_confidence = sum(r.get("confidence", 0) for r in successful_results) / len(successful_results)
        
        # Calculate accuracy distribution
        accuracy_scores = [r.get("overall_accuracy", 0) for r in successful_results]
        high_accuracy = len([score for score in accuracy_scores if score >= 0.8])
        medium_accuracy = len([score for score in accuracy_scores if 0.5 <= score < 0.8])
        low_accuracy = len([score for score in accuracy_scores if score < 0.5])
        
        return {
            "success_rate": success_rate,
            "average_response_time": avg_response_time,
            "average_accuracy": avg_accuracy,
            "average_confidence": avg_confidence,
            "accuracy_distribution": {
                "high": high_accuracy,
                "medium": medium_accuracy,
                "low": low_accuracy
            },
            "total_tests": len(results),
            "successful_tests": len(successful_results)
        }
    
    async def get_system_health_metrics(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        try:
            # Get document count
            doc_count = await self.vector_service.get_document_count()
            
            # Get collections info
            collections = await self.vector_service.get_collections()
            
            # Test a simple query
            test_query = "시스템 상태 확인"
            test_result = await self.measure_query_accuracy(test_query)
            
            return {
                "document_count": doc_count,
                "collections": collections,
                "test_query_result": test_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global accuracy service instance
accuracy_service = AccuracyService()
