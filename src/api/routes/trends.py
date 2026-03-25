"""Trends and analytics endpoints"""

from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.analytics.trend_analyzer import TrendAnalyzer

router = APIRouter()


class MovingAverageResponse(BaseModel):
    date: str
    file_count: int
    moving_avg_7day: float
    moving_avg_30day: float


class DailyCountResponse(BaseModel):
    arrival_date: str
    file_count: int
    total_size_bytes: int
    first_arrival: Optional[str] = None
    last_arrival: Optional[str] = None


class HourlyPatternResponse(BaseModel):
    day_of_week: int
    hour_of_day: int
    file_count: int
    avg_size_bytes: float


@router.get("/moving-average/{source_system_id}", response_model=List[MovingAverageResponse])
async def get_moving_average(
    source_system_id: str,
    days: int = Query(30, ge=7, le=90),
):
    """Get moving average trends for a source system"""
    analyzer = TrendAnalyzer()
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    try:
        points = analyzer.calculate_moving_average(
            source_system_id=source_system_id,
            window_days=7,
            end_date=end_date,
            lookback_days=days
        )
        return [p.to_dict() for p in points]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily/{source_system_id}", response_model=List[DailyCountResponse])
async def get_daily_counts(
    source_system_id: str,
    days: int = Query(30, ge=1, le=90),
):
    """Get daily file counts for a source system"""
    analyzer = TrendAnalyzer()
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    try:
        counts = analyzer.get_daily_counts(source_system_id, start_date, end_date)
        return [c.to_dict() for c in counts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hourly-patterns/{source_system_id}", response_model=List[HourlyPatternResponse])
async def get_hourly_patterns(
    source_system_id: str,
    days: int = Query(30, ge=7, le=90),
):
    """Get hourly arrival patterns for a source system"""
    analyzer = TrendAnalyzer()
    
    try:
        patterns = analyzer.get_hourly_patterns(source_system_id, days_back=days)
        return [p.to_dict() for p in patterns]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_all_systems_summary(
    target_date: Optional[date] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get summary for all source systems with optional date range filtering"""
    analyzer = TrendAnalyzer()
    
    try:
        # If start_date and end_date are provided, use date range
        # Otherwise fall back to target_date (single day) or today
        if start_date and end_date:
            summary = analyzer.get_all_systems_summary_range(
                start_date=start_date,
                end_date=end_date
            )
        else:
            summary = analyzer.get_all_systems_summary(target_date=target_date)
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
