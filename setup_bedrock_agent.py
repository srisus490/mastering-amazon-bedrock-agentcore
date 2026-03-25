"""Setup script for creating and configuring Bedrock Agent with action groups."""

import json
import os
import sys
import time

import boto3
from botocore.exceptions import ClientError

# Configuration
AGENT_NAME = "FileMonitoringAgent"
AGENT_DESCRIPTION = "Intelligent agent for file monitoring dashboard - answers questions about system health, violations, trends, insights, and predictions"
FOUNDATION_MODEL = "anthropic.claude-3-sonnet-20240229-v1:0"
REGION = os.getenv("BEDROCK_REGION", "us-east-1")
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID", "MJBJ5LOYSO")

# Agent instruction
AGENT_INSTRUCTION = """You are an intelligent file monitoring assistant. You help users understand their file monitoring systems.

You have access to these tools:
- get_system_health: Check health of any system
- get_violations: Query SLA violations
- get_trends: Analyze file arrival trends
- compare_systems: Compare multiple systems
- get_insights: Generate AI insights about system behavior
- get_forecast: Predict future file arrivals
- analyze_root_cause: Investigate why violations occurred
- query_all_systems: Get overview of all systems

You also have access to a knowledge base with system documentation.

When answering:
1. Use tools to get current data
2. Combine multiple tools if needed for complex questions
3. Provide clear, concise answers
4. Include relevant metrics and timestamps
5. Suggest follow-up actions when appropriate

Be proactive - if you need more information, call the appropriate tools."""


def create_agent(bedrock_agent_client, iam_client):
    """Create the Bedrock Agent."""
    print(f"\n🤖 Creating Bedrock Agent: {AGENT_NAME}")
    
    # Create IAM role for agent
    role_name = f"{AGENT_NAME}Role"
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        role_response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"Role for {AGENT_NAME}"
        )
        role_arn = role_response['Role']['Arn']
        print(f"✅ Created IAM role: {role_arn}")
        
        # Attach policies
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
        )
        
        # Wait for role to be available
        print("⏳ Waiting for IAM role to propagate...")
        time.sleep(10)
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            role_arn = iam_client.get_role(RoleName=role_name)['Role']['Arn']
            print(f"ℹ️  Using existing IAM role: {role_arn}")
        else:
            raise
    
    # Create agent
    try:
        agent_response = bedrock_agent_client.create_agent(
            agentName=AGENT_NAME,
            agentResourceRoleArn=role_arn,
            description=AGENT_DESCRIPTION,
            foundationModel=FOUNDATION_MODEL,
            instruction=AGENT_INSTRUCTION,
            idleSessionTTLInSeconds=1800  # 30 minutes
        )
        
        agent_id = agent_response['agent']['agentId']
        print(f"✅ Created agent with ID: {agent_id}")
        
        # Wait for agent to be ready
        print("⏳ Waiting for agent to be ready...")
        time.sleep(30)
        
        # Check agent status
        max_retries = 10
        for i in range(max_retries):
            agent_status = bedrock_agent_client.get_agent(agentId=agent_id)
            status = agent_status['agent']['agentStatus']
            print(f"   Agent status: {status}")
            
            if status in ['NOT_PREPARED', 'PREPARED']:
                print("✅ Agent is ready!")
                break
            elif status == 'FAILED':
                raise Exception("Agent creation failed")
            
            if i < max_retries - 1:
                print(f"   Waiting... ({i+1}/{max_retries})")
                time.sleep(10)
        
        return agent_id, role_arn
        
    except ClientError as e:
        print(f"❌ Error creating agent: {e}")
        raise


def create_action_group_schema():
    """Create OpenAPI schema for action groups."""
    schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "File Monitoring API",
            "version": "1.0.0",
            "description": "API for file monitoring dashboard operations"
        },
        "paths": {
            "/system-health": {
                "get": {
                    "summary": "Get system health status",
                    "description": "Returns health metrics for a specific system including file counts, SLA scores, and violations",
                    "operationId": "getSystemHealth",
                    "parameters": [
                        {
                            "name": "system_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "System ID (e.g., PROD_SALES, PROD_BACKUP)"
                        },
                        {
                            "name": "days",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 7},
                            "description": "Number of days to analyze"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "System health data",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "/violations": {
                "get": {
                    "summary": "Get SLA violations",
                    "description": "Returns SLA violations for specified systems and time period",
                    "operationId": "getViolations",
                    "parameters": [
                        {
                            "name": "system_ids",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "Comma-separated system IDs"
                        },
                        {
                            "name": "days",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 7}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Violations data"}
                    }
                }
            },
            "/trends": {
                "get": {
                    "summary": "Get file arrival trends",
                    "description": "Returns trend analysis for file arrivals over time",
                    "operationId": "getTrends",
                    "parameters": [
                        {
                            "name": "system_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "days",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 14}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Trend data"}
                    }
                }
            },
            "/compare-systems": {
                "get": {
                    "summary": "Compare multiple systems",
                    "description": "Compares metrics across multiple systems",
                    "operationId": "compareSystems",
                    "parameters": [
                        {
                            "name": "system_ids",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Comma-separated system IDs to compare"
                        }
                    ],
                    "responses": {
                        "200": {"description": "Comparison data"}
                    }
                }
            },
            "/insights": {
                "get": {
                    "summary": "Generate AI insights",
                    "description": "Generates intelligent insights about system behavior",
                    "operationId": "getInsights",
                    "parameters": [
                        {
                            "name": "system_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "days",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 30}
                        }
                    ],
                    "responses": {
                        "200": {"description": "AI-generated insights"}
                    }
                }
            },
            "/forecast": {
                "get": {
                    "summary": "Get forecast predictions",
                    "description": "Predicts future file arrivals based on historical patterns",
                    "operationId": "getForecast",
                    "parameters": [
                        {
                            "name": "system_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Forecast predictions"}
                    }
                }
            },
            "/root-cause": {
                "get": {
                    "summary": "Analyze root cause",
                    "description": "Analyzes root causes of SLA violations",
                    "operationId": "analyzeRootCause",
                    "parameters": [
                        {
                            "name": "system_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "days",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 7}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Root cause analysis"}
                    }
                }
            },
            "/all-systems": {
                "get": {
                    "summary": "Get all systems overview",
                    "description": "Returns overview of all monitored systems",
                    "operationId": "queryAllSystems",
                    "responses": {
                        "200": {"description": "All systems data"}
                    }
                }
            }
        }
    }
    
    return schema


def create_action_group(bedrock_agent_client, agent_id):
    """Create action group for the agent."""
    print("\n🔧 Creating action group...")
    
    schema = create_action_group_schema()
    
    # Get API Gateway endpoint from environment
    api_endpoint = os.getenv("API_ENDPOINT", "http://localhost:8000")
    
    try:
        response = bedrock_agent_client.create_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupName='FileMonitoringActions',
            description='Actions for querying file monitoring data',
            actionGroupExecutor={
                'customControl': 'RETURN_CONTROL'  # We'll handle execution in our code
            },
            apiSchema={
                'payload': json.dumps(schema)
            }
        )
        
        action_group_id = response['agentActionGroup']['actionGroupId']
        print(f"✅ Created action group: {action_group_id}")
        return action_group_id
        
    except ClientError as e:
        print(f"❌ Error creating action group: {e}")
        raise


def associate_knowledge_base(bedrock_agent_client, agent_id):
    """Associate knowledge base with agent."""
    if not KNOWLEDGE_BASE_ID:
        print("\n⚠️  No KNOWLEDGE_BASE_ID configured, skipping KB association")
        return None
    
    print(f"\n📚 Associating knowledge base: {KNOWLEDGE_BASE_ID}")
    
    try:
        response = bedrock_agent_client.associate_agent_knowledge_base(
            agentId=agent_id,
            agentVersion='DRAFT',
            description='System documentation and knowledge base',
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            knowledgeBaseState='ENABLED'
        )
        
        print(f"✅ Associated knowledge base")
        return response
        
    except ClientError as e:
        print(f"⚠️  Could not associate KB: {e}")
        return None


def prepare_agent(bedrock_agent_client, agent_id):
    """Prepare agent (create version and alias)."""
    print("\n🔄 Preparing agent...")
    
    try:
        # Prepare agent
        bedrock_agent_client.prepare_agent(agentId=agent_id)
        print("✅ Agent prepared")
        
        # Wait for preparation
        print("⏳ Waiting for agent to be ready...")
        time.sleep(30)
        
        # Create alias
        alias_response = bedrock_agent_client.create_agent_alias(
            agentId=agent_id,
            agentAliasName='prod',
            description='Production alias'
        )
        
        alias_id = alias_response['agentAlias']['agentAliasId']
        print(f"✅ Created alias: {alias_id}")
        
        return alias_id
        
    except ClientError as e:
        print(f"❌ Error preparing agent: {e}")
        raise


def main():
    """Main setup function."""
    print("=" * 60)
    print("🚀 Bedrock Agent Setup")
    print("=" * 60)
    
    # Initialize clients
    bedrock_agent_client = boto3.client('bedrock-agent', region_name=REGION)
    iam_client = boto3.client('iam', region_name=REGION)
    
    try:
        # Create agent
        agent_id, role_arn = create_agent(bedrock_agent_client, iam_client)
        
        # Create action group
        action_group_id = create_action_group(bedrock_agent_client, agent_id)
        
        # Associate knowledge base
        associate_knowledge_base(bedrock_agent_client, agent_id)
        
        # Prepare agent
        alias_id = prepare_agent(bedrock_agent_client, agent_id)
        
        # Print summary
        print("\n" + "=" * 60)
        print("✅ SETUP COMPLETE!")
        print("=" * 60)
        print(f"\nAgent ID: {agent_id}")
        print(f"Alias ID: {alias_id}")
        print(f"Region: {REGION}")
        print("\nAdd these to your .env file:")
        print(f"BEDROCK_AGENT_ID={agent_id}")
        print(f"BEDROCK_AGENT_ALIAS_ID={alias_id}")
        print("\n" + "=" * 60)
        
        return agent_id, alias_id
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
