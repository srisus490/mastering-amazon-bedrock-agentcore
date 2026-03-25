# File Monitoring Agent - Deployment Guide

This guide provides comprehensive instructions for deploying the File Monitoring Agent to AWS Bedrock AgentCore Runtime.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Variables](#environment-variables)
4. [Deployment Steps](#deployment-steps)
5. [Configuration](#configuration)
6. [Testing the Deployment](#testing-the-deployment)
7. [Updating the Agent](#updating-the-agent)
8. [Troubleshooting](#troubleshooting)
9. [Local vs Runtime Agent](#local-vs-runtime-agent)
10. [API Usage Examples](#api-usage-examples)

## Overview

The File Monitoring Agent is deployed as a containerized application to AWS Bedrock AgentCore Runtime. This deployment model provides:

- **Isolation**: Agent runs in its own container with dedicated resources
- **Scalability**: AWS manages scaling based on demand
- **Centralized Management**: Agent is managed through AWS console and APIs
- **Observability**: Built-in logging and monitoring through CloudWatch

The deployment process involves:
1. Building a Docker container with the agent code
2. Pushing the container to AWS ECR (Elastic Container Registry)
3. Creating an AgentCore Runtime resource that runs the container
4. Configuring the application to invoke the deployed agent via API

## Prerequisites

Before deploying, ensure you have:

### Required Tools
- **Docker**: For building container images
- **AWS CLI**: Version 2.x or later, configured with credentials
- **jq**: JSON processor for parsing AWS CLI output
- **Bash**: For running the deployment script (Git Bash on Windows)

### AWS Permissions
Your AWS credentials must have permissions for:
- ECR: Create repositories, push images
- IAM: Create/manage execution roles
- Bedrock AgentCore: Create/update runtime agents
- CloudWatch: Create log groups (for observability)

### AWS Resources
- **AWS Account**: Active AWS account with Bedrock access
- **AWS Region**: us-east-1 (or your preferred region)
- **Knowledge Base**: ID MJBJ5LOYSO (system documentation)

## Environment Variables

### Required for Deployment

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for deployment | `us-east-1` |
| `DATABASE_URL` | Database connection string (runtime) | `sqlite:///data/file_monitoring.db` |

### Required for Application

| Variable | Description | Example |
|----------|-------------|---------|
| `AGENTCORE_RUNTIME_AGENT_ARN` | ARN of deployed agent | `arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/file_monitoring_agent-ABC123` |
| `AWS_REGION` | AWS region for API calls | `us-east-1` |
| `DATABASE_URL` | Database connection string | `sqlite:///data/file_monitoring.db` |

### Setting Environment Variables

**Linux/Mac:**
```bash
export AWS_REGION=us-east-1
export DATABASE_URL=sqlite:///data/file_monitoring.db
export AGENTCORE_RUNTIME_AGENT_ARN=arn:aws:bedrock-agentcore:...
```

**Windows (PowerShell):**
```powershell
$env:AWS_REGION="us-east-1"
$env:DATABASE_URL="sqlite:///data/file_monitoring.db"
$env:AGENTCORE_RUNTIME_AGENT_ARN="arn:aws:bedrock-agentcore:..."
```

## Deployment Steps

### Step 1: Navigate to Agent Directory

```bash
cd runtime/file_monitoring_agent
```

### Step 2: Verify Prerequisites

Check that all required files are present:
- `file_monitoring_agent.py` - Agent entrypoint
- `agent_action_handler.py` - Tool execution logic
- `database_connection.py` - Database access
- `models.py` - Database models
- `sql_query_generator.py` - SQL query generation
- `Dockerfile` - Container definition
- `.bedrock_agentcore.yaml` - Agent configuration
- `requirements.txt` - Python dependencies
- `deploy.sh` - Deployment script

### Step 3: Configure Environment

Set required environment variables:

```bash
export AWS_REGION=us-east-1
export DATABASE_URL=sqlite:///data/file_monitoring.db
```

### Step 4: Run Deployment Script

Make the script executable and run it:

```bash
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. Create ECR repository (if needed)
2. Authenticate Docker to ECR
3. Build Docker container
4. Push container to ECR
5. Create/update execution role
6. Deploy agent to AgentCore Runtime
7. Output agent ARN and ID

### Step 5: Save Agent ARN

The deployment script outputs the agent ARN. Save it for application configuration:

```bash
export AGENTCORE_RUNTIME_AGENT_ARN=<agent-arn-from-output>
```

The ARN is also saved to `deployment-info.txt` for reference.

### Step 6: Verify Deployment

Check that the agent is running:

```bash
aws bedrock-agentcore get-runtime \
    --region us-east-1 \
    --runtime-id <agent-id>
```

## Configuration

### Dockerfile Configuration

The Dockerfile defines the container environment:

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim
WORKDIR /app

# Environment variables
ENV UV_SYSTEM_PYTHON=1 \
    PYTHONUNBUFFERED=1 \
    AWS_REGION=us-east-1

# Install dependencies
COPY requirements.txt .
RUN uv pip install -r requirements.txt
RUN uv pip install aws-opentelemetry-distro

# Create non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

# Expose port for AgentCore Runtime
EXPOSE 9000

# Copy application code
COPY . .

# Run with OpenTelemetry instrumentation
CMD ["opentelemetry-instrument", "python", "-m", "file_monitoring_agent"]
```

### .bedrock_agentcore.yaml Configuration

This file configures the agent deployment:

```yaml
default_agent: file_monitoring_agent
agents:
  file_monitoring_agent:
    name: file_monitoring_agent
    entrypoint: file_monitoring_agent.py
    deployment_type: container
    platform: linux/arm64
    aws:
      region: us-east-1
      network_configuration:
        network_mode: PUBLIC
      observability:
        enabled: true
```

Key settings:
- `network_mode: PUBLIC` - Agent is accessible via API
- `observability: enabled` - CloudWatch logging enabled
- `platform: linux/arm64` - Container architecture

### Knowledge Base Configuration

The agent is configured to access AWS Bedrock Knowledge Base:
- **Knowledge Base ID**: MJBJ5LOYSO
- **Purpose**: System documentation and troubleshooting guides
- **Usage**: Agent queries KB for documentation-related questions

## Testing the Deployment

### Quick Test via AWS CLI

Test the agent with a simple query:

```bash
aws bedrock-agentcore-runtime invoke-agent \
    --region us-east-1 \
    --agent-arn <your-agent-arn> \
    --session-id test-session-$(date +%s) \
    --prompt "Hello, can you help me?"
```

### Test with Tool Invocation

Test a query that requires database tools:

```bash
aws bedrock-agentcore-runtime invoke-agent \
    --region us-east-1 \
    --agent-arn <your-agent-arn> \
    --session-id test-session-$(date +%s) \
    --prompt "How is PROD_SALES performing?"
```

### Test via Application

Update your application's environment variables and test the chat endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/chat/agent \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What systems are being monitored?",
    "session_id": "test-session-123"
  }'
```

## Updating the Agent

When you make changes to the agent code, follow these steps to update the deployment:

### Step 1: Make Code Changes

Edit the agent files as needed:
- `file_monitoring_agent.py` - Agent logic
- `agent_action_handler.py` - Tool implementations
- `models.py` - Database models

### Step 2: Test Locally (Optional)

Test changes locally before deploying:

```bash
python file_monitoring_agent.py
```

### Step 3: Rebuild and Redeploy

Run the deployment script again:

```bash
./deploy.sh
```

The script will:
- Build a new container with your changes
- Push the new image to ECR
- Update the existing agent with the new image

### Step 4: Verify Update

Test the updated agent to ensure changes work as expected.

### Step 5: Monitor Logs

Check CloudWatch logs for any errors:

```bash
aws logs tail /aws/bedrock-agentcore/file_monitoring_agent \
    --region us-east-1 \
    --follow
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: Docker Build Fails

**Symptoms:**
- Error during `docker build` command
- Missing dependencies or files

**Solutions:**
1. Verify all required files are present in the directory
2. Check that `requirements.txt` lists all dependencies
3. Ensure Docker daemon is running: `docker ps`
4. Check `.dockerignore` isn't excluding required files

#### Issue: ECR Push Fails

**Symptoms:**
- Authentication errors
- Permission denied errors

**Solutions:**
1. Verify AWS credentials: `aws sts get-caller-identity`
2. Re-authenticate to ECR:
   ```bash
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin <ecr-repo>
   ```
3. Check IAM permissions for ECR operations

#### Issue: Agent Creation Fails

**Symptoms:**
- Error creating AgentCore Runtime resource
- Invalid execution role errors

**Solutions:**
1. Verify execution role exists and has correct permissions
2. Check that role trust policy allows bedrock-agentcore.amazonaws.com
3. Ensure role has AmazonBedrockFullAccess policy attached
4. Wait 10-15 seconds after role creation for propagation

#### Issue: Agent Invocation Fails

**Symptoms:**
- Timeout errors
- Agent unavailable errors
- Database connection errors

**Solutions:**
1. Check agent status:
   ```bash
   aws bedrock-agentcore get-runtime --runtime-id <agent-id>
   ```
2. Verify DATABASE_URL is set correctly in container environment
3. Check CloudWatch logs for error details:
   ```bash
   aws logs tail /aws/bedrock-agentcore/file_monitoring_agent --follow
   ```
4. Ensure database is accessible from agent container

#### Issue: Tool Execution Fails

**Symptoms:**
- Agent responds but tools don't execute
- Database query errors

**Solutions:**
1. Verify database connection string is correct
2. Check that database file exists and is readable
3. Verify database schema matches models
4. Check CloudWatch logs for SQL errors

#### Issue: Knowledge Base Not Accessible

**Symptoms:**
- Agent can't access documentation
- KB query errors in logs

**Solutions:**
1. Verify Knowledge Base ID (MJBJ5LOYSO) is correct
2. Check execution role has Bedrock KB permissions
3. Ensure KB is in the same region as agent

### Debugging Tips

**View Agent Logs:**
```bash
aws logs tail /aws/bedrock-agentcore/file_monitoring_agent \
    --region us-east-1 \
    --follow \
    --format short
```

**Check Agent Status:**
```bash
aws bedrock-agentcore get-runtime \
    --region us-east-1 \
    --runtime-id <agent-id> \
    --query 'runtime.status'
```

**List All Agents:**
```bash
aws bedrock-agentcore list-runtimes \
    --region us-east-1 \
    --query 'runtimes[*].[name,runtimeId,status]' \
    --output table
```

**Test Database Connection:**
```bash
# From within the container
python -c "from database_connection import init_db; init_db('$DATABASE_URL')"
```

## Local vs Runtime Agent

### Local Agent (Original Implementation)

**Location**: `src/ai/agentcore_client.py`

**Characteristics:**
- Runs in the application process
- Direct access to application database
- Uses Bedrock Runtime API for Claude invocations
- No container overhead
- Tightly coupled with application

**Pros:**
- Simple deployment (no separate infrastructure)
- Fast startup (no container initialization)
- Direct database access

**Cons:**
- Resource sharing with application
- Harder to scale independently
- No isolation from application failures

### Runtime Agent (New Implementation)

**Location**: `runtime/file_monitoring_agent/`

**Characteristics:**
- Runs in separate container on AWS infrastructure
- Accessed via AgentCore Runtime API
- Managed by AWS (scaling, monitoring, etc.)
- Isolated from application
- Uses environment variables for configuration

**Pros:**
- Independent scaling
- Better isolation and fault tolerance
- Centralized management
- Built-in observability
- Consistent with other deployed agents

**Cons:**
- Additional deployment complexity
- Network latency for API calls
- Requires AWS infrastructure

### Migration Path

1. **Phase 1**: Deploy runtime agent alongside local agent
2. **Phase 2**: Update application to use runtime agent
3. **Phase 3**: Test both implementations in parallel
4. **Phase 4**: Switch to runtime agent as primary
5. **Phase 5**: Deprecate local agent implementation

## API Usage Examples

### Python Example (Using boto3)

```python
import boto3
import json

# Initialize client
bedrock_agentcore = boto3.client(
    'bedrock-agentcore-runtime',
    region_name='us-east-1'
)

# Invoke agent
response = bedrock_agentcore.invoke_agent(
    agentArn='arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/file_monitoring_agent-ABC123',
    sessionId='user-session-123',
    prompt='How is PROD_SALES performing?'
)

# Parse response
for event in response['completion']:
    if 'chunk' in event:
        chunk = event['chunk']
        if 'bytes' in chunk:
            text = chunk['bytes'].decode('utf-8')
            print(text)
```

### Python Example (Using Runtime Client Wrapper)

```python
from src.ai.agentcore_runtime_client import AgentCoreRuntimeClient

# Initialize client
client = AgentCoreRuntimeClient(
    agent_arn='arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/file_monitoring_agent-ABC123',
    region='us-east-1'
)

# Invoke agent
result = client.invoke(
    query='What systems are being monitored?',
    session_id='user-session-123'
)

print(f"Response: {result['response']}")
print(f"Tools used: {result['tools_used']}")
print(f"Response time: {result['response_time_ms']}ms")
```

### cURL Example

```bash
# Note: This is a simplified example. Actual AWS API calls require SigV4 signing.
# Use AWS CLI or SDK for production use.

aws bedrock-agentcore-runtime invoke-agent \
    --region us-east-1 \
    --agent-arn arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/file_monitoring_agent-ABC123 \
    --session-id user-session-123 \
    --prompt "Compare PROD_SALES and PROD_ORDERS" \
    --output json
```

### FastAPI Endpoint Example

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.ai.agentcore_runtime_client import AgentCoreRuntimeClient
import os

router = APIRouter()
runtime_client = AgentCoreRuntimeClient(
    agent_arn=os.getenv('AGENTCORE_RUNTIME_AGENT_ARN'),
    region=os.getenv('AWS_REGION', 'us-east-1')
)

class ChatRequest(BaseModel):
    query: str
    session_id: str = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tools_used: list[str]

@router.post("/api/v1/chat/agent", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    try:
        result = runtime_client.invoke(
            query=request.query,
            session_id=request.session_id
        )
        return ChatResponse(
            response=result['response'],
            session_id=result['session_id'],
            tools_used=result['tools_used']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Session Management Example

```python
# Maintain conversation context across multiple queries
session_id = "user-123-session"

# First query
result1 = client.invoke(
    query="What systems are being monitored?",
    session_id=session_id
)

# Follow-up query (agent remembers context)
result2 = client.invoke(
    query="How is the first one performing?",
    session_id=session_id
)
# Agent knows "first one" refers to the first system from previous query
```

### Error Handling Example

```python
from botocore.exceptions import ClientError

try:
    result = client.invoke(
        query="How is INVALID_SYSTEM performing?",
        session_id="test-session"
    )
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'ThrottlingException':
        print("Too many requests, please retry")
    elif error_code == 'ValidationException':
        print("Invalid request parameters")
    else:
        print(f"Unexpected error: {e}")
except Exception as e:
    print(f"Runtime error: {e}")
```

## Additional Resources

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Strands Agent Framework](https://github.com/aws-samples/strands)
- [Docker Documentation](https://docs.docker.com/)
- [AWS CLI Reference](https://docs.aws.amazon.com/cli/latest/)

## Support

For issues or questions:
1. Check CloudWatch logs for error details
2. Review this troubleshooting guide
3. Consult AWS Bedrock documentation
4. Contact your AWS support team

---

**Last Updated**: 2024
**Version**: 1.0
