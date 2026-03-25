"""Response generator for creating natural language responses using Bedrock."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.ai.cohere_client import CohereClient, CohereError as BedrockError
from src.ai.knowledge_base_client import get_kb_client
from src.core.logging import get_logger

logger = get_logger(__name__)


class ResponseGenerator:
    """Generates natural language responses using Amazon Bedrock."""
    
    # Maximum output tokens
    MAX_OUTPUT_TOKENS = 1000
    
    # Database schema summary (minimal for cost optimization)
    SCHEMA_SUMMARY = """
    Database Tables:
    - source_systems: id, name, is_active
    - file_arrivals: source_system_id, filename, arrival_timestamp, file_size_bytes
    - sla_violations: source_system_id, violation_date, violation_type, severity
    - sla_scores: source_system_id, score_date, score (0-100)
    """
    
    def __init__(self, bedrock_client: Optional[CohereClient] = None):
        """
        Initialize the response generator.
        
        Args:
            bedrock_client: Optional BedrockClient instance (creates new if None)
        """
        self.bedrock_client = bedrock_client or CohereClient()
        self.kb_client = get_kb_client()
    
    def generateResponse(
        self,
        query_result: Any,
        user_query: str,
        context: Optional[List[Dict]] = None,
        kb_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a natural language response from query results.
        
        Args:
            query_result: Results from database query
            user_query: Original user question
            context: Recent conversation messages
            kb_context: Retrieved Knowledge Base context (optional)
            
        Returns:
            Dictionary with response text and token usage
        """
        try:
            # Build the prompt with KB context
            prompt = self.buildPrompt(query_result, user_query, context, kb_context)
            
            # Invoke Bedrock
            start_time = datetime.now()
            response_text = self.bedrock_client.invoke_model(
                prompt=prompt,
                max_tokens=self.MAX_OUTPUT_TOKENS,
                temperature=0.7
            )
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Extract and clean response
            cleaned_response = self.extractResponse(response_text)
            
            # Estimate token usage (rough approximation)
            input_tokens = len(prompt.split()) * 1.3  # Rough token estimate
            output_tokens = len(cleaned_response.split()) * 1.3
            
            # Log token usage for cost monitoring
            logger.info(
                "Bedrock API call completed",
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                processing_time_seconds=processing_time,
                query_length=len(user_query),
                kb_context_used=kb_context is not None
            )
            
            return {
                'response': cleaned_response,
                'tokens_used': {
                    'input': int(input_tokens),
                    'output': int(output_tokens),
                    'cached': 0
                }
            }
            
        except BedrockError as e:
            logger.error(f"Bedrock error generating response: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def buildPrompt(
        self,
        query_result: Any,
        user_query: str,
        context: Optional[List[Dict]] = None,
        kb_context: Optional[str] = None
    ) -> str:
        """
        Construct a prompt for Bedrock.
        
        Args:
            query_result: Database query results
            user_query: User's question
            context: Recent conversation messages
            kb_context: Retrieved Knowledge Base context
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        # System instructions
        prompt_parts.append(
            "You are a helpful assistant for a file monitoring dashboard. "
            "Provide concise, natural language responses based on the data and knowledge provided. "
            "Format data as tables or lists when appropriate. "
            "Cite sources from the knowledge base when using that information. "
            "Limit your response to 200 words."
        )
        
        # Add Knowledge Base context first (most important)
        if kb_context:
            prompt_parts.append("\n" + kb_context)
            prompt_parts.append("\nUse the above knowledge base information to provide accurate answers.")
        
        # Add recent context (last 3 messages for cost optimization)
        if context:
            recent_context = context[-3:]
            if recent_context:
                prompt_parts.append("\nRecent Conversation:")
                for msg in recent_context:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    prompt_parts.append(f"{role.capitalize()}: {content}")
        
        # Add database schema (minimal) - only if no KB context
        if not kb_context:
            prompt_parts.append(f"\n{self.SCHEMA_SUMMARY}")
        
        # Add query results
        prompt_parts.append("\nQuery Results:")
        formatted_data = self.formatDataForPrompt(query_result)
        prompt_parts.append(formatted_data)
        
        # Add user query
        prompt_parts.append(f"\nUser Question: {user_query}")
        
        # Add response instructions
        prompt_parts.append(
            "\nProvide a clear, concise answer. "
            "If the data shows a table, format it as a markdown table. "
            "Include relevant metrics and timestamps. "
            "If no data is found, explain why. "
            "If you used knowledge base information, mention the source."
        )
        
        return "\n".join(prompt_parts)
    
    def formatDataForPrompt(self, data: Any) -> str:
        """
        Format query results for inclusion in prompt.
        
        Args:
            data: Query results (list of dicts, single dict, or None)
            
        Returns:
            Formatted string representation
        """
        if data is None or (isinstance(data, list) and len(data) == 0):
            return "No data found."
        
        # Convert to list if single dict
        if isinstance(data, dict):
            data = [data]
        
        # If it's a list of dicts, format as JSON
        if isinstance(data, list):
            # Limit to first 50 rows for cost optimization
            limited_data = data[:50]
            
            try:
                # Pretty print JSON
                return json.dumps(limited_data, indent=2, default=str)
            except Exception as e:
                logger.warning(f"Error formatting data as JSON: {e}")
                return str(limited_data)
        
        return str(data)
    
    def extractResponse(self, bedrock_output: str) -> str:
        """
        Parse and clean Bedrock response.
        
        Args:
            bedrock_output: Raw output from Bedrock
            
        Returns:
            Cleaned response text
        """
        # Remove any leading/trailing whitespace
        response = bedrock_output.strip()
        
        # Ensure response isn't too long (enforce token limit)
        words = response.split()
        if len(words) > 250:  # Roughly 1000 tokens
            response = ' '.join(words[:250]) + '...'
        
        return response
    
    def formatTableResponse(self, data: List[Dict]) -> str:
        """
        Format data as a markdown table.
        
        Args:
            data: List of dictionaries with consistent keys
            
        Returns:
            Markdown table string
        """
        if not data:
            return "No data available."
        
        # Get headers from first row
        headers = list(data[0].keys())
        
        # Build markdown table
        table_parts = []
        
        # Header row
        table_parts.append('| ' + ' | '.join(headers) + ' |')
        
        # Separator row
        table_parts.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        
        # Data rows (limit to 20 for readability)
        for row in data[:20]:
            values = [str(row.get(h, '')) for h in headers]
            table_parts.append('| ' + ' | '.join(values) + ' |')
        
        if len(data) > 20:
            table_parts.append(f"\n... and {len(data) - 20} more rows")
        
        return '\n'.join(table_parts)
    
    def formatMetricResponse(self, metric_name: str, value: Any, unit: str = '') -> str:
        """
        Format a single metric for display.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Optional unit string
            
        Returns:
            Formatted metric string
        """
        formatted_value = value
        
        # Format numbers with thousand separators
        if isinstance(value, (int, float)):
            if isinstance(value, float):
                formatted_value = f"{value:,.2f}"
            else:
                formatted_value = f"{value:,}"
        
        unit_str = f" {unit}" if unit else ""
        return f"**{metric_name}**: {formatted_value}{unit_str}"
    
    def generateSuggestions(
        self,
        query_type: str,
        system_ids: List[str]
    ) -> List[str]:
        """
        Generate follow-up question suggestions.
        
        Args:
            query_type: Type of query that was processed
            system_ids: Systems mentioned in the query
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        if query_type == "SYSTEM_HEALTH" and system_ids:
            system_id = system_ids[0]
            suggestions = [
                f"Show me violations for {system_id}",
                f"What's the trend for {system_id}?",
                f"Why is {system_id} having issues?"
            ]
        elif query_type == "SLA_VIOLATIONS":
            suggestions = [
                "What caused these violations?",
                "Show me the trend over time",
                "Compare with other systems"
            ]
        elif query_type == "FILE_TRENDS":
            suggestions = [
                "Are there any anomalies?",
                "What's the forecast for next week?",
                "Show me the SLA score"
            ]
        else:
            # Generic suggestions
            suggestions = [
                "Show me system health",
                "What violations occurred recently?",
                "Compare all systems"
            ]
        
        return suggestions[:3]  # Limit to 3 suggestions
