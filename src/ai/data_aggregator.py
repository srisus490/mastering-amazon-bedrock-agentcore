"""Data aggregator for AI insights analysis."""

from datetime import date, datetime, timedelta
from typing import Dict, List

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.ai.logger import ai_logger
from src.database.connection import get_db_session
from src.database.models import FileArrivalModel, SLAViolationModel, SLAScoreModel


class DataAggregator:
    """
    Aggregates file monitoring data for AI analysis.
    
    Provides aggregated metrics and patterns without exposing
    individual file names or sensitive information.
    """
    
    def __init__(self):
        """Initialize data aggregator."""
        ai_logger.info("DataAggregator initialized")
    
    def get_file_arrival_summary(
        self,
        source_system_id: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Get aggregated file arrival statistics.
        
        Args:
            source_system_id: Source system identifier
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with daily counts, timing patterns, and totals
        """
        try:
            with get_db_session() as session:
                # Get daily counts
                daily_query = text("""
                    SELECT 
                        DATE(arrival_timestamp) as arrival_date,
                        COUNT(*) as file_count,
                        SUM(file_size_bytes) as total_size_bytes,
                        MIN(arrival_timestamp) as first_arrival,
                        MAX(arrival_timestamp) as last_arrival,
                        AVG(file_size_bytes) as avg_size_bytes
                    FROM file_arrivals
                    WHERE source_system_id = :source_system_id
                      AND DATE(arrival_timestamp) BETWEEN :start_date AND :end_date
                    GROUP BY DATE(arrival_timestamp)
                    ORDER BY arrival_date
                """)
                
                daily_results = session.execute(
                    daily_query,
                    {
                        "source_system_id": source_system_id,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    }
                ).fetchall()
                
                daily_counts = [
                    {
                        "date": row.arrival_date,
                        "count": row.file_count,
                        "total_size": row.total_size_bytes,
                        "avg_size": round(row.avg_size_bytes, 2) if row.avg_size_bytes else 0,
                        "first_arrival": row.first_arrival,
                        "last_arrival": row.last_arrival,
                    }
                    for row in daily_results
                ]
                
                # Get hourly patterns
                hourly_query = text("""
                    SELECT 
                        CAST(strftime('%H', arrival_timestamp) AS INTEGER) as hour,
                        COUNT(*) as file_count,
                        AVG(file_size_bytes) as avg_size_bytes
                    FROM file_arrivals
                    WHERE source_system_id = :source_system_id
                      AND DATE(arrival_timestamp) BETWEEN :start_date AND :end_date
                    GROUP BY hour
                    ORDER BY hour
                """)
                
                hourly_results = session.execute(
                    hourly_query,
                    {
                        "source_system_id": source_system_id,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    }
                ).fetchall()
                
                hourly_patterns = [
                    {
                        "hour": row.hour,
                        "count": row.file_count,
                        "avg_size": round(row.avg_size_bytes, 2) if row.avg_size_bytes else 0,
                    }
                    for row in hourly_results
                ]
                
                # Calculate summary statistics
                total_files = sum(d["count"] for d in daily_counts)
                total_size = sum(d["total_size"] for d in daily_counts)
                avg_daily_count = total_files / len(daily_counts) if daily_counts else 0
                
                # Identify days with no files
                all_dates = set()
                current = start_date
                while current <= end_date:
                    all_dates.add(current.isoformat())
                    current += timedelta(days=1)
                
                dates_with_files = {d["date"] for d in daily_counts}
                missing_dates = sorted(list(all_dates - dates_with_files))
                
                summary = {
                    "source_system_id": source_system_id,
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                        "days": (end_date - start_date).days + 1
                    },
                    "daily_counts": daily_counts,
                    "hourly_patterns": hourly_patterns,
                    "summary": {
                        "total_files": total_files,
                        "total_size_bytes": total_size,
                        "avg_daily_count": round(avg_daily_count, 2),
                        "days_with_files": len(daily_counts),
                        "days_without_files": len(missing_dates),
                        "missing_dates": missing_dates[:10]  # Limit to first 10
                    }
                }
                
                ai_logger.debug(
                    "File arrival summary generated",
                    source_system_id=source_system_id,
                    total_files=total_files,
                    days_analyzed=(end_date - start_date).days + 1
                )
                
                return summary
                
        except Exception as e:
            ai_logger.error(
                "Error generating file arrival summary",
                source_system_id=source_system_id,
                error=str(e)
            )
            raise
    
    def get_sla_violation_summary(
        self,
        source_system_id: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Get aggregated SLA violation data.
        
        Args:
            source_system_id: Source system identifier
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with violations by type, severity, and dates
        """
        try:
            with get_db_session() as session:
                # Get violations
                violations = session.query(SLAViolationModel).filter(
                    SLAViolationModel.source_system_id == source_system_id,
                    SLAViolationModel.violation_date >= start_date,
                    SLAViolationModel.violation_date <= end_date
                ).all()
                
                # Group by type
                by_type = {}
                by_severity = {}
                violation_dates = []
                
                for v in violations:
                    # By type
                    if v.violation_type not in by_type:
                        by_type[v.violation_type] = []
                    by_type[v.violation_type].append({
                        "date": v.violation_date.isoformat(),
                        "severity": v.severity,
                        "expected": v.expected_value,
                        "actual": v.actual_value
                    })
                    
                    # By severity
                    by_severity[v.severity] = by_severity.get(v.severity, 0) + 1
                    
                    # Dates
                    violation_dates.append(v.violation_date.isoformat())
                
                # Get SLA scores for the period
                scores = session.query(SLAScoreModel).filter(
                    SLAScoreModel.source_system_id == source_system_id,
                    SLAScoreModel.score_date >= start_date,
                    SLAScoreModel.score_date <= end_date
                ).all()
                
                avg_score = sum(s.score for s in scores) / len(scores) if scores else None
                
                summary = {
                    "source_system_id": source_system_id,
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "total_violations": len(violations),
                    "by_type": by_type,
                    "by_severity": by_severity,
                    "violation_dates": sorted(set(violation_dates)),
                    "avg_sla_score": round(avg_score, 2) if avg_score else None
                }
                
                ai_logger.debug(
                    "SLA violation summary generated",
                    source_system_id=source_system_id,
                    total_violations=len(violations)
                )
                
                return summary
                
        except Exception as e:
            ai_logger.error(
                "Error generating SLA violation summary",
                source_system_id=source_system_id,
                error=str(e)
            )
            raise
    
    def get_historical_patterns(
        self,
        source_system_id: str,
        days: int = 60
    ) -> Dict:
        """
        Get historical patterns for forecasting.
        
        Limits data to maximum 90 days to control processing time.
        
        Args:
            source_system_id: Source system identifier
            days: Number of days to analyze (max 90)
            
        Returns:
            Dictionary with daily counts, day-of-week patterns, and trends
        """
        # Enforce 90-day limit
        days = min(days, 90)
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        try:
            with get_db_session() as session:
                # Get daily counts
                daily_query = text("""
                    SELECT 
                        DATE(arrival_timestamp) as arrival_date,
                        COUNT(*) as file_count,
                        CAST(strftime('%w', arrival_timestamp) AS INTEGER) as day_of_week
                    FROM file_arrivals
                    WHERE source_system_id = :source_system_id
                      AND DATE(arrival_timestamp) BETWEEN :start_date AND :end_date
                    GROUP BY DATE(arrival_timestamp)
                    ORDER BY arrival_date
                """)
                
                daily_results = session.execute(
                    daily_query,
                    {
                        "source_system_id": source_system_id,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    }
                ).fetchall()
                
                daily_counts = [
                    {
                        "date": row.arrival_date,
                        "count": row.file_count,
                        "day_of_week": row.day_of_week
                    }
                    for row in daily_results
                ]
                
                # Calculate day-of-week averages
                dow_counts = {}
                for d in daily_counts:
                    dow = d["day_of_week"]
                    if dow not in dow_counts:
                        dow_counts[dow] = []
                    dow_counts[dow].append(d["count"])
                
                dow_averages = {
                    dow: round(sum(counts) / len(counts), 2)
                    for dow, counts in dow_counts.items()
                }
                
                # Calculate trend (simple linear regression slope)
                if len(daily_counts) > 1:
                    counts = [d["count"] for d in daily_counts]
                    n = len(counts)
                    x_mean = (n - 1) / 2
                    y_mean = sum(counts) / n
                    
                    numerator = sum((i - x_mean) * (counts[i] - y_mean) for i in range(n))
                    denominator = sum((i - x_mean) ** 2 for i in range(n))
                    
                    trend_slope = numerator / denominator if denominator != 0 else 0
                else:
                    trend_slope = 0
                
                summary = {
                    "source_system_id": source_system_id,
                    "historical_period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                        "days": days
                    },
                    "daily_counts": daily_counts,
                    "day_of_week_averages": dow_averages,
                    "trend": {
                        "slope": round(trend_slope, 4),
                        "direction": "increasing" if trend_slope > 0.1 else "decreasing" if trend_slope < -0.1 else "stable"
                    },
                    "statistics": {
                        "avg_count": round(sum(d["count"] for d in daily_counts) / len(daily_counts), 2) if daily_counts else 0,
                        "min_count": min(d["count"] for d in daily_counts) if daily_counts else 0,
                        "max_count": max(d["count"] for d in daily_counts) if daily_counts else 0
                    }
                }
                
                ai_logger.debug(
                    "Historical patterns generated",
                    source_system_id=source_system_id,
                    days_analyzed=days,
                    data_points=len(daily_counts)
                )
                
                return summary
                
        except Exception as e:
            ai_logger.error(
                "Error generating historical patterns",
                source_system_id=source_system_id,
                error=str(e)
            )
            raise
