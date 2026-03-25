"""Database utility functions"""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.database.models import (
    Base,
    ConfigurationAuditModel,
    FileArrivalModel,
    SLADefinitionModel,
    SLAViolationModel,
    SourceSystemModel,
)
from src.models import (
    FileArrivalEvent,
    SLADefinition,
    SLAViolation,
    SourceSystem,
)


def create_tables(engine) -> None:
    """
    Create all database tables.
    
    Args:
        engine: SQLAlchemy engine
    """
    Base.metadata.create_all(bind=engine)


def drop_tables(engine) -> None:
    """
    Drop all database tables.
    
    Args:
        engine: SQLAlchemy engine
    """
    Base.metadata.drop_all(bind=engine)


# Conversion functions between dataclasses and ORM models

def source_system_to_model(source_system: SourceSystem) -> SourceSystemModel:
    """Convert SourceSystem dataclass to ORM model"""
    return SourceSystemModel(
        id=source_system.id,
        name=source_system.name,
        directory_path=source_system.directory_path,
        is_active=source_system.is_active,
        created_at=source_system.created_at,
        updated_at=source_system.updated_at,
    )


def model_to_source_system(model: SourceSystemModel) -> SourceSystem:
    """Convert ORM model to SourceSystem dataclass"""
    return SourceSystem(
        id=model.id,
        name=model.name,
        directory_path=model.directory_path,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def sla_definition_to_model(sla: SLADefinition) -> SLADefinitionModel:
    """Convert SLADefinition dataclass to ORM model"""
    return SLADefinitionModel(
        id=sla.id,
        source_system_id=sla.source_system_id,
        expected_arrival_time=sla.expected_arrival_time,
        expected_arrival_window_minutes=sla.expected_arrival_window_minutes,
        minimum_files_per_day=sla.minimum_files_per_day,
        weight=sla.weight,
        effective_from=sla.effective_from,
        effective_to=sla.effective_to,
    )


def model_to_sla_definition(model: SLADefinitionModel) -> SLADefinition:
    """Convert ORM model to SLADefinition dataclass"""
    return SLADefinition(
        id=model.id,
        source_system_id=model.source_system_id,
        expected_arrival_time=model.expected_arrival_time,
        expected_arrival_window_minutes=model.expected_arrival_window_minutes,
        minimum_files_per_day=model.minimum_files_per_day,
        weight=float(model.weight),
        effective_from=model.effective_from,
        effective_to=model.effective_to,
    )


def file_arrival_to_model(event: FileArrivalEvent) -> FileArrivalModel:
    """Convert FileArrivalEvent dataclass to ORM model"""
    return FileArrivalModel(
        source_system_id=event.source_system_id,
        filename=event.filename,
        file_path=event.file_path,
        arrival_timestamp=event.arrival_timestamp,
        file_size_bytes=event.file_size_bytes,
        checksum=event.checksum,
    )


def sla_violation_to_model(violation: SLAViolation) -> SLAViolationModel:
    """Convert SLAViolation dataclass to ORM model"""
    return SLAViolationModel(
        id=violation.id,
        source_system_id=violation.source_system_id,
        violation_date=violation.violation_date,
        violation_type=violation.violation_type,
        expected_value=violation.expected_value,
        actual_value=violation.actual_value,
        severity=violation.severity,
        created_at=violation.created_at,
    )


# Repository functions

def save_source_system(session: Session, source_system: SourceSystem) -> SourceSystemModel:
    """
    Save a source system to the database.
    
    Args:
        session: Database session
        source_system: SourceSystem dataclass
        
    Returns:
        Saved ORM model
    """
    model = source_system_to_model(source_system)
    session.add(model)
    session.flush()
    return model


def get_source_system(session: Session, system_id: str) -> Optional[SourceSystem]:
    """
    Get a source system by ID.
    
    Args:
        session: Database session
        system_id: Source system ID
        
    Returns:
        SourceSystem dataclass or None
    """
    model = session.query(SourceSystemModel).filter_by(id=system_id).first()
    return model_to_source_system(model) if model else None


def get_all_source_systems(session: Session, active_only: bool = False) -> List[SourceSystem]:
    """
    Get all source systems.
    
    Args:
        session: Database session
        active_only: If True, return only active systems
        
    Returns:
        List of SourceSystem dataclasses
    """
    query = session.query(SourceSystemModel)
    if active_only:
        query = query.filter_by(is_active=True)
    
    models = query.all()
    return [model_to_source_system(model) for model in models]


def save_file_arrival(session: Session, event: FileArrivalEvent) -> FileArrivalModel:
    """
    Save a file arrival event to the database.
    
    Args:
        session: Database session
        event: FileArrivalEvent dataclass
        
    Returns:
        Saved ORM model
    """
    model = file_arrival_to_model(event)
    session.add(model)
    session.flush()
    return model


def log_configuration_change(
    session: Session,
    user_id: Optional[str],
    action: str,
    entity_type: str,
    entity_id: Optional[str],
    old_value: Optional[str],
    new_value: Optional[str],
) -> ConfigurationAuditModel:
    """
    Log a configuration change to the audit table.
    
    Args:
        session: Database session
        user_id: User who made the change
        action: Action performed (create, update, delete)
        entity_type: Type of entity changed
        entity_id: ID of the entity
        old_value: Old value (JSON string)
        new_value: New value (JSON string)
        
    Returns:
        Saved audit log model
    """
    audit = ConfigurationAuditModel(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
    )
    session.add(audit)
    session.flush()
    return audit
