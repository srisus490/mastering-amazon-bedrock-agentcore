"""Amazon Bedrock client for AI model invocation."""

import json
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from src.ai.config import ai_config
from src.ai.logger import ai_logger


class BedrockError(Exception):
    """Base exception for Bedrock client errors."""
    pass


class BedrockAuthError(BedrockError):
    """Authentication error with Bedrock."""
    pass


class BedrockTimeoutError(BedrockError):
    """Timeout error when calling Bedrock."""
    pass


class BedrockUnavailableError(BedrockError):
    """Bedrock service unavailable."""
    pass


class BedrockRateLimitError(BedrockError):
    """Rate limit exceeded."""
    pass


class BedrockClient:
    """
    Client for interacting with Amazon Bedrock.
    
    Handles model invocation, error handling, and credential validation.
    """
    
    def __init__(
        self,
        region: Optional[str] = None,
        model_id: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize Bedrock client.
        
        Args:
            region: AWS region (defaults to config)
            model_id: Bedrock model ID (defaults to config)
            timeout: Request timeout in seconds (defaults to config)
        """
        self.region = region or ai_config.bedrock_region
        self.model_id = model_id or ai_config.bedrock_model_id
        self.timeout = timeout or ai_config.bedrock_timeout
        
        # Configure boto3 client with timeout
        config = Config(
            region_name=self.region,
            connect_timeout=self.timeout,
            read_timeout=self.timeout,
            retries={"max_attempts": 2, "mode": "standard"}
        )
        
        try:
            self.client = boto3.client("bedrock-runtime", config=config)
            ai_logger.info(
                "Bedrock client initialized",
                region=self.region,
                model_id=self.model_id,
                timeout=self.timeout
            )
        except Exception as e:
            ai_logger.error("Failed to initialize Bedrock client", error=str(e))
            raise BedrockError(f"Failed to initialize Bedrock client: {e}")
    
    def invoke_model(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Invoke Claude model with a prompt.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens in response (defaults to config)
            temperature: Temperature for response generation (defaults to config)
            
        Returns:
            Generated text response
            
        Raises:
            BedrockAuthError: If authentication fails
            BedrockTimeoutError: If request times out
            BedrockUnavailableError: If service is unavailable
            BedrockRateLimitError: If rate limit is exceeded
            BedrockError: For other errors
        """
        max_tokens = max_tokens or ai_config.bedrock_max_tokens
        temperature = temperature or ai_config.bedrock_temperature
        
        # Construct request body for Claude 3
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            ai_logger.debug(
                "Invoking Bedrock model",
                model_id=self.model_id,
                prompt_length=len(prompt),
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response["body"].read())
            
            # Extract text from Claude 3 response format
            if "content" in response_body and len(response_body["content"]) > 0:
                generated_text = response_body["content"][0]["text"]
            else:
                raise BedrockError("Invalid response format from Bedrock")
            
            ai_logger.debug(
                "Bedrock model invoked successfully",
                response_length=len(generated_text),
                stop_reason=response_body.get("stop_reason")
            )
            
            return generated_text
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            ai_logger.error(
                "Bedrock client error",
                error_code=error_code,
                error_message=error_message
            )
            
            # Map AWS error codes to specific exceptions
            if error_code in ["UnauthorizedException", "AccessDeniedException"]:
                raise BedrockAuthError(f"Authentication failed: {error_message}")
            elif error_code == "ThrottlingException":
                raise BedrockRateLimitError(f"Rate limit exceeded: {error_message}")
            elif error_code == "ServiceUnavailableException":
                raise BedrockUnavailableError(f"Service unavailable: {error_message}")
            elif error_code == "TimeoutError":
                raise BedrockTimeoutError(f"Request timed out: {error_message}")
            else:
                raise BedrockError(f"Bedrock error ({error_code}): {error_message}")
                
        except BotoCoreError as e:
            ai_logger.error("Boto core error", error=str(e))
            raise BedrockError(f"Boto core error: {e}")
            
        except json.JSONDecodeError as e:
            ai_logger.error("Failed to parse Bedrock response", error=str(e))
            raise BedrockError(f"Failed to parse response: {e}")
            
        except Exception as e:
            ai_logger.error("Unexpected error invoking Bedrock", error=str(e))
            raise BedrockError(f"Unexpected error: {e}")
    
    def validate_credentials(self) -> bool:
        """
        Check if AWS credentials are valid.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            # Try to list foundation models as a credential check
            sts_client = boto3.client("sts", region_name=self.region)
            sts_client.get_caller_identity()
            
            ai_logger.info("AWS credentials validated successfully")
            return True
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            ai_logger.error(
                "AWS credential validation failed",
                error_code=error_code
            )
            return False
            
        except Exception as e:
            ai_logger.error("Unexpected error validating credentials", error=str(e))
            return False

    
    def invoke_model_with_tools(
        self,
        prompt: str,
        system_prompt: str,
        tools: list,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Invoke model with tool definitions (for agentic AI).
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            tools: List of tool definitions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text response
        """
        max_tokens = max_tokens or ai_config.bedrock_max_tokens
        temperature = temperature or ai_config.bedrock_temperature
        
        # Construct request with tools
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "tools": tools
        }
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response["body"].read())
            
            # Extract text
            if "content" in response_body and len(response_body["content"]) > 0:
                generated_text = response_body["content"][0]["text"]
            else:
                generated_text = "I'm here to help with file monitoring questions."
            
            return generated_text
            
        except Exception as e:
            ai_logger.error(f"Error invoking model with tools: {e}")
            return "I'm having trouble processing that request. Please try again."
