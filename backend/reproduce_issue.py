import asyncio
import sys
import os
from sqlalchemy import text

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.database_service import db_service

async def reproduce():
    print("Initializing database service...")
    await db_service.initialize()
    
    async with db_service.get_session() as session:
        # Check if user_id column exists in langchain_pg_collection
        print("Checking if user_id column exists in langchain_pg_collection...")
        try:
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'langchain_pg_collection' AND column_name = 'user_id'
            """))
            row = result.fetchone()
            print(f"user_id column exists: {row is not None}")
        except Exception as e:
            print(f"Error checking column: {e}")

        # Try to run the problematic query
        collection_name = "테스트 데이터 셋"
        print(f"Running query for collection: {collection_name}")
        
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
        """
        try:
            result = await session.execute(text(query), {"collection_name": collection_name})
            rows = result.fetchall()
            print(f"Query successful. Rows: {len(rows)}")
            for row in rows:
                print(f"Row: {row}")
        except Exception as e:
            print(f"Query failed: {e}")

    await db_service.close()

if __name__ == "__main__":
    asyncio.run(reproduce())
