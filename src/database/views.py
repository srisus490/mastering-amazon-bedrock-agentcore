"""Database views and aggregation queries for SQLite"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.database.models import FileArrivalModel, SLAScoreModel, DashboardCacheModel

logger = get_logger(__name__)


class DailyAggregates:
    """Helper class for daily file count aggregations"""
    
    @staticmethod
    def get_daily_counts(
        session: Session,
        source_system_id: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict]:
        """
        Get daily file counts for a source system.
        
        This replaces the materialized view approach - SQLite doesn't support
        materialized views, but this query is fast enough with proper indexes.
        
        Args:
            session: Database session
            source_system_id: Source system ID
            start_date: Start date
            end_date: End date
            
        Returns:
            List of daily aggregates with date, count, total_size, etc.
        """
        query = text("""
            SELECT 
                DATE(arrival_timestamp) as arrival_date,
                COUNT(*) as file_count,
                SUM(file_size_bytes) as total_size_bytes,
                MIN(arrival_timestamp) as first_arrival,
                MAX(arrival_timestamp) as last_arrival
            FROM file_arrivals
            WHERE source_system_id = :source_system_id
              AND DATE(arrival_timestamp) BETWEEN :start_date AND :end_date
            GROUP BY DATE(arrival_timestamp)
            ORDER BY arrival_date
        """)
        
        result = session.execute(
            query,
            {
                "source_system_id": source_system_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )
        
        return [
            {
                "arrival_date": row.arrival_date,
                "file_count": row.file_count,
                "total_size_bytes": row.total_size_bytes,
                "first_arrival": row.first_arrival,
                "last_arrival": row.last_arrival,
            }
            for row in result
        ]
    
    @staticmethod
    def get_all_systems_daily_counts(
        session: Session,
        target_date: date,
    ) -> List[Dict]:
        """
        Get daily file counts for all source systems on a specific date.
        
        Args:
            session: Database session
            target_date: Target date
            
        Returns:
            List of aggregates by source system
        """
        query = text("""
            SELECT 
                source_system_id,
                COUNT(*) as file_count,
                SUM(file_size_bytes) as total_size_bytes,
                MIN(arrival_timestamp) as first_arrival,
                MAX(arrival_timestamp) as last_arrival
            FROM file_arrivals
            WHERE DATE(arrival_timestamp) = :target_date
            GROUP BY source_system_id
            ORDER BY source_system_id
        """)
        
        result = session.execute(query, {"target_date": target_date.isoformat()})
        
        return [
            {
                "source_system_id": row.source_system_id,
                "file_count": row.file_count,
                "total_size_bytes": row.total_size_bytes,
                "first_arrival": row.first_arrival,
                "last_arrival": row.last_arrival,
            }
            for row in result
        ]


class TrendQueries:
    """Helper class for trend analysis queries using window functions"""
    
    @staticmethod
    def get_moving_averages(
        session: Session,
        source_system_id: str,
        start_date: date,
        end_date: date,
        window_days: int = 7,
    ) -> List[Dict]:
        """
        Calculate moving averages using SQLite window functions.
        
        Args:
            session: Database session
            source_system_id: Source system ID
            start_date: Start date
            end_date: End date
            window_days: Window size for moving average (default 7)
            
        Returns:
            List with date, file_count, and moving averages
        """
        # SQLite window functions work great for this!
        query = text(f"""
            WITH daily_counts AS (
                SELECT 
                    DATE(arrival_timestamp) as arrival_date,
                    COUNT(*) as file_count
                FROM file_arrivals
                WHERE source_system_id = :source_system_id
                  AND DATE(arrival_timestamp) BETWEEN :start_date AND :end_date
                GROUP BY DATE(arrival_timestamp)
            )
            SELECT 
                arrival_date,
                file_count,
                AVG(file_count) OVER (
                    ORDER BY arrival_date 
                    ROWS BETWEEN {window_days - 1} PRECEDING AND CURRENT ROW
                ) as moving_avg_{window_days}day,
                AVG(file_count) OVER (
                    ORDER BY arrival_date 
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) as moving_avg_30day
            FROM daily_counts
            ORDER BY arrival_date
        """)
        
        result = session.execute(
            query,
            {
                "source_system_id": source_system_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )
        
        return [
            {
                "arrival_date": row.arrival_date,
                "file_count": row.file_count,
                f"moving_avg_{window_days}day": float(getattr(row, f"moving_avg_{window_days}day") or 0),
                "moving_avg_30day": float(row.moving_avg_30day or 0),
            }
            for row in result
        ]
    
    @staticmethod
    def get_hourly_patterns(
        session: Session,
        source_system_id: str,
        days_back: int = 90,
    ) -> List[Dict]:
        """
        Get hourly file arrival patterns (day of week + hour).
        
        Args:
            session: Database session
            source_system_id: Source system ID
            days_back: Number of days to look back
            
        Returns:
            List with day_of_week, hour, file_count, avg_size
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # SQLite uses strftime for date extraction
        query = text("""
            SELECT 
                CAST(strftime('%w', arrival_timestamp) AS INTEGER) as day_of_week,
                CAST(strftime('%H', arrival_timestamp) AS INTEGER) as hour_of_day,
                COUNT(*) as file_count,
                AVG(file_size_bytes) as avg_size_bytes
            FROM file_arrivals
            WHERE source_system_id = :source_system_id
              AND arrival_timestamp >= :cutoff_date
            GROUP BY day_of_week, hour_of_day
            ORDER BY day_of_week, hour_of_day
        """)
        
        result = session.execute(
            query,
            {
                "source_system_id": source_system_id,
                "cutoff_date": cutoff_date.isoformat(),
            }
        )
        
        return [
            {
                "day_of_week": row.day_of_week,
                "hour_of_day": row.hour_of_day,
                "file_count": row.file_count,
                "avg_size_bytes": float(row.avg_size_bytes or 0),
            }
            for row in result
        ]


class CacheManager:
    """Helper class for managing dashboard cache"""
    
    @staticmethod
    def get_cached_value(session: Session, cache_key: str) -> Optional[str]:
        """
        Get cached value if not expired.
        
        Args:
            session: Database session
            cache_key: Cache key
            
        Returns:
            Cached value (JSON string) or None if expired/not found
        """
        cache_entry = session.query(DashboardCacheModel).filter(
            DashboardCacheModel.cache_key == cache_key,
            DashboardCacheModel.expires_at > datetime.utcnow(),
        ).first()
        
        if cache_entry:
            logger.debug("Cache hit", cache_key=cache_key)
            return cache_entry.cache_value
        
        logger.debug("Cache miss", cache_key=cache_key)
        return None
    
    @staticmethod
    def set_cached_value(
        session: Session,
        cache_key: str,
        cache_value: str,
        ttl_seconds: int = 300,
    ) -> None:
        """
        Set cached value with TTL.
        
        Args:
            session: Database session
            cache_key: Cache key
            cache_value: Cache value (JSON string)
            ttl_seconds: Time to live in seconds (default 5 minutes)
        """
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        # Upsert: delete if exists, then insert
        session.query(DashboardCacheModel).filter(
            DashboardCacheModel.cache_key == cache_key
        ).delete()
        
        cache_entry = DashboardCacheModel(
            cache_key=cache_key,
            cache_value=cache_value,
            expires_at=expires_at,
        )
        session.add(cache_entry)
        session.commit()
        
        logger.debug("Cache set", cache_key=cache_key, ttl_seconds=ttl_seconds)
    
    @staticmethod
    def clean_expired_cache(session: Session) -> int:
        """
        Clean expired cache entries.
        
        Args:
            session: Database session
            
        Returns:
            Number of entries deleted
        """
        deleted_count = session.query(DashboardCacheModel).filter(
            DashboardCacheModel.expires_at < datetime.utcnow()
        ).delete()
        
        session.commit()
        
        if deleted_count > 0:
            logger.info("Cleaned expired cache entries", count=deleted_count)
        
        return deleted_count


class DatabaseMaintenance:
    """Helper class for database maintenance tasks"""
    
    @staticmethod
    def vacuum_database(session: Session) -> None:
        """
        Run VACUUM to reclaim space and optimize database.
        
        Should be run periodically (e.g., weekly).
        """
        logger.info("Running VACUUM on database...")
        session.execute(text("VACUUM"))
        logger.info("VACUUM completed")
    
    @staticmethod
    def analyze_database(session: Session) -> None:
        """
        Run ANALYZE to update query planner statistics.
        
        Should be run after bulk inserts or periodically.
        """
        logger.info("Running ANALYZE on database...")
        session.execute(text("ANALYZE"))
        logger.info("ANALYZE completed")
    
    @staticmethod
    def get_database_size(session: Session) -> Dict[str, int]:
        """
        Get database size information.
        
        Returns:
            Dict with page_count, page_size, and total_size_bytes
        """
        result = session.execute(text("PRAGMA page_count")).scalar()
        page_count = result or 0
        
        result = session.execute(text("PRAGMA page_size")).scalar()
        page_size = result or 0
        
        total_size = page_count * page_size
        
        return {
            "page_count": page_count,
            "page_size": page_size,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
