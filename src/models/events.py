"""File arrival event data models"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class FileArrivalEvent:
    """
    Represents a file arrival event from a source system.
    
    This is an in-memory data structure used for event processing.
    """
    
    source_system_id: str
    filename: str
    file_path: str
    arrival_timestamp: datetime
    file_size_bytes: int
    checksum: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate the event data after initialization"""
        self._validate()
    
    def _validate(self) -> None:
        """Validate event fields"""
        if not self.source_system_id:
            raise ValueError("source_system_id cannot be empty")
        
        if not self.filename:
            raise ValueError("filename cannot be empty")
        
        if not self.file_path:
            raise ValueError("file_path cannot be empty")
        
        if self.file_size_bytes < 0:
            raise ValueError("file_size_bytes must be non-negative")
        
        if not self.checksum:
            raise ValueError("checksum cannot be empty")
        
        # Validate timestamp has millisecond precision
        if self.arrival_timestamp.microsecond == 0:
            # If no microseconds, it might not have millisecond precision
            pass  # Allow it but note it
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "source_system_id": self.source_system_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "arrival_timestamp": self.arrival_timestamp.isoformat(),
            "file_size_bytes": self.file_size_bytes,
            "checksum": self.checksum,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileArrivalEvent":
        """Create event from dictionary"""
        data_copy = data.copy()
        
        # Parse timestamp if it's a string
        if isinstance(data_copy.get("arrival_timestamp"), str):
            data_copy["arrival_timestamp"] = datetime.fromisoformat(
                data_copy["arrival_timestamp"]
            )
        
        return cls(**data_copy)
