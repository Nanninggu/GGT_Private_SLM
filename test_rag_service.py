#!/usr/bin/env python3
"""
Test script to verify LangChain RAG service model configuration
"""
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.langchain_rag_service import langchain_rag_service
from backend.config.settings import settings

async def test_rag_service():
    print("Testing LangChain RAG service...")
    
    try:
        # Initialize the service
        await langchain_rag_service.initialize()
        print("Service initialized successfully")
        
        # Test different model types
        for model_type in ["fast", "quality", "complex"]:
            print(f"\nTesting model type: {model_type}")
            result = await langchain_rag_service.rag_query(
                "AI에 대해 간단히 설명해주세요", 
                "test_session", 
                model_type
            )
            
            if result["success"]:
                model_info = result.get("model_info", {})
                print(f"  Model: {model_info.get('model', 'unknown')}")
                print(f"  Model Type: {model_info.get('model_type', 'unknown')}")
                print(f"  Response length: {len(result['response'])}")
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_rag_service())
