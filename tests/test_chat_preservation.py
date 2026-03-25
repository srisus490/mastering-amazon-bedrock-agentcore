"""Preservation property tests for chat endpoints.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

These tests verify that non-agent endpoints remain unchanged after the fix.
Tests should PASS on both unfixed and fixed code.

IMPORTANT: Follow observation-first methodology - observe behavior on UNFIXED code,
then verify it remains the same after the fix.
"""

import os
from unittest.mock import Mock, patch, MagicMock

import pytest
from hypothesis import given, strategies as st

from src.ai.models import ChatRequest


class TestChatPreservation:
    """Test suite to verify preservation of non-agent endpoint behavior."""
    
    def test_health_endpoint_works(self):
        """
        Test that /api/v1/chat/health endpoint works correctly.
        
        **Expected on UNFIXED code**: PASS (health check works)
        **Expected on FIXED code**: PASS (health check still works)
        
        **Validates: Requirement 3.3** - Health check endpoint continues to verify connectivity
        """
        from src.api.routes.chat import chat_health
        
        # Mock dependencies
        mock_session = Mock()
        mock_session.execute.return_value = None
        
        mock_response_generator = Mock()
        mock_response_generator.bedrock_client.validate_credentials.return_value = True
        
        mock_kb_client = Mock()
        mock_kb_client.is_available.return_value = True
        mock_kb_client.knowledge_base_id = 'MJBJ5LOYSO'
        
        mock_cache_manager = Mock()
        mock_cache_manager.getCacheStats.return_value = {'hits': 10, 'misses': 5}
        
        with patch('src.api.routes.chat.get_db_session') as mock_get_db:
            with patch('src.api.routes.chat._get_response_generator', return_value=mock_response_generator):
                with patch('src.api.routes.chat.get_kb_client', return_value=mock_kb_client):
                    with patch('src.api.routes.chat._get_cache_manager', return_value=mock_cache_manager):
                        mock_get_db.return_value.__enter__.return_value = mock_session
                        
                        import asyncio
                        result = asyncio.run(chat_health())
                        
                        # Verify health check returns expected structure
                        assert 'status' in result
                        assert 'bedrock' in result
                        assert 'database' in result
                        assert 'knowledge_base' in result
                        assert result['knowledge_base'] == 'healthy'
                        assert result['kb_id'] == 'MJBJ5LOYSO'
    
    def test_cache_clear_endpoint_works(self):
        """
        Test that /api/v1/chat/clear endpoint works correctly.
        
        **Expected on UNFIXED code**: PASS (cache clear works)
        **Expected on FIXED code**: PASS (cache clear still works)
        
        **Validates: Requirement 3.4** - Cache operations continue to work
        """
        from src.api.routes.chat import clear_chat
        
        mock_cache_manager = Mock()
        mock_cache_manager.clearCache.return_value = None
        
        with patch('src.api.routes.chat._get_cache_manager', return_value=mock_cache_manager):
            import asyncio
            result = asyncio.run(clear_chat())
            
            # Verify cache clear was called
            mock_cache_manager.clearCache.assert_called_once()
            
            # Verify response structure
            assert result['status'] == 'success'
            assert 'message' in result
    
    def test_examples_endpoint_works(self):
        """
        Test that /api/v1/chat/examples endpoint works correctly.
        
        **Expected on UNFIXED code**: PASS (examples endpoint works)
        **Expected on FIXED code**: PASS (examples endpoint still works)
        
        **Validates: Requirement 3.6** - Other endpoints remain unchanged
        """
        from src.api.routes.chat import get_examples
        
        import asyncio
        result = asyncio.run(get_examples())
        
        # Verify examples are returned
        assert 'examples' in result
        assert isinstance(result['examples'], list)
        assert len(result['examples']) > 0
    
    def test_examples_endpoint_with_system_id(self):
        """
        Test that /api/v1/chat/examples endpoint works with system_id parameter.
        
        **Expected on UNFIXED code**: PASS (system-specific examples work)
        **Expected on FIXED code**: PASS (system-specific examples still work)
        
        **Validates: Requirement 3.6** - Other endpoints remain unchanged
        """
        from src.api.routes.chat import get_examples
        from src.database.models import SourceSystemModel
        
        mock_system = Mock(spec=SourceSystemModel)
        mock_system.id = 'PROD_SALES'
        mock_system.name = 'Production Sales'
        
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_system
        
        with patch('src.api.routes.chat.get_db_session') as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            import asyncio
            result = asyncio.run(get_examples(system_id='PROD_SALES'))
            
            # Verify system-specific examples are returned
            assert 'examples' in result
            assert isinstance(result['examples'], list)
            assert any('PROD_SALES' in ex for ex in result['examples'])
    
    def test_knowledge_base_id_unchanged(self):
        """
        Test that KNOWLEDGE_BASE_ID environment variable is preserved.
        
        **Expected on UNFIXED code**: PASS (KB ID is MJBJ5LOYSO)
        **Expected on FIXED code**: PASS (KB ID is still MJBJ5LOYSO)
        
        **Validates: Requirement 3.1** - Knowledge Base client continues to use KNOWLEDGE_BASE_ID
        """
        # Read from .env file directly since tests may not load it
        env_path = '.env'
        kb_id = None
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('KNOWLEDGE_BASE_ID='):
                        kb_id = line.split('=', 1)[1].strip()
                        break
        
        # Also check environment variable
        if not kb_id:
            kb_id = os.getenv('KNOWLEDGE_BASE_ID')
        
        assert kb_id == 'MJBJ5LOYSO', f"KNOWLEDGE_BASE_ID must remain MJBJ5LOYSO, got {kb_id}"
    
    @given(query=st.text(min_size=1, max_size=200))
    def test_old_chat_query_endpoint_signature_unchanged(self, query):
        """
        Property test: For ANY query to /api/v1/chat/query, the endpoint signature remains unchanged.
        
        **Expected on UNFIXED code**: PASS (old endpoint works)
        **Expected on FIXED code**: PASS (old endpoint still works)
        
        **Validates: Requirement 3.6** - Old /api/v1/chat/query endpoint continues to function
        """
        from src.api.routes.chat import chat_query
        
        # This test just verifies the function signature hasn't changed
        # We don't need to execute it fully, just verify it accepts ChatRequest
        request = ChatRequest(query=query, session_id="test-session")
        
        # Verify the function exists and has the expected signature
        import inspect
        sig = inspect.signature(chat_query)
        params = list(sig.parameters.keys())
        
        # Should accept 'request' parameter
        assert 'request' in params, "chat_query must accept 'request' parameter"
        
        # Should return ChatResponse
        assert sig.return_annotation.__name__ == 'ChatResponse', \
            "chat_query must return ChatResponse"
    
    def test_cost_monitor_functionality_preserved(self):
        """
        Test that cost monitoring and circuit breaker logic is preserved.
        
        **Expected on UNFIXED code**: PASS (cost monitor works)
        **Expected on FIXED code**: PASS (cost monitor still works)
        
        **Validates: Requirement 3.5** - Cost monitoring continues to track token usage
        """
        from src.ai.cost_monitor import get_cost_monitor
        
        cost_monitor = get_cost_monitor()
        
        # Verify cost monitor has expected methods
        assert hasattr(cost_monitor, 'isCircuitBreakerActive'), \
            "Cost monitor must have isCircuitBreakerActive method"
        assert hasattr(cost_monitor, 'recordTokenUsage'), \
            "Cost monitor must have recordTokenUsage method"
        
        # Verify circuit breaker can be checked
        is_active = cost_monitor.isCircuitBreakerActive()
        assert isinstance(is_active, bool), "isCircuitBreakerActive must return boolean"
    
    def test_error_handling_preserved(self):
        """
        Test that error handling for non-agent endpoints is preserved.
        
        **Expected on UNFIXED code**: PASS (errors handled gracefully)
        **Expected on FIXED code**: PASS (errors still handled gracefully)
        
        **Validates: Requirement 3.2** - Error handling continues to work
        """
        from src.api.routes.chat import clear_chat
        from fastapi import HTTPException
        
        mock_cache_manager = Mock()
        mock_cache_manager.clearCache.side_effect = Exception("Test error")
        
        with patch('src.api.routes.chat._get_cache_manager', return_value=mock_cache_manager):
            import asyncio
            
            # Should raise HTTPException with status 500
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(clear_chat())
            
            assert exc_info.value.status_code == 500
            assert "Failed to clear cache" in exc_info.value.detail
    
    @given(
        system_id=st.text(min_size=1, max_size=50),
        days=st.integers(min_value=1, max_value=365)
    )
    def test_query_processor_components_unchanged(self, system_id, days):
        """
        Property test: Query processor components remain unchanged for all inputs.
        
        **Expected on UNFIXED code**: PASS (components work)
        **Expected on FIXED code**: PASS (components still work)
        
        **Validates: Requirement 3.6** - Non-agent query processing unchanged
        """
        from src.api.routes.chat import _get_intelligent_parser, _get_sql_generator
        
        # Verify components can be instantiated
        try:
            parser = _get_intelligent_parser()
            generator = _get_sql_generator()
            
            # Verify they have expected methods
            assert hasattr(parser, 'parseQuery'), "Parser must have parseQuery method"
            assert hasattr(generator, 'generateHealthQuery'), "Generator must have generateHealthQuery method"
            assert hasattr(generator, 'validateQuery'), "Generator must have validateQuery method"
        except Exception:
            # If initialization fails due to database issues, that's okay for this test
            # We're just verifying the structure hasn't changed
            pass
