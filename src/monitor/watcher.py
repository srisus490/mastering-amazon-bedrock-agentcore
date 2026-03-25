"""Directory watcher for file monitoring"""

import hashlib
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.core.logging import get_logger
from src.models import FileArrivalEvent
from src.monitor.database_writer import DatabaseWriter

logger = get_logger(__name__)


class DirectoryWatcher(FileSystemEventHandler):
    """
    Monitors a single directory for file arrivals.
    
    Uses watchdog library for cross-platform file system monitoring.
    """
    
    def __init__(
        self,
        directory_path: str,
        source_system_id: str,
        on_file_created: Optional[Callable[[FileArrivalEvent], None]] = None,
        database_writer: Optional[DatabaseWriter] = None,
    ):
        """
        Initialize directory watcher.
        
        Args:
            directory_path: Path to directory to monitor
            source_system_id: ID of the source system
            on_file_created: Optional callback function when file is created
            database_writer: DatabaseWriter instance (creates new one if not provided)
        """
        super().__init__()
        self.directory_path = Path(directory_path)
        self.source_system_id = source_system_id
        self.on_file_created_callback = on_file_created
        self.database_writer = database_writer or DatabaseWriter()
        self._observer: Optional[Observer] = None
        self._is_monitoring = False
        
        # Validate directory exists
        if not self.directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")
        
        if not self.directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        logger.info(
            "DirectoryWatcher initialized",
            directory=str(self.directory_path),
            source_system_id=source_system_id,
        )
    
    def start_monitoring(self) -> None:
        """Start monitoring the directory for file arrivals"""
        if self._is_monitoring:
            logger.warning("Already monitoring", directory=str(self.directory_path))
            return
        
        self._observer = Observer()
        self._observer.schedule(self, str(self.directory_path), recursive=False)
        self._observer.start()
        self._is_monitoring = True
        
        logger.info("Started monitoring", directory=str(self.directory_path))
    
    def stop_monitoring(self) -> None:
        """Stop monitoring the directory"""
        if not self._is_monitoring or self._observer is None:
            return
        
        self._observer.stop()
        self._observer.join(timeout=5)
        self._is_monitoring = False
        
        logger.info("Stopped monitoring", directory=str(self.directory_path))
    
    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation event from watchdog.
        
        Writes file arrival directly to SQLite database.
        
        Args:
            event: File system event from watchdog
        """
        # Ignore directory creation events
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Wait a moment to ensure file is fully written
        # This helps avoid reading incomplete files
        time.sleep(0.1)
        
        try:
            # Create file arrival event
            arrival_event = self._create_file_arrival_event(file_path)
            
            logger.info(
                "File detected",
                filename=arrival_event.filename,
                source_system_id=self.source_system_id,
                size_bytes=arrival_event.file_size_bytes,
            )
            
            # Write directly to database
            success = self.database_writer.write_file_arrival(arrival_event)
            
            if not success:
                logger.error(
                    "Failed to write file arrival to database",
                    filename=arrival_event.filename,
                    source_system_id=self.source_system_id,
                )
            
            # Call optional callback if provided
            if self.on_file_created_callback:
                self.on_file_created_callback(arrival_event)
                
        except Exception as e:
            logger.error(
                "Failed to process file creation",
                file_path=file_path,
                error=str(e),
            )
    
    def _create_file_arrival_event(self, file_path: str) -> FileArrivalEvent:
        """
        Create a FileArrivalEvent from a file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileArrivalEvent with file metadata
        """
        path = Path(file_path)
        
        # Get file stats
        stats = path.stat()
        file_size = stats.st_size
        
        # Capture timestamp with millisecond precision
        arrival_timestamp = datetime.now()
        
        # Calculate checksum
        checksum = self._calculate_checksum(file_path)
        
        # Create event
        event = FileArrivalEvent(
            source_system_id=self.source_system_id,
            filename=path.name,
            file_path=str(path.absolute()),
            arrival_timestamp=arrival_timestamp,
            file_size_bytes=file_size,
            checksum=checksum,
        )
        
        return event
    
    def _calculate_checksum(self, file_path: str, algorithm: str = "sha256") -> str:
        """
        Calculate file checksum.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm (default: sha256)
            
        Returns:
            Hexadecimal checksum string
        """
        hash_obj = hashlib.new(algorithm)
        
        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            logger.warning(
                "Failed to calculate checksum",
                file_path=file_path,
                error=str(e),
            )
            return "unknown"
    
    @property
    def is_monitoring(self) -> bool:
        """Check if currently monitoring"""
        return self._is_monitoring


class FileMonitorService:
    """
    Manages multiple directory watchers for different source systems.
    """
    
    def __init__(self, database_writer: Optional[DatabaseWriter] = None):
        """
        Initialize file monitor service.
        
        Args:
            database_writer: Shared DatabaseWriter instance for all watchers
        """
        self.watchers: Dict[str, DirectoryWatcher] = {}
        self.database_writer = database_writer or DatabaseWriter()
        logger.info("FileMonitorService initialized")
    
    def add_watcher(
        self,
        source_system_id: str,
        directory_path: str,
        on_file_created: Optional[Callable[[FileArrivalEvent], None]] = None,
    ) -> DirectoryWatcher:
        """
        Add a directory watcher for a source system.
        
        Args:
            source_system_id: Source system ID
            directory_path: Directory to monitor
            on_file_created: Optional callback for file creation events
            
        Returns:
            Created DirectoryWatcher
        """
        if source_system_id in self.watchers:
            raise ValueError(f"Watcher already exists for {source_system_id}")
        
        watcher = DirectoryWatcher(
            directory_path=directory_path,
            source_system_id=source_system_id,
            on_file_created=on_file_created,
            database_writer=self.database_writer,  # Share database writer
        )
        
        self.watchers[source_system_id] = watcher
        
        logger.info(
            "Added watcher",
            source_system_id=source_system_id,
            directory=directory_path,
        )
        
        return watcher
    
    def remove_watcher(self, source_system_id: str) -> None:
        """
        Remove a directory watcher.
        
        Args:
            source_system_id: Source system ID
        """
        if source_system_id not in self.watchers:
            return
        
        watcher = self.watchers[source_system_id]
        watcher.stop_monitoring()
        del self.watchers[source_system_id]
        
        logger.info("Removed watcher", source_system_id=source_system_id)
    
    def start_all(self) -> None:
        """Start monitoring all configured directories"""
        for source_system_id, watcher in self.watchers.items():
            try:
                watcher.start_monitoring()
            except Exception as e:
                logger.error(
                    "Failed to start watcher",
                    source_system_id=source_system_id,
                    error=str(e),
                )
        
        logger.info(f"Started {len(self.watchers)} watchers")
    
    def stop_all(self) -> None:
        """Stop monitoring all directories"""
        for source_system_id, watcher in self.watchers.items():
            try:
                watcher.stop_monitoring()
            except Exception as e:
                logger.error(
                    "Failed to stop watcher",
                    source_system_id=source_system_id,
                    error=str(e),
                )
        
        logger.info("Stopped all watchers")
    
    def get_watcher(self, source_system_id: str) -> Optional[DirectoryWatcher]:
        """Get a watcher by source system ID"""
        return self.watchers.get(source_system_id)
    
    def get_active_watchers(self) -> Dict[str, DirectoryWatcher]:
        """Get all active watchers"""
        return {
            sid: watcher
            for sid, watcher in self.watchers.items()
            if watcher.is_monitoring
        }
