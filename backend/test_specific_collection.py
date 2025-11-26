import asyncio
import sys
import os

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.database_service import db_service
from sqlalchemy import text

async def test_specific_collection():
    """Test the document query with the '테스트 데이터 셋' collection"""
    print("Initializing database service...")
    await db_service.initialize()
    
    collection_name = "테스트 데이터 셋"
    
    async with db_service.get_session() as session:
        # Check if user_id column exists in langchain_pg_collection
        print(f"\n=== Testing collection '{collection_name}' ===")
        try:
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'langchain_pg_collection' AND column_name = 'user_id'
            """))
            row = result.fetchone()
            has_user_id = row is not None
            print(f"user_id column exists: {has_user_id}")
        except Exception as e:
            print(f"Error checking column: {e}")
            has_user_id = False
        
        # Query documents
        try:
            if has_user_id:
                query = """
                    SELECT
                        (e.cmetadata->>'filename') as id,
                        c.name as collection_name,
                        c.user_id::text as user_id,
                        COUNT(*) as chunk_count
                    FROM langchain_pg_embedding e
                    JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                    WHERE c.name = :collection_name
                    AND (e.cmetadata->>'filename') IS NOT NULL
                    GROUP BY (e.cmetadata->>'filename'), c.name, c.user_id
                """
            else:
                query = """
                    SELECT
                        (e.cmetadata->>'filename') as id,
                        c.name as collection_name,
                        NULL as user_id,
                        COUNT(*) as chunk_count
                    FROM langchain_pg_embedding e
                    JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                    WHERE c.name = :collection_name
                    AND (e.cmetadata->>'filename') IS NOT NULL
                    GROUP BY (e.cmetadata->>'filename'), c.name
                """
            
            result = await session.execute(text(query), {"collection_name": collection_name})
            rows = result.fetchall()
            print(f"\nQuery successful! Found {len(rows)} documents:")
            for row in rows:
                print(f"  - {row.id}")
                print(f"    Collection: {row.collection_name}")
                print(f"    User ID: {row.user_id}")
                print(f"    Chunks: {row.chunk_count}")
        except Exception as e:
            print(f"Query failed: {e}")
            import traceback
            traceback.print_exc()
    
    await db_service.close()
    print("\n=== Test completed successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_specific_collection())
