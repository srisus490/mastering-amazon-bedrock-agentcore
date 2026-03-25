"""SLA violation tracker for SQLite"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from src.core.logging import get_logger
from src.database.connection import get_db_session
from src.database.models import SLAViolationModel

logger = get_logger(__name__)


class ViolationTracker:
    """
    Tracks and records SLA violations to SQLite database.
    """
    
    def __init__(self):
        """Initialize violation tracker"""
        logger.info("ViolationTracker initialized")
    
    def record_violation(
        self,
        source_system_id: str,
        violation_date: date,
        violation_type: str,
        expected_value: Optional[str] = None,
        actual_value: Optional[str] = None,
        severity: str = "medium",
    ) -> int:
        """
        Record an SLA violation to the database.
        
        Args:
            source_system_id: Source system ID
            violation_date: Date of violation
            violation_type: Type of violation
            expected_value: Expected value (optional)
            actual_value: Actual value (optional)
            severity: Severity level (low, medium, high, critical)
            
        Returns:
            ID of created violation
        """
        with get_db_session() as session:
            violation_model = SLAViolationModel(
                source_system_id=source_system_id,
                violation_date=violation_date,
                violation_type=violation_type,
                expected_value=expected_value,
                actual_value=actual_value,
                severity=severity,
            )
            
            session.add(violation_model)
            session.commit()
            
            violation_id = violation_model.id
            
            logger.info(
                "Recorded SLA violation",
                source_system_id=source_system_id,
                violation_type=violation_type,
                severity=severity,
                date=violation_date.isoformat(),
            )
            
            return violation_id
    
    def get_violations(
        self,
        source_system_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        violation_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[SLAViolationModel]:
        """
        Query SLA violations from database.
        
        Args:
            source_system_id: Filter by source system (optional)
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            violation_type: Filter by violation type (optional)
            severity: Filter by severity (optional)
            limit: Maximum number of results
            
        Returns:
            List of SLAViolationModel objects
        """
        with get_db_session() as session:
            query = session.query(SLAViolationModel)
            
            # Apply filters
            if source_system_id:
                query = query.filter_by(source_system_id=source_system_id)
            
            if start_date:
                query = query.filter(SLAViolationModel.violation_date >= start_date)
            
            if end_date:
                query = query.filter(SLAViolationModel.violation_date <= end_date)
            
            if violation_type:
                query = query.filter_by(violation_type=violation_type)
            
            if severity:
                query = query.filter_by(severity=severity)
            
            # Order by date descending
            query = query.order_by(SLAViolationModel.violation_date.desc())
            
            # Apply limit
            query = query.limit(limit)
            
            violations = query.all()
            
            # Access all attributes within session and expunge to prevent DetachedInstanceError
            for v in violations:
                _ = (v.id, v.source_system_id, v.violation_date, v.violation_type,
                     v.expected_value, v.actual_value, v.severity, v.created_at)
                session.expunge(v)
            
            logger.debug(f"Retrieved {len(violations)} violations")
            return violations
    
    def get_violation_count(
        self,
        source_system_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """
        Get count of violations for a source system.
        
        Args:
            source_system_id: Source system ID
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            
        Returns:
            Number of violations
        """
        with get_db_session() as session:
            query = session.query(SLAViolationModel).filter_by(
                source_system_id=source_system_id
            )
            
            if start_date:
                query = query.filter(SLAViolationModel.violation_date >= start_date)
            
            if end_date:
                query = query.filter(SLAViolationModel.violation_date <= end_date)
            
            count = query.count()
            return count
    
    def get_violations_by_severity(
        self,
        source_system_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict[str, int]:
        """
        Get violation counts grouped by severity.
        
        Args:
            source_system_id: Source system ID
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            
        Returns:
            Dictionary mapping severity to count
        """
        violations = self.get_violations(
            source_system_id=source_system_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000,  # Higher limit for aggregation
        )
        
        # Count by severity
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        
        for violation in violations:
            if violation.severity in severity_counts:
                severity_counts[violation.severity] += 1
        
        return severity_counts
    
    def delete_old_violations(
        self,
        days_to_keep: int = 90,
    ) -> int:
        """
        Delete violations older than specified days.
        
        Args:
            days_to_keep: Number of days to keep (default 90)
            
        Returns:
            Number of violations deleted
        """
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        with get_db_session() as session:
            deleted_count = session.query(SLAViolationModel).filter(
                SLAViolationModel.violation_date < cutoff_date
            ).delete()
            
            session.commit()
            
            if deleted_count > 0:
                logger.info(
                    "Deleted old violations",
                    count=deleted_count,
                    cutoff_date=cutoff_date.isoformat(),
                )
            
            return deleted_count
