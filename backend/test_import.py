#!/usr/bin/env python3
"""
Test script to check imports and basic functionality
"""
import sys
import os

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Testing imports...")

try:
    from backend.config.settings import settings
    print(f"✓ Settings loaded: MODEL_NAME = {settings.MODEL_NAME}")
except Exception as e:
    print(f"✗ Settings import failed: {e}")

try:
    from backend.services.ollama_service import ollama_service
    print("✓ Ollama service imported")
except Exception as e:
    print(f"✗ Ollama service import failed: {e}")

try:
    from backend.services.langchain_rag_service import langchain_rag_service
    print("✓ LangChain RAG service imported")
except Exception as e:
    print(f"✗ LangChain RAG service import failed: {e}")

print("Import test completed.")

