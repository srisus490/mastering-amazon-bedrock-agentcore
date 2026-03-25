"""File arrivals endpoints"""

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.database.connection import get_db_session
from src.database.models import FileArrivalModel

router = APIRouter()


class FileArrivalResponse(BaseModel):
    id: int
    source_system_id: str
    file_path: str
    filename: str
    arrival_timestamp: datetime
    file_size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[FileArrivalResponse])
async def list_file_arrivals(
    source_system_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, le=1000),
):
    """Get file arrivals with optional filters"""
    with get_db_session() as session:
        query = session.query(FileArrivalModel)
        
        if source_system_id:
            query = query.filter_by(source_system_id=source_system_id)
        
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.filter(FileArrivalModel.arrival_timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.filter(FileArrivalModel.arrival_timestamp <= end_dt)
        
        query = query.order_by(FileArrivalModel.arrival_timestamp.desc()).limit(limit)
        
        arrivals = query.all()
        
        # Load attributes and expunge
        result = []
        for arrival in arrivals:
            _ = (arrival.id, arrival.source_system_id, arrival.file_path, 
                 arrival.filename, arrival.arrival_timestamp, arrival.file_size_bytes,
                 arrival.checksum, arrival.processed_at)
            session.expunge(arrival)
            result.append(arrival)
        
        return result


@router.get("/count")
async def get_file_count(
    source_system_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get count of file arrivals"""
    with get_db_session() as session:
        query = session.query(FileArrivalModel)
        
        if source_system_id:
            query = query.filter_by(source_system_id=source_system_id)
        
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.filter(FileArrivalModel.arrival_timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.filter(FileArrivalModel.arrival_timestamp <= end_dt)
        
        count = query.count()
        
        return {"count": count}
