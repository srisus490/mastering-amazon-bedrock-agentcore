#!/usr/bin/env python3
"""Test new database features: views, aggregations, cache"""

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import (
    get_db_session,
    init_db,
    FileArrivalModel,
    DailyAggregates,
    TrendQueries,
    CacheManager,
    DatabaseMaintenance,
)
from src.core.logging import get_logger

logger = get_logger(__name__)


def test_daily_aggregates():
    """Test daily aggregation queries"""
    logger.info("Testing daily aggregates...")
    
    with get_db_session() as session:
        # Insert test data
        today = datetime.utcnow()
        for i in range(10):
            arrival = FileArrivalModel(
                source_system_id="SYS001",
                filename=f"test_file_{i}.txt",
                file_path=f"/data/test_{i}.txt",
                arrival_timestamp=today - timedelta(days=i),
                file_size_bytes=1024 * (i + 1),
                checksum=f"checksum_{i}",
            )
            session.add(arrival)
        session.commit()
        
        # Test daily counts
        start_date = (today - timedelta(days=9)).date()
        end_date = today.date()
        
        daily_counts = DailyAggregates.get_daily_counts(
            session, "SYS001", start_date, end_date
        )
        
        logger.info(f"✅ Daily aggregates: {len(daily_counts)} days")
        for day in daily_counts[:3]:
            logger.info(f"  {day['arrival_date']}: {day['file_count']} files, {day['total_size_bytes']} bytes")


def test_moving_averages():
    """Test moving average calculations"""
    logger.info("Testing moving averages...")
    
    with get_db_session() as session:
        today = datetime.utcnow()
        start_date = (today - timedelta(days=30)).date()
        end_date = today.date()
        
        moving_avgs = TrendQueries.get_moving_averages(
            session, "SYS001", start_date, end_date, window_days=7
        )
        
        logger.info(f"✅ Moving averages: {len(moving_avgs)} data points")
        if moving_avgs:
            latest = moving_avgs[-1]
            logger.info(f"  Latest: {latest['arrival_date']}, 7-day avg: {latest['moving_avg_7day']:.2f}")


def test_hourly_patterns():
    """Test hourly pattern analysis"""
    logger.info("Testing hourly patterns...")
    
    with get_db_session() as session:
        patterns = TrendQueries.get_hourly_patterns(session, "SYS001", days_back=30)
        
        logger.info(f"✅ Hourly patterns: {len(patterns)} patterns found")
        if patterns:
            for pattern in patterns[:3]:
                logger.info(f"  Day {pattern['day_of_week']}, Hour {pattern['hour_of_day']}: {pattern['file_count']} files")


def test_cache_manager():
    """Test dashboard cache functionality"""
    logger.info("Testing cache manager...")
    
    with get_db_session() as session:
        # Set cache value
        test_data = {"message": "Hello from cache!", "timestamp": datetime.utcnow().isoformat()}
        CacheManager.set_cached_value(
            session, "test_key", json.dumps(test_data), ttl_seconds=60
        )
        
        # Get cache value
        cached = CacheManager.get_cached_value(session, "test_key")
        if cached:
            data = json.loads(cached)
            logger.info(f"✅ Cache working: {data['message']}")
        
        # Test expired cache
        CacheManager.set_cached_value(
            session, "expired_key", json.dumps({"test": "data"}), ttl_seconds=-1
        )
        expired = CacheManager.get_cached_value(session, "expired_key")
        if expired is None:
            logger.info("✅ Expired cache correctly returns None")
        
        # Clean expired
        cleaned = CacheManager.clean_expired_cache(session)
        logger.info(f"✅ Cleaned {cleaned} expired cache entries")


def test_database_maintenance():
    """Test database maintenance functions"""
    logger.info("Testing database maintenance...")
    
    with get_db_session() as session:
        # Get database size
        size_info = DatabaseMaintenance.get_database_size(session)
        logger.info(f"✅ Database size: {size_info['total_size_mb']} MB")
        
        # Run ANALYZE
        DatabaseMaintenance.analyze_database(session)
        logger.info("✅ ANALYZE completed")


def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("Testing SQLite Database Features")
    logger.info("=" * 60)
    
    # Initialize database
    init_db()
    
    try:
        test_daily_aggregates()
        print()
        
        test_moving_averages()
        print()
        
        test_hourly_patterns()
        print()
        
        test_cache_manager()
        print()
        
        test_database_maintenance()
        print()
        
        logger.info("=" * 60)
        logger.info("✅ All tests passed!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
