"""
Database service for PostgreSQL and pgvector integration
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Text, Float, Integer, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import json

from backend.config.settings import settings

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for PostgreSQL with pgvector support"""
    
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        self.async_session_factory = None
        
    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            # Create async engine for PostgreSQL with vector optimization
            self.async_engine = create_async_engine(
                settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
                pool_size=settings.DB_POOL_MAX_SIZE,
                max_overflow=5,  # 추가 연결 허용
                pool_pre_ping=True,
                pool_recycle=settings.DB_POOL_MAX_LIFETIME,
                pool_timeout=30,  # 연결 타임아웃
                echo=settings.LOG_LEVEL_APP == "DEBUG",
                # 벡터 연산 최적화를 위한 연결 인수
                connect_args={
                    "server_settings": {
                        "jit": "off",  # JIT 컴파일 비활성화 (벡터 연산에 불리)
                        "enable_seqscan": "off" if settings.VECTOR_DB_ENABLE_SEQSCAN else "on",
                        "random_page_cost": str(settings.VECTOR_DB_RANDOM_PAGE_COST),
                        "effective_cache_size": settings.VECTOR_DB_EFFECTIVE_CACHE_SIZE,
                        "max_parallel_workers_per_gather": "4",
                        "parallel_tuple_cost": "0.1"
                    }
                }
            )
            
            # Create session factory
            self.async_session_factory = sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Initialize pgvector extension and create tables
            # pgvector extension is optional - continue even if it fails
            try:
                await self._initialize_pgvector()
            except Exception as e:
                logger.warning(f"Failed to initialize pgvector extension (continuing without it): {e}")
                logger.warning("Vector search features may not be available. To enable, install pgvector extension in PostgreSQL.")
            
            await self._create_tables()
            
            # Create users table
            async with self.async_engine.begin() as conn:
                await self._create_users_table(conn)
            
            # Run migrations
            await self._run_migrations()
            
            logger.info("Database service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            logger.error(f"Database URL: {settings.DATABASE_URL}")
            logger.error(f"Pool size: {settings.DB_POOL_MAX_SIZE}")
            raise
    
    async def _initialize_pgvector(self):
        """Initialize pgvector extension"""
        async with self.async_engine.begin() as conn:
            # Enable pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension enabled")
    
    async def _create_tables(self):
        """Create necessary tables for the application"""
        async with self.async_engine.begin() as conn:
            # Check if documents table exists (user provided table)
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'documents'
                )
            """))
            
            table_exists = result.scalar()
            
            if not table_exists:
                # Create documents table for vector storage (fallback)
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        content TEXT NOT NULL,
                        metadata JSONB,
                        embedding vector(1024),
                        collection_name VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create HNSW index for vector similarity search (최적화된 설정)
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                    ON documents USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 12, ef_construction = 100)
                """))
                
                # Create index for collection_name for faster filtering
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS documents_collection_name_idx 
                    ON documents (collection_name)
                """))
                
                # Create additional performance indexes
                await self._create_performance_indexes(conn)
                
                logger.info("Database tables created successfully")
            else:
                # Check if existing table has correct schema
                # Use a separate connection to avoid "transaction aborted" errors
                try:
                    result = await conn.execute(text("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'documents' AND column_name = 'id'
                    """))
                    id_column = result.fetchone()
                except Exception as e:
                    # If transaction is aborted, use a separate connection
                    logger.warning(f"Transaction error during schema check: {e}. Using separate connection.")
                    async with self.async_engine.connect() as separate_conn:
                        result = await separate_conn.execute(text("""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_name = 'documents' AND column_name = 'id'
                        """))
                        id_column = result.fetchone()
                        await separate_conn.commit()
                
                if id_column and id_column[1] != 'uuid':
                    logger.warning(f"Existing documents table has incorrect id column type: {id_column[1]}. Recreating table...")
                    # Drop and recreate table
                    await conn.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
                    await conn.execute(text("""
                        CREATE TABLE documents (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            content TEXT NOT NULL,
                            metadata JSONB,
                            embedding vector(1024),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    await conn.execute(text("""
                        CREATE INDEX documents_embedding_idx 
                        ON documents USING hnsw (embedding vector_cosine_ops)
                        WITH (m = 16, ef_construction = 200)
                    """))
                    logger.info("Documents table recreated with correct schema")
                else:
                    # Check embedding dimension
                    result = await conn.execute(text("""
                        SELECT udt_name, numeric_precision 
                        FROM information_schema.columns 
                        WHERE table_name = 'documents' AND column_name = 'embedding'
                    """))
                    embedding_column = result.fetchone()
                    
                    if embedding_column:
                        # Check if dimension needs to be updated
                        # First, check if there are any existing embeddings
                        try:
                            count_result = await conn.execute(text("""
                                SELECT COUNT(*) FROM documents WHERE embedding IS NOT NULL
                            """))
                            embedding_count = count_result.scalar()
                            
                            if embedding_count > 0:
                                # If there are existing embeddings, we need to drop the index first
                                logger.warning(f"Found {embedding_count} existing embeddings. Dropping index and updating dimension...")
                                try:
                                    # Drop the index first
                                    await conn.execute(text("DROP INDEX IF EXISTS documents_embedding_idx"))
                                    logger.info("Dropped existing embedding index")
                                except Exception as idx_error:
                                    logger.warning(f"Could not drop index: {idx_error}")
                                
                                # Delete existing embeddings (they're incompatible with new dimension)
                                logger.warning("Deleting existing embeddings with incompatible dimensions...")
                                await conn.execute(text("""
                                    UPDATE documents SET embedding = NULL WHERE embedding IS NOT NULL
                                """))
                                logger.info(f"Cleared {embedding_count} incompatible embeddings")
                            
                            # Now alter the column type
                            await conn.execute(text(f"""
                                ALTER TABLE documents 
                                ALTER COLUMN embedding TYPE vector({settings.OLLAMA_EMBEDDING_DIMENSION})
                            """))
                            logger.info(f"Updated embedding dimension to {settings.OLLAMA_EMBEDDING_DIMENSION}")
                            
                            # Recreate the index
                            try:
                                await conn.execute(text("""
                                    CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                                    ON documents USING hnsw (embedding vector_cosine_ops)
                                    WITH (m = 12, ef_construction = 100)
                                """))
                                logger.info(f"Recreated embedding index with {settings.OLLAMA_EMBEDDING_DIMENSION} dimensions")
                            except Exception as idx_error:
                                logger.warning(f"Could not recreate index: {idx_error}")
                                
                        except Exception as e:
                            error_msg = str(e).lower()
                            if "expected" in error_msg and "dimensions" in error_msg:
                                # This means the column is still 1024, try to fix it
                                logger.warning(f"Embedding dimension mismatch detected: {e}")
                                try:
                                    # Drop index and clear embeddings
                                    await conn.execute(text("DROP INDEX IF EXISTS documents_embedding_idx"))
                                    await conn.execute(text("UPDATE documents SET embedding = NULL WHERE embedding IS NOT NULL"))
                                    await conn.execute(text(f"ALTER TABLE documents ALTER COLUMN embedding TYPE vector({settings.OLLAMA_EMBEDDING_DIMENSION})"))
                                    await conn.execute(text("""
                                        CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                                        ON documents USING hnsw (embedding vector_cosine_ops)
                                        WITH (m = 12, ef_construction = 100)
                                    """))
                                    logger.info(f"Fixed embedding dimension to {settings.OLLAMA_EMBEDDING_DIMENSION}")
                                except Exception as fix_error:
                                    logger.error(f"Failed to fix embedding dimension: {fix_error}")
                            elif "cannot be cast" in error_msg or "dimension" in error_msg:
                                logger.warning(f"Could not alter embedding dimension: {e}. Trying to fix with data cleanup...")
                                try:
                                    # Last resort: drop and recreate the column
                                    await conn.execute(text("DROP INDEX IF EXISTS documents_embedding_idx"))
                                    await conn.execute(text("ALTER TABLE documents DROP COLUMN IF EXISTS embedding"))
                                    await conn.execute(text(f"ALTER TABLE documents ADD COLUMN embedding vector({settings.OLLAMA_EMBEDDING_DIMENSION})"))
                                    await conn.execute(text("""
                                        CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                                        ON documents USING hnsw (embedding vector_cosine_ops)
                                        WITH (m = 12, ef_construction = 100)
                                    """))
                                    logger.info(f"Recreated embedding column with {settings.OLLAMA_EMBEDDING_DIMENSION} dimensions")
                                except Exception as recreate_error:
                                    logger.error(f"Failed to recreate embedding column: {recreate_error}")
                            else:
                                logger.info(f"Embedding dimension check completed: {e}")
                    
                    # Check if collection_name column exists
                    # Use a separate connection to avoid transaction issues
                    try:
                        result = await conn.execute(text("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'documents' AND column_name = 'collection_name'
                        """))
                        collection_column = result.fetchone()
                    except Exception as e:
                        # If transaction is aborted, use a separate connection
                        logger.warning(f"Transaction error during collection_name check: {e}. Using separate connection.")
                        async with self.async_engine.connect() as separate_conn:
                            result = await separate_conn.execute(text("""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name = 'documents' AND column_name = 'collection_name'
                            """))
                            collection_column = result.fetchone()
                            await separate_conn.commit()
                    
                    if not collection_column:
                        # Add collection_name column to existing table
                        await conn.execute(text("""
                            ALTER TABLE documents 
                            ADD COLUMN collection_name VARCHAR(255)
                        """))
                        
                        # Create index for collection_name
                        await conn.execute(text("""
                            CREATE INDEX IF NOT EXISTS documents_collection_name_idx 
                            ON documents (collection_name)
                        """))
                        
                        # Create additional performance indexes
                        await self._create_performance_indexes(conn)
                        
                        logger.info("Added collection_name column to existing documents table")
                    else:
                        logger.info("Using existing documents table with correct schema")
                    
                    # Check if user_id column exists (for upload history tracking)
                    try:
                        result = await conn.execute(text("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'documents' AND column_name = 'user_id'
                        """))
                        user_id_column = result.fetchone()
                    except Exception as e:
                        logger.warning(f"Transaction error during user_id check: {e}. Using separate connection.")
                        async with self.async_engine.connect() as separate_conn:
                            result = await separate_conn.execute(text("""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name = 'documents' AND column_name = 'user_id'
                            """))
                            user_id_column = result.fetchone()
                            await separate_conn.commit()
                    
                    if not user_id_column:
                        # Add user_id column to existing table (NULL allowed for backward compatibility)
                        await conn.execute(text("""
                            ALTER TABLE documents 
                            ADD COLUMN user_id UUID
                        """))
                        
                        # Create index for user_id
                        await conn.execute(text("""
                            CREATE INDEX IF NOT EXISTS documents_user_id_idx 
                            ON documents (user_id)
                        """))
                        
                        logger.info("Added user_id column to existing documents table for upload history tracking")
                    else:
                        logger.info("user_id column already exists in documents table")
            
            # Create chat sessions table (use separate transaction to avoid conflicts)
            try:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        session_id VARCHAR(255) UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
            except Exception as e:
                logger.warning(f"Error creating chat_sessions table: {e}. Using separate connection.")
                async with self.async_engine.connect() as separate_conn:
                    await separate_conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS chat_sessions (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            session_id VARCHAR(255) UNIQUE NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    await separate_conn.commit()
            
            # Create chat messages table (use separate transaction to avoid conflicts)
            try:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        session_id VARCHAR(255) NOT NULL,
                        role VARCHAR(20) NOT NULL,
                        content TEXT NOT NULL,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
                    )
                """))
            except Exception as e:
                logger.warning(f"Error creating chat_messages table: {e}. Using separate connection.")
                async with self.async_engine.connect() as separate_conn:
                    await separate_conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS chat_messages (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            session_id VARCHAR(255) NOT NULL,
                            role VARCHAR(20) NOT NULL,
                            content TEXT NOT NULL,
                            metadata JSONB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
                        )
                    """))
                    await separate_conn.commit()
            
            logger.info("Database tables created successfully")
    
    async def _create_users_table(self, conn):
        """Create users table"""
        try:
            # Check if users table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                )
            """))
            
            table_exists = result.scalar()
            
            if not table_exists:
                # Create users table
                await conn.execute(text("""
                    CREATE TABLE users (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        username VARCHAR(255) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(50) NOT NULL DEFAULT 'user',
                        is_active BOOLEAN NOT NULL DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                """))
                
                # Create indexes for users table
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS users_username_idx ON users (username)
                """))
                
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS users_email_idx ON users (email)
                """))
                
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS users_role_idx ON users (role)
                """))
                
                logger.info("Users table created successfully")
            else:
                logger.info("Users table already exists")
                
        except Exception as e:
            logger.error(f"Failed to create users table: {e}")
            raise
    
    async def _create_performance_indexes(self, conn):
        """Create additional performance indexes for vector database optimization"""
        try:
            # 1. GIN index for JSONB metadata for faster filtering
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS documents_metadata_gin_idx 
                ON documents USING gin (metadata)
            """))
            
            # 2. Composite index for collection + embedding search (HNSW) - 최적화된 설정
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS documents_collection_embedding_idx 
                ON documents USING hnsw (embedding vector_cosine_ops)
                WITH (m = 12, ef_construction = 100)
            """))
            
            # 3. Index for created_at for time-based queries
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS documents_created_at_idx 
                ON documents (created_at DESC)
            """))
            
            # 4. Index for content length for filtering by document size
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS documents_content_length_idx 
                ON documents (length(content))
            """))
            
            # 5. Partial index for active documents (non-null collection_name)
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS documents_active_collection_idx 
                ON documents (collection_name, created_at DESC) 
                WHERE collection_name IS NOT NULL
            """))
            
            logger.info("Performance indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create some performance indexes: {e}")
            # Continue execution even if some indexes fail
    
    async def _run_migrations(self):
        """Run database migrations"""
        try:
            import os
            migration_dir = os.path.join(os.path.dirname(__file__), "..", "migrations")
            logger.info(f"Starting database migrations from directory: {migration_dir}")
            
            # List of migration files in order
            # Note: 000_fix_chat_sessions_schema.sql should run first to fix existing schema
            migration_files = [
                "000_fix_chat_sessions_schema.sql",  # Schema fix must run first
                "create_chat_sessions_table.sql",
                "update_chat_sessions_table.sql",
                "add_description_to_chat_sessions.sql",
                "add_user_id_to_collections.sql",
                "migrate_shared_collections.sql",
                "add_unique_constraints.sql"
            ]
            
            # Execute each migration file
            for migration_file in migration_files:
                migration_path = os.path.join(migration_dir, migration_file)
                logger.info(f"Processing migration file: {migration_file}")
                
                if os.path.exists(migration_path):
                    try:
                        with open(migration_path, 'r', encoding='utf-8') as f:
                            migration_sql = f.read()
                        
                        logger.info(f"Executing migration: {migration_file}")
                        # Split SQL into individual statements
                        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
                        
                        logger.info(f"Executing migration: {migration_file} ({len(statements)} statements)")
                        
                        # Execute each statement in its own transaction for schema changes
                        all_statements_succeeded = True
                        for i, statement in enumerate(statements, 1):
                            if statement.startswith('--') or not statement:
                                continue
                            
                            try:
                                # Execute statement in its own transaction
                                async with self.async_engine.begin() as conn:
                                    await conn.execute(text(statement))
                            except Exception as stmt_error:
                                # Log but continue with other statements
                                logger.debug(f"Statement {i} in {migration_file} skipped: {stmt_error}")
                                all_statements_succeeded = False
                        
                        if all_statements_succeeded:
                            logger.info(f"✅ Migration {migration_file} executed successfully")
                        else:
                            logger.info(f"✅ Migration {migration_file} completed (some statements already applied)")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Migration {migration_file} failed or already applied: {e}")
                        # Continue with other migrations
                else:
                    logger.warning(f"❌ Migration file {migration_file} not found at {migration_path}")
            
            logger.info("Database migrations completed")
                        
        except Exception as e:
            logger.error(f"❌ Failed to run migrations: {e}")
            # Don't raise exception - migrations are not critical for basic functionality
    
    def get_session(self):
        """Get database session context manager"""
        return self.async_session_factory()
    
    async def close(self):
        """Close database connections"""
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("Database connections closed")

# Global database service instance
db_service = DatabaseService()
