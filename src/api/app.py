"""FastAPI application setup"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import file_arrivals, health, sla, source_systems, trends
from src.core.config import get_settings
from src.core.logging import get_logger
from src.database.connection import close_db, init_db

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Intelligent File Monitoring API",
        description="REST API for file monitoring system with SLA tracking",
        version="1.0.0",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(source_systems.router, prefix="/api/v1/source-systems", tags=["Source Systems"])
    app.include_router(file_arrivals.router, prefix="/api/v1/file-arrivals", tags=["File Arrivals"])
    app.include_router(trends.router, prefix="/api/v1/trends", tags=["Trends"])
    app.include_router(sla.router, prefix="/api/v1/sla", tags=["SLA"])
    
    # AI-powered endpoints
    from src.api.routes import ai, ai_insights, chat, simulate
    app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI - Bedrock"])
    app.include_router(ai_insights.router, prefix="/api/v1/ai", tags=["AI - Insights"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(simulate.router, prefix="/api/v1/simulate", tags=["Simulate"])
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize database on startup"""
        logger.info("Starting up API server")
        init_db()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        logger.info("Shutting down API server")
        close_db()
    
    return app
