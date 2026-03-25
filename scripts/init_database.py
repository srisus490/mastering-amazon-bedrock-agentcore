#!/usr/bin/env python3
"""Initialize SQLite database with schema"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.database.connection import init_db
from src.database.models import Base
from src.core.logging import get_logger

logger = get_logger(__name__)


def init_database():
    """Initialize database with schema"""
    logger.info("Initializing SQLite database...")
    
    # Initialize database connection
    engine = init_db()
    
    # Create all tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(engine)
    
    # Insert sample data
    logger.info("Inserting sample source systems...")
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT OR IGNORE INTO source_systems (id, name, directory_path, is_active) VALUES
                ('SYS001', 'Financial System', 'C:/data/sources/financial', 1),
                ('SYS002', 'HR System', 'C:/data/sources/hr', 1),
                ('SYS003', 'Inventory System', 'C:/data/sources/inventory', 1)
        """))
        conn.commit()
    
    logger.info("✅ Database initialized successfully!")
    logger.info(f"Database location: {engine.url}")


if __name__ == "__main__":
    init_database()
