# Implementation Plan: AI-Powered Insights

## Overview

This implementation plan breaks down the AI-powered insights feature into discrete coding tasks. The feature adds three AI capabilities to the dashboard: smart insights (natural language summaries), trend forecasting (7-day predictions), and root cause analysis (SLA violation diagnosis). Implementation follows a bottom-up approach, building core services first, then API endpoints, and finally frontend integration.

## Tasks

- [x] 1. Set up AI module infrastructure
  - Create directory structure for AI insights components
  - Add Amazon Bedrock SDK dependencies to pyproject.toml
  - Create configuration for Bedrock settings (region, model ID, timeouts)
  - Set up logging for AI service operations
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 2. Implement Bedrock Client
  - [x] 2.1 Create BedrockClient class in src/ai/bedrock_client.py
    - Implement __init__ with region, model_id, and timeout parameters
    - Implement invoke_model method using boto3 bedrock-runtime client
    - Implement validate_credentials method to check AWS credentials
    - Add error handling for Bedrock-specific exceptions
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 2.2 Write unit tests for BedrockClient
    - Test initialization with valid and invalid credentials
    - Test invoke_model with mock Bedrock responses
    - Test timeout handling
    - Test error scenarios (auth failures, rate limits)
    - _Requirements: 8.2, 8.4_

- [x] 3. Implement Cache Manager
  - [x] 3.1 Create CacheManager class in src/ai/cache_manager.py
    - Implement generate_cache_key method using hash of parameters
    - Implement get_cached_insight method with TTL checking
    - Implement set_cached_insight method using dashboard_cache table
    - Implement cleanup_expired_cache method
    - Use SQLAlchemy to interact with DashboardCacheModel
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.8_

  - [ ]* 3.2 Write property test for cache key uniqueness
    - **Property 1: Cache Key Uniqueness**
    - **Validates: Requirements 6.1**

  - [ ]* 3.3 Write property test for TTL enforcement
    - **Property 2: Cache TTL Enforcement**
    - **Validates: Requirements 6.4, 6.6, 6.7**

  - [ ]* 3.4 Write unit tests for CacheManager
    - Test cache hit and miss scenarios
    - Test TTL expiration
    - Test cleanup of expired entries
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 4. Implement Data Aggregator
  - [x] 4.1 Create DataAggregator class in src/ai/data_aggregator.py
    - Implement get_file_arrival_summary method
    - Query FileArrivalModel for daily counts and timing patterns
    - Implement get_sla_violation_summary method
    - Query SLAViolationModel and group by type and severity
    - Implement get_historical_patterns method
    - Calculate day-of-week patterns and trends
    - Limit historical data to maximum 90 days
    - _Requirements: 1.1, 1.2, 3.1, 3.2, 10.4, 10.5_

  - [ ]* 4.2 Write property test for historical data limit
    - **Property 10: Historical Data Limit**
    - **Validates: Requirements 10.4, 10.5**

  - [ ]* 4.3 Write property test for aggregated data only
    - **Property 7: Aggregated Data Only**
    - **Validates: Requirements 9.1**

  - [ ]* 4.4 Write unit tests for DataAggregator
    - Test aggregation with sample database data
    - Test date range filtering
    - Test handling of systems with no data
    - _Requirements: 1.1, 1.2, 3.1, 3.2_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement Prompt Builder
  - [x] 6.1 Create PromptBuilder class in src/ai/prompt_builder.py
    - Implement build_insights_prompt method
    - Create structured prompt with data summary and instructions
    - Implement build_forecast_prompt method
    - Create prompt with historical patterns and forecasting instructions
    - Implement build_root_cause_prompt method
    - Create prompt with violations and context for analysis
    - Sanitize all input data to prevent prompt injection
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 9.5_

  - [ ]* 6.2 Write property test for data sanitization
    - **Property 6: Data Sanitization**
    - **Validates: Requirements 9.5**

  - [ ]* 6.3 Write unit tests for PromptBuilder
    - Test prompt generation with various data inputs
    - Test sanitization of special characters
    - Test prompt structure and formatting
    - _Requirements: 9.5_

- [x] 7. Implement AI Insights Service
  - [x] 7.1 Create AIInsightsService class in src/ai/insights_service.py
    - Implement __init__ with BedrockClient, CacheManager, DataAggregator dependencies
    - Implement generate_smart_insights method
    - Check cache, aggregate data, build prompt, call Bedrock, parse response
    - Implement generate_forecast method
    - Get historical patterns, build prompt, call Bedrock, parse predictions
    - Implement generate_root_cause_analysis method
    - Get violations, build prompt, call Bedrock, parse causes
    - Add error handling with fallback to stale cache
    - Add retry logic for timeouts
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 7.2 Write property test for insights context completeness
    - **Property 3: Insights Context Completeness**
    - **Validates: Requirements 1.1, 1.2**

  - [ ]* 7.3 Write property test for forecast date range
    - **Property 4: Forecast Date Range**
    - **Validates: Requirements 2.2**

  - [ ]* 7.4 Write property test for root cause conditional display
    - **Property 5: Root Cause Conditional Display**
    - **Validates: Requirements 3.6**

  - [ ]* 7.5 Write property test for error fallback to cache
    - **Property 8: Error Fallback to Cache**
    - **Validates: Requirements 7.1**

  - [ ]* 7.6 Write unit tests for AIInsightsService
    - Test each method with mock dependencies
    - Test cache hit and miss flows
    - Test error handling scenarios
    - Test retry logic
    - _Requirements: 1.6, 1.7, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 8. Create Pydantic models for API
  - [x] 8.1 Create models in src/ai/models.py
    - Define InsightsRequest, ForecastRequest, RootCauseRequest
    - Define SmartInsightsResponse with Trend and Anomaly nested models
    - Define ForecastResponse with DailyPrediction and ConfidenceRange nested models
    - Define RootCauseResponse with RootCause and Correlation nested models
    - Add field validation and descriptions
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 8.2 Write unit tests for Pydantic models
    - Test model validation with valid and invalid data
    - Test serialization and deserialization
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement API endpoints
  - [x] 10.1 Create AI routes in src/api/routes/ai_insights.py
    - Create FastAPI router for /api/v1/ai prefix
    - Implement POST /insights endpoint
    - Accept InsightsRequest, call AIInsightsService, return SmartInsightsResponse
    - Implement POST /forecast endpoint
    - Accept ForecastRequest, call AIInsightsService, return ForecastResponse
    - Implement POST /root-cause endpoint
    - Accept RootCauseRequest, call AIInsightsService, return RootCauseResponse
    - Add error handling with appropriate HTTP status codes
    - Add request validation
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 7.2, 7.3, 7.6, 7.7_

  - [ ]* 10.2 Write property test for concurrent request handling
    - **Property 9: Concurrent Request Handling**
    - **Validates: Requirements 10.3**

  - [ ]* 10.3 Write property test for response time with cache
    - **Property 11: Response Time with Cache**
    - **Validates: Requirements 10.1**

  - [ ]* 10.4 Write unit tests for API endpoints
    - Test each endpoint with valid requests
    - Test validation errors (400)
    - Test system not found (404)
    - Test AI service errors (500, 503)
    - _Requirements: 4.7, 7.7_

- [x] 11. Register AI routes in main app
  - [x] 11.1 Update src/api/app.py
    - Import ai_insights router
    - Register router with app.include_router
    - Add to existing AI routes section
    - _Requirements: 4.1, 4.3, 4.5_

- [x] 12. Implement frontend API client methods
  - [x] 12.1 Extend APIClient class in web-dashboard/js/api-client.js
    - Add getSmartInsights method with POST to /api/v1/ai/insights
    - Add getForecast method with POST to /api/v1/ai/forecast
    - Add getRootCauseAnalysis method with POST to /api/v1/ai/root-cause
    - Use existing _fetchWithRetry for error handling
    - _Requirements: 4.1, 4.3, 4.5, 5.5_

  - [ ]* 12.2 Write unit tests for API client methods
    - Test each method with mock fetch responses
    - Test error handling
    - _Requirements: 5.5_

- [x] 13. Create AI Insights Manager frontend component
  - [x] 13.1 Create AIInsightsManager class in web-dashboard/js/ai-insights-manager.js
    - Implement constructor with apiClient and uiManager dependencies
    - Implement loadInsights method to load all three insight types
    - Implement loadSmartInsights method
    - Implement loadForecast method
    - Implement loadRootCause method
    - Implement renderInsights method to display smart insights
    - Implement renderForecast method with Chart.js visualization
    - Implement renderRootCause method with conditional display
    - Implement handleError method for user-friendly error messages
    - Add loading state management
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 7.6, 7.7_

  - [ ]* 13.2 Write unit tests for AIInsightsManager
    - Test rendering with mock data
    - Test error handling
    - Test loading states
    - _Requirements: 5.3, 5.5, 7.6_

- [x] 14. Add AI insights UI to dashboard HTML
  - [x] 14.1 Update web-dashboard/index.html
    - Add AI insights section after system overview
    - Create collapsible panels for insights, forecast, and root cause
    - Add loading spinners for each panel
    - Add error message containers
    - Add chart canvas for forecast visualization
    - _Requirements: 5.1, 5.2, 5.3, 5.7_

- [x] 15. Add AI insights CSS styling
  - [x] 15.1 Update web-dashboard/css/main.css
    - Add styles for AI insights section
    - Style collapsible panels
    - Style loading spinners
    - Style error messages
    - Style forecast chart container
    - Ensure responsive design
    - _Requirements: 5.2, 5.3_

- [x] 16. Integrate AI insights into main app
  - [x] 16.1 Update web-dashboard/js/app.js
    - Import AIInsightsManager
    - Initialize AIInsightsManager with apiClient and uiManager
    - Add event listener for system selection changes
    - Add event listener for date range changes
    - Call loadInsights when context changes
    - Handle asynchronous loading without blocking other features
    - _Requirements: 5.1, 5.4, 10.6_

  - [ ]* 16.2 Write integration tests for dashboard
    - Test AI insights loading on system selection
    - Test AI insights refresh on date range change
    - Test error scenarios
    - _Requirements: 5.4, 5.5_

- [ ] 17. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 18. Add environment configuration
  - [ ] 18.1 Update .env.example
    - Add BEDROCK_REGION variable
    - Add BEDROCK_MODEL_ID variable (default: anthropic.claude-3-sonnet-20240229-v1:0)
    - Add BEDROCK_TIMEOUT variable (default: 30)
    - Add BEDROCK_MAX_TOKENS variable (default: 4000)
    - Add AI_CACHE_TTL_INSIGHTS variable (default: 3600)
    - Add AI_CACHE_TTL_FORECAST variable (default: 21600)
    - Add documentation for each variable
    - _Requirements: 8.1, 8.3, 8.4, 8.5, 8.6, 8.7_

- [ ] 19. Add graceful degradation for missing configuration
  - [ ] 19.1 Update AIInsightsService initialization
    - Check for required environment variables
    - Log warning if Bedrock configuration is missing
    - Return graceful error responses when AI is not configured
    - Update API endpoints to return 501 when AI is not configured
    - _Requirements: 8.6, 7.7_

  - [ ]* 19.2 Write unit tests for configuration handling
    - Test behavior with missing environment variables
    - Test graceful degradation
    - _Requirements: 8.6_

- [ ] 20. Add property test for confidence level consistency
  - [ ]* 20.1 Write property test for forecast confidence ranges
    - **Property 12: Confidence Level Consistency**
    - **Validates: Requirements 2.3**

- [ ] 21. Final integration and wiring
  - [ ] 21.1 Wire all components together
    - Ensure AIInsightsService is properly initialized in API routes
    - Ensure frontend components are properly connected
    - Test end-to-end flow from UI to AI service and back
    - Verify caching works correctly
    - Verify error handling works across all layers
    - _Requirements: All_

  - [ ]* 21.2 Write end-to-end integration tests
    - Test complete flow with mock Bedrock
    - Test caching behavior
    - Test error propagation
    - _Requirements: All_

- [ ] 22. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis (Python) and fast-check (JavaScript)
- Unit tests validate specific examples and edge cases
- The implementation follows a bottom-up approach: core services → API → frontend
- AI service calls are asynchronous and non-blocking
- Caching is critical for cost control and performance
