"""SLA evaluator for compliance checking"""

from datetime import date, datetime, time, timedelta
from typing import List, Optional

from src.core.logging import get_logger
from src.database.connection import get_db_session
from src.database.models import SLADefinitionModel, FileArrivalModel
from src.models import FileArrivalEvent

logger = get_logger(__name__)


class SLAEvaluator:
    """
    Evaluates file arrivals against SLA definitions using SQLite.
    
    Checks if files arrive within expected time windows and
    identifies missing files and late arrivals.
    """
    
    def __init__(self):
        """Initialize SLA evaluator"""
        logger.info("SLAEvaluator initialized")
    
    def get_sla_definition(self, source_system_id: str, target_date: date) -> Optional[SLADefinitionModel]:
        """
        Get active SLA definition for a source system on a specific date.
        
        Args:
            source_system_id: Source system ID
            target_date: Date to check SLA for
            
        Returns:
            SLA definition model or None if not found
        """
        with get_db_session() as session:
            query = session.query(SLADefinitionModel).filter(
                SLADefinitionModel.source_system_id == source_system_id,
                SLADefinitionModel.effective_from <= target_date,
            )
            
            # Check if effective_to is null or after target_date
            query = query.filter(
                (SLADefinitionModel.effective_to.is_(None)) |
                (SLADefinitionModel.effective_to >= target_date)
            )
            
            sla = query.first()
            
            if sla:
                # Access all attributes within session to load them
                _ = (sla.id, sla.source_system_id, sla.expected_arrival_time,
                     sla.expected_arrival_window_minutes, sla.minimum_files_per_day,
                     sla.weight, sla.effective_from, sla.effective_to, sla.created_at)
                
                # Expunge from session to prevent DetachedInstanceError
                session.expunge(sla)
                
                logger.debug(
                    "Found SLA definition",
                    source_system_id=source_system_id,
                    expected_time=str(sla.expected_arrival_time),
                )
            
            return sla
    
    def is_within_sla_window(
        self,
        arrival_time: datetime,
        sla: SLADefinitionModel,
    ) -> bool:
        """
        Check if arrival time is within SLA window.
        
        Args:
            arrival_time: Actual arrival timestamp
            sla: SLA definition
            
        Returns:
            True if within SLA window, False otherwise
        """
        # Calculate expected arrival time for the day
        arrival_date = arrival_time.date()
        expected_datetime = datetime.combine(arrival_date, sla.expected_arrival_time)
        
        # Calculate tolerance window
        window_delta = timedelta(minutes=sla.expected_arrival_window_minutes)
        earliest_allowed = expected_datetime - window_delta
        latest_allowed = expected_datetime + window_delta
        
        # Check if arrival is within window
        is_compliant = earliest_allowed <= arrival_time <= latest_allowed
        
        if not is_compliant:
            logger.info(
                "SLA window violation detected",
                source_system_id=sla.source_system_id,
                expected=expected_datetime.isoformat(),
                actual=arrival_time.isoformat(),
                window_minutes=sla.expected_arrival_window_minutes,
            )
        
        return is_compliant
    
    def calculate_lateness_minutes(
        self,
        arrival_time: datetime,
        sla: SLADefinitionModel,
    ) -> float:
        """
        Calculate how late (or early) an arrival is.
        
        Args:
            arrival_time: Actual arrival timestamp
            sla: SLA definition
            
        Returns:
            Minutes late (positive) or early (negative)
        """
        # Calculate expected arrival time
        arrival_date = arrival_time.date()
        expected_datetime = datetime.combine(arrival_date, sla.expected_arrival_time)
        
        # Calculate difference in minutes
        diff = arrival_time - expected_datetime
        lateness_minutes = diff.total_seconds() / 60.0
        
        return lateness_minutes
    
    def get_violation_severity(
        self,
        lateness_minutes: float,
        sla: SLADefinitionModel,
    ) -> str:
        """
        Determine severity of SLA violation based on lateness.
        
        Args:
            lateness_minutes: How late/early (absolute value)
            sla: SLA definition
            
        Returns:
            Severity: "critical", "high", "medium", "low"
        """
        abs_lateness = abs(lateness_minutes)
        window = sla.expected_arrival_window_minutes
        
        # No violation if within window
        if abs_lateness <= window:
            return "low"
        
        # Calculate how far outside window
        excess = abs_lateness - window
        
        # Severity thresholds based on window size
        if excess > window * 2:  # More than 3x window
            return "critical"
        elif excess > window:  # More than 2x window
            return "high"
        elif excess > window / 2:  # More than 1.5x window
            return "medium"
        else:
            return "low"
    
    def check_daily_file_count(
        self,
        source_system_id: str,
        target_date: date,
    ) -> tuple[int, bool]:
        """
        Check if minimum daily file count is met.
        
        Args:
            source_system_id: Source system ID
            target_date: Date to check
            
        Returns:
            Tuple of (actual_count, is_compliant)
        """
        sla = self.get_sla_definition(source_system_id, target_date)
        
        if not sla:
            return (0, True)  # No SLA = always compliant
        
        # Count files for the day
        with get_db_session() as session:
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            count = session.query(FileArrivalModel).filter(
                FileArrivalModel.source_system_id == source_system_id,
                FileArrivalModel.arrival_timestamp >= start_datetime,
                FileArrivalModel.arrival_timestamp <= end_datetime,
            ).count()
            
            is_compliant = count >= sla.minimum_files_per_day
            
            if not is_compliant:
                logger.info(
                    "Daily file count violation",
                    source_system_id=source_system_id,
                    date=target_date.isoformat(),
                    expected=sla.minimum_files_per_day,
                    actual=count,
                )
            
            return (count, is_compliant)
