# Implementation Plan: AgentCore Runtime Deployment

## Overview

This plan implements the deployment of the File Monitoring Agent to AWS Bedrock AgentCore Runtime. The implementation transforms the existing local agent into a containerized runtime agent that can be deployed to AWS and invoked via API. The work is organized into discrete steps that build incrementally, starting with the deployment package structure, then implementing agent logic and tools, configuring database access, updating the application client, and finally testing the end-to-end integration.

## Tasks

- [x] 1. Set up deployment package structure and configuration files
  - Create runtime/file_monitoring_agent directory structure
  - Create .bedrock_agentcore.yaml with agent configuration (Nova Lite model, Knowledge Base ID MJBJ5LOYSO, network mode PUBLIC, observability enabled)
  - Create Dockerfile with Python 3.10 base image, port 9000 exposure, and OpenTelemetry instrumentation
  - Create requirements.txt with dependencies (bedrock-agentcore>=1.0.5, strands-agents>=1.14.0, boto3>=1.40.62, sqlalchemy>=2.0.0)
  - Create .dockerignore to exclude unnecessary files from container
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.10_

- [x] 2. Implement database connection module for runtime environment
  - [x] 2.1 Create database_connection.py module
    - Implement init_db function that reads DATABASE_URL from environment variables
    - Implement get_db_session context manager for session management
    - Configure SQLAlchemy engine with connection pooling
    - Add connection verification on initialization
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.7, 6.8_
  
  - [ ]* 2.2 Write unit tests for database connection module
    - Test connection initialization with valid DATABASE_URL
    - Test connection failure handling
    - Test session context manager (commit/rollback)
    - Test connection pool behavior
    - _Requirements: 6.5, 6.6_

- [x] 3. Copy and adapt database models and action handler
  - [x] 3.1 Copy database models to runtime package
    - Copy src/database/models.py to runtime/file_monitoring_agent/models.py
    - Ensure all model classes are included (SourceSystemModel, SLADefinitionModel, SLAViolationModel, FileArrivalModel, SLAScoreModel)
    - _Requirements: 6.4_
  
  - [x] 3.2 Copy and adapt action handler for runtime environment
    - Copy src/ai/agent_action_handler.py to runtime/file_monitoring_agent/agent_action_handler.py
    - Update imports to use local database_connection module
    - Ensure all action methods are preserved (handle_action, _get_system_health, _get_violations, _query_all_systems, _compare_systems)
    - _Requirements: 2.8, 2.9_
  
  - [ ]* 3.3 Write unit tests for action handler
    - Test SQL query generation for each action type
    - Test result formatting and JSON serialization
    - Test error handling for SQL execution failures
    - Use in-memory SQLite database for test isolation
    - _Requirements: 2.5, 2.6, 2.7_

- [x] 4. Implement agent entrypoint with tool definitions
  - [x] 4.1 Create file_monitoring_agent.py entrypoint module
    - Import strands Agent, BedrockModel, and tool decorator
    - Import BedrockAgentCoreApp from bedrock_agentcore.runtime
    - Initialize BedrockAgentCoreApp instance
    - Configure BedrockModel with Nova Lite model ID (us.amazon.nova-lite-v1:0)
    - Create system prompt describing agent role, available tools, and usage instructions
    - Initialize Agent with BedrockModel and system prompt
    - _Requirements: 1.6, 1.7, 3.1, 3.2, 3.3_
  
  - [x] 4.2 Implement tool functions with @tool decorator
    - Implement get_system_health tool accepting system_id and days parameters
    - Implement get_violations tool accepting system_ids and days parameters
    - Implement get_all_systems tool with no parameters
    - Implement compare_systems tool accepting system_ids parameter
    - Each tool should delegate to AgentActionHandler for execution
    - Each tool should return JSON-formatted results or error messages
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  
  - [x] 4.3 Implement @app.entrypoint function
    - Create invoke_file_monitoring_agent function decorated with @app.entrypoint
    - Extract prompt from payload dictionary
    - Invoke agent with user input
    - Extract and return response text
    - _Requirements: 1.9_
  
  - [ ]* 4.4 Write unit tests for agent tools
    - Test each tool function with valid parameters
    - Test parameter validation (missing required params, invalid types)
    - Test error handling for database failures
    - Mock action handler to isolate tool logic
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  
  - [ ]* 4.5 Write property test for tool invocation delegation
    - **Property 1: Tool Invocation Delegates to Action Handler**
    - **Validates: Requirements 2.5**
    - Generate random tool names and parameters
    - Verify action handler's handle_action method is called
    - Run minimum 100 iterations
  
  - [ ]* 4.6 Write property test for successful tool execution
    - **Property 2: Successful Tool Execution Returns Valid JSON**
    - **Validates: Requirements 2.6**
    - Generate random valid tool parameters
    - Verify result can be parsed as JSON
    - Run minimum 100 iterations
  
  - [ ]* 4.7 Write property test for failed tool execution
    - **Property 3: Failed Tool Execution Returns Error Message**
    - **Validates: Requirements 2.7**
    - Generate random invalid parameters (non-existent system IDs, negative days)
    - Verify result contains "error" key with non-empty message
    - Run minimum 100 iterations

- [x] 5. Checkpoint - Verify deployment package is complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement runtime client for application integration
  - [x] 6.1 Create agentcore_runtime_client.py module
    - Create AgentCoreRuntimeClient class
    - Implement __init__ method accepting agent_arn and region parameters
    - Initialize boto3 bedrock-agentcore-runtime client
    - _Requirements: 5.1_
  
  - [x] 6.2 Implement invoke method
    - Accept query and optional session_id parameters
    - Generate session_id if not provided
    - Call invoke_agent API with agentArn, sessionId, and prompt
    - Parse response and extract response text
    - Return dictionary with response, session_id, tools_used, and response_time_ms
    - _Requirements: 5.3, 5.4, 5.5_
  
  - [x] 6.3 Implement error handling in runtime client
    - Handle HTTP 503 (agent unavailable) with user-friendly message
    - Handle HTTP 403 (authentication errors) without exposing auth details
    - Handle timeout errors with helpful message
    - Handle malformed responses with error message
    - Log all errors with relevant details (agent ARN, request ID, error type)
    - _Requirements: 5.6_
  
  - [x] 6.4 Implement invocation logging
    - Log each invocation with query, session_id, and response_time
    - Use structured logging format for easy parsing
    - _Requirements: 5.9_
  
  - [ ]* 6.5 Write unit tests for runtime client
    - Test invoke method with various query types
    - Test session ID handling and generation
    - Test response parsing for different response structures
    - Test error handling for API failures
    - Mock boto3 client to avoid actual AWS calls
    - _Requirements: 5.1, 5.3, 5.4, 5.5, 5.6_
  
  - [ ]* 6.6 Write property test for application invokes runtime agent
    - **Property 4: Application Invokes Runtime Agent for User Queries**
    - **Validates: Requirements 5.3**
    - Generate random user query strings
    - Verify runtime client's invoke method is called with query
    - Run minimum 100 iterations
  
  - [ ]* 6.7 Write property test for session ID preservation
    - **Property 5: Session ID Preservation**
    - **Validates: Requirements 5.4**
    - Generate random session IDs and queries
    - Verify session ID is passed to invoke_agent API
    - Run minimum 100 iterations
  
  - [ ]* 6.8 Write property test for response text extraction
    - **Property 6: Response Text Extraction**
    - **Validates: Requirements 5.5**
    - Generate random mock API responses with various structures
    - Verify response text is successfully extracted
    - Run minimum 100 iterations
  
  - [ ]* 6.9 Write property test for API error handling
    - **Property 7: API Error Handling**
    - **Validates: Requirements 5.6**
    - Generate random API error types (timeout, 503, 403)
    - Verify user-friendly error message returned (no stack traces)
    - Run minimum 100 iterations
  
  - [ ]* 6.10 Write property test for agent invocation logging
    - **Property 8: Agent Invocation Logging**
    - **Validates: Requirements 5.9**
    - Generate random queries and session IDs
    - Verify log entry created with query, session_id, and response_time
    - Run minimum 100 iterations

- [x] 7. Update FastAPI application to use runtime client
  - [x] 7.1 Update chat API endpoint to use runtime client
    - Import AgentCoreRuntimeClient in chat endpoint module
    - Read AGENTCORE_RUNTIME_AGENT_ARN from environment variables
    - Initialize runtime client with agent ARN
    - Update endpoint handler to call runtime client's invoke method
    - Pass session_id from request to runtime client
    - Return response from runtime agent
    - Preserve existing /api/v1/chat/agent endpoint interface
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.7_
  
  - [x] 7.2 Add error handling to chat endpoint
    - Catch runtime client exceptions
    - Return appropriate HTTP status codes (503 for unavailable, 500 for errors)
    - Return user-friendly error messages in response body
    - _Requirements: 5.6_
  
  - [ ]* 7.3 Write integration tests for chat endpoint with runtime agent
    - Test chat endpoint with simple query (e.g., "Hello")
    - Test chat endpoint with tool-requiring query (e.g., "How is PROD_SALES?")
    - Test session management across multiple requests
    - Test error handling when agent is unavailable
    - Mock runtime client for test isolation
    - _Requirements: 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] 8. Checkpoint - Verify application integration is complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Create deployment script and documentation
  - [x] 9.1 Create deployment script
    - Create deploy.sh script in runtime/file_monitoring_agent directory
    - Add commands to build Docker container
    - Add commands to push container to AWS ECR
    - Add commands to create/update AgentCore Runtime agent resource
    - Add commands to configure execution role with necessary permissions
    - Add commands to enable observability
    - Output agent ARN and agent ID after successful deployment
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.7, 4.8, 4.9_
  
  - [x] 9.2 Create deployment documentation
    - Create DEPLOYMENT.md in runtime/file_monitoring_agent directory
    - Document step-by-step deployment instructions
    - List all required environment variables (DATABASE_URL, AWS_REGION, AGENTCORE_RUNTIME_AGENT_ARN)
    - Explain how to build and push Docker container
    - Explain how to configure .bedrock_agentcore.yaml
    - Provide troubleshooting guidance for common issues
    - Document how to update agent after code changes
    - Document differences between local agent and runtime agent
    - Provide examples of invoking runtime agent via API
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [x] 10. Create end-to-end test script
  - [x] 10.1 Create test script for deployed agent
    - Create test_runtime_agent.py script
    - Test simple query invocation (e.g., "Hello")
    - Test tool-requiring query (e.g., "How is PROD_SALES?")
    - Verify appropriate responses for both query types
    - Verify database tools are executed correctly
    - Test session context maintenance across multiple queries
    - Measure and verify response time (< 5 seconds for simple queries)
    - Test error handling for invalid inputs (e.g., invalid system_id)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_
  
  - [ ]* 10.2 Write property test for session context maintenance
    - **Property 9: Session Context Maintenance**
    - **Validates: Requirements 7.5**
    - Generate random sequences of related queries with same session ID
    - Verify later responses reference earlier context
    - Run minimum 100 iterations
  
  - [ ]* 10.3 Write property test for graceful error handling
    - **Property 10: Graceful Error Handling for Invalid Inputs**
    - **Validates: Requirements 7.7**
    - Generate random invalid inputs (malformed JSON, SQL injection attempts)
    - Verify error message returned (not crash or stack trace)
    - Run minimum 100 iterations

- [x] 11. Final checkpoint - Verify end-to-end functionality
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties across many inputs
- Unit tests validate specific examples and edge cases
- The deployment package follows the established pattern from existing runtime agents
- Database access is configured via environment variables for flexibility
- The runtime client provides a clean abstraction for invoking the deployed agent
- Error handling is comprehensive to ensure graceful degradation
