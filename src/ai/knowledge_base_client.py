"""Amazon Bedrock Knowledge Base client for retrieval."""

import boto3
from typing import List, Dict, Optional
from src.core.logging import get_logger
from src.ai.config import get_ai_config

logger = get_logger(__name__)


class KnowledgeBaseClient:
    """Client for Amazon Bedrock Knowledge Base retrieval."""
    
    def __init__(self, knowledge_base_id: Optional[str] = None, region: Optional[str] = None):
        """
        Initialize Knowledge Base client.
        
        Args:
            knowledge_base_id: Knowledge Base ID (from env if not provided)
            region: AWS region (from env if not provided)
        """
        config = get_ai_config()
        self.knowledge_base_id = knowledge_base_id or config.get('KNOWLEDGE_BASE_ID')
        self.region = region or config.get('KNOWLEDGE_BASE_REGION', 'us-east-1')
        
        if not self.knowledge_base_id:
            logger.warning("Knowledge Base ID not configured - retrieval will be disabled")
            self.client = None
            return
        
        try:
            self.client = boto3.client(
                'bedrock-agent-runtime',
                region_name=self.region
            )
            logger.info(f"Knowledge Base client initialized: {self.knowledge_base_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Knowledge Base client: {e}")
            self.client = None
    
    def retrieve(
        self,
        query: str,
        max_results: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Retrieve relevant documents from Knowledge Base.
        
        Args:
            query: User's query text
            max_results: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1)
        
        Returns:
            List of retrieved documents with content and metadata
        """
        if not self.client:
            logger.warning("Knowledge Base client not available - skipping retrieval")
            return []
        
        try:
            logger.info(f"Retrieving from KB: {query[:100]}...")
            
            response = self.client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results,
                        'overrideSearchType': 'HYBRID'  # Use both semantic and keyword search
                    }
                }
            )
            
            # Extract and filter results
            results = []
            for item in response.get('retrievalResults', []):
                score = item.get('score', 0)
                
                # Filter by similarity threshold
                if score >= similarity_threshold:
                    results.append({
                        'content': item.get('content', {}).get('text', ''),
                        'score': score,
                        'source': item.get('location', {}).get('s3Location', {}).get('uri', 'Unknown'),
                        'metadata': item.get('metadata', {})
                    })
            
            logger.info(f"Retrieved {len(results)} documents (threshold: {similarity_threshold})")
            return results
            
        except Exception as e:
            logger.error(f"Knowledge Base retrieval failed: {e}")
            return []
    
    def format_context(self, retrieved_docs: List[Dict]) -> str:
        """
        Format retrieved documents into context string for LLM.
        
        Args:
            retrieved_docs: List of retrieved documents
        
        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return ""
        
        context_parts = ["# Retrieved Knowledge Base Context\n"]
        
        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(f"\n## Document {i} (Relevance: {doc['score']:.2f})")
            context_parts.append(f"Source: {doc['source']}")
            context_parts.append(f"\n{doc['content']}\n")
            context_parts.append("-" * 80)
        
        return "\n".join(context_parts)
    
    def is_available(self) -> bool:
        """Check if Knowledge Base is available."""
        return self.client is not None


# Singleton instance
_kb_client = None


def get_kb_client() -> KnowledgeBaseClient:
    """Get or create Knowledge Base client singleton."""
    global _kb_client
    if _kb_client is None:
        _kb_client = KnowledgeBaseClient()
    return _kb_client
