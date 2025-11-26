import asyncio
import os
import sys
import logging
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.database_service import db_service

async def inspect_data():
    print("Initializing database...")
    await db_service.initialize()
    
    async with db_service.get_session() as session:
        print("\n=== langchain_pg_collection ===")
        result = await session.execute(text("SELECT uuid, name FROM langchain_pg_collection"))
        collections = result.fetchall()
        collection_map = {}
        for c in collections:
            print(f"UUID: {c.uuid}, Name: {c.name}")
            collection_map[str(c.uuid)] = c.name
            
        print("\n=== langchain_pg_embedding counts by collection_id ===")
        result = await session.execute(text("""
            SELECT collection_id, COUNT(*) as count 
            FROM langchain_pg_embedding 
            GROUP BY collection_id
        """))
        counts = result.fetchall()
        
        for c in counts:
            c_uuid = str(c.collection_id)
            c_name = collection_map.get(c_uuid, "UNKNOWN")
            print(f"Collection ID: {c_uuid} ({c_name}), Count: {c.count}")

if __name__ == "__main__":
    asyncio.run(inspect_data())
