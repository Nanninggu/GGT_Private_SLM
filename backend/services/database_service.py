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

from config.settings import settings

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
            await self._initialize_pgvector()
            await self._create_tables()
            
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
                
                # Create HNSW index for vector similarity search
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                    ON documents USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 200)
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
                result = await conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'documents' AND column_name = 'id'
                """))
                id_column = result.fetchone()
                
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
                    # Check if collection_name column exists
                    result = await conn.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'documents' AND column_name = 'collection_name'
                    """))
                    collection_column = result.fetchone()
                    
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
            
            # Create chat sessions table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create chat messages table
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
            
            logger.info("Database tables created successfully")
    
    async def _create_performance_indexes(self, conn):
        """Create additional performance indexes for vector database optimization"""
        try:
            # 1. GIN index for JSONB metadata for faster filtering
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS documents_metadata_gin_idx 
                ON documents USING gin (metadata)
            """))
            
            # 2. Composite index for collection + embedding search (HNSW)
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS documents_collection_embedding_idx 
                ON documents USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 200)
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
