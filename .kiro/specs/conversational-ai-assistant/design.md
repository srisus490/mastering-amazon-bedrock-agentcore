# Design Document: Conversational AI Assistant

## Overview

The Conversational AI Assistant adds a natural language query interface to the Intelligent File Monitoring Dashboard. The design leverages the existing Amazon Bedrock integration (Claude 3 Sonnet) and FastAPI backend to provide a chat-based interface for querying file monitoring data.

### Key Design Principles

1. **Minimal Backend Changes**: Reuse existing Bedrock client, database models, and API infrastructure
2. **Cost-Conscious**: Aggressive caching and token optimization to minimize Bedrock costs
3. **Progressive Enhancement**: Chat feature enhances but doesn't replace existing dashboard functionality
4. **Stateless Backend**: Conversation context managed client-side for scalability
5. **Responsive UI**: Non-blocking operations with typing indicators and streaming responses

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Dashboard (Frontend)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Chat Widget  │  │ Chat Manager │  │ Message      │     │
│  │ (UI)         │──│ (State)      │──│ Formatter    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Chat         │  │ Query        │  │ Response     │     │
│  │ Endpoint     │──│ Processor    │──│ Generator    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Cache        │  │ SQL Query    │  │ Bedrock      │     │
│  │ Manager      │  │ Generator    │  │ Client       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────┬───────────────┘
                         │                    │
                         ▼                    ▼
                  ┌─────────────┐      ┌─────────────┐
                  │   SQLite    │      │   Amazon    │
                  │   Database  │      │   Bedrock   │
                  └─────────────┘      └─────────────┘
```

### Component Interaction Flow

```
User Query → Chat Widget → Chat Endpoint → Query Processor
                                              │
                                              ├─→ Check Cache
                                              │   (hit: return cached)
                                              │
                                              ├─→ Parse Intent
                                              │   (identify query type)
                                              │
                                              ├─→ Generate SQL
                                              │   (if data query)
                                              │
                                              ├─→ Execute Query
                                              │   (fetch from DB)
                                              │
                                              └─→ Generate Response
                                                  (via Bedrock)
                                                  │
                                                  └─→ Format & Cache
                                                      │
                                                      └─→ Return to User
```

## Components and Interfaces

### 1. Frontend Components

#### ChatWidget (JavaScript)

**Purpose**: Floating UI component for chat interface

**Properties**:
- `isOpen: boolean` - Widget expansion state
- `messages: Message[]` - Conversation history
- `isTyping: boolean` - AI typing indicator state

**Methods**:
- `toggle()` - Expand/collapse widget
- `sendMessage(text: string)` - Submit user query
- `appendMessage(message: Message)` - Add message to history
- `clear()` - Reset conversation

**Events**:
- `onMessageSent` - Fired when user submits query
- `onWidgetToggled` - Fired when widget opens/closes

#### ChatManager (JavaScript)

**Purpose**: Manages conversation state and API communication

**Properties**:
- `conversationContext: Message[]` - Last 10 messages
- `sessionId: string` - Unique session identifier
- `apiClient: APIClient` - Reference to API client

**Methods**:
- `sendQuery(query: string, context: Message[])` - Send query to backend
- `addToContext(message: Message)` - Add message to context
- `clearContext()` - Reset conversation context
- `saveToSessionStorage()` - Persist conversation
- `loadFromSessionStorage()` - Restore conversation

#### MessageFormatter (JavaScript)

**Purpose**: Formats AI responses for display

**Methods**:
- `formatTable(data: object[])` - Convert data to HTML table
- `formatMetric(value: number, label: string)` - Format single metric
- `formatList(items: string[])` - Format bullet list
- `formatTimestamp(date: Date)` - Format date consistently

### 2. Backend Components

#### ChatEndpoint (FastAPI)

**Purpose**: REST API endpoint for chat queries

**Route**: `POST /api/v1/chat/query`

**Request Body**:
```typescript
{
  query: string,              // User's natural language query
  context: Message[],         // Last 10 messages (optional)
  sessionId: string,          // Session identifier (optional)
  includeSystemContext: boolean  // Include current dashboard state
}
```

**Response Body**:
```typescript
{
  response: string,           // AI-generated response
  data: object | null,        // Structured data if applicable
  suggestions: string[],      // Follow-up question suggestions
  cached: boolean,            // Whether response was cached
  tokensUsed: {
    input: number,
    output: number
  }
}
```

**Additional Routes**:
- `POST /api/v1/chat/clear` - Clear conversation cache
- `GET /api/v1/chat/examples` - Get example questions
- `GET /api/v1/chat/health` - Check chat service health

#### QueryProcessor

**Purpose**: Parses natural language queries and determines intent

**Methods**:
- `parseQuery(query: string, context: Message[])` - Extract intent and entities
- `identifyQueryType(query: string)` - Classify query (health, violations, trends, etc.)
- `extractSystemNames(query: string)` - Find system references
- `extractDateReferences(query: string)` - Parse date mentions
- `resolveContextReferences(query: string, context: Message[])` - Resolve "it", "that system", etc.

**Query Types**:
- `SYSTEM_HEALTH` - "How is PROD_SALES doing?"
- `SLA_VIOLATIONS` - "Show me violations"
- `FILE_TRENDS` - "What's the trend for PROD_ANALYTICS?"
- `SYSTEM_COMPARISON` - "Compare PROD_SALES and PROD_INVENTORY"
- `ROOT_CAUSE` - "Why is PROD_SALES slow?"
- `GENERAL_INFO` - "What systems do we have?"

#### SQLQueryGenerator

**Purpose**: Converts parsed queries into SQL

**Methods**:
- `generateHealthQuery(systemId: string)` - Query for system health
- `generateViolationsQuery(filters: object)` - Query for SLA violations
- `generateTrendsQuery(systemId: string, dateRange: object)` - Query for trends
- `generateComparisonQuery(systemIds: string[])` - Query for comparisons
- `validateQuery(sql: string)` - Ensure query is safe and valid

**Safety Features**:
- Read-only queries (SELECT only)
- Parameterized queries to prevent injection
- Result set limits (max 1000 rows)
- Query timeout (5 seconds)

#### ResponseGenerator

**Purpose**: Generates natural language responses using Bedrock

**Methods**:
- `generateResponse(queryResult: object, userQuery: string, context: Message[])` - Create response
- `buildPrompt(queryResult: object, userQuery: string, context: Message[])` - Construct Bedrock prompt
- `formatDataForPrompt(data: object)` - Summarize data for prompt
- `extractResponse(bedrockOutput: string)` - Parse Bedrock response

**Prompt Structure**:
```
System: You are a helpful assistant for a file monitoring dashboard.

Context: [Last 3 messages from conversation]

Database Schema: [Relevant table schemas]

User Query: [User's question]

Query Results: [Summarized data from database]

Instructions: Provide a concise, natural language response. Format data as tables or lists when appropriate. Limit response to 200 words.
```

#### CacheManager

**Purpose**: Caches responses to reduce Bedrock costs

**Methods**:
- `getCachedResponse(queryHash: string)` - Retrieve cached response
- `setCachedResponse(queryHash: string, response: object, ttl: number)` - Store response
- `generateQueryHash(query: string, context: Message[])` - Create cache key
- `clearCache()` - Remove all cached responses

**Cache Strategy**:
- Cache key: Hash of (normalized query + relevant context)
- TTL: 5 minutes for data queries, 1 hour for static queries
- Storage: In-memory cache (Python dict) with LRU eviction
- Max size: 1000 entries

## Data Models

### Message

```typescript
interface Message {
  id: string;              // Unique message ID
  role: 'user' | 'assistant';
  content: string;         // Message text
  timestamp: Date;         // When message was sent
  data?: object;           // Structured data (for assistant messages)
  tokensUsed?: {
    input: number;
    output: number;
  };
}
```

### ChatRequest

```python
class ChatRequest(BaseModel):
    query: str
    context: List[Message] = []
    session_id: Optional[str] = None
    include_system_context: bool = False
```

### ChatResponse

```python
class ChatResponse(BaseModel):
    response: str
    data: Optional[Dict] = None
    suggestions: List[str] = []
    cached: bool = False
    tokens_used: TokenUsage
```

### TokenUsage

```python
class TokenUsage(BaseModel):
    input: int
    output: int
    cached: int = 0  # Tokens saved by caching
```

### QueryIntent

```python
class QueryIntent(BaseModel):
    query_type: str  # SYSTEM_HEALTH, SLA_VIOLATIONS, etc.
    system_ids: List[str] = []
    date_range: Optional[DateRange] = None
    filters: Dict[str, Any] = {}
    confidence: float  # 0.0 to 1.0
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Chat Interface Expansion
*For any* initial widget state, when the chat button is clicked, the interface should transition to the expanded state with conversation history and input field visible.
**Validates: Requirements 1.2, 1.3**

### Property 2: Interface Minimization Preserves State
*For any* conversation state, when the user clicks outside the interface or presses ESC, the interface should minimize while preserving all messages in the conversation.
**Validates: Requirements 1.4**

### Property 3: Interface Persistence Across Navigation
*For any* dashboard page navigation, the chat interface should remain accessible and functional without requiring page reload.
**Validates: Requirements 1.5**

### Property 4: System Name Entity Extraction
*For any* query containing a known system name, the Query Processor should correctly identify and extract the corresponding source system ID.
**Validates: Requirements 2.2**

### Property 5: SQL Query Generation for Data Requests
*For any* query classified as a data request, the Database Query Generator should produce valid, parameterized SQL that matches the database schema.
**Validates: Requirements 2.3**

### Property 6: Ambiguous Query Clarification
*For any* query with multiple possible interpretations, the system should request clarification before executing any database operations.
**Validates: Requirements 2.4**

### Property 7: Unparseable Query Suggestions
*For any* query that cannot be parsed into a valid intent, the system should provide at least one suggestion for rephrasing.
**Validates: Requirements 2.5**

### Property 8: SQL Query Validation
*For any* generated SQL query, validation against the database schema should occur before execution, rejecting invalid queries.
**Validates: Requirements 3.1**

### Property 9: Context-Aware Date Filtering
*For any* query with date context (explicit or from conversation), appropriate date range filters should be applied to the generated SQL.
**Validates: Requirements 3.2**

### Property 10: Result Set Size Limiting
*For any* database query result, the number of rows returned should not exceed 1000 to prevent performance issues.
**Validates: Requirements 3.3**

### Property 11: Expensive Query Detection
*For any* query estimated to be expensive (large date range, multiple joins, etc.), the system should suggest narrowing the scope before execution.
**Validates: Requirements 3.4**

### Property 12: Query Failure Error Handling
*For any* database query failure, the system should log the error details and provide a user-friendly error message without exposing technical details.
**Validates: Requirements 3.5**

### Property 13: Tabular Data Formatting
*For any* query result containing multiple rows with consistent fields, the response should format the data as an HTML table with headers.
**Validates: Requirements 4.2**

### Property 14: Metric Highlighting
*For any* query result containing numeric metrics, important values (highs, lows, averages) should be visually highlighted in the response.
**Validates: Requirements 4.3**

### Property 15: Empty Result Explanation
*For any* query returning zero results, the response should include an explanation of why no data was found (e.g., date range, filters, system status).
**Validates: Requirements 4.4**

### Property 16: Response Timestamp Inclusion
*For any* response containing data from the database, timestamps indicating data freshness should be included.
**Validates: Requirements 4.5**

### Property 17: Conversation Context Initialization
*For any* new conversation session, a fresh Conversation Context should be created with zero messages.
**Validates: Requirements 5.1**

### Property 18: Conversation Context Size Limiting
*For any* message exchange, the Conversation Context should store at most the last 10 messages, removing older messages when the limit is exceeded.
**Validates: Requirements 5.2, 8.4**

### Property 19: Context-Based Reference Resolution
*For any* query containing references like "that system", "it", or "yesterday", the system should resolve them using the Conversation Context.
**Validates: Requirements 5.3**

### Property 20: Conversation Context Clearing
*For any* clear history action, all messages should be removed from the Conversation Context and the session should reset to initial state.
**Validates: Requirements 5.5, 10.4**

### Property 21: System Health Query Response
*For any* query classified as a health check, the response should include current system status and recent SLA scores for the referenced system(s).
**Validates: Requirements 6.1**

### Property 22: SLA Violation Query Filtering
*For any* query about SLA violations, the response should include violations filtered by the specified date range and severity level.
**Validates: Requirements 6.2**

### Property 23: File Trend Query Patterns
*For any* query about file trends, the response should include daily or hourly patterns for the specified time period.
**Validates: Requirements 6.3**

### Property 24: System Comparison Metrics
*For any* query comparing multiple systems, the response should include comparative metrics for all specified systems.
**Validates: Requirements 6.4**

### Property 25: Root Cause Analysis Integration
*For any* query about root causes or "why" questions, the system should invoke the existing AI insights service and include its analysis in the response.
**Validates: Requirements 6.5**

### Property 26: Processing Indicator Display
*For any* query being processed, a typing indicator should be visible in the chat interface until the response is received.
**Validates: Requirements 7.3**

### Property 27: Long-Running Query Progress
*For any* query exceeding 5 seconds of processing time, a progress message should be displayed to the user.
**Validates: Requirements 7.4**

### Property 28: Response Caching for Repeated Queries
*For any* query repeated within 5 minutes with the same context, the cached response should be returned without invoking Bedrock.
**Validates: Requirements 8.2**

### Property 29: Prompt Context Minimization
*For any* Bedrock prompt, only the relevant database schema tables and conversation context should be included, excluding unnecessary data.
**Validates: Requirements 8.3**

### Property 30: Response Token Limiting
*For any* Bedrock response, the output should be limited to a maximum of 1000 tokens to control costs.
**Validates: Requirements 8.6**

### Property 31: Database Operation Batching
*For any* query requiring multiple database operations, they should be batched into a single transaction or connection to minimize overhead.
**Validates: Requirements 8.7**

### Property 32: Empty Conversation Suggestions
*For any* empty conversation state, the system should display suggested questions based on the current dashboard state (selected system, date range, etc.).
**Validates: Requirements 9.2**

### Property 33: Example Question Submission
*For any* example question clicked by the user, it should be submitted as a query with the same behavior as manually typed queries.
**Validates: Requirements 9.3**

### Property 34: Context-Aware System Suggestions
*For any* dashboard state with an active system selection, suggested questions should be specific to that system.
**Validates: Requirements 9.5**

### Property 35: Session Storage Persistence
*For any* navigation between dashboard pages, the Conversation Context should be persisted to browser session storage and restored on the new page.
**Validates: Requirements 10.1**

### Property 36: Page Refresh Restoration
*For any* page refresh with existing session storage, the conversation should be restored with all messages intact.
**Validates: Requirements 10.2**

### Property 37: Session Isolation
*For any* new browser session, no conversation data from previous sessions should be accessible.
**Validates: Requirements 10.5**

### Property 38: Bedrock Service Unavailability Handling
*For any* Bedrock service error (timeout, unavailable, etc.), the system should display a message indicating AI features are temporarily offline.
**Validates: Requirements 11.1**

### Property 39: Database Query Failure Explanation
*For any* database query failure, the system should provide an explanation of the error and suggest alternative queries.
**Validates: Requirements 11.2**

### Property 40: Network Loss Message Queuing
*For any* network connection loss, messages should be queued locally and automatically retried when connection is restored.
**Validates: Requirements 11.3**

### Property 41: Rate Limit Error Handling
*For any* Bedrock rate limit error, the system should inform the user and suggest waiting before retrying.
**Validates: Requirements 11.4**

### Property 42: Authentication Failure Instructions
*For any* authentication failure with Bedrock, the system should provide clear instructions for resolving credential issues.
**Validates: Requirements 11.5**

### Property 43: Keyboard Navigation Accessibility
*For any* keyboard interaction (Tab, Enter, ESC), the chat interface should be fully navigable and functional.
**Validates: Requirements 12.1**

### Property 44: Input Focus Visual Feedback
*For any* input field focus event, visual feedback (border highlight, shadow, etc.) should be displayed.
**Validates: Requirements 12.4**

### Property 45: Text Resizing Layout Preservation
*For any* text size increase up to 200%, the chat interface layout should remain functional without horizontal scrolling or overlapping elements.
**Validates: Requirements 12.5**

### Property 46: Date Format Consistency
*For any* date displayed in a response, the format should match the dashboard's date format configuration.
**Validates: Requirements 13.3**

### Property 47: Large Number Formatting
*For any* number greater than 999 in a response, thousand separators should be used for readability.
**Validates: Requirements 13.4**

### Property 48: Percentage Precision
*For any* percentage value in a response, it should be displayed with appropriate precision (typically 1-2 decimal places).
**Validates: Requirements 13.5**

### Property 49: System ID Consistency
*For any* system referenced in a response, the system ID should match exactly with the IDs used in the dashboard and database.
**Validates: Requirements 14.1**

### Property 50: Dashboard Filter Integration
*For any* query with active dashboard filters (date range, severity, etc.), those filters should be considered in the query context.
**Validates: Requirements 14.2, 14.4**

### Property 51: Metric Calculation Consistency
*For any* metric displayed in a response (SLA score, file count, etc.), the calculation method should match the existing API endpoints.
**Validates: Requirements 14.3**

### Property 52: Bedrock API Call Logging
*For any* Bedrock API invocation, input and output token counts should be logged for cost tracking.
**Validates: Requirements 15.1**

### Property 53: Token Usage Threshold Alerting
*For any* hour where token usage exceeds 100,000 tokens, an alert notification should be sent to administrators.
**Validates: Requirements 15.2**

### Property 54: Cost-Based Circuit Breaker
*For any* day where costs exceed the configured threshold, the chat feature should be temporarily disabled until manual re-enablement.
**Validates: Requirements 15.3**

### Property 55: Expensive Query Cost Estimation
*For any* query classified as expensive, a cost estimation should be provided to the user before execution.
**Validates: Requirements 15.4**

### Property 56: Cache Hit Rate Tracking
*For any* cache operation (hit or miss), the hit rate should be tracked and logged for cost savings analysis.
**Validates: Requirements 15.5**

## Error Handling

### Error Categories

1. **User Input Errors**
   - Unparseable queries → Provide suggestions
   - Ambiguous queries → Request clarification
   - Invalid system names → List available systems

2. **Database Errors**
   - Connection failures → Retry with exponential backoff
   - Query timeouts → Suggest narrowing scope
   - Schema validation failures → Log and return generic error

3. **AI Service Errors**
   - Bedrock unavailable → Display offline message, use cached responses if available
   - Rate limits → Inform user, implement exponential backoff
   - Authentication failures → Provide credential resolution instructions
   - Timeout → Retry once, then fail gracefully

4. **Network Errors**
   - Connection loss → Queue messages, retry on reconnection
   - Slow responses → Show progress indicators
   - Partial failures → Return partial results with warning

### Error Response Format

```typescript
{
  error: {
    code: string,           // ERROR_CODE
    message: string,        // User-friendly message
    details: string,        // Technical details (optional)
    suggestions: string[],  // Actionable suggestions
    retryable: boolean      // Whether retry might succeed
  }
}
```

### Fallback Strategies

1. **Cached Response Fallback**: If Bedrock fails, return cached response if available (even if stale)
2. **Simplified Query Fallback**: If complex query fails, try simplified version
3. **Direct Data Fallback**: If AI response fails, return raw data with basic formatting
4. **Example Questions Fallback**: If suggestions fail, show static example questions

## Testing Strategy

### Dual Testing Approach

The testing strategy combines unit tests for specific examples and edge cases with property-based tests for universal correctness properties. Both are necessary for comprehensive coverage:

- **Unit tests** validate specific scenarios, edge cases, and error conditions
- **Property tests** verify universal properties across all inputs through randomization

### Unit Testing

**Focus Areas**:
- Example queries for each query type (health, violations, trends, etc.)
- Edge cases: empty results, malformed input, missing context
- Error conditions: service failures, timeouts, invalid credentials
- Integration points: Bedrock client, database queries, cache operations

**Test Organization**:
```
tests/
  chat/
    test_chat_endpoint.py          # API endpoint tests
    test_query_processor.py        # Query parsing tests
    test_sql_generator.py          # SQL generation tests
    test_response_generator.py     # Response formatting tests
    test_cache_manager.py          # Caching tests
    test_error_handling.py         # Error scenarios
  frontend/
    test_chat_widget.test.js       # UI component tests
    test_chat_manager.test.js      # State management tests
    test_message_formatter.test.js # Formatting tests
```

### Property-Based Testing

**Configuration**:
- Use `hypothesis` library for Python backend tests
- Use `fast-check` library for JavaScript frontend tests
- Minimum 100 iterations per property test
- Each test tagged with: `Feature: conversational-ai-assistant, Property {number}: {property_text}`

**Property Test Examples**:

1. **Property 18: Context Size Limiting**
   ```python
   @given(messages=st.lists(st.text(), min_size=0, max_size=50))
   def test_context_size_limit(messages):
       # Feature: conversational-ai-assistant, Property 18
       context = ConversationContext()
       for msg in messages:
           context.add_message(msg)
       assert len(context.messages) <= 10
   ```

2. **Property 10: Result Set Limiting**
   ```python
   @given(query=st.text(), result_size=st.integers(min_value=0, max_value=10000))
   def test_result_set_limit(query, result_size):
       # Feature: conversational-ai-assistant, Property 10
       results = execute_query(query)
       assert len(results) <= 1000
   ```

3. **Property 28: Response Caching**
   ```python
   @given(query=st.text(), context=st.lists(st.text(), max_size=10))
   def test_response_caching(query, context):
       # Feature: conversational-ai-assistant, Property 28
       response1 = process_query(query, context)
       response2 = process_query(query, context)  # Within 5 min
       assert response2.cached == True
       assert response2.response == response1.response
   ```

**Property Test Coverage**:
- All 56 correctness properties should have corresponding property tests
- Properties marked as "example" should have unit tests instead
- Properties marked as "no" (not testable) should be validated through manual testing or monitoring

### Integration Testing

**Test Scenarios**:
1. End-to-end query flow: User input → Backend processing → Response display
2. Conversation context persistence across page navigation
3. Cache effectiveness under load
4. Error recovery and fallback mechanisms
5. Integration with existing dashboard features

### Performance Testing

**Benchmarks**:
- Simple query response time: < 3 seconds (target)
- Complex query response time: < 5 seconds (target)
- Cache hit rate: > 70% (target)
- Token usage per query: < 2000 tokens average (target)

**Load Testing**:
- Concurrent users: 50 simultaneous conversations
- Query throughput: 100 queries per minute
- Cache memory usage: < 100MB

### Cost Testing

**Monitoring**:
- Track token usage per query type
- Measure cache effectiveness (cost savings)
- Alert on threshold breaches
- Daily cost reports

**Cost Optimization Validation**:
- Verify prompt caching reduces costs by > 80%
- Verify response caching eliminates redundant Bedrock calls
- Verify token limits are enforced

## Cost Analysis

### Bedrock Pricing (Claude 3 Sonnet)

**Current Pricing** (as of 2024):
- Input tokens: $0.003 per 1K tokens
- Output tokens: $0.015 per 1K tokens
- Cached input tokens: $0.0003 per 1K tokens (90% savings)

### Cost Per Query Estimation

**Without Optimization**:
```
Average query breakdown:
- User query: 50 tokens
- Conversation context (10 messages): 500 tokens
- Database schema: 1000 tokens
- Query results summary: 300 tokens
- System prompt: 200 tokens
Total input: 2050 tokens

- AI response: 400 tokens
Total output: 400 tokens

Cost per query:
- Input: 2050 * $0.003 / 1000 = $0.00615
- Output: 400 * $0.015 / 1000 = $0.006
- Total: $0.01215 per query
```

**With Optimization** (Caching + Limits):
```
Optimized query breakdown:
- User query: 50 tokens (new)
- Conversation context (last 3 messages): 150 tokens (new)
- Database schema: 800 tokens (cached - 90% savings)
- System prompt: 200 tokens (cached - 90% savings)
- Query results summary: 200 tokens (new)
Total input: 400 new + 1000 cached

- AI response (limited): 300 tokens
Total output: 300 tokens

Cost per query:
- New input: 400 * $0.003 / 1000 = $0.0012
- Cached input: 1000 * $0.0003 / 1000 = $0.0003
- Output: 300 * $0.015 / 1000 = $0.0045
- Total: $0.006 per query (50% savings)
```

**With Response Caching** (70% cache hit rate):
```
Effective cost per query:
- 30% queries hit Bedrock: 0.30 * $0.006 = $0.0018
- 70% queries use cache: 0.70 * $0.00 = $0.00
- Average: $0.0018 per query (85% total savings)
```

### Monthly Cost Projections

**Usage Scenarios**:

1. **Low Usage** (10 users, 20 queries/user/day):
   - Daily queries: 200
   - Monthly queries: 6,000
   - Monthly cost: 6,000 * $0.0018 = **$10.80**

2. **Medium Usage** (50 users, 30 queries/user/day):
   - Daily queries: 1,500
   - Monthly queries: 45,000
   - Monthly cost: 45,000 * $0.0018 = **$81.00**

3. **High Usage** (100 users, 40 queries/user/day):
   - Daily queries: 4,000
   - Monthly queries: 120,000
   - Monthly cost: 120,000 * $0.0018 = **$216.00**

### Cost Control Mechanisms

**Implemented in Design**:

1. **Prompt Caching** (90% savings on repeated context)
   - Cache database schema across queries
   - Cache system prompts
   - Cache conversation context when unchanged

2. **Response Caching** (Eliminates redundant calls)
   - 5-minute TTL for data queries
   - 1-hour TTL for static queries
   - Cache key: hash(query + context)

3. **Token Limits**
   - Max conversation context: 10 messages (~500 tokens)
   - Max response length: 1000 tokens
   - Minimal schema inclusion: only relevant tables

4. **Query Optimization**
   - Batch database operations
   - Limit result sets to 1000 rows
   - Summarize large datasets before sending to AI

5. **Circuit Breakers**
   - Hourly token limit: 100,000 tokens → alert
   - Daily cost threshold: configurable → disable feature
   - Rate limiting: prevent abuse

### Cost Monitoring Dashboard

**Metrics to Track**:
- Queries per hour/day/month
- Average tokens per query (input/output)
- Cache hit rate (target: >70%)
- Cost per query (target: <$0.002)
- Total daily/monthly costs
- Cost savings from caching

**Alerts**:
- Token usage > 100K/hour
- Cache hit rate < 50%
- Daily cost > threshold
- Unusual query patterns (potential abuse)

### Cost Comparison with Alternatives

**Without AI Assistant** (Manual Dashboard Usage):
- Cost: $0 (no AI)
- User time: 5-10 minutes per data exploration
- Requires SQL knowledge

**With AI Assistant** (Optimized):
- Cost: $0.0018 per query
- User time: 30 seconds per query
- No SQL knowledge required
- ROI: Time savings justify cost for most organizations

**Alternative: GPT-4** (More expensive):
- Input: $0.01 per 1K tokens
- Output: $0.03 per 1K tokens
- Cost per query: ~$0.025 (14x more expensive)

**Alternative: Claude 3 Haiku** (Cheaper but less capable):
- Input: $0.00025 per 1K tokens
- Output: $0.00125 per 1K tokens
- Cost per query: ~$0.0008 (56% cheaper)
- Trade-off: Lower quality responses

### Recommendation

The design uses **Claude 3 Sonnet** as the optimal balance between cost and quality:
- Significantly cheaper than GPT-4
- Better quality than Haiku for complex queries
- With optimization: **$0.0018 per query**
- Expected monthly cost: **$10-$200** depending on usage
- ROI positive for teams with >5 users
