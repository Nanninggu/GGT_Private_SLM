"""
Performance monitoring controller for vector database optimization
"""
import asyncio
from typing import Dict, Any

from backend.services.vector_service import vector_service
from backend.services.cache_service import cache_service
from backend.services.database_service import db_service


class PerformanceController:
    """Controller for performance monitoring and optimization"""

    def __init__(self):
        pass

    async def get_vector_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive vector database performance statistics"""
        try:
            stats = await vector_service.get_performance_stats()
            return {
                "success": True,
                "data": stats
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            stats = cache_service.get_cache_stats()
            return {
                "success": True,
                "data": stats
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def clear_cache(self) -> Dict[str, Any]:
        """Clear all caches"""
        try:
            cache_service.clear_cache()
            return {
                "success": True,
                "message": "Cache cleared successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def preload_embeddings(self, texts: list) -> Dict[str, Any]:
        """Preload common embeddings for better performance"""
        try:
            if not texts or not isinstance(texts, list):
                return {
                    "success": False,
                    "error": "Texts must be a non-empty list"
                }
            
            await vector_service.preload_common_embeddings(texts)
            return {
                "success": True,
                "message": f"Preloaded {len(texts)} embeddings successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        try:
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                return {
                    "success": False,
                    "error": "Database not initialized"
                }
            
            async with db_service.get_session() as session:
                # Get table statistics
                result = await session.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples,
                        last_vacuum,
                        last_autovacuum,
                        last_analyze,
                        last_autoanalyze
                    FROM pg_stat_user_tables 
                    WHERE tablename = 'documents'
                """)
                
                table_stats = result.fetchone()
                
                # Get index statistics
                index_result = await session.execute("""
                    SELECT 
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch,
                        idx_blks_read,
                        idx_blks_hit
                    FROM pg_stat_user_indexes 
                    WHERE tablename = 'documents'
                    ORDER BY idx_scan DESC
                """)
                
                index_stats = [dict(row._mapping) for row in index_result]
                
                # Get connection statistics
                conn_result = await session.execute("""
                    SELECT 
                        numbackends as active_connections,
                        xact_commit as committed_transactions,
                        xact_rollback as rolled_back_transactions,
                        blks_read as blocks_read,
                        blks_hit as blocks_hit,
                        tup_returned as tuples_returned,
                        tup_fetched as tuples_fetched,
                        tup_inserted as tuples_inserted,
                        tup_updated as tuples_updated,
                        tup_deleted as tuples_deleted
                    FROM pg_stat_database 
                    WHERE datname = current_database()
                """)
                
                db_stats = conn_result.fetchone()
                
                return {
                    "success": True,
                    "data": {
                        "table_stats": dict(table_stats._mapping) if table_stats else {},
                        "index_stats": index_stats,
                        "database_stats": dict(db_stats._mapping) if db_stats else {}
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def optimize_database(self) -> Dict[str, Any]:
        """Run database optimization tasks"""
        try:
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                return {
                    "success": False,
                    "error": "Database not initialized"
                }
            
            async with db_service.get_session() as session:
                # Update table statistics
                await session.execute("ANALYZE documents")
                
                # Vacuum if needed (only if there are dead tuples)
                result = await session.execute("""
                    SELECT n_dead_tup 
                    FROM pg_stat_user_tables 
                    WHERE tablename = 'documents'
                """)
                dead_tuples = result.scalar()
                
                if dead_tuples and dead_tuples > 1000:  # Only vacuum if significant dead tuples
                    await session.execute("VACUUM documents")
                    vacuum_message = f"Vacuumed documents table (removed {dead_tuples} dead tuples)"
                else:
                    vacuum_message = "No vacuum needed (dead tuples < 1000)"
                
                return {
                    "success": True,
                    "message": f"Database optimization completed. {vacuum_message}",
                    "dead_tuples": dead_tuples
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
