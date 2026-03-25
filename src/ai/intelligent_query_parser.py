"""Intelligent query parser using Bedrock for natural language understanding."""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from src.ai.cohere_client import CohereClient, CohereError as BedrockError
from src.core.logging import get_logger

logger = get_logger(__name__)


class IntelligentQueryParser:
    """Uses Bedrock to intelligently parse user queries."""
    
    def __init__(self, available_systems: List[str], bedrock_client: Optional[CohereClient] = None):
        """
        Initialize the intelligent query parser.
        
        Args:
            available_systems: List of available system IDs
            bedrock_client: Optional CohereClient instance
        """
        self.available_systems = available_systems
        self.bedrock_client = bedrock_client or CohereClient()
    
    def parseQuery(self, query: str, context: Optional[List[Dict]] = None) -> Dict:
        """
        Parse a natural language query using Bedrock.
        
        Args:
            query: User's natural language query
            context: Previous conversation messages
            
        Returns:
            Dictionary with parsed intent, systems, date_range, and response_type
        """
        try:
            prompt = self._buildParsingPrompt(query, context)
            
            # Invoke Bedrock with lower temperature for more consistent parsing
            response_text = self.bedrock_client.invoke_model(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse the JSON response
            parsed = self._extractParsedIntent(response_text)
            
            logger.info(
                "Parsed query with Bedrock",
                query=query,
                intent=parsed.get('intent'),
                systems=parsed.get('systems'),
                is_greeting=parsed.get('is_greeting', False)
            )
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing query with Bedrock: {e}")
            # Fallback to simple parsing
            return self._fallbackParse(query)
    
    def _buildParsingPrompt(self, query: str, context: Optional[List[Dict]] = None) -> str:
        """Build prompt for query parsing."""
        
        systems_list = ", ".join(self.available_systems)
        
        prompt = f"""You are a query parser for a file monitoring system. Parse the user's query and return a JSON response.

Available Systems: {systems_list}

Query Types:
- GREETING: User is greeting or saying hello/hi/hey
- OUT_OF_SCOPE: General knowledge questions (time, weather, calculations, etc.) — NOT file monitoring related
- SYSTEM_HEALTH: Asking about system status, health, or how a system is doing
- SLA_VIOLATIONS: Asking about violations, breaches, or missed SLAs
- FILE_TRENDS: Asking about trends, patterns, or historical data
- SYSTEM_COMPARISON: Comparing multiple systems
- ROOT_CAUSE: Asking why something happened or root cause analysis
- GENERAL_INFO: General questions about the dashboard or systems

Date References:
- "today", "yesterday", "last week", "last 7 days", "last 30 days", "last month"

"""
        
        if context:
            recent = context[-2:]
            prompt += "\nRecent Conversation:\n"
            for msg in recent:
                prompt += f"{msg.get('role')}: {msg.get('content')}\n"
        
        prompt += f"""
User Query: "{query}"

Return ONLY a JSON object with this exact structure:
{{
  "is_greeting": true/false,
  "is_out_of_scope": true/false,
  "intent": "GREETING|OUT_OF_SCOPE|SYSTEM_HEALTH|SLA_VIOLATIONS|FILE_TRENDS|SYSTEM_COMPARISON|ROOT_CAUSE|GENERAL_INFO",
  "systems": ["SYSTEM_ID1", "SYSTEM_ID2"],
  "date_reference": "today|yesterday|last week|last 7 days|last 30 days|last month|null",
  "confidence": 0.0-1.0,
  "greeting_response": "friendly greeting if is_greeting is true, otherwise null",
  "out_of_scope_response": null
}}

Rules:
1. Extract ALL system IDs mentioned (match case-insensitively — "prod_hr", "PROD_HR", "prod hr" all refer to the same system; always return the system ID in UPPERCASE exactly as it appears in the Available Systems list)
2. If user says hi/hello/hey, set is_greeting=true and provide a friendly greeting_response
3. If question is about time, weather, general knowledge, or anything NOT related to file monitoring, set is_out_of_scope=true (the system will still answer it using AI)
4. "how is X" or "status of X" = SYSTEM_HEALTH
5. If no systems mentioned but asking about "all systems" or "everything", include all available systems
6. Be intelligent about system name variations (backup = PROD_BACKUP, sales = PROD_SALES, hr = PROD_HR, etc.)
7. Return ONLY valid JSON, no extra text

JSON Response:"""
        
        return prompt
    
    def _extractParsedIntent(self, response_text: str) -> Dict:
        """Extract and validate parsed intent from Bedrock response."""
        try:
            # Find JSON in response
            response_text = response_text.strip()
            
            # Try to find JSON object
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx+1]
                parsed = json.loads(json_str)
                
                # Validate and normalize
                return self._validateParsedIntent(parsed)
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            logger.warning(f"Failed to parse Bedrock response as JSON: {e}")
            return self._fallbackParse(response_text)
    
    def _validateParsedIntent(self, parsed: Dict) -> Dict:
        """Validate and normalize parsed intent."""
        
        # Ensure required fields
        result = {
            'is_greeting': parsed.get('is_greeting', False),
            'is_out_of_scope': parsed.get('is_out_of_scope', False),
            'intent': parsed.get('intent', 'GENERAL_INFO'),
            'systems': parsed.get('systems', []),
            'date_reference': parsed.get('date_reference'),
            'confidence': parsed.get('confidence', 0.8),
            'greeting_response': parsed.get('greeting_response'),
            'out_of_scope_response': parsed.get('out_of_scope_response')
        }
        
        # Validate systems exist — case-insensitive match, always return canonical uppercase ID
        available_upper = {s.upper(): s for s in self.available_systems}
        valid_systems = []
        for sys in result['systems']:
            canonical = available_upper.get(sys.upper())
            if canonical and canonical not in valid_systems:
                valid_systems.append(canonical)
        result['systems'] = valid_systems
        
        # Convert date reference to date range
        result['date_range'] = self._parseDateReference(result['date_reference'])
        
        return result
    
    def _parseDateReference(self, date_ref: Optional[str]) -> Optional[Tuple[datetime, datetime]]:
        """Convert date reference string to date range tuple."""
        if not date_ref or date_ref == 'null':
            return None
        
        now = datetime.now()
        
        date_map = {
            'today': (now.replace(hour=0, minute=0, second=0, microsecond=0), now),
            'yesterday': (
                (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                (now - timedelta(days=1)).replace(hour=23, minute=59, second=59)
            ),
            'last week': (now - timedelta(days=7), now),
            'last 7 days': (now - timedelta(days=7), now),
            'last 30 days': (now - timedelta(days=30), now),
            'last month': (now - timedelta(days=30), now)
        }
        
        return date_map.get(date_ref.lower())
    
    def _fallbackParse(self, query: str) -> Dict:
        """Simple fallback parsing when Bedrock fails."""
        query_lower = query.lower().strip()
        
        # Check for greetings
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
        is_greeting = any(query_lower.startswith(g) for g in greetings)
        
        # Simple system extraction — case-insensitive
        systems = []
        query_lower_clean = query_lower.replace('_', ' ')
        for sys_id in self.available_systems:
            sys_lower = sys_id.lower()
            sys_spaced = sys_lower.replace('_', ' ')
            if sys_lower in query_lower or sys_spaced in query_lower_clean:
                systems.append(sys_id)
        
        # Simple intent detection
        intent = 'GENERAL_INFO'
        if is_greeting:
            intent = 'GREETING'
        elif 'how' in query_lower or 'status' in query_lower or 'health' in query_lower:
            intent = 'SYSTEM_HEALTH'
        elif 'violation' in query_lower or 'breach' in query_lower:
            intent = 'SLA_VIOLATIONS'
        elif 'compare' in query_lower:
            intent = 'SYSTEM_COMPARISON'
        
        return {
            'is_greeting': is_greeting,
            'is_out_of_scope': False,
            'intent': intent,
            'systems': systems,
            'date_reference': None,
            'date_range': None,
            'confidence': 0.5,
            'greeting_response': "Hello! How can I help you with the file monitoring dashboard?" if is_greeting else None,
            'out_of_scope_response': None
        }
