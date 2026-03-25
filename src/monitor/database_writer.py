"""Database writer for file arrival events"""

from datetime import datetime
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.database.connection import get_db_session
from src.database.models import FileArrivalModel
from src.models import FileArrivalEvent

logger = get_logger(__name__)


class DatabaseWriter:
    """
    Writes file arrival events directly to SQLite database.
    
    This replaces the message queue approach - files are written
    immediately to the database when detected.
    """
    
    def __init__(self, max_retries: int = 3):
        """
        Initialize database writer.
        
        Args:
            max_retries: Maximum number of retry attempts on failure
        """
        self.max_retries = max_retries
        logger.info("DatabaseWriter initialized", max_retries=max_retries)
    
    def write_file_arrival(self, event: FileArrivalEvent) -> bool:
        """
        Write a file arrival event to the database.
        
        Args:
            event: FileArrivalEvent to write
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                with get_db_session() as session:
                    # Create database model from event
                    file_arrival = FileArrivalModel(
                        source_system_id=event.source_system_id,
                        filename=event.filename,
                        file_path=event.file_path,
                        arrival_timestamp=event.arrival_timestamp,
                        file_size_bytes=event.file_size_bytes,
                        checksum=event.checksum,
                        processed_at=datetime.utcnow(),
                    )
                    
                    # Add to session and commit
                    session.add(file_arrival)
                    session.commit()
                    
                    logger.info(
                        "File arrival written to database",
                        filename=event.filename,
                        source_system_id=event.source_system_id,
                        file_id=file_arrival.id,
                    )
                    
                    return True
                    
            except SQLAlchemyError as e:
                logger.error(
                    "Database write failed",
                    filename=event.filename,
                    source_system_id=event.source_system_id,
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                )
                
                # If this was the last attempt, give up
                if attempt >= self.max_retries:
                    logger.error(
                        "Failed to write file arrival after all retries",
                        filename=event.filename,
                        source_system_id=event.source_system_id,
                    )
                    return False
                
                # Wait a bit before retrying (exponential backoff)
                import time
                time.sleep(0.1 * (2 ** (attempt - 1)))
            
            except Exception as e:
                logger.error(
                    "Unexpected error writing to database",
                    filename=event.filename,
                    source_system_id=event.source_system_id,
                    error=str(e),
                )
                return False
        
        return False
    
    def write_batch(self, events: list[FileArrivalEvent]) -> int:
        """
        Write multiple file arrival events in a single transaction.
        
        Args:
            events: List of FileArrivalEvent objects
            
        Returns:
            Number of events successfully written
        """
        if not events:
            return 0
        
        try:
            with get_db_session() as session:
                file_arrivals = [
                    FileArrivalModel(
                        source_system_id=event.source_system_id,
                        filename=event.filename,
                        file_path=event.file_path,
                        arrival_timestamp=event.arrival_timestamp,
                        file_size_bytes=event.file_size_bytes,
                        checksum=event.checksum,
                        processed_at=datetime.utcnow(),
                    )
                    for event in events
                ]
                
                session.add_all(file_arrivals)
                session.commit()
                
                logger.info(
                    "Batch write successful",
                    count=len(events),
                )
                
                return len(events)
                
        except SQLAlchemyError as e:
            logger.error(
                "Batch write failed",
                count=len(events),
                error=str(e),
            )
            return 0
        
        except Exception as e:
            logger.error(
                "Unexpected error in batch write",
                count=len(events),
                error=str(e),
            )
            return 0
