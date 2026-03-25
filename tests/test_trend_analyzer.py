"""Tests for trend analyzer"""

from datetime import date, datetime, timedelta

import pytest

from src.analytics.trend_analyzer import (
    DailyCount,
    HourlyPattern,
    MovingAveragePoint,
    TrendAnalyzer,
)
from src.database.connection import create_test_engine, init_db
from src.database.models import Base, FileArrivalModel, SourceSystemModel


@pytest.fixture
def test_db_with_data():
    """Create a test database with sample file arrival data"""
    # Create engine and tables
    engine = create_test_engine()
    Base.metadata.create_all(bind=engine)
    
    # Initialize database connection
    init_db(database_url="sqlite:///:memory:")
    
    # Recreate tables on the initialized connection
    from src.database.connection import get_engine, get_db_session
    Base.metadata.create_all(bind=get_engine())
    
    # Create test source systems
    with get_db_session() as session:
        source_systems = [
            SourceSystemModel(
                id="SYS001",
                name="Test System 1",
                directory_path="/test/path1",
                is_active=True,
            ),
            SourceSystemModel(
                id="SYS002",
                name="Test System 2",
                directory_path="/test/path2",
                is_active=True,
            ),
        ]
        session.add_all(source_systems)
        session.commit()
        
        # Create sample file arrivals for the last 30 days
        base_date = datetime.now() - timedelta(days=30)
        file_arrivals = []
        
        for day in range(30):
            current_date = base_date + timedelta(days=day)
            
            # SYS001: 10-15 files per day
            for i in range(10 + (day % 6)):
                file_arrivals.append(
                    FileArrivalModel(
                        source_system_id="SYS001",
                        filename=f"file_{day}_{i}.txt",
                        file_path=f"/test/file_{day}_{i}.txt",
                        arrival_timestamp=current_date.replace(hour=9 + (i % 8)),
                        file_size_bytes=1024 * (i + 1),
                        checksum=f"checksum_{day}_{i}",
                    )
                )
            
            # SYS002: 5-8 files per day
            for i in range(5 + (day % 4)):
                file_arrivals.append(
                    FileArrivalModel(
                        source_system_id="SYS002",
                        filename=f"file_{day}_{i}.txt",
                        file_path=f"/test/file_{day}_{i}.txt",
                        arrival_timestamp=current_date.replace(hour=10 + (i % 6)),
                        file_size_bytes=2048 * (i + 1),
                        checksum=f"checksum_{day}_{i}",
                    )
                )
        
        session.add_all(file_arrivals)
        session.commit()
    
    yield engine
    
    # Cleanup
    from src.database.connection import close_db
    close_db()


class TestMovingAveragePoint:
    """Tests for MovingAveragePoint class"""
    
    def test_create_point(self):
        """Test creating a moving average point"""
        point = MovingAveragePoint(
            date=date(2024, 1, 15),
            file_count=10,
            moving_avg_7day=9.5,
            moving_avg_30day=10.2,
        )
        
        assert point.date == date(2024, 1, 15)
        assert point.file_count == 10
        assert point.moving_avg_7day == 9.5
        assert point.moving_avg_30day == 10.2
    
    def test_to_dict(self):
        """Test converting to dictionary"""
        point = MovingAveragePoint(
            date=date(2024, 1, 15),
            file_count=10,
            moving_avg_7day=9.5,
            moving_avg_30day=10.2,
        )
        
        result = point.to_dict()
        assert result["date"] == "2024-01-15"
        assert result["file_count"] == 10
        assert result["moving_avg_7day"] == 9.5
        assert result["moving_avg_30day"] == 10.2


class TestDailyCount:
    """Tests for DailyCount class"""
    
    def test_create_count(self):
        """Test creating a daily count"""
        count = DailyCount(
            arrival_date=date(2024, 1, 15),
            file_count=10,
            total_size_bytes=10240,
        )
        
        assert count.arrival_date == date(2024, 1, 15)
        assert count.file_count == 10
        assert count.total_size_bytes == 10240
    
    def test_to_dict(self):
        """Test converting to dictionary"""
        count = DailyCount(
            arrival_date=date(2024, 1, 15),
            file_count=10,
            total_size_bytes=10240,
            first_arrival=datetime(2024, 1, 15, 9, 0, 0),
            last_arrival=datetime(2024, 1, 15, 17, 0, 0),
        )
        
        result = count.to_dict()
        assert result["arrival_date"] == "2024-01-15"
        assert result["file_count"] == 10
        assert result["total_size_bytes"] == 10240
        assert "2024-01-15" in result["first_arrival"]
        assert "2024-01-15" in result["last_arrival"]


class TestHourlyPattern:
    """Tests for HourlyPattern class"""
    
    def test_create_pattern(self):
        """Test creating an hourly pattern"""
        pattern = HourlyPattern(
            day_of_week=1,
            hour_of_day=9,
            file_count=50,
            avg_size_bytes=2048.5,
        )
        
        assert pattern.day_of_week == 1
        assert pattern.hour_of_day == 9
        assert pattern.file_count == 50
        assert pattern.avg_size_bytes == 2048.5
    
    def test_to_dict(self):
        """Test converting to dictionary"""
        pattern = HourlyPattern(
            day_of_week=1,
            hour_of_day=9,
            file_count=50,
            avg_size_bytes=2048.5,
        )
        
        result = pattern.to_dict()
        assert result["day_of_week"] == 1
        assert result["hour_of_day"] == 9
        assert result["file_count"] == 50
        assert result["avg_size_bytes"] == 2048.5


class TestTrendAnalyzer:
    """Tests for TrendAnalyzer class"""
    
    def test_create_analyzer(self):
        """Test creating a trend analyzer"""
        analyzer = TrendAnalyzer()
        assert analyzer is not None
    
    def test_calculate_moving_average(self, test_db_with_data):
        """Test calculating moving average"""
        analyzer = TrendAnalyzer()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        points = analyzer.calculate_moving_average(
            source_system_id="SYS001",
            window_days=7,
            end_date=end_date,
            lookback_days=30,
        )
        
        # Should have data points
        assert len(points) > 0
        
        # Check point structure
        for point in points:
            assert isinstance(point, MovingAveragePoint)
            assert point.file_count >= 0
            assert point.moving_avg_7day >= 0
    
    def test_get_daily_counts(self, test_db_with_data):
        """Test getting daily counts"""
        analyzer = TrendAnalyzer()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        counts = analyzer.get_daily_counts(
            source_system_id="SYS001",
            start_date=start_date,
            end_date=end_date,
        )
        
        # Should have 30 days of data
        assert len(counts) > 0
        assert len(counts) <= 30
        
        # Check count structure
        for count in counts:
            assert isinstance(count, DailyCount)
            assert count.file_count > 0
            assert count.total_size_bytes > 0
    
    def test_get_weekly_aggregation(self, test_db_with_data):
        """Test getting weekly aggregations"""
        analyzer = TrendAnalyzer()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        weekly = analyzer.get_weekly_aggregation(
            source_system_id="SYS001",
            start_date=start_date,
            end_date=end_date,
        )
        
        # Should have ~4 weeks of data
        assert len(weekly) > 0
        assert len(weekly) <= 5
        
        # Check structure
        for week in weekly:
            assert "year" in week
            assert "week" in week
            assert "file_count" in week
            assert "total_size_bytes" in week
            assert week["file_count"] > 0
    
    def test_get_monthly_aggregation(self, test_db_with_data):
        """Test getting monthly aggregations"""
        analyzer = TrendAnalyzer()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=60)
        
        monthly = analyzer.get_monthly_aggregation(
            source_system_id="SYS001",
            start_date=start_date,
            end_date=end_date,
        )
        
        # Should have 1-2 months of data
        assert len(monthly) > 0
        assert len(monthly) <= 3
        
        # Check structure
        for month in monthly:
            assert "year" in month
            assert "month" in month
            assert "file_count" in month
            assert "total_size_bytes" in month
            assert month["file_count"] > 0
    
    def test_get_hourly_patterns(self, test_db_with_data):
        """Test getting hourly patterns"""
        analyzer = TrendAnalyzer()
        
        patterns = analyzer.get_hourly_patterns(
            source_system_id="SYS001",
            days_back=30,
        )
        
        # Should have patterns
        assert len(patterns) > 0
        
        # Check pattern structure
        for pattern in patterns:
            assert isinstance(pattern, HourlyPattern)
            assert 0 <= pattern.day_of_week <= 6
            assert 0 <= pattern.hour_of_day <= 23
            assert pattern.file_count > 0
    
    def test_get_all_systems_summary(self, test_db_with_data):
        """Test getting summary for all systems"""
        analyzer = TrendAnalyzer()
        
        summary = analyzer.get_all_systems_summary(
            target_date=date.today(),
        )
        
        # Should have data for both systems (if files exist today)
        # Or empty if no files today
        assert isinstance(summary, list)
        
        # If we have data, check structure
        for item in summary:
            assert "source_system_id" in item
            assert "file_count" in item
            assert "total_size_bytes" in item
    
    def test_multiple_source_systems(self, test_db_with_data):
        """Test analyzing multiple source systems"""
        analyzer = TrendAnalyzer()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Get counts for both systems
        counts_sys1 = analyzer.get_daily_counts("SYS001", start_date, end_date)
        counts_sys2 = analyzer.get_daily_counts("SYS002", start_date, end_date)
        
        # Both should have data
        assert len(counts_sys1) > 0
        assert len(counts_sys2) > 0
        
        # SYS001 should have more files (10-15 vs 5-8 per day)
        total_sys1 = sum(c.file_count for c in counts_sys1)
        total_sys2 = sum(c.file_count for c in counts_sys2)
        assert total_sys1 > total_sys2
