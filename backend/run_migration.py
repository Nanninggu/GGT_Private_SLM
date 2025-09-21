#!/usr/bin/env python3
"""
Database migration script to add user_id column to collections
"""
import asyncio
import sys
import os
from sqlalchemy import text

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import db_service

async def run_migration():
    """Run the user_id migration"""
    try:
        print("🔄 Starting database migration...")
        
        # Initialize database service
        await db_service.initialize()
        
        # Read migration SQL
        migration_file = os.path.join(os.path.dirname(__file__), "migrations", "add_user_id_to_collections.sql")
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        async with db_service.get_session() as session:
            # Split SQL by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    print(f"Executing: {statement[:50]}...")
                    await session.execute(text(statement))
            
            await session.commit()
        
        print("✅ Migration completed successfully!")
        print("📝 Added user_id column to langchain_pg_collection table")
        print("🔍 Created index for better query performance")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)
