"""Health check endpoints"""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "file-monitoring-api",
    }


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Intelligent File Monitoring API",
        "version": "1.0.0",
        "docs": "/docs",
    }
