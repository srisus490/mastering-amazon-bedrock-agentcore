# Migration Guide: Simplifying to PostgreSQL-Only Architecture

## Overview

This guide explains how to migrate from the complex multi-database architecture to a simplified, cost-effective PostgreSQL-only architecture.

## What's Changing

### Services to Remove
1. **InfluxDB** → Use PostgreSQL with proper indexing for time-series data
2. **Redis** → Use PostgreSQL cache table + simple in-memory caching
3. **RabbitMQ** → Direct writes to PostgreSQL (no message queue)

### Code Changes Required

## 1. Update Dependencies

### Remove from `pyproject.toml`:
```toml
# REMOVE THESE
influxdb-client = "^1.38.0"
redis = "^5.0.0"
pika = "^1.3.2"
```

### Keep these:
```toml
# KEEP THESE
sqlalchemy = "^2.0.23"
psycopg2-binary = "^2.9.9"
watchdog = "^3.0.0"
fastapi = "^0.104.1"
```

## 2. Update Docker Compose

### Old `docker-compose.yml` (Complex):
```yaml
services:
  postgres:
    # ...
  influxdb:
    # REMOVE THIS
  redis:
    # REMOVE THIS
  rabbitmq:
    # REMOVE THIS
```

### New `docker-compose.yml` (Simplified):
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: file_monitoring
      POSTGRES_USER: monitoring_user
      POSTGRES_PASSWORD: monitoring_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/init-scripts/postgres:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U monitoring_user"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## 3. Update Database Schema

### Add to PostgreSQL:

```sql
-- Materialized view for dashboard (replaces InfluxDB queries)
CREATE MATERIALIZED VIEW daily_file_counts AS
SELECT 
    source_system_id,
    DATE(arrival_timestamp) as arrival_date,
    COUNT(*) as file_count,
    SUM(file_size_bytes) as total_size_bytes,
    MIN(arrival_timestamp) as first_arrival,
    MAX(arrival_timestamp) as last_arrival
FROM file_arrivals
GROUP BY source_system_id, DATE(arrival_timestamp);

CREATE INDEX idx_daily_counts_source_date ON daily_file_counts(source_system_id, arrival_date);

-- Cache table (replaces Redis)
CREATE TABLE dashboard_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_value JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cache_expires ON dashboard_cache(expires_at);

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_daily_counts() RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_file_counts;
END;
$$ LANGUAGE plpgsql;

-- Function to clean expired cache
CREATE OR REPLACE FUNCTION clean_expired_cache() RETURNS void AS $$
BEGIN
    DELETE FROM dashboard_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;
```

## 4. Refactor File Monitor Service

### Old Code (with RabbitMQ):
```python
# src/monitor/watcher.py
class DirectoryWatcher:
    def on_file_created(self, file_path: str):
        event = self._create_file_arrival_event(file_path)
        # Publish to RabbitMQ
        self.emitter.publish(event)  # ❌ REMOVE THIS
```

### New Code (direct PostgreSQL):
```python
# src/monitor/watcher.py
from src.database.connection import get_db_session
from src.database.models import FileArrivalModel

class DirectoryWatcher:
    def on_file_created(self, file_path: str):
        event = self._create_file_arrival_event(file_path)
        
        # Write directly to PostgreSQL
        try:
            with get_db_session() as session:
                arrival_model = FileArrivalModel(
                    source_system_id=event.source_system_id,
                    filename=event.filename,
                    file_path=event.file_path,
                    arrival_timestamp=event.arrival_timestamp,
                    file_size_bytes=event.file_size_bytes,
                    checksum=event.checksum,
                )
                session.add(arrival_model)
                session.commit()
                
                logger.info(
                    "File arrival recorded",
                    source_system_id=event.source_system_id,
                    filename=event.filename,
                )
        except Exception as e:
            logger.error(
                "Failed to record file arrival",
                error=str(e),
                filename=event.filename,
            )
```

## 5. Remove Event Processor Service

### Files to Delete:
- `src/processor/consumer.py` (RabbitMQ consumer)
- `src/processor/recorders.py` (InfluxDB, Redis writers)
- `src/processor/processor.py` (Event coordinator)
- `tests/test_processor.py`

### Why?
With direct writes to PostgreSQL, we don't need a separate event processor service.

## 6. Create Simplified Trend Analyzer

### New File: `src/analytics/trends.py`

```python
"""Trend analyzer using PostgreSQL"""

from datetime import date, timedelta
from typing import List
from dataclasses import dataclass

from sqlalchemy import text
from src.database.connection import get_db_session
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MovingAveragePoint:
    date: date
    file_count: int
    moving_avg_7day: float
    moving_avg_30day: float


class TrendAnalyzer:
    """Calculate trends using PostgreSQL window functions"""
    
    def get_moving_averages(
        self,
        source_system_id: str,
        start_date: date,
        end_date: date,
    ) -> List[MovingAveragePoint]:
        """
        Calculate moving averages using PostgreSQL window functions.
        
        This replaces InfluxDB queries with pure SQL.
        """
        query = text("""
            SELECT 
                arrival_date,
                file_count,
                AVG(file_count) OVER (
                    ORDER BY arrival_date 
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) as moving_avg_7day,
                AVG(file_count) OVER (
                    ORDER BY arrival_date 
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) as moving_avg_30day
            FROM daily_file_counts
            WHERE source_system_id = :source_system_id
              AND arrival_date BETWEEN :start_date AND :end_date
            ORDER BY arrival_date
        """)
        
        with get_db_session() as session:
            result = session.execute(
                query,
                {
                    "source_system_id": source_system_id,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )
            
            points = []
            for row in result:
                point = MovingAveragePoint(
                    date=row.arrival_date,
                    file_count=row.file_count,
                    moving_avg_7day=float(row.moving_avg_7day or 0),
                    moving_avg_30day=float(row.moving_avg_30day or 0),
                )
                points.append(point)
            
            return points
    
    def get_daily_counts(
        self,
        source_system_id: str,
        start_date: date,
        end_date: date,
    ) -> List[dict]:
        """Get daily file counts from materialized view"""
        query = text("""
            SELECT 
                arrival_date,
                file_count,
                total_size_bytes,
                first_arrival,
                last_arrival
            FROM daily_file_counts
            WHERE source_system_id = :source_system_id
              AND arrival_date BETWEEN :start_date AND :end_date
            ORDER BY arrival_date
        """)
        
        with get_db_session() as session:
            result = session.execute(
                query,
                {
                    "source_system_id": source_system_id,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )
            
            return [dict(row._mapping) for row in result]
    
    def refresh_materialized_view(self) -> None:
        """Refresh the daily counts materialized view"""
        with get_db_session() as session:
            session.execute(text("SELECT refresh_daily_counts()"))
            session.commit()
            logger.info("Refreshed daily_file_counts materialized view")
```

## 7. Update Configuration

### Old `.env`:
```env
# REMOVE THESE
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token
INFLUXDB_ORG=monitoring
INFLUXDB_BUCKET=file_arrivals

REDIS_URL=redis://localhost:6379/0

RABBITMQ_URL=amqp://guest:guest@localhost:5672/
RABBITMQ_QUEUE=file-arrivals
```

### New `.env` (Simplified):
```env
# PostgreSQL only
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=file_monitoring
DATABASE_USER=monitoring_user
DATABASE_PASSWORD=monitoring_pass
```

### Update `src/core/config.py`:

```python
# REMOVE THESE CLASSES
class InfluxDBConfig:  # ❌ DELETE
class RedisConfig:     # ❌ DELETE
class RabbitMQConfig:  # ❌ DELETE

# KEEP ONLY
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "file_monitoring"
    user: str = "monitoring_user"
    password: str = "monitoring_pass"
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
```

## 8. Update Tests

### Remove Test Files:
- `tests/test_timeseries.py` (InfluxDB tests)
- `tests/test_processor.py` (Event processor tests)

### Update Integration Tests:
```python
# tests/test_integration.py
def test_file_detection_to_database():
    """Test file detection writes directly to PostgreSQL"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create watcher
        watcher = DirectoryWatcher(
            directory_path=temp_dir,
            source_system_id="TEST_SYS",
        )
        
        watcher.start_monitoring()
        time.sleep(0.5)
        
        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Test content")
        
        time.sleep(1.0)
        watcher.stop_monitoring()
        
        # Verify in PostgreSQL
        with get_db_session() as session:
            arrival = session.query(FileArrivalModel).filter_by(
                source_system_id="TEST_SYS",
                filename="test.txt"
            ).first()
            
            assert arrival is not None
            assert arrival.file_size_bytes > 0
```

## 9. Performance Optimization

### Add Indexes:
```sql
-- Indexes for time-series queries
CREATE INDEX idx_arrivals_timestamp ON file_arrivals(arrival_timestamp);
CREATE INDEX idx_arrivals_source_time ON file_arrivals(source_system_id, arrival_timestamp);
CREATE INDEX idx_arrivals_date ON file_arrivals(DATE(arrival_timestamp));
```

### Optional - Table Partitioning:
```sql
-- Partition by month for better performance
CREATE TABLE file_arrivals_2024_01 PARTITION OF file_arrivals
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE file_arrivals_2024_02 PARTITION OF file_arrivals
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- etc.
```

### Connection Pooling:
```python
# src/database/connection.py
from sqlalchemy import create_engine

engine = create_engine(
    settings.database.url,
    pool_size=10,        # 10 connections in pool
    max_overflow=20,     # Up to 30 total connections
    pool_pre_ping=True,  # Verify connections before use
)
```

## 10. Deployment Steps

1. **Backup existing data** (if migrating from old system)
2. **Stop old services** (InfluxDB, Redis, RabbitMQ)
3. **Update code** (remove dependencies, update imports)
4. **Run database migrations** (add materialized views, cache table)
5. **Update Docker Compose** (remove unnecessary services)
6. **Deploy new code**
7. **Test thoroughly**
8. **Monitor performance**

## Cost Savings Summary

### Before (Complex):
- PostgreSQL RDS: $50-150/month
- InfluxDB Cloud: $50-200/month
- Redis ElastiCache: $30-100/month
- RabbitMQ Amazon MQ: $50-150/month
- **Total: $180-600/month**

### After (Simplified):
- PostgreSQL RDS: $50-150/month
- **Total: $50-150/month**

### Savings: $130-450/month (70-90% reduction)

## Benefits

✅ **Lower costs** - 70-90% reduction in infrastructure costs
✅ **Simpler architecture** - One database instead of four services
✅ **Easier maintenance** - Fewer components to manage
✅ **Better reliability** - Fewer failure points
✅ **Faster development** - Less complexity
✅ **Same functionality** - All features preserved

## Questions?

If you have questions about the migration, check:
1. `design-simplified.md` - Simplified architecture design
2. `tasks-simplified.md` - New implementation plan
3. This guide - Migration steps

**PostgreSQL is powerful enough to handle everything!**
