#!/bin/bash

# File Monitoring Agent - Deployment Script
# This script builds and deploys the File Monitoring Agent to AWS Bedrock AgentCore Runtime

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AGENT_NAME="file_monitoring_agent"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/bedrock-agentcore-${AGENT_NAME}"
EXECUTION_ROLE_NAME="AmazonBedrockAgentCoreSDKRuntime-${AWS_REGION}"
MODEL_ID="us.amazon.nova-lite-v1:0"
KNOWLEDGE_BASE_ID="MJBJ5LOYSO"

echo -e "${GREEN}=== File Monitoring Agent Deployment ===${NC}"
echo "Agent Name: ${AGENT_NAME}"
echo "AWS Region: ${AWS_REGION}"
echo "AWS Account: ${AWS_ACCOUNT_ID}"
echo ""

# Check required environment variables
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}Warning: DATABASE_URL not set. Agent will need this at runtime.${NC}"
fi

# Step 1: Create ECR repository if it doesn't exist
echo -e "${GREEN}Step 1: Checking ECR repository...${NC}"
if ! aws ecr describe-repositories --repository-names "bedrock-agentcore-${AGENT_NAME}" --region ${AWS_REGION} > /dev/null 2>&1; then
    echo "Creating ECR repository..."
    aws ecr create-repository \
        --repository-name "bedrock-agentcore-${AGENT_NAME}" \
        --region ${AWS_REGION} \
        --image-scanning-configuration scanOnPush=true
    echo -e "${GREEN}ECR repository created.${NC}"
else
    echo "ECR repository already exists."
fi

# Step 2: Authenticate Docker to ECR
echo -e "${GREEN}Step 2: Authenticating Docker to ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPOSITORY}

# Step 3: Build Docker container
echo -e "${GREEN}Step 3: Building Docker container...${NC}"
docker build -t ${AGENT_NAME}:latest .
docker tag ${AGENT_NAME}:latest ${ECR_REPOSITORY}:latest

# Step 4: Push container to ECR
echo -e "${GREEN}Step 4: Pushing container to ECR...${NC}"
docker push ${ECR_REPOSITORY}:latest
IMAGE_URI="${ECR_REPOSITORY}:latest"
echo "Image URI: ${IMAGE_URI}"

# Step 5: Create or get execution role
echo -e "${GREEN}Step 5: Checking execution role...${NC}"
if ! aws iam get-role --role-name ${EXECUTION_ROLE_NAME} > /dev/null 2>&1; then
    echo "Creating execution role..."
    
    # Create trust policy
    cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create role
    aws iam create-role \
        --role-name ${EXECUTION_ROLE_NAME} \
        --assume-role-policy-document file:///tmp/trust-policy.json
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name ${EXECUTION_ROLE_NAME} \
        --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
    
    aws iam attach-role-policy \
        --role-name ${EXECUTION_ROLE_NAME} \
        --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
    
    echo -e "${GREEN}Execution role created.${NC}"
    sleep 10  # Wait for role to propagate
else
    echo "Execution role already exists."
fi

EXECUTION_ROLE_ARN=$(aws iam get-role --role-name ${EXECUTION_ROLE_NAME} --query 'Role.Arn' --output text)
echo "Execution Role ARN: ${EXECUTION_ROLE_ARN}"

# Step 6: Deploy agent to AgentCore Runtime
echo -e "${GREEN}Step 6: Deploying agent to AgentCore Runtime...${NC}"

# Check if agent already exists
AGENT_EXISTS=$(aws bedrock-agentcore list-runtimes --region ${AWS_REGION} --query "runtimes[?name=='${AGENT_NAME}'].runtimeId" --output text)

if [ -z "$AGENT_EXISTS" ]; then
    echo "Creating new agent..."
    
    # Create agent configuration
    cat > /tmp/agent-config.json <<EOF
{
  "name": "${AGENT_NAME}",
  "description": "File Monitoring Agent for querying system health and SLA violations",
  "executionRoleArn": "${EXECUTION_ROLE_ARN}",
  "containerConfiguration": {
    "imageUri": "${IMAGE_URI}",
    "environmentVariables": {
      "AWS_REGION": "${AWS_REGION}",
      "MODEL_ID": "${MODEL_ID}",
      "KNOWLEDGE_BASE_ID": "${KNOWLEDGE_BASE_ID}"
    }
  },
  "networkConfiguration": {
    "networkMode": "PUBLIC"
  },
  "observabilityConfiguration": {
    "enabled": true
  }
}
EOF

    # Create agent
    AGENT_RESPONSE=$(aws bedrock-agentcore create-runtime \
        --region ${AWS_REGION} \
        --cli-input-json file:///tmp/agent-config.json)
    
    AGENT_ID=$(echo $AGENT_RESPONSE | jq -r '.runtimeId')
    AGENT_ARN=$(echo $AGENT_RESPONSE | jq -r '.runtimeArn')
    
    echo -e "${GREEN}Agent created successfully!${NC}"
else
    echo "Agent already exists. Updating..."
    AGENT_ID=$AGENT_EXISTS
    
    # Update agent
    aws bedrock-agentcore update-runtime \
        --region ${AWS_REGION} \
        --runtime-id ${AGENT_ID} \
        --container-configuration imageUri=${IMAGE_URI}
    
    AGENT_ARN=$(aws bedrock-agentcore get-runtime --region ${AWS_REGION} --runtime-id ${AGENT_ID} --query 'runtime.runtimeArn' --output text)
    
    echo -e "${GREEN}Agent updated successfully!${NC}"
fi

# Step 7: Output deployment information
echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo -e "${GREEN}Agent ID:${NC} ${AGENT_ID}"
echo -e "${GREEN}Agent ARN:${NC} ${AGENT_ARN}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Set environment variable: export AGENTCORE_RUNTIME_AGENT_ARN=${AGENT_ARN}"
echo "2. Ensure DATABASE_URL is configured in your application environment"
echo "3. Test the agent using the test script: python test_runtime_agent.py"
echo ""
echo -e "${GREEN}Deployment information saved to deployment-info.txt${NC}"

# Save deployment info
cat > deployment-info.txt <<EOF
File Monitoring Agent Deployment Information
============================================
Deployment Date: $(date)
Agent Name: ${AGENT_NAME}
Agent ID: ${AGENT_ID}
Agent ARN: ${AGENT_ARN}
AWS Region: ${AWS_REGION}
AWS Account: ${AWS_ACCOUNT_ID}
ECR Repository: ${ECR_REPOSITORY}
Image URI: ${IMAGE_URI}
Execution Role: ${EXECUTION_ROLE_ARN}
Model ID: ${MODEL_ID}
Knowledge Base ID: ${KNOWLEDGE_BASE_ID}

Environment Variables Required:
- AGENTCORE_RUNTIME_AGENT_ARN=${AGENT_ARN}
- DATABASE_URL=<your-database-connection-string>
- AWS_REGION=${AWS_REGION}
EOF

echo -e "${GREEN}Done!${NC}"
