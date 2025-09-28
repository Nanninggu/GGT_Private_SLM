#!/usr/bin/env python3
"""
Migration script to update existing shared collections to new structure
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from services.database_service import DatabaseService
from sqlalchemy import text

async def run_migration():
    """Run the shared collection migration"""
    print("Starting shared collection migration...")
    
    # Initialize database service
    db_service = DatabaseService()
    await db_service.initialize()
    
    try:
        async with db_service.get_session() as session:
            # Read migration SQL file
            migration_file = backend_dir / "migrations" / "migrate_shared_collections.sql"
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            # Split SQL into individual statements
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement.startswith('--') or not statement:
                    continue
                    
                print(f"Executing statement {i}...")
                print(f"SQL: {statement[:100]}...")
                
                await session.execute(text(statement))
                await session.commit()
                
                print(f"✅ Statement {i} completed")
            
            print("\n🎉 Migration completed successfully!")
            
            # Verify migration results
            result = await session.execute(text("""
                SELECT 
                    name,
                    user_id,
                    cmetadata->>'is_shared' as is_shared
                FROM langchain_pg_collection 
                WHERE user_id = 'system'
                ORDER BY name
            """))
            
            collections = result.fetchall()
            print(f"\n📊 Found {len(collections)} migrated shared collections:")
            for collection in collections:
                print(f"  - {collection.name} (user_id: {collection.user_id}, is_shared: {collection.is_shared})")
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await db_service.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
