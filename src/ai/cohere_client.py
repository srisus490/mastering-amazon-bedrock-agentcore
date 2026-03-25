"""Cohere client — drop-in replacement for BedrockClient."""

from typing import Optional

import cohere

from src.ai.config import ai_config
from src.ai.logger import ai_logger


class CohereError(Exception):
    """Base exception for Cohere client errors."""
    pass


class CohereAuthError(CohereError):
    """Authentication error with Cohere."""
    pass


class CohereTimeoutError(CohereError):
    """Timeout error when calling Cohere."""
    pass


class CohereUnavailableError(CohereError):
    """Cohere service unavailable."""
    pass


class CohereRateLimitError(CohereError):
    """Rate limit exceeded."""
    pass


class CohereClient:
    """
    Client for interacting with Cohere.

    Exposes the same interface as BedrockClient so it can be used
    as a drop-in replacement throughout the codebase.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.api_key = api_key or ai_config.cohere_api_key
        self.model = model or ai_config.cohere_model
        self.timeout = timeout or ai_config.bedrock_timeout  # reuse timeout setting

        if not self.api_key:
            raise CohereAuthError(
                "COHERE_API_KEY is not set. Add it to your .env file."
            )

        try:
            self.client = cohere.ClientV2(api_key=self.api_key, timeout=self.timeout)
            ai_logger.info(
                "Cohere client initialized",
                model=self.model,
                timeout=self.timeout,
            )
        except Exception as e:
            ai_logger.error("Failed to initialize Cohere client", error=str(e))
            raise CohereError(f"Failed to initialize Cohere client: {e}")

    def invoke_model(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a prompt to Cohere and return the generated text.

        Matches the BedrockClient.invoke_model() signature exactly.
        """
        max_tokens = max_tokens or ai_config.bedrock_max_tokens
        temperature = temperature if temperature is not None else ai_config.bedrock_temperature

        try:
            ai_logger.debug(
                "Invoking Cohere model",
                model=self.model,
                prompt_length=len(prompt),
                max_tokens=max_tokens,
                temperature=temperature,
            )

            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            generated_text = response.message.content[0].text

            ai_logger.debug(
                "Cohere model invoked successfully",
                response_length=len(generated_text),
            )

            return generated_text

        except cohere.errors.UnauthorizedError as e:
            raise CohereAuthError(f"Authentication failed: {e}")
        except cohere.errors.TooManyRequestsError as e:
            raise CohereRateLimitError(f"Rate limit exceeded: {e}")
        except cohere.errors.ServiceUnavailableError as e:
            raise CohereUnavailableError(f"Service unavailable: {e}")
        except Exception as e:
            error_str = str(e).lower()
            if "timeout" in error_str:
                raise CohereTimeoutError(f"Request timed out: {e}")
            if "unauthorized" in error_str or "api key" in error_str:
                raise CohereAuthError(f"Authentication failed: {e}")
            ai_logger.error("Unexpected error invoking Cohere", error=str(e))
            raise CohereError(f"Unexpected error: {e}")

    def validate_credentials(self) -> bool:
        """Check if the Cohere API key is valid."""
        try:
            # Lightweight call to verify the key works
            self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            ai_logger.info("Cohere credentials validated successfully")
            return True
        except Exception as e:
            ai_logger.error("Cohere credential validation failed", error=str(e))
            return False

    def invoke_model_with_tools(
        self,
        prompt: str,
        system_prompt: str,
        tools: list,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Invoke model with a system prompt (tools list is accepted but ignored —
        Cohere tool-use requires a different flow; for now we just prepend the
        system prompt to keep parity with the Bedrock interface).
        """
        max_tokens = max_tokens or ai_config.bedrock_max_tokens
        temperature = temperature if temperature is not None else ai_config.bedrock_temperature

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.message.content[0].text
        except Exception as e:
            ai_logger.error(f"Error invoking Cohere model with tools: {e}")
            return "I'm having trouble processing that request. Please try again."
