"""SQLAlchemy ORM models for SQLite database"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class SourceSystemModel(Base):
    """Source systems configuration table"""
    
    __tablename__ = "source_systems"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    directory_path = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    sla_definitions = relationship("SLADefinitionModel", back_populates="source_system", cascade="all, delete-orphan")
    sla_violations = relationship("SLAViolationModel", back_populates="source_system", cascade="all, delete-orphan")
    file_arrivals = relationship("FileArrivalModel", back_populates="source_system", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<SourceSystem(id='{self.id}', name='{self.name}', is_active={self.is_active})>"


class SLADefinitionModel(Base):
    """SLA definitions table"""
    
    __tablename__ = "sla_definitions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_system_id = Column(String(50), ForeignKey("source_systems.id", ondelete="CASCADE"), nullable=False)
    expected_arrival_time = Column(Time, nullable=False)
    expected_arrival_window_minutes = Column(Integer, nullable=False)
    minimum_files_per_day = Column(Integer, nullable=False)
    weight = Column(Numeric(3, 2), default=1.0, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    source_system = relationship("SourceSystemModel", back_populates="sla_definitions")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("weight >= 0 AND weight <= 1", name="valid_weight"),
        CheckConstraint("expected_arrival_window_minutes > 0", name="valid_window"),
        CheckConstraint("minimum_files_per_day >= 0", name="valid_min_files"),
    )
    
    def __repr__(self) -> str:
        return f"<SLADefinition(id={self.id}, source_system_id='{self.source_system_id}')>"


class SLAViolationModel(Base):
    """SLA violations table"""
    
    __tablename__ = "sla_violations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_system_id = Column(String(50), ForeignKey("source_systems.id", ondelete="CASCADE"), nullable=False)
    violation_date = Column(Date, nullable=False)
    violation_type = Column(String(50), nullable=False)
    expected_value = Column(String(100), nullable=True)
    actual_value = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    source_system = relationship("SourceSystemModel", back_populates="sla_violations")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="valid_severity"
        ),
        Index("idx_sla_violations_date", "violation_date"),
        Index("idx_sla_violations_source_system", "source_system_id", "violation_date"),
    )
    
    def __repr__(self) -> str:
        return f"<SLAViolation(id={self.id}, type='{self.violation_type}', severity='{self.severity}')>"


class FileArrivalModel(Base):
    """File arrival details table"""
    
    __tablename__ = "file_arrivals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_system_id = Column(String(50), ForeignKey("source_systems.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    arrival_timestamp = Column(DateTime, nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    source_system = relationship("SourceSystemModel", back_populates="file_arrivals")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("file_size_bytes >= 0", name="valid_file_size"),
        Index("idx_file_arrivals_timestamp", "arrival_timestamp"),
        Index("idx_file_arrivals_source_system", "source_system_id", "arrival_timestamp"),
        Index("idx_file_arrivals_date", "source_system_id", "arrival_timestamp"),  # For date-based queries
    )
    
    def __repr__(self) -> str:
        return f"<FileArrival(id={self.id}, filename='{self.filename}', source_system_id='{self.source_system_id}')>"


class ConfigurationAuditModel(Base):
    """Configuration audit log table"""
    
    __tablename__ = "configuration_audit"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=True)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_config_audit_timestamp", "timestamp"),
    )
    
    def __repr__(self) -> str:
        return f"<ConfigurationAudit(id={self.id}, action='{self.action}', entity_type='{self.entity_type}')>"


class SLAScoreModel(Base):
    """SLA scores table - cached daily calculations"""
    
    __tablename__ = "sla_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_system_id = Column(String(50), ForeignKey("source_systems.id", ondelete="CASCADE"), nullable=False)
    score_date = Column(Date, nullable=False)
    score = Column(Numeric(5, 2), nullable=False)
    total_checks = Column(Integer, nullable=False)
    passed_checks = Column(Integer, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="valid_score"),
        Index("idx_sla_scores_source_date", "source_system_id", "score_date", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<SLAScore(id={self.id}, source_system_id='{self.source_system_id}', score={self.score})>"


class DashboardCacheModel(Base):
    """Dashboard cache table - replaces Redis"""
    
    __tablename__ = "dashboard_cache"
    
    cache_key = Column(String(255), primary_key=True)
    cache_value = Column(Text, nullable=False)  # JSON data stored as text
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_cache_expires", "expires_at"),
    )
    
    def __repr__(self) -> str:
        return f"<DashboardCache(key='{self.cache_key}', expires_at={self.expires_at})>"
