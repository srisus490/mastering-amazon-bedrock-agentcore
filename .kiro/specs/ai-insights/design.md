# Design Document: AI-Powered Insights

## Overview

This design document describes the architecture and implementation approach for integrating AI-powered insights into the Intelligent File Monitoring System dashboard. The feature leverages Amazon Bedrock with Claude 3 Sonnet to provide three core capabilities: smart insights (natural language summaries), trend forecasting (7-day predictions), and root cause analysis (SLA violation diagnosis).

The implementation extends the existing FastAPI backend with new AI service modules and API endpoints, while enhancing the vanilla JavaScript frontend with new UI components for displaying AI-generated content. A caching layer using the existing SQLite database minimizes API costs while maintaining acceptable data freshness.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Dashboard (Frontend)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Insights   │  │  Forecasting │  │ Root Cause   │     │
│  │   Component  │  │  Component   │  │  Component   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          │ HTTP/JSON        │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AI Routes (/api/v1/ai/*)                │  │
│  │  • POST /insights    • POST /forecast                │  │
│  │  • POST /root-cause                                  │  │
│  └────────┬─────────────────────────────────────────────┘  │
│           │                                                  │
│  ┌────────▼──────────────────────────────────────────────┐ │
│  │           AI Insights Service                         │ │
│  │  • Orchestrates AI calls                             │ │
│  │  • Manages caching                                   │ │
│  │  • Aggregates data                                   │ │
│  └────┬──────────────────────────┬───────────────────────┘ │
│       │                          │                          │
│  ┌────▼────────┐          ┌──────▼──────┐                 │
│  │   Cache     │          │   Bedrock   │                 │
│  │   Manager   │          │   Client    │                 │
│  └────┬────────┘          └──────┬──────┘                 │
└───────┼────────────────────────────┼──────────────────────┘
        │                            │
        ▼                            ▼
┌──────────────┐          ┌──────────────────┐
│   SQLite     │          │  Amazon Bedrock  │
│   Database   │          │  (Claude 3)      │
└──────────────┘          └──────────────────┘
```

### Component Interaction Flow

1. **User Action**: User selects a system and date range in the dashboard
2. **Frontend Request**: Dashboard sends HTTP POST to AI endpoint with context
3. **Cache Check**: Backend checks SQLite cache for existing insights
4. **Cache Hit**: If valid cache exists, return immediately
5. **Cache Miss**: If no cache or expired, proceed to AI service
6. **Data Aggregation**: Backend queries database for relevant metrics
7. **AI Request**: Backend sends aggregated data to Amazon Bedrock
8. **AI Response**: Bedrock returns generated insights
9. **Cache Update**: Backend stores response in cache with TTL
10. **Frontend Display**: Dashboard renders insights in UI

## Components and Interfaces

### Backend Components

#### 1. AI Insights Service (`src/ai/insights_service.py`)

Core service that orchestrates AI insight generation.

```python
class AIInsightsService:
    """
    Service for generating AI-powered insights about file monitoring data.
    """
    
    def __init__(self, bedrock_client: BedrockClient, cache_manager: CacheManager):
        """Initialize with Bedrock client and cache manager."""
        pass
    
    def generate_smart_insights(
        self, 
        source_system_id: str, 
        start_date: date, 
        end_date: date
    ) -> SmartInsightsResponse:
        """
        Generate natural language insights about system health.
        
        Returns:
            SmartInsightsResponse with insights text, trends, anomalies, recommendations
        """
        pass
    
    def generate_forecast(
        self, 
        source_system_id: str, 
        historical_days: int = 60
    ) -> ForecastResponse:
        """
        Generate 7-day forecast of file arrivals.
        
        Returns:
            ForecastResponse with daily predictions and confidence levels
        """
        pass
    
    def generate_root_cause_analysis(
        self, 
        source_system_id: str, 
        start_date: date, 
        end_date: date
    ) -> RootCauseResponse:
        """
        Analyze SLA violations and suggest root causes.
        
        Returns:
            RootCauseResponse with causes, correlations, remediation actions
        """
        pass
```

#### 2. Bedrock Client (`src/ai/bedrock_client.py`)

Wrapper for Amazon Bedrock API interactions.

```python
class BedrockClient:
    """
    Client for interacting with Amazon Bedrock.
    """
    
    def __init__(self, region: str, model_id: str, timeout: int = 30):
        """Initialize Bedrock client with configuration."""
        pass
    
    def invoke_model(
        self, 
        prompt: str, 
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """
        Invoke Claude model with a prompt.
        
        Returns:
            Generated text response
        """
        pass
    
    def validate_credentials(self) -> bool:
        """Check if AWS credentials are valid."""
        pass
```

#### 3. Cache Manager (`src/ai/cache_manager.py`)

Manages caching of AI responses in SQLite.

```python
class CacheManager:
    """
    Manages caching of AI insights in database.
    """
    
    def get_cached_insight(
        self, 
        cache_key: str
    ) -> Optional[dict]:
        """
        Retrieve cached insight if valid.
        
        Returns:
            Cached data or None if expired/missing
        """
        pass
    
    def set_cached_insight(
        self, 
        cache_key: str, 
        data: dict, 
        ttl_seconds: int
    ) -> None:
        """Store insight in cache with TTL."""
        pass
    
    def generate_cache_key(
        self, 
        insight_type: str, 
        source_system_id: str, 
        **params
    ) -> str:
        """Generate unique cache key from parameters."""
        pass
    
    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries. Returns count removed."""
        pass
```

#### 4. Data Aggregator (`src/ai/data_aggregator.py`)

Aggregates database metrics for AI analysis.

```python
class DataAggregator:
    """
    Aggregates file monitoring data for AI analysis.
    """
    
    def get_file_arrival_summary(
        self, 
        source_system_id: str, 
        start_date: date, 
        end_date: date
    ) -> dict:
        """
        Get aggregated file arrival statistics.
        
        Returns:
            Dict with daily counts, timing patterns, totals
        """
        pass
    
    def get_sla_violation_summary(
        self, 
        source_system_id: str, 
        start_date: date, 
        end_date: date
    ) -> dict:
        """
        Get aggregated SLA violation data.
        
        Returns:
            Dict with violations by type, severity, dates
        """
        pass
    
    def get_historical_patterns(
        self, 
        source_system_id: str, 
        days: int
    ) -> dict:
        """
        Get historical patterns for forecasting.
        
        Returns:
            Dict with daily counts, day-of-week patterns, trends
        """
        pass
```

#### 5. Prompt Builder (`src/ai/prompt_builder.py`)

Constructs prompts for Claude based on data and task.

```python
class PromptBuilder:
    """
    Builds prompts for different AI tasks.
    """
    
    def build_insights_prompt(self, data_summary: dict) -> str:
        """Build prompt for smart insights generation."""
        pass
    
    def build_forecast_prompt(self, historical_data: dict) -> str:
        """Build prompt for trend forecasting."""
        pass
    
    def build_root_cause_prompt(
        self, 
        violations: dict, 
        context: dict
    ) -> str:
        """Build prompt for root cause analysis."""
        pass
```

### API Endpoints

#### POST /api/v1/ai/insights

Generate smart insights for a system.

**Request:**
```json
{
  "source_system_id": "PROD_SALES",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

**Response:**
```json
{
  "source_system_id": "PROD_SALES",
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "insights": "The PROD_SALES system shows healthy file arrival patterns...",
  "trends": [
    {
      "type": "increasing",
      "description": "File counts increased by 15% over the period",
      "confidence": "high"
    }
  ],
  "anomalies": [
    {
      "date": "2024-01-15",
      "description": "Unusual spike of 45 files (normal: 25-30)",
      "severity": "low"
    }
  ],
  "recommendations": [
    "Consider adjusting SLA thresholds to account for growth trend",
    "Investigate cause of January 15th spike"
  ],
  "generated_at": "2024-01-31T10:30:00Z",
  "cached": false
}
```

#### POST /api/v1/ai/forecast

Generate 7-day forecast for a system.

**Request:**
```json
{
  "source_system_id": "PROD_SALES",
  "historical_days": 60
}
```

**Response:**
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
      "confidence_range": {
        "min": 25,
        "max": 31
      }
    },
    {
      "date": "2024-02-02",
      "predicted_count": 27,
      "confidence_level": "high",
      "confidence_range": {
        "min": 24,
        "max": 30
      }
    }
  ],
  "patterns_identified": [
    "Weekday average: 28 files",
    "Weekend average: 15 files",
    "Slight upward trend observed"
  ],
  "cached": false
}
```

#### POST /api/v1/ai/root-cause

Analyze root causes of SLA violations.

**Request:**
```json
{
  "source_system_id": "PROD_SALES",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

**Response:**
```json
{
  "source_system_id": "PROD_SALES",
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "violations_analyzed": 5,
  "root_causes": [
    {
      "cause": "Late file arrivals",
      "affected_dates": ["2024-01-10", "2024-01-17"],
      "description": "Files arrived 2-3 hours after expected time",
      "confidence": "high"
    },
    {
      "cause": "Missing files",
      "affected_dates": ["2024-01-22"],
      "description": "Expected files did not arrive",
      "confidence": "high"
    }
  ],
  "correlations": [
    {
      "pattern": "Late arrivals correlate with Monday mornings",
      "strength": "moderate"
    }
  ],
  "remediation_actions": [
    "Review upstream system processing on Sunday nights",
    "Consider extending Monday morning SLA window by 1 hour",
    "Set up alerts for missing files by 10 AM"
  ],
  "generated_at": "2024-01-31T10:30:00Z",
  "cached": false
}
```

### Frontend Components

#### 1. AI Insights Manager (`web-dashboard/js/ai-insights-manager.js`)

Manages AI insights display and interactions.

```javascript
class AIInsightsManager {
    constructor(apiClient, uiManager) {
        this.apiClient = apiClient;
        this.uiManager = uiManager;
        this.currentSystemId = null;
        this.currentDateRange = null;
    }
    
    async loadInsights(systemId, startDate, endDate) {
        // Load all three types of insights
    }
    
    async loadSmartInsights(systemId, startDate, endDate) {
        // Load and display smart insights
    }
    
    async loadForecast(systemId) {
        // Load and display forecast
    }
    
    async loadRootCause(systemId, startDate, endDate) {
        // Load and display root cause analysis
    }
    
    renderInsights(data) {
        // Render insights in UI
    }
    
    renderForecast(data) {
        // Render forecast with chart
    }
    
    renderRootCause(data) {
        // Render root cause analysis
    }
    
    handleError(error, insightType) {
        // Display user-friendly error messages
    }
}
```

#### 2. API Client Extension (`web-dashboard/js/api-client.js`)

Add new methods to existing APIClient class.

```javascript
// Add to existing APIClient class

async getSmartInsights(sourceSystemId, startDate, endDate) {
    const url = `${this.baseURL}/api/v1/ai/insights`;
    return this._fetchWithRetry(url, {
        method: 'POST',
        body: JSON.stringify({
            source_system_id: sourceSystemId,
            start_date: startDate,
            end_date: endDate
        })
    });
}

async getForecast(sourceSystemId, historicalDays = 60) {
    const url = `${this.baseURL}/api/v1/ai/forecast`;
    return this._fetchWithRetry(url, {
        method: 'POST',
        body: JSON.stringify({
            source_system_id: sourceSystemId,
            historical_days: historicalDays
        })
    });
}

async getRootCauseAnalysis(sourceSystemId, startDate, endDate) {
    const url = `${this.baseURL}/api/v1/ai/root-cause`;
    return this._fetchWithRetry(url, {
        method: 'POST',
        body: JSON.stringify({
            source_system_id: sourceSystemId,
            start_date: startDate,
            end_date: endDate
        })
    });
}
```

## Data Models

### Response Models (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

class Trend(BaseModel):
    type: str = Field(..., description="Type of trend: increasing, decreasing, stable")
    description: str
    confidence: str = Field(..., description="Confidence level: high, medium, low")

class Anomaly(BaseModel):
    date: date
    description: str
    severity: str = Field(..., description="Severity: high, medium, low")

class SmartInsightsResponse(BaseModel):
    source_system_id: str
    date_range: dict
    insights: str = Field(..., description="Natural language insights")
    trends: List[Trend]
    anomalies: List[Anomaly]
    recommendations: List[str]
    generated_at: datetime
    cached: bool

class ConfidenceRange(BaseModel):
    min: int
    max: int

class DailyPrediction(BaseModel):
    date: date
    predicted_count: int
    confidence_level: str
    confidence_range: ConfidenceRange

class ForecastResponse(BaseModel):
    source_system_id: str
    forecast_generated_at: datetime
    historical_period: dict
    predictions: List[DailyPrediction]
    patterns_identified: List[str]
    cached: bool

class RootCause(BaseModel):
    cause: str
    affected_dates: List[date]
    description: str
    confidence: str

class Correlation(BaseModel):
    pattern: str
    strength: str = Field(..., description="Strength: strong, moderate, weak")

class RootCauseResponse(BaseModel):
    source_system_id: str
    date_range: dict
    violations_analyzed: int
    root_causes: List[RootCause]
    correlations: List[Correlation]
    remediation_actions: List[str]
    generated_at: datetime
    cached: bool
```

### Request Models (Pydantic)

```python
class InsightsRequest(BaseModel):
    source_system_id: str
    start_date: date
    end_date: date

class ForecastRequest(BaseModel):
    source_system_id: str
    historical_days: int = Field(default=60, ge=30, le=90)

class RootCauseRequest(BaseModel):
    source_system_id: str
    start_date: date
    end_date: date
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Cache Key Uniqueness

*For any* two different combinations of insight type, system ID, and parameters, the generated cache keys should be distinct to prevent cache collisions.

**Validates: Requirements 6.1**

### Property 2: Cache TTL Enforcement

*For any* cached insight, if the current time minus the cached timestamp exceeds the TTL, the system should not return the cached data and should call the AI service instead.

**Validates: Requirements 6.4, 6.6, 6.7**

### Property 3: Insights Context Completeness

*For any* smart insights request, the data sent to the AI service should include file arrival counts, timing patterns, and SLA scores for the specified date range.

**Validates: Requirements 1.1, 1.2**

### Property 4: Forecast Date Range

*For any* forecast response, the predictions array should contain exactly 7 elements with consecutive dates starting from tomorrow.

**Validates: Requirements 2.2**

### Property 5: Root Cause Conditional Display

*For any* root cause analysis request, if no SLA violations exist in the date range, the response should indicate healthy status rather than attempting to analyze non-existent violations.

**Validates: Requirements 3.6**

### Property 6: Data Sanitization

*For any* user input sent to the AI service, the system should remove or escape special characters that could be used for prompt injection.

**Validates: Requirements 9.5**

### Property 7: Aggregated Data Only

*For any* AI service request, the data payload should contain only aggregated metrics and should not include individual file names or file paths.

**Validates: Requirements 9.1**

### Property 8: Error Fallback to Cache

*For any* AI service request that fails, if cached data exists regardless of TTL, the system should return the cached data with a flag indicating it may be stale.

**Validates: Requirements 7.1**

### Property 9: Concurrent Request Handling

*For any* set of simultaneous AI insight requests for different systems, the system should process them concurrently without blocking each other.

**Validates: Requirements 10.3**

### Property 10: Historical Data Limit

*For any* forecast request, the system should limit the historical data sent to the AI service to a maximum of 90 days even if more data exists.

**Validates: Requirements 10.4, 10.5**

### Property 11: Response Time with Cache

*For any* AI insight request where valid cached data exists, the response time should be less than 100 milliseconds.

**Validates: Requirements 10.1**

### Property 12: Confidence Level Consistency

*For any* forecast prediction, the confidence range minimum should be less than or equal to the predicted count, and the predicted count should be less than or equal to the confidence range maximum.

**Validates: Requirements 2.3**

## Error Handling

### Error Categories

1. **AI Service Errors**
   - Bedrock API unavailable (503)
   - Authentication failures (401)
   - Rate limiting (429)
   - Timeout (504)
   - Invalid response format (500)

2. **Data Errors**
   - System not found (404)
   - Invalid date range (400)
   - Insufficient historical data (400)

3. **Cache Errors**
   - Database connection failure (fallback to no cache)
   - Cache corruption (clear and retry)

### Error Handling Strategy

```python
class AIInsightsService:
    def generate_smart_insights(self, source_system_id, start_date, end_date):
        try:
            # Check cache first
            cached = self.cache_manager.get_cached_insight(cache_key)
            if cached:
                return cached
            
            # Aggregate data
            data = self.data_aggregator.get_file_arrival_summary(...)
            
            # Call AI service with retry
            try:
                response = self.bedrock_client.invoke_model(prompt)
            except BedrockTimeoutError:
                # Retry once
                response = self.bedrock_client.invoke_model(prompt)
            except BedrockUnavailableError:
                # Return stale cache if available
                stale_cache = self.cache_manager.get_cached_insight(
                    cache_key, 
                    ignore_ttl=True
                )
                if stale_cache:
                    stale_cache['cached'] = True
                    stale_cache['stale'] = True
                    return stale_cache
                raise
            
            # Cache and return
            self.cache_manager.set_cached_insight(cache_key, response, ttl)
            return response
            
        except Exception as e:
            logger.error(f"Insights generation failed: {e}")
            raise
```

### Frontend Error Display

```javascript
handleError(error, insightType) {
    const messages = {
        503: "AI service is temporarily unavailable. Showing cached data if available.",
        429: "Too many requests. Please try again in a moment.",
        404: "System not found. Please select a valid system.",
        400: "Invalid request. Please check your date range.",
        500: "An error occurred generating insights. Please try again."
    };
    
    const message = messages[error.status] || messages[500];
    this.uiManager.showError(message, insightType);
}
```

## Testing Strategy

### Unit Testing

Unit tests will verify specific examples and edge cases:

- **Cache Manager**: Test cache key generation, TTL expiration, cleanup
- **Data Aggregator**: Test aggregation logic with sample data
- **Prompt Builder**: Test prompt construction with various data inputs
- **API Endpoints**: Test request validation, error responses
- **Frontend Components**: Test rendering with mock data, error handling

### Property-Based Testing

Property tests will verify universal properties across all inputs using a property-based testing library (Hypothesis for Python, fast-check for JavaScript). Each test will run a minimum of 100 iterations.

- **Property 1 (Cache Key Uniqueness)**: Generate random combinations of parameters, verify all cache keys are unique
  - **Feature: ai-insights, Property 1**: Cache key uniqueness
  
- **Property 2 (Cache TTL Enforcement)**: Generate random timestamps and TTLs, verify cache expiration logic
  - **Feature: ai-insights, Property 2**: Cache TTL enforcement
  
- **Property 6 (Data Sanitization)**: Generate random strings with special characters, verify sanitization
  - **Feature: ai-insights, Property 6**: Data sanitization
  
- **Property 10 (Historical Data Limit)**: Generate random day counts, verify data is limited to 90 days
  - **Feature: ai-insights, Property 10**: Historical data limit
  
- **Property 12 (Confidence Level Consistency)**: Generate random predictions, verify confidence ranges are valid
  - **Feature: ai-insights, Property 12**: Confidence level consistency

### Integration Testing

Integration tests will verify component interactions:

- **End-to-End AI Flow**: Mock Bedrock, test full request flow from API to cache
- **Cache Integration**: Test cache operations with real SQLite database
- **Frontend Integration**: Test API client with mock backend responses
- **Error Scenarios**: Test error handling with simulated failures

### Manual Testing

Manual testing will verify:

- AI insight quality and relevance
- Dashboard UI/UX for AI components
- Performance under realistic load
- Error message clarity
