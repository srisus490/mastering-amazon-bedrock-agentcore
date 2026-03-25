"""Configuration manager for dynamic directory management"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.database.connection import get_db_session
from src.database.utils import get_all_source_systems
from src.models import SourceSystem

logger = get_logger(__name__)


class ConfigurationManager:
    """
    Manages directory-to-source-system mappings and configuration.
    
    Supports hot-reload of configuration changes from database.
    """
    
    def __init__(self):
        """Initialize configuration manager"""
        self._directory_mappings: Dict[str, str] = {}  # directory -> source_system_id
        self._source_systems: Dict[str, SourceSystem] = {}  # source_system_id -> SourceSystem
        logger.info("ConfigurationManager initialized")
    
    def load_from_database(self) -> None:
        """
        Load directory configurations from database.
        
        This method can be called periodically to hot-reload configurations.
        """
        try:
            with get_db_session() as session:
                # Get all active source systems
                source_systems = get_all_source_systems(session, active_only=True)
                
                # Clear existing mappings
                self._directory_mappings.clear()
                self._source_systems.clear()
                
                # Build new mappings
                for system in source_systems:
                    self._source_systems[system.id] = system
                    self._directory_mappings[system.directory_path] = system.id
                
                logger.info(
                    "Loaded configuration from database",
                    source_system_count=len(source_systems),
                )
                
        except Exception as e:
            logger.error("Failed to load configuration from database", error=str(e))
            raise
    
    def load_from_dict(self, config: Dict[str, str]) -> None:
        """
        Load directory configurations from a dictionary.
        
        Args:
            config: Dictionary mapping directory paths to source system IDs
        """
        self._directory_mappings.clear()
        self._source_systems.clear()
        
        for directory, source_system_id in config.items():
            # Create minimal SourceSystem objects
            system = SourceSystem(
                id=source_system_id,
                name=source_system_id,
                directory_path=directory,
            )
            self._source_systems[source_system_id] = system
            self._directory_mappings[directory] = source_system_id
        
        logger.info(
            "Loaded configuration from dict",
            source_system_count=len(config),
        )
    
    def get_source_system_id(self, directory_path: str) -> Optional[str]:
        """
        Get source system ID for a directory path.
        
        Args:
            directory_path: Directory path
            
        Returns:
            Source system ID or None if not found
        """
        # Normalize path
        normalized_path = str(Path(directory_path).resolve())
        
        # Try exact match first
        if normalized_path in self._directory_mappings:
            return self._directory_mappings[normalized_path]
        
        # Try original path
        if directory_path in self._directory_mappings:
            return self._directory_mappings[directory_path]
        
        return None
    
    def get_source_system(self, source_system_id: str) -> Optional[SourceSystem]:
        """
        Get source system by ID.
        
        Args:
            source_system_id: Source system ID
            
        Returns:
            SourceSystem or None if not found
        """
        return self._source_systems.get(source_system_id)
    
    def get_all_directories(self) -> List[str]:
        """
        Get all configured directory paths.
        
        Returns:
            List of directory paths
        """
        return list(self._directory_mappings.keys())
    
    def get_all_source_systems(self) -> List[SourceSystem]:
        """
        Get all configured source systems.
        
        Returns:
            List of SourceSystem objects
        """
        return list(self._source_systems.values())
    
    def validate_directory(self, directory_path: str) -> bool:
        """
        Validate that a directory exists and is accessible.
        
        Args:
            directory_path: Directory path to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            path = Path(directory_path)
            
            # Check if exists
            if not path.exists():
                logger.warning(
                    "Directory does not exist",
                    directory=directory_path,
                )
                return False
            
            # Check if is directory
            if not path.is_dir():
                logger.warning(
                    "Path is not a directory",
                    directory=directory_path,
                )
                return False
            
            # Check if readable
            if not os.access(path, os.R_OK):
                logger.warning(
                    "Directory is not readable",
                    directory=directory_path,
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to validate directory",
                directory=directory_path,
                error=str(e),
            )
            return False
    
    def validate_all_directories(self) -> Dict[str, bool]:
        """
        Validate all configured directories.
        
        Returns:
            Dictionary mapping directory paths to validation results
        """
        results = {}
        for directory in self.get_all_directories():
            results[directory] = self.validate_directory(directory)
        
        valid_count = sum(1 for v in results.values() if v)
        logger.info(
            "Validated directories",
            total=len(results),
            valid=valid_count,
            invalid=len(results) - valid_count,
        )
        
        return results
    
    def add_source_system(self, source_system: SourceSystem) -> None:
        """
        Add a source system to the configuration.
        
        Args:
            source_system: SourceSystem to add
        """
        self._source_systems[source_system.id] = source_system
        self._directory_mappings[source_system.directory_path] = source_system.id
        
        logger.info(
            "Added source system",
            source_system_id=source_system.id,
            directory=source_system.directory_path,
        )
    
    def remove_source_system(self, source_system_id: str) -> None:
        """
        Remove a source system from the configuration.
        
        Args:
            source_system_id: Source system ID to remove
        """
        if source_system_id not in self._source_systems:
            return
        
        system = self._source_systems[source_system_id]
        
        # Remove from mappings
        if system.directory_path in self._directory_mappings:
            del self._directory_mappings[system.directory_path]
        
        del self._source_systems[source_system_id]
        
        logger.info("Removed source system", source_system_id=source_system_id)
    
    @property
    def source_system_count(self) -> int:
        """Get the number of configured source systems"""
        return len(self._source_systems)
