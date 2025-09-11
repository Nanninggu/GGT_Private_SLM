"""
Check database schema
"""
import asyncio
import sys
import os

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.database_service import db_service
from sqlalchemy import text

async def check_schema():
    """Check langchain_pg_collection table schema"""
    try:
        async with db_service.get_session() as session:
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'langchain_pg_collection'
                ORDER BY ordinal_position
            """))
            
            print("langchain_pg_collection table schema:")
            print("-" * 50)
            for row in result:
                print(f"Column: {row.column_name}")
                print(f"  Type: {row.data_type}")
                print(f"  Nullable: {row.is_nullable}")
                print(f"  Default: {row.column_default}")
                print()
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())



