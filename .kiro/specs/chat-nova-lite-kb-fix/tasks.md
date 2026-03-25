# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Fault Condition** - Chat Queries Use Bedrock Agent
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to concrete failing cases: queries to `/api/v1/chat/agent` endpoint
  - Test that chat requests to `/api/v1/chat/agent` currently use agentcore_client (FileMonitoringAgent) instead of bedrock_agent_client (BedrockAgentClient)
  - Test that BEDROCK_AGENT_ID is not configured in .env file
  - Test that chat_with_agent() uses get_agentcore_client() instead of get_agent_client()
  - Test concrete failing case: send "ok, any SLA violations ??" to `/api/v1/chat/agent` and verify it returns server error
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found: server errors, missing environment config, wrong client usage
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [-] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Agent Endpoints Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-agent endpoints
  - Test that `/api/v1/chat/query` (old SQL-based chat) works correctly on unfixed code
  - Test that `/api/v1/chat/health` (health check) works correctly on unfixed code
  - Test that cache clearing operations work correctly on unfixed code
  - Test that cost monitoring and circuit breaker logic work correctly on unfixed code
  - Write property-based tests capturing observed behavior patterns for all non-agent operations
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [-] 3. Fix for chat agent routing to use Bedrock Agent instead of direct model invocation

  - [ ] 3.1 Configure environment variables
    - Add BEDROCK_AGENT_ID=CRJ79K3SQR to .env file
    - Add BEDROCK_AGENT_ALIAS_ID (optional, defaults to TSTALIASID if not set)
    - _Bug_Condition: isBugCondition(input) where input.endpoint == '/api/v1/chat/agent' AND BEDROCK_AGENT_ID is not configured_
    - _Expected_Behavior: BEDROCK_AGENT_ID is set to CRJ79K3SQR to enable BedrockAgentClient_
    - _Preservation: Other environment variables remain unchanged_
    - _Requirements: 2.1, 2.2_

  - [ ] 3.2 Update chat_with_agent() to use BedrockAgentClient
    - Change from `agent = get_agentcore_client()` to `agent = get_agent_client()`
    - Change from `agent.invoke(query=request.query, session_id=request.session_id)` to `agent.invoke_agent(prompt=request.query, session_id=request.session_id)`
    - Update response extraction to handle new format with trace data instead of tools_used
    - Keep token estimation logic unchanged
    - Ensure error handling is appropriate for agent invocation failures
    - _Bug_Condition: isBugCondition(input) where chat_with_agent uses get_agentcore_client() instead of get_agent_client()_
    - _Expected_Behavior: expectedBehavior(result) where result uses BedrockAgentClient.invoke_agent() with Nova Lite 1.0 and Knowledge Base_
    - _Preservation: Other endpoints (health checks, cache, old chat) remain unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ] 3.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Chat Queries Use Bedrock Agent
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - Verify chat requests to `/api/v1/chat/agent` now use BedrockAgentClient
    - Verify BEDROCK_AGENT_ID is configured in .env
    - Verify chat_with_agent() uses get_agent_client()
    - Verify concrete case: "ok, any SLA violations ??" returns proper response without server error
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 3.4 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Agent Endpoints Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - Verify `/api/v1/chat/query` still works correctly
    - Verify `/api/v1/chat/health` still works correctly
    - Verify cache operations still work correctly
    - Verify cost monitoring and circuit breaker still work correctly
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
