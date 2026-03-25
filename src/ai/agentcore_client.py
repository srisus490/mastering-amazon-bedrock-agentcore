"""Intelligent agent using Claude with tool calling (agentic AI)."""

import json
from typing import Any, Dict, List, Optional

import boto3
from botocore.config import Config

from src.ai.agent_action_handler import get_action_handler
from src.ai.config import ai_config
from src.core.logging import get_logger

logger = get_logger(__name__)


class FileMonitoringAgent:
    """Intelligent agent using Claude with native tool calling."""
    
    def __init__(self):
        """Initialize the agent with tools."""
        # Initialize Bedrock Runtime client directly
        config = Config(
            region_name=ai_config.bedrock_region,
            connect_timeout=30,
            read_timeout=30,
            retries={"max_attempts": 2, "mode": "standard"}
        )
        self.bedrock_runtime = boto3.client("bedrock-runtime", config=config)
        self.model_id = ai_config.bedrock_model_id
        
        self.action_handler = get_action_handler()
        self.tools = self._create_tool_definitions()
        
        logger.info("Intelligent Agent initialized", tool_count=len(self.tools))
    
    def _create_tool_definitions(self) -> List[Dict]:
        """Create tool definitions for Claude."""
        return [
            {
                "name": "get_system_health",
                "description": "Get health status and metrics for a specific system. Returns file counts, SLA scores, and violation counts.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "system_id": {
                            "type": "string",
                            "description": "System ID (e.g., PROD_SALES, PROD_BACKUP)"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to analyze (default: 7)"
                        }
                    },
                    "required": ["system_id"]
                }
            },
            {
                "name": "get_violations",
                "description": "Get SLA violations for systems. Can filter by specific systems and time period.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "system_ids": {
                            "type": "string",
                            "description": "Comma-separated system IDs (optional)"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back (default: 7)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_all_systems",
                "description": "Get a list of all monitored systems with their basic information.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "compare_systems",
                "description": "Compare metrics across multiple systems side-by-side.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "system_ids": {
                            "type": "string",
                            "description": "Comma-separated system IDs to compare"
                        }
                    },
                    "required": ["system_ids"]
                }
            }
        ]
    
    def _execute_tool(self, tool_name: str, tool_input: Dict) -> Dict:
        """Execute a tool and return results."""
        logger.info(f"Executing tool: {tool_name}", input=tool_input)
        
        # Convert tool input to action handler format
        params = [{"name": k, "value": str(v)} for k, v in tool_input.items()]
        
        # Map tool names to API paths
        tool_map = {
            "get_system_health": "/system-health",
            "get_violations": "/violations",
            "get_all_systems": "/all-systems",
            "compare_systems": "/compare-systems"
        }
        
        api_path = tool_map.get(tool_name)
        if not api_path:
            return {"error": f"Unknown tool: {tool_name}"}
        
        result = self.action_handler.handle_action("FileMonitoring", api_path, params)
        return result
    
    def invoke(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke the agent with a user query using Claude's tool calling.
        
        Args:
            query: User's natural language query
            session_id: Optional session ID
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            logger.info(f"Invoking agent: {query[:100]}")
            
            # Build system prompt
            system_prompt = """You are an intelligent file monitoring assistant. You help users understand their file monitoring systems.

You have access to tools to query system data. Use them when needed to answer questions accurately.

When answering:
1. Use tools to get current data when the question is about specific systems or metrics
2. For greetings (hi, hello), respond warmly without using tools
3. For general questions (time, weather), respond politely that you're focused on file monitoring
4. Provide clear, concise answers with relevant metrics
5. Be proactive - if you need data, call the appropriate tool

Available systems include: PROD_SALES, PROD_BACKUP, PROD_HR, PROD_ANALYTICS, and others."""
            
            # Conversation history
            messages = [{"role": "user", "content": query}]
            tools_used = []
            
            # Agentic loop - let Claude use tools iteratively
            max_iterations = 5
            for iteration in range(max_iterations):
                # Call Claude with tools
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "system": system_prompt,
                    "messages": messages,
                    "tools": self.tools
                }
                
                response = self.bedrock_runtime.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body)
                )
                
                response_body = json.loads(response["body"].read())
                stop_reason = response_body.get("stop_reason")
                content_blocks = response_body.get("content", [])
                
                logger.info(f"Claude response - iteration {iteration + 1}", stop_reason=stop_reason)
                
                # Add assistant's response to conversation
                messages.append({
                    "role": "assistant",
                    "content": content_blocks
                })
                
                # Check if Claude wants to use tools
                if stop_reason == "tool_use":
                    # Extract tool use requests
                    tool_results = []
                    
                    for block in content_blocks:
                        if block.get("type") == "tool_use":
                            tool_name = block.get("name")
                            tool_input = block.get("input", {})
                            tool_use_id = block.get("id")
                            
                            logger.info(f"Executing tool: {tool_name}", input=tool_input)
                            
                            # Execute the tool
                            result = self._execute_tool(tool_name, tool_input)
                            tools_used.append(tool_name)
                            
                            # Add tool result to conversation
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": json.dumps(result)
                            })
                    
                    # Add tool results as user message
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })
                    
                    # Continue loop to let Claude process tool results
                    continue
                
                # If no tool use, extract final response
                response_text = ""
                for block in content_blocks:
                    if block.get("type") == "text":
                        response_text += block.get("text", "")
                
                return {
                    'response': response_text,
                    'session_id': session_id,
                    'tools_used': tools_used,
                    'trace': {'iterations': iteration + 1}
                }
            
            # Max iterations reached
            return {
                'response': "I've gathered the information but need more time to process it. Please try asking again.",
                'session_id': session_id,
                'tools_used': tools_used,
                'trace': {'max_iterations_reached': True}
            }
            
        except Exception as e:
            logger.error(f"Error invoking agent: {e}", exc_info=True)
            # Fallback response
            return {
                'response': "I'm having trouble processing that request. Please try rephrasing your question.",
                'session_id': session_id,
                'tools_used': [],
                'trace': {'error': str(e)}
            }
    
    def is_available(self) -> bool:
        """Check if agent is available."""
        return True


# Global instance
_agent = None


def get_agentcore_client() -> FileMonitoringAgent:
    """Get or create global agent instance."""
    global _agent
    if _agent is None:
        _agent = FileMonitoringAgent()
    return _agent
