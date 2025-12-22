from __future__ import annotations

import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from api.schemas import ChatTurn


class ConversationManager:
    """
    Manages conversation history by conversation_id.
    Stores conversations in memory with automatic cleanup of old conversations.
    """
    
    def __init__(self, max_age_hours: int = 24):
        """
        Initialize the conversation manager.
        
        Args:
            max_age_hours: Maximum age in hours before a conversation is considered stale (default: 24)
        """
        self.conversations: Dict[str, List[ChatTurn]] = {}
        self.conversation_metadata: Dict[str, dict] = {}  # Store user_id, created_at, last_accessed
        self.max_age_hours = max_age_hours
        self.lock = threading.Lock()
    
    def get_history(self, conversation_id: str) -> List[ChatTurn]:
        """
        Get conversation history for a given conversation_id.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            List of ChatTurn objects representing the conversation history
        """
        with self.lock:
            # Clean up stale conversations
            self._cleanup_stale()
            
            return self.conversations.get(conversation_id, [])
    
    def add_turn(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Add a turn to the conversation history.
        
        Args:
            conversation_id: Unique identifier for the conversation
            user_message: The user's message
            assistant_message: The assistant's response
            user_id: Optional user identifier
        """
        with self.lock:
            # Clean up stale conversations
            self._cleanup_stale()
            
            # Initialize conversation if it doesn't exist
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
                self.conversation_metadata[conversation_id] = {
                    "user_id": user_id,
                    "created_at": datetime.now(),
                    "last_accessed": datetime.now(),
                }
            
            # Add the new turn
            turn = ChatTurn(user=user_message, assistant=assistant_message)
            self.conversations[conversation_id].append(turn)
            
            # Update metadata
            self.conversation_metadata[conversation_id]["last_accessed"] = datetime.now()
            if user_id:
                self.conversation_metadata[conversation_id]["user_id"] = user_id
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear a specific conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            True if conversation was found and cleared, False otherwise
        """
        with self.lock:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
                del self.conversation_metadata[conversation_id]
                return True
            return False
    
    def get_conversation_count(self) -> int:
        """Get the total number of active conversations."""
        with self.lock:
            self._cleanup_stale()
            return len(self.conversations)
    
    def _cleanup_stale(self) -> None:
        """Remove conversations that haven't been accessed recently."""
        now = datetime.now()
        stale_ids = [
            conv_id
            for conv_id, metadata in self.conversation_metadata.items()
            if (now - metadata["last_accessed"]).total_seconds() > (self.max_age_hours * 3600)
        ]
        
        for conv_id in stale_ids:
            del self.conversations[conv_id]
            del self.conversation_metadata[conv_id]


# Global conversation manager instance
conversation_manager = ConversationManager()

