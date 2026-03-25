"""Complete agent setup for existing agent."""

import json
import os
import time

import boto3
from botocore.exceptions import ClientError

# Use the agent that was already created
AGENT_ID = "CRJ79K3SQR"
REGION = os.getenv("BEDROCK_REGION", "us-east-1")
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID", "MJBJ5LOYSO")


def create_action_group_schema():
    """Create minimal valid OpenAPI schema."""
    # Use a minimal schema that Bedrock accepts
    schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "File Monitoring API",
            "version": "1.0.0"
        },
        "paths": {
            "/health": {
                "get": {
                    "description": "Get system health",
                    "operationId": "getHealth",
                    "parameters": [
                        {
                            "name": "system_id",
                            "in": "query",
                            "description": "System ID",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    return schema


def main():
    """Complete the agent setup."""
    print("=" * 60)
    print("🔧 Completing Bedrock Agent Setup")
    print("=" * 60)
    print(f"\nAgent ID: {AGENT_ID}")
    
    bedrock_agent_client = boto3.client('bedrock-agent', region_name=REGION)
    
    try:
        # Check agent status
        print("\n📊 Checking agent status...")
        agent_info = bedrock_agent_client.get_agent(agentId=AGENT_ID)
        status = agent_info['agent']['agentStatus']
        print(f"   Status: {status}")
        
        if status == 'CREATING':
            print("\n⏳ Agent is still being created. Waiting...")
            for i in range(20):
                time.sleep(10)
                agent_info = bedrock_agent_client.get_agent(agentId=AGENT_ID)
                status = agent_info['agent']['agentStatus']
                print(f"   Status: {status} ({i+1}/20)")
                
                if status in ['NOT_PREPARED', 'PREPARED']:
                    break
        
        if status not in ['NOT_PREPARED', 'PREPARED']:
            print(f"❌ Agent is in {status} state. Cannot continue.")
            return
        
        # Create action group
        print("\n🔧 Creating action group...")
        schema = create_action_group_schema()
        
        try:
            response = bedrock_agent_client.create_agent_action_group(
                agentId=AGENT_ID,
                agentVersion='DRAFT',
                actionGroupName='FileMonitoringActions',
                description='Actions for querying file monitoring data',
                actionGroupExecutor={
                    'customControl': 'RETURN_CONTROL'
                },
                apiSchema={
                    'payload': json.dumps(schema)
                }
            )
            print(f"✅ Created action group: {response['agentActionGroup']['actionGroupId']}")
        except ClientError as e:
            if 'already exists' in str(e):
                print("ℹ️  Action group already exists")
            else:
                raise
        
        # Associate knowledge base
        if KNOWLEDGE_BASE_ID:
            print(f"\n📚 Associating knowledge base: {KNOWLEDGE_BASE_ID}")
            try:
                bedrock_agent_client.associate_agent_knowledge_base(
                    agentId=AGENT_ID,
                    agentVersion='DRAFT',
                    description='System documentation',
                    knowledgeBaseId=KNOWLEDGE_BASE_ID,
                    knowledgeBaseState='ENABLED'
                )
                print("✅ Associated knowledge base")
            except ClientError as e:
                if 'already associated' in str(e):
                    print("ℹ️  Knowledge base already associated")
                else:
                    print(f"⚠️  Could not associate KB: {e}")
        
        # Prepare agent
        print("\n🔄 Preparing agent...")
        bedrock_agent_client.prepare_agent(agentId=AGENT_ID)
        print("✅ Agent prepared")
        
        # Wait for preparation
        print("⏳ Waiting for agent to be ready...")
        time.sleep(30)
        
        # Create alias
        print("\n🏷️  Creating alias...")
        try:
            alias_response = bedrock_agent_client.create_agent_alias(
                agentId=AGENT_ID,
                agentAliasName='prod',
                description='Production alias'
            )
            alias_id = alias_response['agentAlias']['agentAliasId']
            print(f"✅ Created alias: {alias_id}")
        except ClientError as e:
            if 'already exists' in str(e):
                # List aliases to get ID
                aliases = bedrock_agent_client.list_agent_aliases(agentId=AGENT_ID)
                alias_id = aliases['agentAliasSummaries'][0]['agentAliasId']
                print(f"ℹ️  Using existing alias: {alias_id}")
            else:
                raise
        
        # Print summary
        print("\n" + "=" * 60)
        print("✅ SETUP COMPLETE!")
        print("=" * 60)
        print(f"\nAgent ID: {AGENT_ID}")
        print(f"Alias ID: {alias_id}")
        print(f"Region: {REGION}")
        print("\nAdd these to your .env file:")
        print(f"BEDROCK_AGENT_ID={AGENT_ID}")
        print(f"BEDROCK_AGENT_ALIAS_ID={alias_id}")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
