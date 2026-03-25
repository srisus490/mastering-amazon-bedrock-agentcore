"""Quick test script for Bedrock Agent."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ai.bedrock_agent_client import get_agent_client


def test_agent():
    """Test the Bedrock Agent with sample queries."""
    
    agent = get_agent_client()
    
    if not agent.is_available():
        print("❌ Agent not configured!")
        print("Run: python setup_bedrock_agent.py")
        return
    
    print("🤖 Testing Bedrock Agent\n")
    print("=" * 60)
    
    test_queries = [
        "Hello!",
        "What time is it?",
        "How is PROD_BACKUP doing?",
        "Show me all systems",
        "Compare PROD_SALES and PROD_INVENTORY"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 60)
        
        try:
            response = agent.invoke_agent(query, enable_trace=True)
            
            print(f"Response: {response['response']}")
            
            # Show tools used
            tools = response.get('trace', {}).get('tool_calls', [])
            if tools:
                print(f"\nTools used: {len(tools)}")
                for tool in tools:
                    print(f"  - {tool.get('action_group')}: {tool.get('api_path')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")


if __name__ == "__main__":
    test_agent()
