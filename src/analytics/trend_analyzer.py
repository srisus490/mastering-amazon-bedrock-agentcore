"""Trend analyzer for file arrival patterns using SQLite"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from src.core.logging import get_logger
from src.database.connection import get_db_session
from src.database.views import DailyAggregates, TrendQueries

logger = get_logger(__name__)


class MovingAveragePoint:
    """Data point for moving average calculations"""
    
    def __init__(
        self,
        date: date,
        file_count: int,
        moving_avg_7day: float,
        moving_avg_30day: float,
    ):
        self.date = date
        self.file_count = file_count
        self.moving_avg_7day = moving_avg_7day
        self.moving_avg_30day = moving_avg_30day
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "date": self.date.isoformat(),
            "file_count": self.file_count,
            "moving_avg_7day": round(self.moving_avg_7day, 2),
            "moving_avg_30day": round(self.moving_avg_30day, 2),
        }


class DailyCount:
    """Daily file count data"""
    
    def __init__(
        self,
        arrival_date: date,
        file_count: int,
        total_size_bytes: int,
        first_arrival: Optional[datetime] = None,
        last_arrival: Optional[datetime] = None,
    ):
        self.arrival_date = arrival_date
        self.file_count = file_count
        self.total_size_bytes = total_size_bytes
        self.first_arrival = first_arrival
        self.last_arrival = last_arrival
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "arrival_date": self.arrival_date.isoformat(),
            "file_count": self.file_count,
            "total_size_bytes": self.total_size_bytes,
            "first_arrival": self.first_arrival.isoformat() if self.first_arrival else None,
            "last_arrival": self.last_arrival.isoformat() if self.last_arrival else None,
        }


class HourlyPattern:
    """Hourly file arrival pattern"""
    
    def __init__(
        self,
        day_of_week: int,
        hour_of_day: int,
        file_count: int,
        avg_size_bytes: float,
    ):
        self.day_of_week = day_of_week
        self.hour_of_day = hour_of_day
        self.file_count = file_count
        self.avg_size_bytes = avg_size_bytes
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "day_of_week": self.day_of_week,
            "hour_of_day": self.hour_of_day,
            "file_count": self.file_count,
            "avg_size_bytes": round(self.avg_size_bytes, 2),
        }


class TrendAnalyzer:
    """
    Analyzes file arrival trends using SQLite window functions.
    
    Provides moving averages, daily/weekly/monthly aggregations,
    and pattern detection without needing InfluxDB.
    """
    
    def __init__(self):
        """Initialize trend analyzer"""
        logger.info("TrendAnalyzer initialized")
    
    def calculate_moving_average(
        self,
        source_system_id: str,
        window_days: int = 7,
        end_date: Optional[date] = None,
        lookback_days: int = 90,
    ) -> List[MovingAveragePoint]:
        """
        Calculate moving average for file arrivals.
        
        Args:
            source_system_id: Source system ID
            window_days: Window size for moving average (default 7)
            end_date: End date (default today)
            lookback_days: Number of days to look back (default 90)
            
        Returns:
            List of MovingAveragePoint objects
        """
        if end_date is None:
            end_date = date.today()
        
        start_date = end_date - timedelta(days=lookback_days)
        
        logger.info(
            "Calculating moving average",
            source_system_id=source_system_id,
            window_days=window_days,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        
        try:
            with get_db_session() as session:
                results = TrendQueries.get_moving_averages(
                    session=session,
                    source_system_id=source_system_id,
                    start_date=start_date,
                    end_date=end_date,
                    window_days=window_days,
                )
                
                points = [
                    MovingAveragePoint(
                        date=datetime.fromisoformat(row["arrival_date"]).date(),
                        file_count=row["file_count"],
                        moving_avg_7day=row.get(f"moving_avg_{window_days}day", 0.0),
                        moving_avg_30day=row.get("moving_avg_30day", 0.0),
                    )
                    for row in results
                ]
                
                logger.info(
                    "Moving average calculated",
                    source_system_id=source_system_id,
                    data_points=len(points),
                )
                
                return points
                
        except Exception as e:
            logger.error(
                "Failed to calculate moving average",
                source_system_id=source_system_id,
                error=str(e),
            )
            raise
    
    def get_daily_counts(
        self,
        source_system_id: str,
        start_date: date,
        end_date: date,
    ) -> List[DailyCount]:
        """
        Get daily file counts for a source system.
        
        Args:
            source_system_id: Source system ID
            start_date: Start date
            end_date: End date
            
        Returns:
            List of DailyCount objects
        """
        logger.info(
            "Getting daily counts",
            source_system_id=source_system_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        
        try:
            with get_db_session() as session:
                results = DailyAggregates.get_daily_counts(
                    session=session,
                    source_system_id=source_system_id,
                    start_date=start_date,
                    end_date=end_date,
                )
                
                counts = [
                    DailyCount(
                        arrival_date=datetime.fromisoformat(row["arrival_date"]).date(),
                        file_count=row["file_count"],
                        total_size_bytes=row["total_size_bytes"],
                        first_arrival=datetime.fromisoformat(row["first_arrival"]) if row["first_arrival"] else None,
                        last_arrival=datetime.fromisoformat(row["last_arrival"]) if row["last_arrival"] else None,
                    )
                    for row in results
                ]
                
                logger.info(
                    "Daily counts retrieved",
                    source_system_id=source_system_id,
                    count=len(counts),
                )
                
                return counts
                
        except Exception as e:
            logger.error(
                "Failed to get daily counts",
                source_system_id=source_system_id,
                error=str(e),
            )
            raise
    
    def get_weekly_aggregation(
        self,
        source_system_id: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict]:
        """
        Get weekly aggregations (sum by week).
        
        Args:
            source_system_id: Source system ID
            start_date: Start date
            end_date: End date
            
        Returns:
            List of weekly aggregates
        """
        daily_counts = self.get_daily_counts(source_system_id, start_date, end_date)
        
        # Group by week
        weekly_data = {}
        for count in daily_counts:
            # Get ISO week number
            week_key = count.arrival_date.isocalendar()[:2]  # (year, week)
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "year": week_key[0],
                    "week": week_key[1],
                    "file_count": 0,
                    "total_size_bytes": 0,
                }
            
            weekly_data[week_key]["file_count"] += count.file_count
            weekly_data[week_key]["total_size_bytes"] += count.total_size_bytes
        
        # Convert to sorted list
        result = sorted(weekly_data.values(), key=lambda x: (x["year"], x["week"]))
        
        logger.info(
            "Weekly aggregation calculated",
            source_system_id=source_system_id,
            weeks=len(result),
        )
        
        return result
    
    def get_monthly_aggregation(
        self,
        source_system_id: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict]:
        """
        Get monthly aggregations (sum by month).
        
        Args:
            source_system_id: Source system ID
            start_date: Start date
            end_date: End date
            
        Returns:
            List of monthly aggregates
        """
        daily_counts = self.get_daily_counts(source_system_id, start_date, end_date)
        
        # Group by month
        monthly_data = {}
        for count in daily_counts:
            month_key = (count.arrival_date.year, count.arrival_date.month)
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "year": month_key[0],
                    "month": month_key[1],
                    "file_count": 0,
                    "total_size_bytes": 0,
                }
            
            monthly_data[month_key]["file_count"] += count.file_count
            monthly_data[month_key]["total_size_bytes"] += count.total_size_bytes
        
        # Convert to sorted list
        result = sorted(monthly_data.values(), key=lambda x: (x["year"], x["month"]))
        
        logger.info(
            "Monthly aggregation calculated",
            source_system_id=source_system_id,
            months=len(result),
        )
        
        return result
    
    def get_hourly_patterns(
        self,
        source_system_id: str,
        days_back: int = 90,
    ) -> List[HourlyPattern]:
        """
        Get hourly file arrival patterns (day of week + hour).
        
        Args:
            source_system_id: Source system ID
            days_back: Number of days to analyze (default 90)
            
        Returns:
            List of HourlyPattern objects
        """
        logger.info(
            "Getting hourly patterns",
            source_system_id=source_system_id,
            days_back=days_back,
        )
        
        try:
            with get_db_session() as session:
                results = TrendQueries.get_hourly_patterns(
                    session=session,
                    source_system_id=source_system_id,
                    days_back=days_back,
                )
                
                patterns = [
                    HourlyPattern(
                        day_of_week=row["day_of_week"],
                        hour_of_day=row["hour_of_day"],
                        file_count=row["file_count"],
                        avg_size_bytes=row["avg_size_bytes"],
                    )
                    for row in results
                ]
                
                logger.info(
                    "Hourly patterns retrieved",
                    source_system_id=source_system_id,
                    patterns=len(patterns),
                )
                
                return patterns
                
        except Exception as e:
            logger.error(
                "Failed to get hourly patterns",
                source_system_id=source_system_id,
                error=str(e),
            )
            raise
    
    def get_all_systems_summary(
        self,
        target_date: Optional[date] = None,
    ) -> List[Dict]:
        """
        Get summary for all source systems on a specific date.
        
        Args:
            target_date: Target date (default today)
            
        Returns:
            List of summaries by source system
        """
        if target_date is None:
            target_date = date.today()
        
        logger.info(
            "Getting all systems summary",
            target_date=target_date.isoformat(),
        )
        
        try:
            with get_db_session() as session:
                results = DailyAggregates.get_all_systems_daily_counts(
                    session=session,
                    target_date=target_date,
                )

                # If no data for today, fall back to last 30 days range
                if not results:
                    logger.info("No data for target date, falling back to last 30 days")
                    from sqlalchemy import text
                    from datetime import timedelta
                    fallback_end = target_date
                    fallback_start = target_date - timedelta(days=30)
                    query = text("""
                        SELECT
                            source_system_id,
                            COUNT(*) as file_count,
                            SUM(file_size_bytes) as total_size_bytes,
                            MIN(arrival_timestamp) as first_arrival,
                            MAX(arrival_timestamp) as last_arrival
                        FROM file_arrivals
                        WHERE DATE(arrival_timestamp) BETWEEN :start_date AND :end_date
                        GROUP BY source_system_id
                        ORDER BY source_system_id
                    """)
                    result = session.execute(query, {
                        "start_date": fallback_start.isoformat(),
                        "end_date": fallback_end.isoformat(),
                    })
                    results = [
                        {
                            "source_system_id": row.source_system_id,
                            "file_count": row.file_count,
                            "total_size_bytes": row.total_size_bytes,
                            "first_arrival": row.first_arrival,
                            "last_arrival": row.last_arrival,
                        }
                        for row in result
                    ]

                logger.info(
                    "All systems summary retrieved",
                    systems=len(results),
                )
                
                return results
                
        except Exception as e:
            logger.error(
                "Failed to get all systems summary",
                error=str(e),
            )
            raise
    
    def get_all_systems_summary_range(
        self,
        start_date: date,
        end_date: date,
    ) -> List[Dict]:
        """
        Get summary for all source systems within a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of summaries by source system with aggregated counts
        """
        logger.info(
            "Getting all systems summary for date range",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        
        try:
            with get_db_session() as session:
                from sqlalchemy import text
                
                query = text("""
                    SELECT 
                        source_system_id,
                        COUNT(*) as file_count,
                        SUM(file_size_bytes) as total_size_bytes,
                        MIN(arrival_timestamp) as first_arrival,
                        MAX(arrival_timestamp) as last_arrival
                    FROM file_arrivals
                    WHERE DATE(arrival_timestamp) BETWEEN :start_date AND :end_date
                    GROUP BY source_system_id
                    ORDER BY source_system_id
                """)
                
                result = session.execute(
                    query,
                    {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    }
                )
                
                results = [
                    {
                        "source_system_id": row.source_system_id,
                        "file_count": row.file_count,
                        "total_size_bytes": row.total_size_bytes,
                        "first_arrival": row.first_arrival,
                        "last_arrival": row.last_arrival,
                    }
                    for row in result
                ]
                
                logger.info(
                    "All systems summary for date range retrieved",
                    systems=len(results),
                )
                
                return results
                
        except Exception as e:
            logger.error(
                "Failed to get all systems summary for date range",
                error=str(e),
            )
            raise
