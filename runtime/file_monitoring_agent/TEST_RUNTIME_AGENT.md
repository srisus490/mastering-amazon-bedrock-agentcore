# Runtime Agent Test Script

This document describes how to use the `test_runtime_agent.py` script to test the deployed AgentCore Runtime agent.

## Overview

The test script validates the deployed File Monitoring Agent by running a comprehensive suite of tests that verify:

1. **Simple Query Handling** - Tests conversational queries that don't require tools (e.g., "Hello")
2. **Tool-Requiring Queries** - Tests queries that need database tools (e.g., "How is PROD_SALES?")
3. **Session Context Maintenance** - Verifies conversation context is maintained across multiple queries
4. **Response Time Performance** - Ensures simple queries respond within 5 seconds
5. **Error Handling** - Tests graceful handling of invalid system IDs and parameters

## Prerequisites

1. **Deployed Agent**: The File Monitoring Agent must be deployed to AWS Bedrock AgentCore Runtime
2. **Agent ARN**: You need the ARN of the deployed agent
3. **AWS Credentials**: Valid AWS credentials configured (via environment variables, AWS CLI, or IAM role)
4. **Python Dependencies**: The script requires the same dependencies as the application

## Usage

### Basic Usage

```bash
# Set the agent ARN environment variable
export AGENTCORE_RUNTIME_AGENT_ARN='arn:aws:bedrock-agentcore:us-east-1:123456789012:agent/your-agent-id'

# Run the test script
python runtime/file_monitoring_agent/test_runtime_agent.py
```

### With Custom Region

```bash
# Set both agent ARN and region
export AGENTCORE_RUNTIME_AGENT_ARN='arn:aws:bedrock-agentcore:us-west-2:123456789012:agent/your-agent-id'
export AWS_REGION='us-west-2'

# Run the test script
python runtime/file_monitoring_agent/test_runtime_agent.py
```

### From Project Root

```bash
# Run from the project root directory
cd /path/to/project
export AGENTCORE_RUNTIME_AGENT_ARN='arn:aws:bedrock-agentcore:...'
python runtime/file_monitoring_agent/test_runtime_agent.py
```

## Test Cases

### Test 1: Simple Query
- **Query**: "Hello"
- **Expected**: Conversational greeting response without tool usage
- **Validates**: Requirement 7.1

### Test 2: Tool-Requiring Query
- **Query**: "How is PROD_SALES?"
- **Expected**: Response with system health information (requires database tool execution)
- **Validates**: Requirements 7.2, 7.3, 7.4

### Test 3: Session Context Maintenance
- **Query 1**: "What systems are being monitored?"
- **Query 2**: "Tell me more about the first one"
- **Expected**: Same session ID maintained, contextual responses
- **Validates**: Requirement 7.5

### Test 4: Response Time Performance
- **Query**: "Hello, how are you?"
- **Expected**: Response time < 5000ms
- **Validates**: Requirement 7.6

### Test 5: Error Handling - Invalid System ID
- **Query**: "How is INVALID_SYSTEM_XYZ?"
- **Expected**: Graceful error message (no crash or stack trace)
- **Validates**: Requirement 7.7

### Test 6: Error Handling - Invalid Parameters
- **Query**: "" (empty string)
- **Expected**: Graceful handling (no crash or stack trace)
- **Validates**: Requirement 7.7

## Output Format

The script provides detailed output for each test:

```
================================================================================
AgentCore Runtime Agent Test Suite
================================================================================
Agent ARN: arn:aws:bedrock-agentcore:us-east-1:123456789012:agent/abc123
Region: us-east-1
================================================================================

Test 1: Simple Query (Hello)
--------------------------------------------------------------------------------
✓ PASS - Response: Hello! I'm here to help you with your file monitoring...
  Response time: 1234ms
  Tools used: []

Test 2: Tool-Requiring Query (How is PROD_SALES?)
--------------------------------------------------------------------------------
✓ PASS - Response contains system information
  Response preview: Based on the data, PROD_SALES system has an SLA score...
  Response time: 2345ms
  Tools used: ['/system-health']

...

================================================================================
Test Summary
================================================================================
Total Tests: 6
Passed: 6
Failed: 0

Average Response Time: 1850ms

================================================================================
✓ ALL TESTS PASSED
================================================================================
```

## Exit Codes

- **0**: All tests passed
- **1**: One or more tests failed or configuration error

## Troubleshooting

### Error: AGENTCORE_RUNTIME_AGENT_ARN environment variable not set

**Solution**: Set the environment variable with your agent's ARN:
```bash
export AGENTCORE_RUNTIME_AGENT_ARN='arn:aws:bedrock-agentcore:us-east-1:123456789012:agent/your-agent-id'
```

### Error: Unable to locate credentials

**Solution**: Configure AWS credentials using one of these methods:
```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID='your-access-key'
export AWS_SECRET_ACCESS_KEY='your-secret-key'

# Option 2: AWS CLI
aws configure

# Option 3: Use IAM role (if running on EC2/ECS)
```

### Error: Agent temporarily unavailable

**Solution**: 
- Verify the agent is deployed and running in AWS
- Check the agent ARN is correct
- Ensure the agent is in the same region as specified
- Wait a few moments and retry (agent may be starting up)

### Test Failures

If specific tests fail:

1. **Simple Query fails**: Check agent logs to see if there are initialization errors
2. **Tool-Requiring Query fails**: Verify database connection is configured correctly in the agent
3. **Session Context fails**: This may be expected if the agent doesn't maintain context (check agent implementation)
4. **Response Time fails**: Agent may be cold-starting or under load; retry after warm-up
5. **Error Handling fails**: Check agent logs for unexpected errors

## Integration with CI/CD

The test script can be integrated into CI/CD pipelines:

```bash
#!/bin/bash
# Example CI/CD script

# Deploy agent
./runtime/file_monitoring_agent/deploy.sh

# Extract agent ARN from deployment output
export AGENTCORE_RUNTIME_AGENT_ARN=$(cat deployment_output.json | jq -r '.agentArn')

# Run tests
python runtime/file_monitoring_agent/test_runtime_agent.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "Tests passed - deployment successful"
    exit 0
else
    echo "Tests failed - rolling back deployment"
    exit 1
fi
```

## Additional Notes

- The test script uses the `AgentCoreRuntimeClient` from `src/ai/agentcore_runtime_client.py`
- Tests are designed to be idempotent and can be run multiple times
- Some tests may pass even if the database doesn't contain the expected data (e.g., PROD_SALES system)
- Response times may vary based on network latency, agent cold start, and database query complexity
- The script generates unique session IDs for each test run to avoid conflicts

## Related Documentation

- [Deployment Guide](DEPLOYMENT.md) - How to deploy the agent
- [Requirements Document](../../.kiro/specs/agentcore-runtime-deployment/requirements.md) - Full requirements
- [Design Document](../../.kiro/specs/agentcore-runtime-deployment/design.md) - Architecture and design
