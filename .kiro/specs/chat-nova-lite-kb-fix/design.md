# Chat Nova Lite KB Fix - Bugfix Design

## Overview

The chat assistant currently fails with server errors because the application uses direct Claude 3 Sonnet model invocation through agentcore_client.py instead of the properly configured Bedrock Agent (CRJ79K3SQR) that has Nova Lite 1.0 and Knowledge Base integration. The fix involves configuring the application to use the existing BedrockAgentClient (bedrock_agent_client.py) which properly invokes the AWS Bedrock Agent. This is a configuration and routing change, not a model or agent creation task - the agent already exists and works perfectly in AWS console.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when chat queries are processed using agentcore_client.py (direct model invocation) instead of bedrock_agent_client.py (proper agent invocation)
- **Property (P)**: The desired behavior - chat queries should be processed by the Bedrock Agent (CRJ79K3SQR) using Nova Lite 1.0 with Knowledge Base retrieval
- **Preservation**: Existing functionality that must remain unchanged - health checks, caching, cost monitoring, error handling, and backward compatibility with old endpoints
- **FileMonitoringAgent**: The class in agentcore_client.py that performs direct Claude 3 Sonnet model invocation (incorrect approach)
- **BedrockAgentClient**: The class in bedrock_agent_client.py that properly invokes AWS Bedrock Agents (correct approach)
- **BEDROCK_AGENT_ID**: Environment variable that must be set to CRJ79K3SQR to configure the agent
- **BEDROCK_AGENT_ALIAS_ID**: Environment variable for the agent alias (defaults to TSTALIASID if not set)

## Bug Details

### Fault Condition

The bug manifests when the chat endpoint processes user queries. The `/api/v1/chat/agent` endpoint uses `get_agentcore_client()` which returns a FileMonitoringAgent instance that performs direct bedrock-runtime model invocation instead of using the properly configured Bedrock Agent.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type ChatRequest
  OUTPUT: boolean
  
  RETURN (input.endpoint == '/api/v1/chat/agent')
         AND (chat_with_agent uses get_agentcore_client())
         AND (BEDROCK_AGENT_ID is not configured in .env)
         AND (agentcore_client.py performs direct model invocation)
END FUNCTION
```

### Examples

- User sends "ok, any SLA violations ??" → System returns "Server error. Please try again later" instead of using Bedrock Agent with Nova Lite 1.0 and Knowledge Base
- User sends any chat query → System uses FileMonitoringAgent.invoke() which calls bedrock-runtime directly instead of bedrock-agent-runtime
- Application initializes → No BEDROCK_AGENT_ID in .env file, so BedrockAgentClient cannot be used
- Frontend calls `/api/v1/chat/agent` → Routes to chat_with_agent() which uses agentcore_client instead of bedrock_agent_client

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Knowledge Base client initialization must continue to use KNOWLEDGE_BASE_ID (MJBJ5LOYSO)
- Error handling must continue to gracefully handle failures and return appropriate error messages
- Health check endpoint must continue to verify connectivity to Bedrock, database, and Knowledge Base
- Chat cache must continue to cache responses with appropriate TTL settings
- Cost monitoring must continue to track token usage and enforce circuit breaker limits
- The old `/api/v1/chat/query` endpoint must continue to function for backward compatibility

**Scope:**
All functionality that does NOT involve the `/api/v1/chat/agent` endpoint should be completely unaffected by this fix. This includes:
- The `/api/v1/chat/query` endpoint (old SQL-based chat)
- Health check endpoints
- Cache clearing endpoints
- Example queries endpoints
- Database query execution
- Cost monitoring and circuit breaker logic

## Hypothesized Root Cause

Based on the bug description, the root causes are:

1. **Missing Environment Configuration**: The .env file does not have BEDROCK_AGENT_ID=CRJ79K3SQR configured, preventing the application from knowing which agent to use

2. **Incorrect Client Usage**: The chat_with_agent() function in src/api/routes/chat.py uses get_agentcore_client() instead of get_agent_client(), routing requests to the wrong implementation

3. **Direct Model Invocation**: The FileMonitoringAgent class in agentcore_client.py uses boto3.client('bedrock-runtime') for direct model invocation instead of boto3.client('bedrock-agent-runtime') for proper agent invocation

4. **No Agent Alias Configuration**: The BEDROCK_AGENT_ALIAS_ID may not be configured, though bedrock_agent_client.py has a default fallback to 'TSTALIASID'

## Correctness Properties

Property 1: Fault Condition - Chat Queries Use Bedrock Agent

_For any_ chat request sent to the `/api/v1/chat/agent` endpoint, the fixed implementation SHALL invoke the Bedrock Agent (CRJ79K3SQR) using BedrockAgentClient.invoke_agent(), which will use Nova Lite 1.0 with Knowledge Base integration as configured in AWS console, and return a proper response without server errors.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation - Non-Agent Endpoints Unchanged

_For any_ request that is NOT sent to the `/api/v1/chat/agent` endpoint (including `/api/v1/chat/query`, health checks, cache operations, and examples), the fixed code SHALL produce exactly the same behavior as the original code, preserving all existing functionality for non-agent chat operations.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File 1**: `.env`

**Changes**:
1. **Add BEDROCK_AGENT_ID**: Add `BEDROCK_AGENT_ID=CRJ79K3SQR` to configure the agent
2. **Add BEDROCK_AGENT_ALIAS_ID** (optional): Add `BEDROCK_AGENT_ALIAS_ID=<alias_id>` if a specific alias is needed (defaults to TSTALIASID)

**File 2**: `src/api/routes/chat.py`

**Function**: `chat_with_agent()`

**Specific Changes**:
1. **Replace Client Import Usage**: Change from `agent = get_agentcore_client()` to `agent = get_agent_client()`
   - This switches from FileMonitoringAgent (direct model invocation) to BedrockAgentClient (proper agent invocation)

2. **Update Invocation Call**: Change from `agent.invoke(query=request.query, session_id=request.session_id)` to `agent.invoke_agent(prompt=request.query, session_id=request.session_id)`
   - BedrockAgentClient uses `invoke_agent()` method with `prompt` parameter
   - FileMonitoringAgent uses `invoke()` method with `query` parameter

3. **Update Response Extraction**: Change from extracting `tools_used` to extracting `trace` data
   - BedrockAgentClient returns: `{'response': str, 'session_id': str, 'trace': dict, 'content_type': str}`
   - FileMonitoringAgent returns: `{'response': str, 'tools_used': list}`

4. **Update Token Estimation**: Keep the same token estimation logic (it's just an estimate)

5. **Update Error Handling**: Ensure error messages are appropriate for agent invocation failures

**File 3**: No changes needed to `src/ai/bedrock_agent_client.py`
- This file already has the correct implementation
- It already reads BEDROCK_AGENT_ID from environment
- It already has proper error handling and logging
- It already processes agent responses correctly

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code (verify that agentcore_client fails), then verify the fix works correctly (bedrock_agent_client succeeds) and preserves existing behavior (other endpoints unchanged).

### Exploratory Fault Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that the current implementation uses agentcore_client and fails, while the AWS console agent works correctly.

**Test Plan**: Write tests that call the `/api/v1/chat/agent` endpoint with various queries and verify that the system currently uses agentcore_client (FileMonitoringAgent) instead of bedrock_agent_client (BedrockAgentClient). Run these tests on the UNFIXED code to observe failures.

**Test Cases**:
1. **SLA Violations Query Test**: Send "ok, any SLA violations ??" to `/api/v1/chat/agent` (will fail with server error on unfixed code)
2. **Environment Check Test**: Verify BEDROCK_AGENT_ID is not in .env file (will be missing on unfixed code)
3. **Client Type Test**: Verify chat_with_agent() uses get_agentcore_client() (will be true on unfixed code)
4. **AWS Console Test**: Manually test the same query in AWS Bedrock Agent console (will succeed, confirming agent works)

**Expected Counterexamples**:
- Chat queries return "Server error. Please try again later"
- BEDROCK_AGENT_ID environment variable is not set
- chat_with_agent() function uses FileMonitoringAgent instead of BedrockAgentClient
- AWS console testing shows the agent works perfectly with Nova Lite 1.0

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (chat queries to `/api/v1/chat/agent`), the fixed function uses BedrockAgentClient and produces successful responses.

**Pseudocode:**
```
FOR ALL request WHERE request.endpoint == '/api/v1/chat/agent' DO
  result := chat_with_agent_fixed(request)
  ASSERT result uses BedrockAgentClient.invoke_agent()
  ASSERT result.response is not "Server error"
  ASSERT result uses Nova Lite 1.0 with Knowledge Base
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (non-agent endpoints), the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL request WHERE request.endpoint != '/api/v1/chat/agent' DO
  ASSERT original_behavior(request) = fixed_behavior(request)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across different endpoints
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-agent operations

**Test Plan**: Observe behavior on UNFIXED code first for other endpoints (health checks, cache, old chat endpoint), then write property-based tests capturing that behavior.

**Test Cases**:
1. **Old Chat Endpoint Preservation**: Observe that `/api/v1/chat/query` works correctly on unfixed code, then verify it continues working after fix
2. **Health Check Preservation**: Observe that `/api/v1/chat/health` works correctly on unfixed code, then verify it continues working after fix
3. **Cache Operations Preservation**: Observe that cache clearing works correctly on unfixed code, then verify it continues working after fix
4. **Cost Monitor Preservation**: Observe that circuit breaker logic works correctly on unfixed code, then verify it continues working after fix

### Unit Tests

- Test that BEDROCK_AGENT_ID is configured in environment
- Test that chat_with_agent() uses get_agent_client() instead of get_agentcore_client()
- Test that BedrockAgentClient.invoke_agent() is called with correct parameters
- Test that response extraction handles the new response format (with trace data)
- Test error handling when agent invocation fails

### Property-Based Tests

- Generate random chat queries and verify they are routed to BedrockAgentClient
- Generate random session IDs and verify they are passed correctly to the agent
- Generate random requests to non-agent endpoints and verify behavior is unchanged
- Test that all health check variations continue to work correctly

### Integration Tests

- Test full chat flow: send query → verify agent invocation → verify response format
- Test that Knowledge Base retrieval works (query about SLA violations)
- Test that session continuity works across multiple queries
- Test that cost monitoring and circuit breaker still function correctly
- Test that error responses are properly formatted when agent fails
