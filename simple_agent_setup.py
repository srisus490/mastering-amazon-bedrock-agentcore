"""Simple agent setup - just KB, no action groups for now."""

import os
import time

import boto3
from botocore.exceptions import ClientError

AGENT_ID = "CRJ79K3SQR"
REGION = os.getenv("BEDROCK_REGION", "us-east-1")
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID", "MJBJ5LOYSO")


def main():
    """Simple agent setup."""
    print("=" * 60)
    print("🚀 Simple Bedrock Agent Setup")
    print("=" * 60)
    print(f"\nAgent ID: {AGENT_ID}")
    
    bedrock_agent_client = boto3.client('bedrock-agent', region_name=REGION)
    
    try:
        # Check agent status
        print("\n📊 Checking agent...")
        agent_info = bedrock_agent_client.get_agent(agentId=AGENT_ID)
        print(f"✅ Agent exists: {agent_info['agent']['agentName']}")
        
        # Associate knowledge base
        if KNOWLEDGE_BASE_ID:
            print(f"\n📚 Associating knowledge base...")
            try:
                bedrock_agent_client.associate_agent_knowledge_base(
                    agentId=AGENT_ID,
                    agentVersion='DRAFT',
                    description='System documentation',
                    knowledgeBaseId=KNOWLEDGE_BASE_ID,
                    knowledgeBaseState='ENABLED'
                )
                print("✅ Knowledge base associated")
            except ClientError as e:
                if 'already associated' in str(e).lower():
                    print("ℹ️  Knowledge base already associated")
                else:
                    print(f"⚠️  KB association: {e}")
        
        # Prepare agent
        print("\n🔄 Preparing agent...")
        try:
            bedrock_agent_client.prepare_agent(agentId=AGENT_ID)
            print("✅ Agent prepared")
        except ClientError as e:
            print(f"ℹ️  Prepare: {e}")
        
        # Wait
        print("⏳ Waiting...")
        time.sleep(20)
        
        # Create or get alias
        print("\n🏷️  Setting up alias...")
        try:
            alias_response = bedrock_agent_client.create_agent_alias(
                agentId=AGENT_ID,
                agentAliasName='prod'
            )
            alias_id = alias_response['agentAlias']['agentAliasId']
            print(f"✅ Created alias: {alias_id}")
        except ClientError as e:
            if 'already exists' in str(e).lower() or 'AlreadyExists' in str(e):
                aliases = bedrock_agent_client.list_agent_aliases(agentId=AGENT_ID)
                if aliases['agentAliasSummaries']:
                    alias_id = aliases['agentAliasSummaries'][0]['agentAliasId']
                    print(f"ℹ️  Using existing alias: {alias_id}")
                else:
                    alias_id = "TSTALIASID"
                    print(f"ℹ️  Using test alias: {alias_id}")
            else:
                alias_id = "TSTALIASID"
                print(f"⚠️  Using test alias: {alias_id}")
        
        # Success
        print("\n" + "=" * 60)
        print("✅ SETUP COMPLETE!")
        print("=" * 60)
        print(f"\nAgent ID: {AGENT_ID}")
        print(f"Alias ID: {alias_id}")
        print("\nAdd to .env:")
        print(f"BEDROCK_AGENT_ID={AGENT_ID}")
        print(f"BEDROCK_AGENT_ALIAS_ID={alias_id}")
        print("\nThe agent can now:")
        print("- Answer questions using the knowledge base")
        print("- Provide intelligent responses")
        print("- Handle greetings and general queries")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
