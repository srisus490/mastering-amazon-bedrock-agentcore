"""AI-powered endpoints using Amazon Bedrock"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.ai.anomaly_detector import BedrockAnomalyDetector
from src.ai.bedrock_agent import AgentOrchestrator, FileMonitoringAgent
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for agent queries"""
    query: str
    session_id: Optional[str] = None
    enable_trace: bool = False


class AnalysisRequest(BaseModel):
    """Request model for AI analysis"""
    days: int = 30


@router.post("/analyze-anomalies/{source_system_id}")
async def analyze_anomalies(
    source_system_id: str,
    days: int = Query(30, ge=7, le=90),
):
    """
    Use AI to detect anomalies in file arrival patterns.
    
    This endpoint uses Amazon Bedrock (Claude 3) to analyze historical
    file arrival patterns and identify:
    - Unusual spikes or drops in file counts
    - Missing data days
    - Timing inconsistencies
    - Trend changes
    - Risk assessment
    
    **Example Response:**
    ```json
    {
      "source_system_id": "PROD_SALES",
      "analysis_date": "2026-02-15",
      "ai_analysis": {
        "anomalies": [...],
        "risk_level": "Low",
        "recommendations": [...]
      }
    }
    ```
    """
    logger.info(
        "AI anomaly analysis requested",
        source_system_id=source_system_id,
        days=days,
    )
    
    try:
        detector = BedrockAnomalyDetector()
        analysis = detector.analyze_pattern(source_system_id, days)
        return analysis
    except Exception as e:
        logger.error(
            "Anomaly analysis failed",
            source_system_id=source_system_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/{source_system_id}")
async def predict_next_week(
    source_system_id: str,
    historical_days: int = Query(60, ge=30, le=180),
):
    """
    Use AI to predict file arrivals for the next 7 days.
    
    This endpoint uses Amazon Bedrock to analyze historical patterns
    and predict expected file counts for the upcoming week.
    
    **Example Response:**
    ```json
    {
      "source_system_id": "PROD_SALES",
      "predictions": {
        "predictions": [
          {
            "date": "2026-02-16",
            "predicted_count": 12,
            "confidence": "High"
          }
        ]
      }
    }
    ```
    """
    logger.info(
        "AI prediction requested",
        source_system_id=source_system_id,
        historical_days=historical_days,
    )
    
    try:
        detector = BedrockAnomalyDetector()
        prediction = detector.predict_next_week(source_system_id, historical_days)
        return prediction
    except Exception as e:
        logger.error(
            "Prediction failed",
            source_system_id=source_system_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend-sla/{source_system_id}")
async def recommend_sla_adjustments(
    source_system_id: str,
    days: int = Query(90, ge=30, le=180),
):
    """
    Use AI to recommend optimal SLA settings based on actual patterns.
    
    This endpoint analyzes historical file arrival patterns and recommends
    optimal SLA parameters:
    - Expected arrival time
    - Tolerance window
    - Minimum files per day
    
    **Example Response:**
    ```json
    {
      "source_system_id": "PROD_SALES",
      "current_sla": {...},
      "recommendations": {
        "recommended_sla": {...},
        "reasoning": "..."
      }
    }
    ```
    """
    logger.info(
        "SLA recommendation requested",
        source_system_id=source_system_id,
        days=days,
    )
    
    try:
        detector = BedrockAnomalyDetector()
        recommendations = detector.recommend_sla_adjustments(source_system_id, days)
        return recommendations
    except Exception as e:
        logger.error(
            "SLA recommendation failed",
            source_system_id=source_system_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/query")
async def query_agent(request: QueryRequest):
    """
    Query Bedrock Agent with natural language.
    
    This endpoint allows you to ask questions in natural language about
    your file monitoring system. The AI agent can:
    - Query current system status
    - Analyze trends and patterns
    - Compare systems
    - Provide recommendations
    
    **Example Queries:**
    - "Show me systems with SLA violations today"
    - "Which system has the most files this week?"
    - "Compare PROD_SALES and PROD_INVENTORY"
    - "What's the health status of all systems?"
    
    **Note:** Requires Bedrock Agent to be configured with agent_id and agent_alias_id.
    Set these in environment variables:
    - BEDROCK_AGENT_ID
    - BEDROCK_AGENT_ALIAS_ID
    
    **Example Request:**
    ```json
    {
      "query": "Show me systems with violations today",
      "session_id": "optional-session-id"
    }
    ```
    """
    logger.info(
        "Agent query requested",
        query=request.query[:100],
        session_id=request.session_id,
    )
    
    try:
        import os
        
        agent_id = os.getenv('BEDROCK_AGENT_ID')
        agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
        
        if not agent_id or not agent_alias_id:
            raise HTTPException(
                status_code=501,
                detail="Bedrock Agent not configured. Set BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID environment variables."
            )
        
        agent = FileMonitoringAgent(agent_id, agent_alias_id)
        response = agent.query(
            request.query,
            request.session_id,
            request.enable_trace,
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Agent query failed",
            query=request.query[:100],
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/complex-query")
async def complex_query(request: QueryRequest):
    """
    Process complex queries using AI orchestration.
    
    This endpoint combines multiple AI capabilities:
    - Bedrock Agent for natural language understanding
    - Anomaly Detector for pattern analysis
    - Direct database queries for real-time data
    
    The orchestrator automatically determines which AI services to use
    based on your query.
    
    **Example Queries:**
    - "Analyze anomalies in PROD_SALES and predict next week"
    - "Show me unusual patterns across all systems"
    - "What systems need SLA adjustments?"
    
    **Example Request:**
    ```json
    {
      "query": "Analyze anomalies in PROD_SALES",
      "session_id": "optional-session-id"
    }
    ```
    """
    logger.info(
        "Complex query requested",
        query=request.query[:100],
    )
    
    try:
        import os
        
        agent_id = os.getenv('BEDROCK_AGENT_ID')
        agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
        
        if not agent_id or not agent_alias_id:
            # Fall back to anomaly detector only
            detector = BedrockAnomalyDetector()
            
            # Try to extract system ID from query
            from src.database.connection import get_db_session
            from src.database.models import SourceSystemModel
            
            system_id = None
            with get_db_session() as session:
                systems = session.query(SourceSystemModel).all()
                for sys in systems:
                    _ = (sys.id, sys.name)
                    session.expunge(sys)
                    if sys.id.lower() in request.query.lower():
                        system_id = sys.id
                        break
            
            if system_id:
                analysis = detector.analyze_pattern(system_id)
                return {
                    "type": "anomaly_analysis",
                    "result": analysis,
                    "note": "Bedrock Agent not configured. Using anomaly detector only."
                }
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Could not identify system in query. Please specify a system ID."
                )
        
        # Use full orchestration
        agent = FileMonitoringAgent(agent_id, agent_alias_id)
        detector = BedrockAnomalyDetector()
        orchestrator = AgentOrchestrator(agent, detector)
        
        response = orchestrator.process_complex_query(
            request.query,
            request.session_id,
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Complex query failed",
            query=request.query[:100],
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/start-session")
async def start_session():
    """
    Start a new conversation session with the AI agent.
    
    Returns a session ID that can be used for subsequent queries
    to maintain conversation context.
    
    **Example Response:**
    ```json
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "message": "Session started"
    }
    ```
    """
    import uuid
    
    session_id = str(uuid.uuid4())
    
    logger.info("New session started", session_id=session_id)
    
    return {
        "session_id": session_id,
        "message": "Session started. Use this session_id in your queries to maintain context.",
    }
