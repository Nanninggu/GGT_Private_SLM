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
            # Create async engine for PostgreSQL
            self.async_engine = create_async_engine(
                settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
                pool_size=settings.DB_POOL_MAX_SIZE,
                max_overflow=0,
                pool_pre_ping=True,
                pool_recycle=settings.DB_POOL_MAX_LIFETIME,
                echo=settings.LOG_LEVEL_APP == "DEBUG"
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
