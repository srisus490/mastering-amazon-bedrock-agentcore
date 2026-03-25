"""Source systems endpoints"""

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.database.connection import get_db_session
from src.database.models import SourceSystemModel

router = APIRouter()


class SourceSystemResponse(BaseModel):
    id: str
    name: str
    directory_path: str
    is_active: bool
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[SourceSystemResponse])
async def list_source_systems():
    """Get all source systems"""
    with get_db_session() as session:
        systems = session.query(SourceSystemModel).all()
        
        # Load attributes and expunge
        result = []
        for sys in systems:
            _ = (sys.id, sys.name, sys.directory_path, sys.is_active, sys.created_at)
            session.expunge(sys)
            result.append(sys)
        
        return result


@router.get("/{system_id}", response_model=SourceSystemResponse)
async def get_source_system(system_id: str):
    """Get a specific source system"""
    with get_db_session() as session:
        system = session.query(SourceSystemModel).filter_by(id=system_id).first()
        
        if not system:
            raise HTTPException(status_code=404, detail="Source system not found")
        
        # Load attributes and expunge
        _ = (system.id, system.name, system.directory_path, system.is_active, system.created_at)
        session.expunge(system)
        
        return system
