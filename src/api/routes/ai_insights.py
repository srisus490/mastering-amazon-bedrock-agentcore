"""AI Insights API endpoints."""

from fastapi import APIRouter, HTTPException, status

from src.ai.cohere_client import CohereError as BedrockError, CohereUnavailableError as BedrockUnavailableError
from src.ai.insights_service import AIInsightsService
from src.ai.models import (
    ForecastRequest,
    ForecastResponse,
    InsightsRequest,
    RootCauseRequest,
    RootCauseResponse,
    SmartInsightsResponse,
)
from src.core.logging import get_logger
from src.database.connection import get_db_session
from src.database.models import SourceSystemModel

logger = get_logger(__name__)
router = APIRouter()

# Initialize AI service (singleton)
_ai_service = None


def get_ai_service() -> AIInsightsService:
    """Get or create AI insights service instance."""
    global _ai_service
    if _ai_service is None:
        try:
            _ai_service = AIInsightsService()
            logger.info("AI Insights Service initialized")
        except Exception as e:
            logger.error("Failed to initialize AI Insights Service", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not available. Please check configuration."
            )
    return _ai_service


def validate_system_exists(source_system_id: str) -> None:
    """
    Validate that source system exists.
    
    Args:
        source_system_id: Source system identifier
        
    Raises:
        HTTPException: If system not found
    """
    with get_db_session() as session:
        system = session.query(SourceSystemModel).filter(
            SourceSystemModel.id == source_system_id
        ).first()
        
        if not system:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source system '{source_system_id}' not found"
            )


@router.post("/insights", response_model=SmartInsightsResponse)
async def generate_insights(request: InsightsRequest):
    """
    Generate AI-powered smart insights about system health.
    
    Analyzes file arrival patterns, timing, and trends to provide:
    - Natural language summary of system health
    - Identified trends (increasing, decreasing, stable)
    - Detected anomalies (spikes, missing data, timing issues)
    - Actionable recommendations
    
    Results are cached for 1 hour to optimize costs and performance.
    
    **Example Request:**
    ```json
    {
      "source_system_id": "PROD_SALES",
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "source_system_id": "PROD_SALES",
      "date_range": {"start": "2024-01-01", "end": "2024-01-31"},
      "insights": "The PROD_SALES system shows healthy patterns...",
      "trends": [
        {
          "type": "increasing",
          "description": "File counts increased by 15%",
          "confidence": "high"
        }
      ],
      "anomalies": [],
      "recommendations": ["Consider adjusting SLA thresholds"],
      "generated_at": "2024-01-31T10:30:00Z",
      "cached": false
    }
    ```
    """
    logger.info(
        "Smart insights requested",
        source_system_id=request.source_system_id,
        start_date=request.start_date.isoformat(),
        end_date=request.end_date.isoformat()
    )
    
    # Validate system exists
    validate_system_exists(request.source_system_id)
    
    # Validate date range
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date"
        )
    
    try:
        service = get_ai_service()
        insights = service.generate_smart_insights(
            request.source_system_id,
            request.start_date,
            request.end_date
        )
        
        logger.info(
            "Smart insights generated",
            source_system_id=request.source_system_id,
            cached=insights.get("cached", False)
        )
        
        return insights
        
    except BedrockUnavailableError as e:
        logger.error("Bedrock service unavailable", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again later."
        )
    except BedrockError as e:
        logger.error("Bedrock error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "Failed to generate insights",
            source_system_id=request.source_system_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate insights"
        )


@router.post("/forecast", response_model=ForecastResponse)
async def generate_forecast(request: ForecastRequest):
    """
    Generate 7-day forecast of file arrivals using AI.
    
    Analyzes historical patterns including:
    - Day-of-week patterns
    - Trends (increasing, decreasing, stable)
    - Seasonal variations
    
    Provides predictions with confidence levels and ranges.
    
    Results are cached for 6 hours to optimize costs and performance.
    
    **Example Request:**
    ```json
    {
      "source_system_id": "PROD_SALES",
      "historical_days": 60
    }
    ```
    
    **Example Response:**
    ```json
    {
      "source_system_id": "PROD_SALES",
      "forecast_generated_at": "2024-01-31T10:30:00Z",
      "historical_period": {
        "days": 60,
        "start_date": "2023-12-02",
        "end_date": "2024-01-31"
      },
      "predictions": [
        {
          "date": "2024-02-01",
          "predicted_count": 28,
          "confidence_level": "high",
          "confidence_range": {"min": 25, "max": 31}
        }
      ],
      "patterns_identified": ["Weekday average: 28 files"],
      "cached": false
    }
    ```
    """
    logger.info(
        "Forecast requested",
        source_system_id=request.source_system_id,
        historical_days=request.historical_days
    )
    
    # Validate system exists
    validate_system_exists(request.source_system_id)
    
    try:
        service = get_ai_service()
        forecast = service.generate_forecast(
            request.source_system_id,
            request.historical_days
        )
        
        logger.info(
            "Forecast generated",
            source_system_id=request.source_system_id,
            cached=forecast.get("cached", False)
        )
        
        return forecast
        
    except BedrockUnavailableError as e:
        logger.error("Bedrock service unavailable", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again later."
        )
    except BedrockError as e:
        logger.error("Bedrock error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "Failed to generate forecast",
            source_system_id=request.source_system_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate forecast"
        )


@router.post("/root-cause", response_model=RootCauseResponse)
async def generate_root_cause_analysis(request: RootCauseRequest):
    """
    Analyze root causes of SLA violations using AI.
    
    Examines SLA violations and correlates them with:
    - File arrival patterns
    - Timing issues
    - Missing data
    - System behavior
    
    Provides:
    - Identified root causes with confidence levels
    - Correlations and patterns
    - Specific remediation actions
    
    If no violations exist, provides healthy status confirmation.
    
    Results are cached for 1 hour to optimize costs and performance.
    
    **Example Request:**
    ```json
    {
      "source_system_id": "PROD_SALES",
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "source_system_id": "PROD_SALES",
      "date_range": {"start": "2024-01-01", "end": "2024-01-31"},
      "violations_analyzed": 5,
      "root_causes": [
        {
          "cause": "Late file arrivals",
          "description": "Files arrived 2-3 hours late",
          "confidence": "high",
          "affected_dates": ["2024-01-10", "2024-01-17"]
        }
      ],
      "correlations": [
        {
          "pattern": "Late arrivals on Monday mornings",
          "strength": "moderate"
        }
      ],
      "remediation_actions": [
        "Review upstream processing on Sunday nights"
      ],
      "generated_at": "2024-01-31T10:30:00Z",
      "cached": false
    }
    ```
    """
    logger.info(
        "Root cause analysis requested",
        source_system_id=request.source_system_id,
        start_date=request.start_date.isoformat(),
        end_date=request.end_date.isoformat()
    )
    
    # Validate system exists
    validate_system_exists(request.source_system_id)
    
    # Validate date range
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date"
        )
    
    try:
        service = get_ai_service()
        root_cause = service.generate_root_cause_analysis(
            request.source_system_id,
            request.start_date,
            request.end_date
        )
        
        logger.info(
            "Root cause analysis generated",
            source_system_id=request.source_system_id,
            violations=root_cause.get("violations_analyzed", 0),
            cached=root_cause.get("cached", False)
        )
        
        return root_cause
        
    except BedrockUnavailableError as e:
        logger.error("Bedrock service unavailable", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again later."
        )
    except BedrockError as e:
        logger.error("Bedrock error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "Failed to generate root cause analysis",
            source_system_id=request.source_system_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate root cause analysis"
        )
