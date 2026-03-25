"""
AgentCore Runtime Client for invoking deployed agents.

This module provides a client wrapper for invoking AWS Bedrock AgentCore Runtime
agents from the FastAPI application. It handles API communication, response parsing,
error handling, and logging.
"""

import uuid
import time
import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError


# Configure logging
logger = logging.getLogger(__name__)


class AgentCoreRuntimeClient:
    """
    Client for invoking AWS Bedrock AgentCore Runtime agents.
    
    This client wraps the boto3 bedrock-agentcore-runtime client and provides
    a simplified interface for invoking agents with proper error handling,
    response parsing, and logging.
    """
    
    def __init__(self, agent_arn: str, region: str = "us-east-1"):
        """
        Initialize the runtime client.
        
        Args:
            agent_arn: ARN of the deployed AgentCore Runtime agent
            region: AWS region where the agent is deployed (default: us-east-1)
        """
        self.agent_arn = agent_arn
        self.region = region
        
        # Initialize boto3 bedrock-agentcore client
        self.bedrock_agentcore = boto3.client(
            "bedrock-agentcore",
            region_name=region
        )
        
        logger.info(f"Initialized AgentCore Runtime client for agent: {agent_arn}")
    
    def invoke(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke the runtime agent with a query.
        
        Args:
            query: User's natural language query
            session_id: Optional session ID for maintaining conversation context.
                       If not provided, a new session ID will be generated.
        
        Returns:
            Dictionary containing:
                - response: Agent's text response
                - session_id: Session ID used for the invocation
                - tools_used: List of tools invoked by the agent
                - response_time_ms: Response time in milliseconds
        
        Raises:
            Exception: For unrecoverable errors (re-raised after logging)
        """
        # Generate session ID if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Record start time for response time calculation
        start_time = time.time()
        
        # Log invocation
        logger.info(f"Invoking agent with query: '{query[:100]}...' session_id: {session_id}")
        
        try:
            # Call invoke_agent_runtime API with correct parameters
            # The payload needs to be a JSON string containing the prompt
            import json
            payload_data = {
                "prompt": query
            }
            
            response = self.bedrock_agentcore.invoke_agent_runtime(
                agentRuntimeArn=self.agent_arn,
                runtimeSessionId=session_id,
                payload=json.dumps(payload_data)
            )
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Parse response and extract information
            result = self._parse_response(response)
            result["session_id"] = session_id
            result["response_time_ms"] = response_time_ms
            
            # Log successful invocation
            logger.info(
                f"Agent invocation successful - "
                f"session_id: {session_id}, "
                f"response_time: {response_time_ms}ms, "
                f"tools_used: {result.get('tools_used', [])}"
            )
            
            return result
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            request_id = e.response.get("ResponseMetadata", {}).get("RequestId", "Unknown")
            
            # Handle specific error codes with user-friendly messages
            if error_code == "ServiceUnavailableException" or e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 503:
                error_msg = "Agent temporarily unavailable, please try again"
                logger.error(
                    f"Agent unavailable - agent_arn: {self.agent_arn}, "
                    f"request_id: {request_id}, error: {str(e)}"
                )
                
            elif error_code == "AccessDeniedException" or e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 403:
                error_msg = "Unable to process request"
                logger.error(
                    f"Authentication error - agent_arn: {self.agent_arn}, "
                    f"request_id: {request_id}, error_type: {error_code}"
                )
                
            else:
                error_msg = f"Error invoking agent: {error_code}"
                logger.error(
                    f"Agent invocation error - agent_arn: {self.agent_arn}, "
                    f"request_id: {request_id}, error_type: {error_code}, "
                    f"error: {str(e)}"
                )
            
            # Return error response instead of raising
            return {
                "response": error_msg,
                "session_id": session_id,
                "tools_used": [],
                "response_time_ms": int((time.time() - start_time) * 1000),
                "error": True
            }
            
        except EndpointConnectionError as e:
            error_msg = "Request timed out, please try a simpler query"
            logger.error(
                f"Timeout error - agent_arn: {self.agent_arn}, "
                f"session_id: {session_id}, query: '{query[:100]}...', "
                f"error: {str(e)}"
            )
            
            return {
                "response": error_msg,
                "session_id": session_id,
                "tools_used": [],
                "response_time_ms": int((time.time() - start_time) * 1000),
                "error": True
            }
            
        except Exception as e:
            error_msg = "An unexpected error occurred"
            logger.error(
                f"Unexpected error - agent_arn: {self.agent_arn}, "
                f"session_id: {session_id}, query: '{query[:100]}...', "
                f"error_type: {type(e).__name__}, error: {str(e)}"
            )
            
            return {
                "response": error_msg,
                "session_id": session_id,
                "tools_used": [],
                "response_time_ms": int((time.time() - start_time) * 1000),
                "error": True
            }
    
    def _parse_response(self, response: Dict) -> Dict[str, Any]:
        """
        Extract response text and metadata from API result.
        
        Args:
            response: Raw response from invoke_agent_runtime API
        
        Returns:
            Dictionary containing parsed response data
        
        Raises:
            ValueError: If response format is malformed
        """
        try:
            # Extract response text from the streaming body
            response_text = ""
            tools_used = []
            
            # Read the streaming body
            if "response" in response:
                response_body = response["response"].read()
                response_data = json.loads(response_body.decode("utf-8"))
                
                # Extract text from the result
                if "result" in response_data:
                    result = response_data["result"]
                    if "content" in result:
                        # Concatenate all text content
                        for content_item in result["content"]:
                            if "text" in content_item:
                                response_text += content_item["text"]
                
                # TODO: Extract tool usage information if available in response
                # This may require parsing trace information if provided
            
            if not response_text:
                logger.warning(f"Empty response text from agent. Raw response keys: {response.keys()}")
                response_text = "No response from agent"
            
            return {
                "response": response_text,
                "tools_used": tools_used
            }
            
        except Exception as e:
            error_msg = f"Received invalid response from agent"
            logger.error(
                f"Response parsing error - agent_arn: {self.agent_arn}, "
                f"error: {str(e)}, raw_response: {str(response)[:500]}"
            )
            raise ValueError(error_msg) from e
