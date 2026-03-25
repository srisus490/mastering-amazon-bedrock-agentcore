"""Source system data models"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class SourceSystem:
    """
    Represents a source system that sends files to monitored directories.
    """
    
    id: str
    name: str
    directory_path: str
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate the source system data after initialization"""
        self._validate()
    
    def _validate(self) -> None:
        """Validate source system fields"""
        if not self.id:
            raise ValueError("id cannot be empty")
        
        if not self.name:
            raise ValueError("name cannot be empty")
        
        if not self.directory_path:
            raise ValueError("directory_path cannot be empty")
        
        # Validate ID format (alphanumeric and underscores only)
        if not self.id.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "id must contain only alphanumeric characters, hyphens, and underscores"
            )
    
    def activate(self) -> None:
        """Activate the source system"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the source system"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def update_directory(self, new_path: str) -> None:
        """Update the directory path"""
        if not new_path:
            raise ValueError("directory_path cannot be empty")
        self.directory_path = new_path
        self.updated_at = datetime.utcnow()
