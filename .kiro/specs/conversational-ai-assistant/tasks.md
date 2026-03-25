# Implementation Plan: Conversational AI Assistant

## Overview

This implementation plan breaks down the Conversational AI Assistant feature into discrete coding tasks. The approach follows an incremental strategy: backend API first, then frontend integration, with testing integrated throughout. Each task builds on previous work to ensure continuous integration.

## Tasks

- [x] 1. Set up backend infrastructure for chat feature
  - Create new API route module `src/api/routes/chat.py`
  - Define Pydantic models for chat requests/responses in `src/ai/models.py`
  - Add chat router to main FastAPI app in `src/api/app.py`
  - _Requirements: 1.1, 2.1, 14.5_

- [ ]* 1.1 Write unit tests for chat endpoint setup
  - Test endpoint registration and basic health check
  - Test request/response model validation
  - _Requirements: 1.1_

- [x] 2. Implement Query Processor for natural language parsing
  - [x] 2.1 Create `src/ai/query_processor.py` with QueryProcessor class
    - Implement `parseQuery()` method to extract intent and entities
    - Implement `identifyQueryType()` to classify queries (SYSTEM_HEALTH, SLA_VIOLATIONS, etc.)
    - Implement `extractSystemNames()` to find system references in queries
    - Implement `extractDateReferences()` to parse date mentions
    - Implement `resolveContextReferences()` to handle "it", "that system", etc.
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 5.3_

  - [ ]* 2.2 Write property test for system name extraction
    - **Property 4: System Name Entity Extraction**
    - **Validates: Requirements 2.2**

  - [ ]* 2.3 Write property test for context reference resolution
    - **Property 19: Context-Based Reference Resolution**
    - **Validates: Requirements 5.3**

  - [ ]* 2.4 Write unit tests for query type classification
    - Test classification of health, violations, trends, comparison, root cause queries
    - Test ambiguous query detection
    - Test unparseable query handling
    - _Requirements: 2.4, 2.5_

- [x] 3. Implement SQL Query Generator
  - [x] 3.1 Create `src/ai/sql_query_generator.py` with SQLQueryGenerator class
    - Implement `generateHealthQuery()` for system health queries
    - Implement `generateViolationsQuery()` for SLA violation queries
    - Implement `generateTrendsQuery()` for trend analysis queries
    - Implement `generateComparisonQuery()` for system comparison queries
    - Implement `validateQuery()` to ensure query safety (read-only, parameterized)
    - Add result set limiting (max 1000 rows)
    - Add query timeout configuration (5 seconds)
    - _Requirements: 2.3, 3.1, 3.2, 3.3, 3.4_

  - [ ]* 3.2 Write property test for SQL query generation
    - **Property 5: SQL Query Generation for Data Requests**
    - **Validates: Requirements 2.3**

  - [ ]* 3.3 Write property test for SQL query validation
    - **Property 8: SQL Query Validation**
    - **Validates: Requirements 3.1**

  - [ ]* 3.4 Write property test for result set limiting
    - **Property 10: Result Set Size Limiting**
    - **Validates: Requirements 3.3**

  - [ ]* 3.5 Write unit tests for query generation
    - Test each query type with sample inputs
    - Test parameterization and SQL injection prevention
    - Test expensive query detection
    - _Requirements: 3.1, 3.4_

- [x] 4. Implement Response Generator with Bedrock integration
  - [x] 4.1 Create `src/ai/response_generator.py` with ResponseGenerator class
    - Implement `generateResponse()` to create natural language responses
    - Implement `buildPrompt()` to construct Bedrock prompts with context
    - Implement `formatDataForPrompt()` to summarize query results
    - Implement `extractResponse()` to parse Bedrock output
    - Add token limiting (max 1000 output tokens)
    - Integrate with existing BedrockClient from `src/ai/bedrock_client.py`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 8.3, 8.5, 8.6, 14.5_

  - [ ]* 4.2 Write property test for response generation
    - **Property 13: Tabular Data Formatting**
    - **Validates: Requirements 4.2**

  - [ ]* 4.3 Write property test for empty result handling
    - **Property 15: Empty Result Explanation**
    - **Validates: Requirements 4.4**

  - [ ]* 4.4 Write property test for response token limiting
    - **Property 30: Response Token Limiting**
    - **Validates: Requirements 8.6**

  - [ ]* 4.5 Write unit tests for response formatting
    - Test table formatting for multi-row results
    - Test metric highlighting
    - Test timestamp inclusion
    - Test integration with BedrockClient
    - _Requirements: 4.2, 4.3, 4.5_

- [x] 5. Implement Cache Manager for cost optimization
  - [x] 5.1 Create `src/ai/chat_cache_manager.py` with ChatCacheManager class
    - Implement `getCachedResponse()` to retrieve cached responses
    - Implement `setCachedResponse()` to store responses with TTL
    - Implement `generateQueryHash()` to create cache keys from query + context
    - Implement `clearCache()` to remove all cached responses
    - Use in-memory dict with LRU eviction (max 1000 entries)
    - Set TTL: 5 minutes for data queries, 1 hour for static queries
    - _Requirements: 7.5, 8.2, 8.3, 15.5_

  - [ ]* 5.2 Write property test for response caching
    - **Property 28: Response Caching for Repeated Queries**
    - **Validates: Requirements 8.2**

  - [ ]* 5.3 Write property test for cache hit rate tracking
    - **Property 56: Cache Hit Rate Tracking**
    - **Validates: Requirements 15.5**

  - [ ]* 5.4 Write unit tests for cache operations
    - Test cache hit/miss scenarios
    - Test TTL expiration
    - Test LRU eviction
    - Test cache key generation
    - _Requirements: 8.2, 15.5_

- [x] 6. Implement Conversation Context Manager
  - [x] 6.1 Create `src/ai/conversation_context.py` with ConversationContext class
    - Implement context initialization with empty message list
    - Implement `addMessage()` to append messages
    - Implement size limiting (max 10 messages with automatic eviction)
    - Implement `clear()` to reset context
    - Implement `toDict()` for serialization
    - _Requirements: 5.1, 5.2, 5.4, 5.5_

  - [ ]* 6.2 Write property test for context size limiting
    - **Property 18: Conversation Context Size Limiting**
    - **Validates: Requirements 5.2, 8.4**

  - [ ]* 6.3 Write property test for context clearing
    - **Property 20: Conversation Context Clearing**
    - **Validates: Requirements 5.5, 10.4**

  - [ ]* 6.4 Write unit tests for context management
    - Test message addition and eviction
    - Test context serialization
    - Test context clearing
    - _Requirements: 5.1, 5.2, 5.5_

- [x] 7. Implement main Chat Endpoint
  - [x] 7.1 Implement POST /api/v1/chat/query endpoint in `src/api/routes/chat.py`
    - Accept ChatRequest (query, context, sessionId, includeSystemContext)
    - Integrate QueryProcessor to parse query
    - Integrate SQLQueryGenerator to generate queries
    - Execute database queries with error handling
    - Integrate ResponseGenerator to create responses
    - Integrate ChatCacheManager for caching
    - Return ChatResponse (response, data, suggestions, cached, tokensUsed)
    - Add comprehensive error handling for all failure modes
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.5, 4.1, 6.1, 6.2, 6.3, 6.4, 6.5, 11.1, 11.2, 11.4, 11.5_

  - [ ]* 7.2 Write integration tests for chat endpoint
    - Test end-to-end query flow for each query type
    - Test error handling scenarios
    - Test caching behavior
    - Test context integration
    - _Requirements: 2.1, 3.5, 11.1, 11.2_

- [x] 8. Implement additional chat endpoints
  - [x] 8.1 Implement POST /api/v1/chat/clear endpoint
    - Clear cache for specific session or all sessions
    - Return success confirmation
    - _Requirements: 5.5_

  - [x] 8.2 Implement GET /api/v1/chat/examples endpoint
    - Return list of example questions
    - Include examples for: health, violations, trends, comparisons, root cause
    - Support context-aware examples based on selected system
    - _Requirements: 9.1, 9.2, 9.4, 9.5_

  - [x] 8.3 Implement GET /api/v1/chat/health endpoint
    - Check Bedrock connectivity
    - Check database connectivity
    - Return service status
    - _Requirements: 11.1_

  - [ ]* 8.4 Write unit tests for additional endpoints
    - Test cache clearing
    - Test example generation
    - Test health check
    - _Requirements: 5.5, 9.1, 11.1_

- [x] 9. Implement cost monitoring and logging
  - [x] 9.1 Add token usage logging to ResponseGenerator
    - Log input/output token counts for each Bedrock call
    - Log cache hits/misses
    - Log query processing time
    - _Requirements: 15.1, 15.5_

  - [x] 9.2 Create `src/ai/cost_monitor.py` with CostMonitor class
    - Implement token usage tracking per hour/day
    - Implement alert mechanism for threshold breaches (100K tokens/hour)
    - Implement cost calculation based on token usage
    - Implement circuit breaker for daily cost threshold
    - _Requirements: 15.2, 15.3, 15.4_

  - [ ]* 9.3 Write property test for token usage logging
    - **Property 52: Bedrock API Call Logging**
    - **Validates: Requirements 15.1**

  - [ ]* 9.4 Write property test for threshold alerting
    - **Property 53: Token Usage Threshold Alerting**
    - **Validates: Requirements 15.2**

  - [ ]* 9.5 Write unit tests for cost monitoring
    - Test token tracking
    - Test alert triggering
    - Test circuit breaker activation
    - _Requirements: 15.2, 15.3_

- [x] 10. Checkpoint - Backend complete, test all endpoints
  - Ensure all backend tests pass
  - Test API endpoints manually with curl or Postman
  - Verify Bedrock integration works
  - Verify caching reduces costs
  - Ask the user if questions arise

- [x] 11. Implement frontend Chat Widget UI component
  - [x] 11.1 Create `web-dashboard/js/chat-widget.js` with ChatWidget class
    - Implement floating chat button in bottom-right corner
    - Implement expand/collapse functionality
    - Implement message display area with scrolling
    - Implement input field with send button
    - Implement typing indicator
    - Implement example questions display
    - Add CSS styling in `web-dashboard/css/chat.css`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 7.3, 9.1, 9.2, 9.3_

  - [ ]* 11.2 Write unit tests for ChatWidget
    - Test widget toggle functionality
    - Test message rendering
    - Test input handling
    - _Requirements: 1.2, 1.3_

- [x] 12. Implement frontend Chat Manager for state and API communication
  - [x] 12.1 Create `web-dashboard/js/chat-manager.js` with ChatManager class
    - Implement conversation context management (last 10 messages)
    - Implement `sendQuery()` to call backend API
    - Implement session storage persistence
    - Implement `saveToSessionStorage()` and `loadFromSessionStorage()`
    - Implement `clearContext()` for history clearing
    - Generate unique session IDs
    - _Requirements: 5.1, 5.2, 5.5, 10.1, 10.2, 10.5_

  - [ ]* 12.2 Write property test for context size limiting (frontend)
    - **Property 18: Conversation Context Size Limiting** (frontend validation)
    - **Validates: Requirements 5.2**

  - [ ]* 12.3 Write property test for session storage persistence
    - **Property 35: Session Storage Persistence**
    - **Validates: Requirements 10.1**

  - [ ]* 12.4 Write unit tests for ChatManager
    - Test context management
    - Test API communication
    - Test session storage operations
    - _Requirements: 5.2, 10.1, 10.2_

- [x] 13. Implement frontend Message Formatter
  - [x] 13.1 Create `web-dashboard/js/message-formatter.js` with MessageFormatter class
    - Implement `formatTable()` to convert data to HTML tables
    - Implement `formatMetric()` to highlight single metrics
    - Implement `formatList()` to create bullet lists
    - Implement `formatTimestamp()` for consistent date formatting
    - Implement number formatting with thousand separators
    - Implement percentage formatting with precision
    - _Requirements: 4.2, 4.3, 13.1, 13.2, 13.3, 13.4, 13.5_

  - [ ]* 13.2 Write property test for date format consistency
    - **Property 46: Date Format Consistency**
    - **Validates: Requirements 13.3**

  - [ ]* 13.3 Write property test for number formatting
    - **Property 47: Large Number Formatting**
    - **Validates: Requirements 13.4**

  - [ ]* 13.4 Write unit tests for message formatting
    - Test table formatting
    - Test metric highlighting
    - Test list formatting
    - Test date/number/percentage formatting
    - _Requirements: 4.2, 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 14. Integrate chat feature with existing dashboard
  - [x] 14.1 Add ChatWidget to main dashboard in `web-dashboard/js/app.js`
    - Initialize ChatWidget and ChatManager on page load
    - Connect to existing APIClient
    - Integrate with dashboard state (selected system, date range, filters)
    - Pass dashboard context to chat queries when includeSystemContext is true
    - _Requirements: 1.5, 14.1, 14.2, 14.4_

  - [x] 14.2 Add keyboard navigation support
    - Implement Tab navigation through chat interface
    - Implement Enter to send messages
    - Implement ESC to close chat
    - Add focus indicators
    - _Requirements: 12.1, 12.4_

  - [x] 14.3 Add accessibility features
    - Add ARIA labels to all interactive elements
    - Ensure color contrast meets WCAG standards
    - Support text resizing up to 200%
    - _Requirements: 12.3, 12.5_

  - [ ]* 14.4 Write integration tests for dashboard integration
    - Test chat widget initialization
    - Test context passing from dashboard
    - Test keyboard navigation
    - _Requirements: 1.5, 12.1, 14.4_

- [x] 15. Implement error handling and offline support
  - [x] 15.1 Add error handling to ChatManager
    - Handle Bedrock service unavailability
    - Handle database query failures
    - Handle network connection loss with message queuing
    - Handle rate limit errors
    - Handle authentication failures
    - Display user-friendly error messages
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 15.2 Write property test for error handling
    - **Property 38: Bedrock Service Unavailability Handling**
    - **Property 40: Network Loss Message Queuing**
    - **Validates: Requirements 11.1, 11.3**

  - [ ]* 15.3 Write unit tests for error scenarios
    - Test each error type
    - Test error message display
    - Test message queuing and retry
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [-] 16. Implement example questions and suggestions
  - [x] 16.1 Add example questions to ChatWidget
    - Display 3-5 examples on first open
    - Show context-aware suggestions based on selected system
    - Make examples clickable to submit as queries
    - Update suggestions when dashboard state changes
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 16.2 Write property test for example submission
    - **Property 33: Example Question Submission**
    - **Validates: Requirements 9.3**

  - [ ]* 16.3 Write unit tests for example questions
    - Test example display
    - Test example click handling
    - Test context-aware suggestions
    - _Requirements: 9.1, 9.2, 9.3, 9.5_

- [x] 17. Add CSS styling and responsive design
  - [x] 17.1 Create `web-dashboard/css/chat.css` with chat-specific styles
    - Style floating chat button
    - Style expanded chat interface (sidebar or modal)
    - Style message bubbles (user vs assistant)
    - Style typing indicator
    - Style example questions
    - Style error messages
    - Ensure responsive design for mobile/tablet
    - Support light/dark theme integration
    - _Requirements: 1.1, 1.2, 1.3, 12.3, 12.5_

  - [ ]* 17.2 Write visual regression tests
    - Test chat widget appearance
    - Test responsive layouts
    - Test theme integration
    - _Requirements: 12.3, 12.5_

- [ ] 18. Implement query type handlers for common questions
  - [ ] 18.1 Add specialized handlers in QueryProcessor
    - Implement health check query handler
    - Implement SLA violation query handler
    - Implement trend analysis query handler
    - Implement system comparison query handler
    - Implement root cause analysis integration (call existing AI insights service)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 18.2 Write property tests for query handlers
    - **Property 21: System Health Query Response**
    - **Property 22: SLA Violation Query Filtering**
    - **Property 23: File Trend Query Patterns**
    - **Property 24: System Comparison Metrics**
    - **Property 25: Root Cause Analysis Integration**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

  - [ ]* 18.3 Write unit tests for each query type
    - Test health queries with sample inputs
    - Test violation queries with filters
    - Test trend queries with date ranges
    - Test comparison queries with multiple systems
    - Test root cause integration
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 19. Add progress indicators and loading states
  - [ ] 19.1 Implement typing indicator in ChatWidget
    - Show animated typing indicator while processing
    - Show progress message for queries exceeding 5 seconds
    - Hide indicator when response arrives
    - _Requirements: 7.3, 7.4_

  - [ ]* 19.2 Write property test for progress indicators
    - **Property 26: Processing Indicator Display**
    - **Property 27: Long-Running Query Progress**
    - **Validates: Requirements 7.3, 7.4**

  - [ ]* 19.3 Write unit tests for loading states
    - Test typing indicator display/hide
    - Test progress message timing
    - _Requirements: 7.3, 7.4_

- [ ] 20. Implement dashboard filter integration
  - [ ] 20.1 Pass dashboard filters to chat context
    - Include selected system in context
    - Include date range filters in context
    - Include severity filters in context
    - Update chat suggestions when filters change
    - _Requirements: 14.2, 14.4_

  - [ ]* 20.2 Write property test for filter integration
    - **Property 50: Dashboard Filter Integration**
    - **Validates: Requirements 14.2, 14.4**

  - [ ]* 20.3 Write unit tests for filter passing
    - Test context includes all active filters
    - Test suggestions update with filter changes
    - _Requirements: 14.2, 14.4_

- [ ] 21. Final checkpoint - End-to-end testing
  - Test complete user flows:
    - Open chat, ask health question, get response
    - Ask follow-up question using context
    - Test with different query types
    - Test error scenarios
    - Test caching behavior
    - Test cost monitoring
  - Verify all acceptance criteria are met
  - Verify cost optimizations are working (cache hit rate >70%)
  - Verify response times meet targets (<3s simple, <5s complex)
  - Ask the user if questions arise

- [ ] 22. Documentation and deployment preparation
  - [ ] 22.1 Update API documentation
    - Document new chat endpoints in OpenAPI/Swagger
    - Add example requests/responses
    - Document error codes
    - _Requirements: All_

  - [ ] 22.2 Create user guide
    - Document how to use chat feature
    - Provide example questions
    - Explain cost implications
    - Document keyboard shortcuts
    - _Requirements: 9.1, 12.1_

  - [ ] 22.3 Update deployment configuration
    - Add environment variables for cost thresholds
    - Update .env.example with chat-specific settings
    - Document Bedrock permissions required
    - _Requirements: 15.2, 15.3_

## Notes

- Tasks marked with `*` are optional property-based and unit tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints (tasks 10 and 21) ensure incremental validation
- Backend tasks (1-10) should be completed before frontend tasks (11-21)
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and error conditions
- Integration tests validate end-to-end flows and component interactions
- Cost monitoring is critical - verify cache effectiveness and token usage throughout development
