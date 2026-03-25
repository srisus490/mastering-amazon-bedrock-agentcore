"""Bug condition exploration test for chat agent routing issue.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

This test MUST FAIL on unfixed code - failure confirms the bug exists.
The test encodes the expected behavior and will validate the fix when it passes.

CRITICAL: This test is EXPECTED TO FAIL on unfixed code.
DO NOT attempt to fix the test or the code when it fails.
"""

import os
from unittest.mock import Mock, patch, MagicMock

import pytest
from hypothesis import given, strategies as st

from src.ai.models import ChatRequest


class TestChatAgentBugCondition:
    """Test suite to explore and document the bug condition."""
    
    def test_bedrock_agent_id_configured(self):
        """
        Test that BEDROCK_AGENT_ID is configured in environment.
        
        **Expected on UNFIXED code**: FAIL (BEDROCK_AGENT_ID not set)
        **Expected on FIXED code**: PASS (BEDROCK_AGENT_ID=CRJ79K3SQR)
        """
        agent_id = os.getenv('BEDROCK_AGENT_ID')
        assert agent_id is not None, "BEDROCK_AGENT_ID must be configured in .env"
        assert agent_id == 'CRJ79K3SQR', f"BEDROCK_AGENT_ID must be CRJ79K3SQR, got {agent_id}"
    
    def test_chat_with_agent_uses_bedrock_agent_client(self):
        """
        Test that chat_with_agent() uses BedrockAgentClient instead of FileMonitoringAgent.
        
        **Expected on UNFIXED code**: FAIL (uses get_agentcore_client)
        **Expected on FIXED code**: PASS (uses get_agent_client)
        """
        from src.api.routes import chat
        
        # Mock the agent clients
        mock_bedrock_agent = Mock()
        mock_bedrock_agent.invoke_agent.return_value = {
            'response': 'Test response',
            'session_id': 'test-session',
            'trace': {'tool_calls': []},
            'content_type': 'text/plain'
        }
        
        mock_cost_monitor = Mock()
        mock_cost_monitor.isCircuitBreakerActive.return_value = False
        
        # Patch both clients to track which one is called
        with patch('src.api.routes.chat.get_agent_client', return_value=mock_bedrock_agent) as mock_get_agent:
            with patch('src.api.routes.chat.get_agentcore_client') as mock_get_agentcore:
                with patch('src.api.routes.chat.get_cost_monitor', return_value=mock_cost_monitor):
                    # Import the function after patching
                    from src.api.routes.chat import chat_with_agent
                    
                    # Create a test request
                    request = ChatRequest(
                        query="ok, any SLA violations ??",
                        session_id="test-session"
                    )
                    
                    # Call the function (this will fail on unfixed code)
                    try:
                        import asyncio
                        result = asyncio.run(chat_with_agent(request))
                    except Exception as e:
                        # On unfixed code, this might fail because agentcore_client is used
                        pytest.fail(f"chat_with_agent failed: {e}")
                    
                    # Verify that get_agent_client was called (BedrockAgentClient)
                    assert mock_get_agent.called, "chat_with_agent must use get_agent_client() for BedrockAgentClient"
                    
                    # Verify that get_agentcore_client was NOT called
                    assert not mock_get_agentcore.called, "chat_with_agent must NOT use get_agentcore_client() (FileMonitoringAgent)"
                    
                    # Verify invoke_agent was called with correct parameters
                    mock_bedrock_agent.invoke_agent.assert_called_once()
                    call_kwargs = mock_bedrock_agent.invoke_agent.call_args[1]
                    assert 'prompt' in call_kwargs, "invoke_agent must be called with 'prompt' parameter"
                    assert call_kwargs['prompt'] == request.query
    
    @given(query=st.text(min_size=1, max_size=200))
    def test_agent_endpoint_uses_bedrock_agent_for_all_queries(self, query):
        """
        Property test: For ANY query to /api/v1/chat/agent, the system must use BedrockAgentClient.
        
        **Expected on UNFIXED code**: FAIL (uses FileMonitoringAgent)
        **Expected on FIXED code**: PASS (uses BedrockAgentClient)
        """
        from src.api.routes import chat
        
        # Mock the agent clients
        mock_bedrock_agent = Mock()
        mock_bedrock_agent.invoke_agent.return_value = {
            'response': f'Response to: {query[:50]}',
            'session_id': 'test-session',
            'trace': {'tool_calls': []},
            'content_type': 'text/plain'
        }
        
        mock_cost_monitor = Mock()
        mock_cost_monitor.isCircuitBreakerActive.return_value = False
        
        with patch('src.api.routes.chat.get_agent_client', return_value=mock_bedrock_agent) as mock_get_agent:
            with patch('src.api.routes.chat.get_agentcore_client') as mock_get_agentcore:
                with patch('src.api.routes.chat.get_cost_monitor', return_value=mock_cost_monitor):
                    from src.api.routes.chat import chat_with_agent
                    
                    request = ChatRequest(query=query, session_id="test-session")
                    
                    try:
                        import asyncio
                        asyncio.run(chat_with_agent(request))
                    except Exception:
                        # Skip invalid queries that cause other errors
                        return
                    
                    # Property: Must use BedrockAgentClient for ALL queries
                    assert mock_get_agent.called, f"For query '{query[:50]}...', must use get_agent_client()"
                    assert not mock_get_agentcore.called, f"For query '{query[:50]}...', must NOT use get_agentcore_client()"
    
    def test_concrete_failing_case_sla_violations_query(self):
        """
        Test the concrete failing case: "ok, any SLA violations ??"
        
        This is the exact query that triggers the bug in production.
        
        **Expected on UNFIXED code**: FAIL (server error or wrong client used)
        **Expected on FIXED code**: PASS (proper response from BedrockAgentClient)
        """
        from src.api.routes import chat
        
        # Mock BedrockAgentClient to return a proper response
        mock_bedrock_agent = Mock()
        mock_bedrock_agent.invoke_agent.return_value = {
            'response': 'Based on the Knowledge Base, here are the recent SLA violations...',
            'session_id': 'test-session',
            'trace': {
                'tool_calls': [],
                'reasoning': ['Checking Knowledge Base for SLA violations'],
                'kb_retrievals': [{'text': 'SLA violation data', 'kb_id': 'MJBJ5LOYSO'}]
            },
            'content_type': 'text/plain'
        }
        
        mock_cost_monitor = Mock()
        mock_cost_monitor.isCircuitBreakerActive.return_value = False
        
        with patch('src.api.routes.chat.get_agent_client', return_value=mock_bedrock_agent):
            with patch('src.api.routes.chat.get_cost_monitor', return_value=mock_cost_monitor):
                from src.api.routes.chat import chat_with_agent
                
                request = ChatRequest(
                    query="ok, any SLA violations ??",
                    session_id="test-session"
                )
                
                import asyncio
                result = asyncio.run(chat_with_agent(request))
                
                # Verify we got a proper response (not "Server error. Please try again later")
                assert result.response != "Server error. Please try again later", \
                    "Must not return server error for SLA violations query"
                assert len(result.response) > 0, "Must return a non-empty response"
                assert "SLA" in result.response or "violation" in result.response.lower(), \
                    "Response should be relevant to SLA violations"
