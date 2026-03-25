"""Bedrock Agent client for intelligent agentic AI capabilities."""

import json
import uuid
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from src.ai.config import ai_config
from src.core.logging import get_logger

logger = get_logger(__name__)


class BedrockAgentClient:
    """Client for Amazon Bedrock Agents with intelligent tool orchestration."""
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_alias_id: Optional[str] = None,
        region: Optional[str] = None
    ):
        """
        Initialize Bedrock Agent client.
        
        Args:
            agent_id: Bedrock Agent ID (from environment if not provided)
            agent_alias_id: Agent alias ID (from environment if not provided)
            region: AWS region (from config if not provided)
        """
        self.region = region or ai_config.bedrock_region
        self.agent_id = agent_id or self._get_env_var('BEDROCK_AGENT_ID')
        self.agent_alias_id = agent_alias_id or self._get_env_var('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')
        
        # Initialize Bedrock Agent Runtime client
        self.client = boto3.client(
            'bedrock-agent-runtime',
            region_name=self.region
        )
        
        logger.info(
            "Bedrock Agent client initialized",
            agent_id=self.agent_id,
            alias_id=self.agent_alias_id,
            region=self.region
        )
    
    def invoke_agent(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        enable_trace: bool = True
    ) -> Dict[str, Any]:
        """
        Invoke the Bedrock Agent with a user prompt.
        
        The agent will:
        1. Understand the user's intent
        2. Decide which tools to call
        3. Execute tools in the right order
        4. Synthesize a final response
        
        Args:
            prompt: User's natural language query
            session_id: Session ID for conversation continuity
            enable_trace: Enable trace for debugging
            
        Returns:
            Dictionary with response, trace, and metadata
        """
        if not self.agent_id:
            raise ValueError("BEDROCK_AGENT_ID not configured. Please set up the agent first.")
        
        session_id = session_id or str(uuid.uuid4())
        
        try:
            logger.info(
                "Invoking Bedrock Agent",
                prompt=prompt[:100],
                session_id=session_id
            )
            
            # Invoke agent
            response = self.client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=prompt,
                enableTrace=enable_trace
            )
            
            # Process streaming response
            result = self._process_agent_response(response)
            
            logger.info(
                "Agent invocation completed",
                session_id=session_id,
                tools_used=len(result.get('trace', {}).get('tool_calls', [])),
                response_length=len(result.get('response', ''))
            )
            
            return result
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"Bedrock Agent error: {error_code} - {error_msg}")
            raise
        except Exception as e:
            logger.error(f"Error invoking Bedrock Agent: {e}")
            raise
    
    def _process_agent_response(self, response: Dict) -> Dict[str, Any]:
        """
        Process the streaming response from Bedrock Agent.
        
        Args:
            response: Response from invoke_agent
            
        Returns:
            Processed response with text, trace, and metadata
        """
        completion = ""
        trace_data = {
            'tool_calls': [],
            'reasoning': [],
            'kb_retrievals': []
        }
        
        # Process event stream
        event_stream = response.get('completion', [])
        
        for event in event_stream:
            # Extract completion text
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    completion += chunk['bytes'].decode('utf-8')
            
            # Extract trace information
            if 'trace' in event:
                trace = event['trace'].get('trace', {})
                
                # Orchestration trace (reasoning)
                if 'orchestrationTrace' in trace:
                    orch_trace = trace['orchestrationTrace']
                    
                    # Rationale (agent's reasoning)
                    if 'rationale' in orch_trace:
                        rationale = orch_trace['rationale']
                        trace_data['reasoning'].append({
                            'text': rationale.get('text', ''),
                            'trace_id': rationale.get('traceId')
                        })
                    
                    # Invocation input (tool being called)
                    if 'invocationInput' in orch_trace:
                        inv_input = orch_trace['invocationInput']
                        if 'actionGroupInvocationInput' in inv_input:
                            action_input = inv_input['actionGroupInvocationInput']
                            trace_data['tool_calls'].append({
                                'action_group': action_input.get('actionGroupName'),
                                'api_path': action_input.get('apiPath'),
                                'parameters': action_input.get('parameters', [])
                            })
                    
                    # Knowledge base lookup
                    if 'knowledgeBaseLookupInput' in orch_trace:
                        kb_input = orch_trace['knowledgeBaseLookupInput']
                        trace_data['kb_retrievals'].append({
                            'text': kb_input.get('text'),
                            'kb_id': kb_input.get('knowledgeBaseId')
                        })
        
        return {
            'response': completion.strip(),
            'session_id': response.get('sessionId'),
            'trace': trace_data,
            'content_type': response.get('contentType', 'text/plain')
        }
    
    def is_available(self) -> bool:
        """Check if Bedrock Agent is configured and available."""
        return bool(self.agent_id)
    
    def _get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable."""
        import os
        return os.getenv(key, default)


# Global instance
_agent_client = None


def get_agent_client() -> BedrockAgentClient:
    """Get or create global Bedrock Agent client instance."""
    global _agent_client
    if _agent_client is None:
        _agent_client = BedrockAgentClient()
    return _agent_client
