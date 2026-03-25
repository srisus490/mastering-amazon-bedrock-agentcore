# Requirements Document

## Introduction

This document specifies requirements for deploying the File Monitoring Agent to AWS Bedrock AgentCore Runtime. The current application uses a local agent implementation (FileMonitoringAgent in src/ai/agentcore_client.py) that directly invokes Claude via Bedrock Runtime API. The goal is to package this agent for AgentCore Runtime deployment, similar to the existing 5 deployed agents (unified_travel_companion, travel_agent_google_drive, etc.), and update the application to invoke the deployed agent via the AgentCore Runtime API.

## Glossary

- **AgentCore_Runtime**: AWS Bedrock service for deploying containerized agents that can be invoked via API
- **File_Monitoring_Agent**: The intelligent agent that answers questions about file monitoring systems using database tools
- **Local_Agent**: Current implementation in src/ai/agentcore_client.py that runs in the application process
- **Runtime_Agent**: The deployed agent running in AgentCore Runtime infrastructure
- **Tool**: A function the agent can call to query data (e.g., get_system_health, get_violations)
- **Action_Handler**: Component that executes tool calls by querying the database
- **Knowledge_Base**: AWS Bedrock Knowledge Base (ID: MJBJ5LOYSO) containing system documentation
- **Nova_Lite**: AWS Bedrock foundation model (us.amazon.nova-lite-v1:0) for agent inference
- **Entrypoint**: Python module that handles agent invocation requests in AgentCore Runtime
- **Deployment_Package**: Docker container with agent code, dependencies, and configuration
- **Application**: The FastAPI backend that will invoke the Runtime_Agent

## Requirements

### Requirement 1: Package Agent for AgentCore Runtime Deployment

**User Story:** As a developer, I want to package the File Monitoring Agent for AgentCore Runtime, so that it can be deployed as a containerized runtime agent.

#### Acceptance Criteria

1. THE Deployment_Package SHALL include a Python entrypoint module that implements the agent logic
2. THE Deployment_Package SHALL include a Dockerfile that builds a container compatible with AgentCore Runtime
3. THE Deployment_Package SHALL include a .bedrock_agentcore.yaml configuration file specifying deployment settings
4. THE Deployment_Package SHALL include a requirements.txt file listing all Python dependencies
5. THE Deployment_Package SHALL include a .dockerignore file to exclude unnecessary files from the container
6. THE Entrypoint SHALL use the strands library Agent class for agent implementation
7. THE Entrypoint SHALL use BedrockModel with Nova_Lite model ID (us.amazon.nova-lite-v1:0)
8. THE Entrypoint SHALL define tools using the @tool decorator for each database query function
9. THE Entrypoint SHALL implement a BedrockAgentCoreApp with an @app.entrypoint decorated function
10. WHEN the container is built, THE Deployment_Package SHALL expose port 9000 for AgentCore Runtime communication

### Requirement 2: Implement Agent Tools for Database Queries

**User Story:** As an agent, I want to access database query tools, so that I can answer questions about file monitoring systems.

#### Acceptance Criteria

1. THE Runtime_Agent SHALL provide a get_system_health tool that accepts system_id and days parameters
2. THE Runtime_Agent SHALL provide a get_violations tool that accepts system_ids and days parameters
3. THE Runtime_Agent SHALL provide a get_all_systems tool that returns all monitored systems
4. THE Runtime_Agent SHALL provide a compare_systems tool that accepts system_ids parameter
5. WHEN a tool is invoked, THE Runtime_Agent SHALL call the Action_Handler to execute the database query
6. WHEN a tool execution succeeds, THE Runtime_Agent SHALL return the query results as JSON
7. IF a tool execution fails, THEN THE Runtime_Agent SHALL return an error message describing the failure
8. THE Runtime_Agent SHALL use the existing Action_Handler implementation from src/ai/agent_action_handler.py
9. THE Runtime_Agent SHALL include the Action_Handler and its dependencies in the Deployment_Package

### Requirement 3: Configure Agent with System Prompt and Knowledge Base

**User Story:** As an agent, I want proper instructions and knowledge base access, so that I can provide accurate and helpful responses.

#### Acceptance Criteria

1. THE Runtime_Agent SHALL use a system prompt that describes its role as a file monitoring assistant
2. THE system prompt SHALL list all available tools and their purposes
3. THE system prompt SHALL instruct the agent to use tools for data queries and respond without tools for greetings
4. THE Runtime_Agent SHALL be configured to access Knowledge_Base (MJBJ5LOYSO) for system documentation
5. THE .bedrock_agentcore.yaml configuration SHALL specify the Knowledge_Base ID in the agent settings
6. WHEN a user asks about system documentation, THE Runtime_Agent SHALL query the Knowledge_Base
7. THE Runtime_Agent SHALL combine tool results with Knowledge_Base information when answering complex questions

### Requirement 4: Deploy Agent to AgentCore Runtime

**User Story:** As a developer, I want to deploy the agent to AWS, so that it runs in AgentCore Runtime infrastructure.

#### Acceptance Criteria

1. THE deployment process SHALL build the Docker container from the Deployment_Package
2. THE deployment process SHALL push the container image to AWS ECR repository
3. THE deployment process SHALL create an AgentCore Runtime agent resource in AWS
4. THE deployment process SHALL configure the agent with Nova_Lite model and Knowledge_Base
5. WHEN deployment completes, THE deployment process SHALL output the agent ARN and agent ID
6. THE deployed Runtime_Agent SHALL appear in the AgentCore Runtime resources list alongside existing agents
7. THE deployment process SHALL configure network mode as PUBLIC for API accessibility
8. THE deployment process SHALL enable observability for monitoring and logging
9. THE deployment process SHALL create an execution role with necessary permissions for Bedrock and database access

### Requirement 5: Update Application to Invoke Runtime Agent

**User Story:** As an application, I want to call the deployed Runtime Agent, so that I can provide intelligent responses without running the agent locally.

#### Acceptance Criteria

1. THE Application SHALL use boto3 bedrock-agentcore-runtime client to invoke the Runtime_Agent
2. THE Application SHALL read the agent ARN from environment variable AGENTCORE_RUNTIME_AGENT_ARN
3. WHEN a user submits a query, THE Application SHALL call invoke_agent API with the query as prompt
4. THE Application SHALL pass session_id to maintain conversation context across invocations
5. WHEN the Runtime_Agent responds, THE Application SHALL extract the response text from the API result
6. THE Application SHALL handle API errors gracefully and return user-friendly error messages
7. THE Application SHALL preserve the existing chat API endpoint (/api/v1/chat/agent) interface
8. THE Application SHALL remove or deprecate the Local_Agent implementation after Runtime_Agent is verified
9. THE Application SHALL log agent invocations including query, session_id, and response time

### Requirement 6: Configure Database Access for Runtime Agent

**User Story:** As a Runtime Agent, I want to access the application database, so that I can execute tool queries.

#### Acceptance Criteria

1. THE Runtime_Agent SHALL read database connection parameters from environment variables
2. THE environment variables SHALL include DATABASE_URL or equivalent connection string
3. THE Runtime_Agent SHALL use SQLAlchemy to connect to the database
4. THE Runtime_Agent SHALL reuse the existing database models from src/database/models.py
5. WHEN the Runtime_Agent starts, THE Runtime_Agent SHALL verify database connectivity
6. IF database connection fails, THEN THE Runtime_Agent SHALL log an error and return a failure status
7. THE Runtime_Agent SHALL use connection pooling for efficient database access
8. THE Runtime_Agent SHALL close database connections properly after tool execution

### Requirement 7: Test End-to-End Agent Invocation

**User Story:** As a developer, I want to verify the deployed agent works correctly, so that I can ensure the migration is successful.

#### Acceptance Criteria

1. THE test process SHALL invoke the Runtime_Agent with a simple query (e.g., "Hello")
2. THE test process SHALL invoke the Runtime_Agent with a tool-requiring query (e.g., "How is PROD_SALES?")
3. THE test process SHALL verify the Runtime_Agent returns appropriate responses for both query types
4. THE test process SHALL verify the Runtime_Agent correctly executes database tools
5. THE test process SHALL verify the Runtime_Agent maintains session context across multiple queries
6. THE test process SHALL measure response time and verify it is acceptable (< 5 seconds for simple queries)
7. THE test process SHALL verify the Runtime_Agent handles errors gracefully (e.g., invalid system_id)
8. THE test process SHALL compare Runtime_Agent responses with Local_Agent responses for consistency

### Requirement 8: Document Deployment and Configuration

**User Story:** As a developer, I want clear documentation, so that I can deploy and maintain the Runtime Agent.

#### Acceptance Criteria

1. THE documentation SHALL provide step-by-step deployment instructions
2. THE documentation SHALL list all required environment variables and their purposes
3. THE documentation SHALL explain how to build and push the Docker container
4. THE documentation SHALL explain how to configure the .bedrock_agentcore.yaml file
5. THE documentation SHALL provide troubleshooting guidance for common deployment issues
6. THE documentation SHALL explain how to update the agent after code changes
7. THE documentation SHALL document the differences between Local_Agent and Runtime_Agent
8. THE documentation SHALL provide examples of invoking the Runtime_Agent via API

