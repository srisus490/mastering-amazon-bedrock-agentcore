"""SLA endpoints"""

from datetime import date, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from src.database.connection import get_db_session
from src.sla.calculator import ScoreCalculator
from src.sla.tracker import ViolationTracker

router = APIRouter()


class SLAScoreResponse(BaseModel):
    date: str
    score: float


class ViolationResponse(BaseModel):
    id: int
    source_system_id: str
    violation_date: date
    violation_type: str
    expected_value: Optional[str]
    actual_value: Optional[str]
    severity: str
    
    class Config:
        from_attributes = True


@router.get("/scores/{source_system_id}", response_model=List[SLAScoreResponse])
async def get_sla_scores(
    source_system_id: str,
    days: int = Query(30, ge=1, le=90),
):
    """Get SLA scores for a source system"""
    calculator = ScoreCalculator()
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    try:
        scores = calculator.calculate_score_range(source_system_id, start_date, end_date)
        return scores
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/average-score/{source_system_id}")
async def get_average_score(
    source_system_id: str,
    days: int = Query(30, ge=1, le=90),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get average SLA score for a source system"""
    calculator = ScoreCalculator()
    
    # Use explicit dates if provided, otherwise use days parameter
    if start_date and end_date:
        calc_start_date = start_date
        calc_end_date = end_date
    else:
        calc_end_date = date.today()
        calc_start_date = calc_end_date - timedelta(days=days)
    
    try:
        avg_score = calculator.get_average_score(source_system_id, calc_start_date, calc_end_date)
        return {
            "source_system_id": source_system_id,
            "start_date": calc_start_date.isoformat(),
            "end_date": calc_end_date.isoformat(),
            "average_score": avg_score,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/violations", response_model=List[ViolationResponse])
async def get_violations(
    source_system_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
):
    """Get SLA violations with optional filters"""
    tracker = ViolationTracker()
    
    try:
        violations = tracker.get_violations(
            source_system_id=source_system_id,
            start_date=start_date,
            end_date=end_date,
            severity=severity,
            limit=limit,
        )
        return violations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/violations/by-severity/{source_system_id}")
async def get_violations_by_severity(
    source_system_id: str,
    days: int = Query(30, ge=1, le=90),
):
    """Get violation counts grouped by severity"""
    tracker = ViolationTracker()
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    try:
        severity_counts = tracker.get_violations_by_severity(
            source_system_id=source_system_id,
            start_date=start_date,
            end_date=end_date,
        )
        return {
            "source_system_id": source_system_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "severity_counts": severity_counts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-systems-summary")
async def get_all_systems_sla_summary(
    days: int = Query(30, ge=1, le=90),
):
    """
    Bulk endpoint: returns SLA average score + worst violation severity
    for ALL systems in a single DB round-trip. Replaces N×2 individual calls.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    try:
        with get_db_session() as session:
            # Average SLA score per system
            score_query = text("""
                SELECT source_system_id,
                       AVG(CAST(score AS FLOAT)) as average_score
                FROM sla_scores
                WHERE score_date BETWEEN :start_date AND :end_date
                GROUP BY source_system_id
            """)
            score_rows = session.execute(score_query, {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }).fetchall()
            scores: Dict[str, float] = {r.source_system_id: round(float(r.average_score), 2) for r in score_rows}

            # Worst violation severity per system (critical > high > medium > low)
            sev_query = text("""
                SELECT source_system_id,
                       CASE
                           WHEN SUM(CASE WHEN severity='critical' THEN 1 ELSE 0 END) > 0 THEN 'critical'
                           WHEN SUM(CASE WHEN severity='high'     THEN 1 ELSE 0 END) > 0 THEN 'high'
                           WHEN SUM(CASE WHEN severity='medium'   THEN 1 ELSE 0 END) > 0 THEN 'medium'
                           WHEN SUM(CASE WHEN severity='low'      THEN 1 ELSE 0 END) > 0 THEN 'low'
                           ELSE NULL
                       END as worst_severity
                FROM sla_violations
                WHERE violation_date BETWEEN :start_date AND :end_date
                GROUP BY source_system_id
            """)
            sev_rows = session.execute(sev_query, {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }).fetchall()
            severities: Dict[str, str] = {r.source_system_id: r.worst_severity for r in sev_rows}

        # Merge into a single response keyed by system id
        all_ids = set(scores.keys()) | set(severities.keys())
        result = {
            sid: {
                "sla_score": scores.get(sid),
                "worst_severity": severities.get(sid),
            }
            for sid in all_ids
        }
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
