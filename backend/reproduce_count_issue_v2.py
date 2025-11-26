import asyncio
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.langchain_vector_service import langchain_vector_service
from backend.services.database_service import db_service
from backend.services.rag_service import rag_service

async def test_get_collections():
    print("Initializing services...")
    await db_service.initialize()
    await langchain_vector_service.initialize()
    
    print("\nCalling get_collections()...")
    
    async with db_service.get_session() as session:
        from sqlalchemy import text
        result = await session.execute(text("SELECT user_id FROM langchain_pg_collection LIMIT 1"))
        row = result.fetchone()
        user_id = row[0] if row else None
        print(f"Using user_id: {user_id}")

    # Test langchain_vector_service
    print("\n--- LangChain Vector Service ---")
    langchain_collections = await langchain_vector_service.get_collections(user_id)
    for c in langchain_collections:
        print(f"Name: {c.get('name')}, Count: {c.get('document_count')}")

    # Test rag_service (which uses vector_service)
    print("\n--- Basic RAG Service ---")
    basic_collections = await rag_service.get_available_collections()
    for c in basic_collections:
        print(f"Name: {c.get('name')}, Count: {c.get('document_count')}")

if __name__ == "__main__":
    asyncio.run(test_get_collections())
