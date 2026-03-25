"""File Monitoring Agent entrypoint for AWS Bedrock AgentCore Runtime.

This module implements the main entrypoint for the File Monitoring Agent running in
AWS Bedrock AgentCore Runtime. It provides tool-calling capabilities for querying
file monitoring system data and answering questions about system health, violations,
and performance.

Validates Requirements: 1.6, 1.7, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3
"""

import json
import logging
import os
from typing import Any, Dict

from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from database_connection import init_db, verify_connection
from agent_action_handler import get_action_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# System prompt describing agent role and capabilities
SYSTEM_PROMPT = """You are an intelligent file monitoring assistant that helps users understand and analyze their file monitoring systems.

Your role is to:
- Answer questions about system health, performance, and SLA compliance
- Provide insights into file arrival patterns and trends
- Help identify and troubleshoot SLA violations
- Compare performance across multiple systems
- Respond to greetings and general questions in a friendly manner

Available Tools:
1. get_system_health: Get health status and metrics for a specific system over a time period
2. get_violations: Get SLA violations for one or more systems over a time period
3. get_all_systems: Get a list of all monitored systems
4. compare_systems: Compare metrics across multiple systems

Instructions:
- Use tools when users ask for specific data about systems (health, violations, comparisons)
- For greetings like "Hello" or "Hi", respond warmly without using tools
- For general questions about capabilities, explain what you can do without using tools
- When using tools, interpret the results and provide clear, helpful explanations
- If a system ID is not found, suggest using get_all_systems to see available systems
- Always be helpful, accurate, and concise in your responses

Remember: You have access to a knowledge base with system documentation. Use it to provide context and troubleshooting guidance when appropriate.
"""

# Initialize database connection on module load
try:
    logger.info("Initializing database connection...")
    init_db()
    if verify_connection():
        logger.info("Database connection verified successfully")
    else:
        logger.error("Database connection verification failed")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    # Don't fail startup - let individual tool calls handle the error


# Tool definitions with @tool decorator

@tool
def get_system_health(system_id: str, days: int = 7) -> str:
    """
    Get health status and metrics for a specific system.
    
    This tool retrieves comprehensive health information including SLA scores,
    file arrival counts, and violation summaries for a specified system over
    a given time period.
    
    Args:
        system_id: The unique identifier of the system to query (e.g., "PROD_SALES")
        days: Number of days to look back (default: 7, range: 1-365)
        
    Returns:
        JSON string containing system health data or error message
        
    Validates: Requirement 2.1
    """
    logger.info(f"Tool invoked: get_system_health(system_id={system_id}, days={days})")
    
    try:
        handler = get_action_handler()
        result = handler.handle_action(
            action_group="file_monitoring",
            api_path="/system-health",
            parameters=[
                {"name": "system_id", "value": system_id},
                {"name": "days", "value": str(days)}
            ]
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = f"Error getting system health: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({"error": error_msg})


@tool
def get_violations(system_ids: str = "", days: int = 7) -> str:
    """
    Get SLA violations for one or more systems.
    
    This tool retrieves detailed information about SLA violations including
    violation types, severity levels, and timestamps. Can query all systems
    or filter to specific systems.
    
    Args:
        system_ids: Comma-separated list of system IDs (e.g., "PROD_SALES,TEST_DATA")
                   Leave empty to get violations for all systems
        days: Number of days to look back (default: 7, range: 1-365)
        
    Returns:
        JSON string containing violations data or error message
        
    Validates: Requirement 2.2
    """
    logger.info(f"Tool invoked: get_violations(system_ids={system_ids}, days={days})")
    
    try:
        handler = get_action_handler()
        result = handler.handle_action(
            action_group="file_monitoring",
            api_path="/violations",
            parameters=[
                {"name": "system_ids", "value": system_ids},
                {"name": "days", "value": str(days)}
            ]
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = f"Error getting violations: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({"error": error_msg})


@tool
def get_all_systems() -> str:
    """
    Get a list of all monitored systems.
    
    This tool retrieves information about all active systems being monitored,
    including their IDs, names, and directory paths. Useful for discovering
    available systems before querying specific system data.
    
    Returns:
        JSON string containing list of all systems or error message
        
    Validates: Requirement 2.3
    """
    logger.info("Tool invoked: get_all_systems()")
    
    try:
        handler = get_action_handler()
        result = handler.handle_action(
            action_group="file_monitoring",
            api_path="/all-systems",
            parameters=[]
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = f"Error getting all systems: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({"error": error_msg})


@tool
def compare_systems(system_ids: str) -> str:
    """
    Compare metrics across multiple systems.
    
    This tool performs a side-by-side comparison of key metrics across
    multiple systems, including SLA scores, file counts, and violation rates.
    Requires at least 2 systems to compare.
    
    Args:
        system_ids: Comma-separated list of system IDs to compare
                   (e.g., "PROD_SALES,PROD_INVENTORY,TEST_DATA")
                   Must include at least 2 system IDs
        
    Returns:
        JSON string containing comparison data or error message
        
    Validates: Requirement 2.4
    """
    logger.info(f"Tool invoked: compare_systems(system_ids={system_ids})")
    
    try:
        handler = get_action_handler()
        result = handler.handle_action(
            action_group="file_monitoring",
            api_path="/compare-systems",
            parameters=[
                {"name": "system_ids", "value": system_ids}
            ]
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = f"Error comparing systems: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({"error": error_msg})


# Initialize agent with BedrockModel and tools
logger.info("Initializing Bedrock Agent with Nova Lite model...")

# Get model ID from environment or use default
MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

logger.info(f"Using model: {MODEL_ID} in region: {AWS_REGION}")

# Create BedrockModel instance
bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    region=AWS_REGION
)

# Create Agent with model, system prompt, and tools
agent = Agent(
    model=bedrock_model,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        get_system_health,
        get_violations,
        get_all_systems,
        compare_systems
    ]
)

logger.info("Agent initialized successfully with 4 tools")


def extract_response_text(response: Any) -> str:
    """
    Extract response text from agent response.
    
    The strands Agent returns a response object that may contain text,
    tool calls, and other metadata. This function extracts the final
    text response to return to the user.
    
    Args:
        response: Agent response object
        
    Returns:
        Extracted response text as string
    """
    # Handle different response types
    if isinstance(response, str):
        return response
    
    # If response has a text attribute
    if hasattr(response, 'text'):
        return response.text
    
    # If response has a content attribute
    if hasattr(response, 'content'):
        content = response.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Extract text from content blocks
            text_parts = []
            for block in content:
                if isinstance(block, dict) and 'text' in block:
                    text_parts.append(block['text'])
                elif isinstance(block, str):
                    text_parts.append(block)
            return '\n'.join(text_parts)
    
    # Fallback: convert to string
    return str(response)


@app.entrypoint
def invoke_file_monitoring_agent(payload: Dict[str, Any]) -> str:
    """
    AgentCore Runtime entrypoint function.
    
    This function is called by AWS Bedrock AgentCore Runtime when the agent
    is invoked. It extracts the user's prompt from the payload, invokes the
    agent with the prompt, and returns the agent's response.
    
    Args:
        payload: Dictionary containing the invocation payload with 'prompt' key
        
    Returns:
        Agent's response text as string
        
    Validates: Requirements 1.9, 3.1, 3.2, 3.3
    """
    logger.info("=== Agent invocation started ===")
    logger.info(f"Payload keys: {list(payload.keys())}")
    
    try:
        # Extract prompt from payload
        user_input = payload.get("prompt", "")
        
        if not user_input:
            logger.warning("No prompt provided in payload")
            return "I didn't receive any input. Please provide a question or request."
        
        logger.info(f"User input: {user_input[:100]}...")  # Log first 100 chars
        
        # Invoke agent with user input
        logger.info("Invoking agent...")
        response = agent(user_input)
        
        # Extract response text
        response_text = extract_response_text(response)
        
        logger.info(f"Agent response length: {len(response_text)} characters")
        logger.info("=== Agent invocation completed successfully ===")
        
        return response_text
        
    except Exception as e:
        error_msg = f"Error processing agent invocation: {str(e)}"
        logger.error(error_msg, exc_info=True)
        logger.info("=== Agent invocation failed ===")
        return f"I encountered an error while processing your request: {str(e)}"


# Module-level initialization complete
logger.info("File Monitoring Agent module loaded successfully")
