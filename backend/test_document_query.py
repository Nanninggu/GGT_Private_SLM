import asyncio
import sys
import os

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.database_service import db_service
from sqlalchemy import text

async def test_document_query():
    """Test the document query with a collection that may not have user_id column"""
    print("Initializing database service...")
    await db_service.initialize()
    
    async with db_service.get_session() as session:
        # Test 1: Check if user_id column exists in langchain_pg_collection
        print("\n=== Test 1: Checking user_id column in langchain_pg_collection ===")
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
        
        # Test 2: Get all LangChain collections
        print("\n=== Test 2: Getting all LangChain collections ===")
        try:
            result = await session.execute(text("""
                SELECT name FROM langchain_pg_collection
            """))
            collections = result.fetchall()
            print(f"Found {len(collections)} collections:")
            for col in collections:
                print(f"  - {col.name}")
        except Exception as e:
            print(f"Error getting collections: {e}")
            collections = []
        
        # Test 3: Query documents from a collection (simulating the API endpoint)
        if collections:
            collection_name = collections[0].name
            print(f"\n=== Test 3: Querying documents from collection '{collection_name}' ===")
            
            try:
                # Build query conditionally based on whether user_id column exists
                if has_user_id:
                    query = """
                        SELECT
                            (e.cmetadata->>'filename') as id,
                            string_agg(e.document, E'\n\n--- 청크 구분선 ---\n\n') as content,
                            jsonb_build_object(
                                'filename', (e.cmetadata->>'filename'),
                                'file_type', MAX(e.cmetadata->>'file_type'),
                                'chunk_count', COUNT(*),
                                'total_chunks', COUNT(*)
                            ) as metadata,
                            c.name as collection_name,
                            c.user_id::text as user_id,
                            MIN(COALESCE(
                                (e.cmetadata->>'created_at')::timestamp,
                                (e.cmetadata->>'created_date')::timestamp,
                                (e.cmetadata->>'upload_date')::timestamp,
                                CURRENT_TIMESTAMP
                            )) as created_at,
                            MAX(COALESCE(
                                (e.cmetadata->>'updated_at')::timestamp,
                                (e.cmetadata->>'modified_date')::timestamp,
                                (e.cmetadata->>'created_at')::timestamp,
                                CURRENT_TIMESTAMP
                            )) as updated_at,
                            CASE WHEN COUNT(CASE WHEN e.embedding IS NOT NULL THEN 1 END) > 0 THEN true ELSE false END as has_embedding
                        FROM langchain_pg_embedding e
                        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                        WHERE c.name = :collection_name
                        AND (e.cmetadata->>'filename') IS NOT NULL
                        GROUP BY (e.cmetadata->>'filename'), c.name, c.user_id
                        LIMIT 5
                    """
                else:
                    query = """
                        SELECT
                            (e.cmetadata->>'filename') as id,
                            string_agg(e.document, E'\n\n--- 청크 구분선 ---\n\n') as content,
                            jsonb_build_object(
                                'filename', (e.cmetadata->>'filename'),
                                'file_type', MAX(e.cmetadata->>'file_type'),
                                'chunk_count', COUNT(*),
                                'total_chunks', COUNT(*)
                            ) as metadata,
                            c.name as collection_name,
                            NULL as user_id,
                            MIN(COALESCE(
                                (e.cmetadata->>'created_at')::timestamp,
                                (e.cmetadata->>'created_date')::timestamp,
                                (e.cmetadata->>'upload_date')::timestamp,
                                CURRENT_TIMESTAMP
                            )) as created_at,
                            MAX(COALESCE(
                                (e.cmetadata->>'updated_at')::timestamp,
                                (e.cmetadata->>'modified_date')::timestamp,
                                (e.cmetadata->>'created_at')::timestamp,
                                CURRENT_TIMESTAMP
                            )) as updated_at,
                            CASE WHEN COUNT(CASE WHEN e.embedding IS NOT NULL THEN 1 END) > 0 THEN true ELSE false END as has_embedding
                        FROM langchain_pg_embedding e
                        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                        WHERE c.name = :collection_name
                        AND (e.cmetadata->>'filename') IS NOT NULL
                        GROUP BY (e.cmetadata->>'filename'), c.name
                        LIMIT 5
                    """
                
                result = await session.execute(text(query), {"collection_name": collection_name})
                rows = result.fetchall()
                print(f"Query successful! Found {len(rows)} documents:")
                for row in rows:
                    print(f"  - {row.id} (user_id: {row.user_id})")
            except Exception as e:
                print(f"Query failed: {e}")
                import traceback
                traceback.print_exc()
    
    await db_service.close()
    print("\n=== Test completed successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_document_query())
