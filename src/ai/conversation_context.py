"""Conversation context manager for maintaining chat history."""

from collections import deque
from typing import Any, Dict, List

from src.core.logging import get_logger

logger = get_logger(__name__)


class ConversationContext:
    """Manages conversation context with automatic size limiting."""
    
    # Maximum number of messages to keep
    MAX_MESSAGES = 10
    
    def __init__(self, max_messages: int = MAX_MESSAGES):
        """
        Initialize conversation context.
        
        Args:
            max_messages: Maximum number of messages to store
        """
        self.max_messages = max_messages
        self._messages: deque = deque(maxlen=max_messages)
        logger.debug(f"Initialized conversation context with max_messages={max_messages}")
    
    def addMessage(self, message: Dict[str, Any]) -> None:
        """
        Add a message to the context.
        
        Automatically evicts oldest message if at capacity.
        
        Args:
            message: Message dictionary with 'role', 'content', etc.
        """
        # Validate message structure
        if not isinstance(message, dict):
            raise ValueError("Message must be a dictionary")
        
        if 'role' not in message or 'content' not in message:
            raise ValueError("Message must have 'role' and 'content' fields")
        
        # Add message (deque automatically handles size limit)
        self._messages.append(message)
        
        logger.debug(
            f"Added message to context",
            role=message.get('role'),
            context_size=len(self._messages)
        )
    
    def getMessages(self) -> List[Dict[str, Any]]:
        """
        Get all messages in the context.
        
        Returns:
            List of message dictionaries
        """
        return list(self._messages)
    
    def clear(self) -> None:
        """Clear all messages from the context."""
        self._messages.clear()
        logger.debug("Cleared conversation context")
    
    def size(self) -> int:
        """
        Get the current number of messages.
        
        Returns:
            Number of messages in context
        """
        return len(self._messages)
    
    def isEmpty(self) -> bool:
        """
        Check if context is empty.
        
        Returns:
            True if no messages, False otherwise
        """
        return len(self._messages) == 0
    
    def getLastMessage(self) -> Dict[str, Any]:
        """
        Get the most recent message.
        
        Returns:
            Last message dictionary or None if empty
        """
        if self.isEmpty():
            return None
        return self._messages[-1]
    
    def getLastUserMessage(self) -> Dict[str, Any]:
        """
        Get the most recent user message.
        
        Returns:
            Last user message or None if not found
        """
        for message in reversed(self._messages):
            if message.get('role') == 'user':
                return message
        return None
    
    def toDict(self) -> Dict[str, Any]:
        """
        Serialize context to dictionary.
        
        Returns:
            Dictionary representation of context
        """
        return {
            'messages': list(self._messages),
            'max_messages': self.max_messages,
            'size': len(self._messages)
        }
    
    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """
        Create context from dictionary.
        
        Args:
            data: Dictionary with 'messages' and optional 'max_messages'
            
        Returns:
            ConversationContext instance
        """
        max_messages = data.get('max_messages', cls.MAX_MESSAGES)
        context = cls(max_messages=max_messages)
        
        for message in data.get('messages', []):
            context.addMessage(message)
        
        return context
    
    def getRecentMessages(self, count: int) -> List[Dict[str, Any]]:
        """
        Get the N most recent messages.
        
        Args:
            count: Number of recent messages to retrieve
            
        Returns:
            List of recent messages
        """
        if count <= 0:
            return []
        
        if count >= len(self._messages):
            return list(self._messages)
        
        return list(self._messages)[-count:]
    
    def __len__(self) -> int:
        """Return the number of messages in context."""
        return len(self._messages)
    
    def __repr__(self) -> str:
        """String representation of context."""
        return f"<ConversationContext(messages={len(self._messages)}, max={self.max_messages})>"
