"""SLA (Service Level Agreement) data models"""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import List, Optional


@dataclass
class SLADefinition:
    """
    Defines SLA requirements for a source system.
    """
    
    source_system_id: str
    expected_arrival_time: time
    expected_arrival_window_minutes: int
    minimum_files_per_day: int
    effective_from: date
    id: Optional[int] = None
    weight: float = 1.0
    effective_to: Optional[date] = None
    
    def __post_init__(self) -> None:
        """Validate the SLA definition after initialization"""
        self._validate()
    
    def _validate(self) -> None:
        """Validate SLA definition fields"""
        if not self.source_system_id:
            raise ValueError("source_system_id cannot be empty")
        
        if self.expected_arrival_window_minutes <= 0:
            raise ValueError("expected_arrival_window_minutes must be positive")
        
        if self.minimum_files_per_day < 0:
            raise ValueError("minimum_files_per_day must be non-negative")
        
        if not (0 <= self.weight <= 1.0):
            raise ValueError("weight must be between 0 and 1")
        
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to must be after effective_from")
    
    def is_active(self, check_date: date) -> bool:
        """Check if this SLA definition is active on a given date"""
        if check_date < self.effective_from:
            return False
        
        if self.effective_to and check_date > self.effective_to:
            return False
        
        return True


@dataclass
class SLAViolation:
    """
    Represents an SLA violation event.
    """
    
    source_system_id: str
    violation_date: date
    violation_type: str  # 'missing_file', 'late_arrival', 'insufficient_count'
    severity: str  # 'low', 'medium', 'high', 'critical'
    id: Optional[int] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    VALID_VIOLATION_TYPES = {'missing_file', 'late_arrival', 'insufficient_count'}
    VALID_SEVERITIES = {'low', 'medium', 'high', 'critical'}
    
    def __post_init__(self) -> None:
        """Validate the SLA violation after initialization"""
        self._validate()
    
    def _validate(self) -> None:
        """Validate SLA violation fields"""
        if not self.source_system_id:
            raise ValueError("source_system_id cannot be empty")
        
        if self.violation_type not in self.VALID_VIOLATION_TYPES:
            raise ValueError(
                f"violation_type must be one of {self.VALID_VIOLATION_TYPES}"
            )
        
        if self.severity not in self.VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {self.VALID_SEVERITIES}")


@dataclass
class SLAScore:
    """
    Represents the calculated SLA score for a source system on a specific date.
    """
    
    source_system_id: str
    date: date
    score: float  # 0-100
    total_checks: int
    passed_checks: int
    violations: List[SLAViolation] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate the SLA score after initialization"""
        self._validate()
    
    def _validate(self) -> None:
        """Validate SLA score fields"""
        if not self.source_system_id:
            raise ValueError("source_system_id cannot be empty")
        
        if not (0 <= self.score <= 100):
            raise ValueError("score must be between 0 and 100")
        
        if self.total_checks < 0:
            raise ValueError("total_checks must be non-negative")
        
        if self.passed_checks < 0:
            raise ValueError("passed_checks must be non-negative")
        
        if self.passed_checks > self.total_checks:
            raise ValueError("passed_checks cannot exceed total_checks")
    
    @property
    def compliance_percentage(self) -> float:
        """Calculate compliance percentage"""
        if self.total_checks == 0:
            return 100.0
        return (self.passed_checks / self.total_checks) * 100
    
    @property
    def violation_count(self) -> int:
        """Get the number of violations"""
        return len(self.violations)
    
    def is_compliant(self, threshold: float = 95.0) -> bool:
        """Check if the score meets the compliance threshold"""
        return self.score >= threshold
