"""Pydantic models for AI insights API."""

from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


# Request Models

class InsightsRequest(BaseModel):
    """Request model for smart insights generation."""
    
    source_system_id: str = Field(..., description="Source system identifier")
    start_date: date = Field(..., description="Start date for analysis")
    end_date: date = Field(..., description="End date for analysis")


class ForecastRequest(BaseModel):
    """Request model for forecast generation."""
    
    source_system_id: str = Field(..., description="Source system identifier")
    historical_days: int = Field(
        default=60,
        ge=30,
        le=90,
        description="Number of historical days to analyze (30-90)"
    )


class RootCauseRequest(BaseModel):
    """Request model for root cause analysis."""
    
    source_system_id: str = Field(..., description="Source system identifier")
    start_date: date = Field(..., description="Start date for analysis")
    end_date: date = Field(..., description="End date for analysis")


# Response Models - Smart Insights

class Trend(BaseModel):
    """Trend identified in the data."""
    
    type: str = Field(..., description="Type of trend (e.g., 'increasing', 'decreasing', 'stable')")
    description: str = Field(..., description="Description of the trend")
    confidence: str = Field(..., description="Confidence level: high, medium, low")


class Anomaly(BaseModel):
    """Anomaly detected in the data."""
    
    description: str = Field(..., description="Description of the anomaly")
    severity: str = Field(..., description="Severity: high, medium, low")
    date: Optional[str] = Field(None, description="Date of anomaly if applicable")


class DateRange(BaseModel):
    """Date range for analysis."""
    
    start: str = Field(..., description="Start date (ISO format)")
    end: str = Field(..., description="End date (ISO format)")


class SmartInsightsResponse(BaseModel):
    """Response model for smart insights."""
    
    source_system_id: str = Field(..., description="Source system identifier")
    date_range: DateRange = Field(..., description="Date range analyzed")
    insights: str = Field(..., description="Natural language insights summary")
    trends: List[Trend] = Field(default_factory=list, description="Trends identified")
    anomalies: List[Anomaly] = Field(default_factory=list, description="Anomalies detected")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    generated_at: str = Field(..., description="Timestamp when insights were generated (ISO format)")
    cached: bool = Field(default=False, description="Whether response was served from cache")
    stale: Optional[bool] = Field(None, description="Whether cached data is stale (past TTL)")


# Response Models - Forecast

class ConfidenceRange(BaseModel):
    """Confidence range for predictions."""
    
    min: int = Field(..., description="Minimum predicted count", ge=0)
    max: int = Field(..., description="Maximum predicted count", ge=0)


class DailyPrediction(BaseModel):
    """Daily prediction for file arrivals."""
    
    date: str = Field(..., description="Prediction date (ISO format)")
    predicted_count: int = Field(..., description="Predicted file count", ge=0)
    confidence_level: str = Field(..., description="Confidence level: high, medium, low")
    confidence_range: ConfidenceRange = Field(..., description="Confidence range for prediction")


class HistoricalPeriod(BaseModel):
    """Historical period used for forecasting."""
    
    days: int = Field(..., description="Number of days analyzed")
    start: str = Field(..., description="Start date (ISO format)")
    end: str = Field(..., description="End date (ISO format)")


class ForecastResponse(BaseModel):
    """Response model for forecast."""
    
    source_system_id: str = Field(..., description="Source system identifier")
    forecast_generated_at: str = Field(..., description="Timestamp when forecast was generated (ISO format)")
    historical_period: HistoricalPeriod = Field(..., description="Historical period analyzed")
    predictions: List[DailyPrediction] = Field(..., description="7-day predictions")
    patterns_identified: List[str] = Field(default_factory=list, description="Patterns identified in historical data")
    cached: bool = Field(default=False, description="Whether response was served from cache")
    stale: Optional[bool] = Field(None, description="Whether cached data is stale (past TTL)")


# Response Models - Root Cause Analysis

class RootCause(BaseModel):
    """Root cause identified for violations."""
    
    cause: str = Field(..., description="Root cause description")
    description: str = Field(..., description="Detailed description")
    confidence: str = Field(..., description="Confidence level: high, medium, low")
    affected_dates: Optional[List[str]] = Field(None, description="Dates affected by this cause")


class Correlation(BaseModel):
    """Correlation pattern identified."""
    
    pattern: str = Field(..., description="Correlation pattern description")
    strength: str = Field(..., description="Correlation strength: strong, moderate, weak")


class RootCauseResponse(BaseModel):
    """Response model for root cause analysis."""
    
    source_system_id: str = Field(..., description="Source system identifier")
    date_range: DateRange = Field(..., description="Date range analyzed")
    violations_analyzed: int = Field(..., description="Number of violations analyzed", ge=0)
    root_causes: List[RootCause] = Field(default_factory=list, description="Root causes identified")
    correlations: List[Correlation] = Field(default_factory=list, description="Correlations identified")
    remediation_actions: List[str] = Field(default_factory=list, description="Recommended remediation actions")
    generated_at: str = Field(..., description="Timestamp when analysis was generated (ISO format)")
    cached: bool = Field(default=False, description="Whether response was served from cache")
    stale: Optional[bool] = Field(None, description="Whether cached data is stale (past TTL)")


# Chat Models

class Message(BaseModel):
    """Chat message model."""
    
    id: str = Field(..., description="Unique message ID")
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message text content")
    timestamp: str = Field(..., description="Message timestamp (ISO format)")
    data: Optional[dict] = Field(None, description="Structured data for assistant messages")
    tokens_used: Optional[dict] = Field(None, description="Token usage for this message")


class ChatRequest(BaseModel):
    """Request model for chat queries."""
    
    query: str = Field(..., description="User's natural language query")
    context: List[Message] = Field(default_factory=list, description="Last 10 messages from conversation")
    session_id: Optional[str] = Field(None, description="Session identifier")
    include_system_context: bool = Field(default=False, description="Include current dashboard state")
    dashboard_context: Optional[dict] = Field(None, description="Active dashboard state: selected_system, start_date, end_date")


class TokenUsage(BaseModel):
    """Token usage information."""
    
    input: int = Field(..., description="Input tokens used", ge=0)
    output: int = Field(..., description="Output tokens used", ge=0)
    cached: int = Field(default=0, description="Tokens saved by caching", ge=0)


class ChatResponse(BaseModel):
    """Response model for chat queries."""
    
    response: str = Field(..., description="AI-generated response")
    data: Optional[Any] = Field(None, description="Structured data if applicable (can be dict or list)")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up question suggestions")
    cached: bool = Field(default=False, description="Whether response was cached")
    tokens_used: TokenUsage = Field(..., description="Token usage information")
