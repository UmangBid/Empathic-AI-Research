"""
Conversation Handler
Manages conversation flow, message limits, and conversation state.
"""

from typing import Dict, Optional, List
from datetime import datetime


class ConversationHandler:
    """
    Handles conversation flow and enforces message limits.
    Tracks conversation state and determines when conversations should end.
    """
    
    def __init__(self, max_messages: int = 20):
        """
        Initialize conversation handler.
        
        Args:
            max_messages: Maximum number of messages allowed per conversation
        """
        self.max_messages = max_messages
        self.conversations = {}  # session_id -> conversation state
        
        print(f"✓ Conversation handler initialized (max {max_messages} messages)")
    
    
    def start_conversation(self, session_id: str, participant_id: str, 
                          bot_type: str) -> Dict:
        """
        Initialize a new conversation.
        
        Args:
            session_id: Unique session identifier
            participant_id: Participant ID (e.g., P001)
            bot_type: Type of bot assigned
            
        Returns:
            Conversation state dictionary
        """
        conversation_state = {
            'session_id': session_id,
            'participant_id': participant_id,
            'bot_type': bot_type,
            'current_message_num': 0,
            'max_messages': self.max_messages,
            'started_at': datetime.utcnow(),
            'is_active': True,
            'is_complete': False,
            'messages': []
        }
        
        self.conversations[session_id] = conversation_state
        
        print(f"✓ Started conversation for session {session_id}")
        return conversation_state
    
    
    def add_message(self, session_id: str, sender: str, content: str) -> Dict:
        """
        Add a message to the conversation.
        
        Args:
            session_id: Session identifier
            sender: "user" or "bot"
            content: Message text
            
        Returns:
            Updated conversation state
        """
        if session_id not in self.conversations:
            raise ValueError(f"Conversation not found for session: {session_id}")
        
        conversation = self.conversations[session_id]
        
        # Create message entry
        message = {
            'sender': sender,
            'content': content,
            'timestamp': datetime.utcnow()
        }
        
        # Add to conversation
        conversation['messages'].append(message)
        
        # Increment message counter (count user messages only, not bot)
        if sender == "user":
            conversation['current_message_num'] += 1
        
        # Check if conversation should end
        if conversation['current_message_num'] >= self.max_messages:
            conversation['is_active'] = False
            conversation['is_complete'] = True
        
        return conversation
    
    
    def get_conversation_state(self, session_id: str) -> Optional[Dict]:
        """
        Get current state of a conversation.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation state dictionary or None if not found
        """
        return self.conversations.get(session_id)
    
    
    def is_conversation_active(self, session_id: str) -> bool:
        """
        Check if conversation is still active (not at message limit).
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if conversation can continue, False if at limit
        """
        conversation = self.conversations.get(session_id)
        if not conversation:
            return False
        
        return conversation['is_active']
    
    
    def get_remaining_messages(self, session_id: str) -> int:
        """
        Get number of messages remaining in conversation.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Number of user messages remaining
        """
        conversation = self.conversations.get(session_id)
        if not conversation:
            return 0
        
        current = conversation['current_message_num']
        max_msgs = conversation['max_messages']
        remaining = max_msgs - current
        
        return max(0, remaining)
    
    
    def get_progress_text(self, session_id: str) -> str:
        """
        Get progress text for display (e.g., "Message 5 of 20").
        
        Args:
            session_id: Session identifier
            
        Returns:
            Progress text string
        """
        conversation = self.conversations.get(session_id)
        if not conversation:
            return "Message 0 of 20"
        
        current = conversation['current_message_num']
        max_msgs = conversation['max_messages']
        
        return f"Message {current} of {max_msgs}"
    
    
    def should_end_conversation(self, session_id: str) -> bool:
        """
        Determine if conversation should end.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if conversation should end
        """
        conversation = self.conversations.get(session_id)
        if not conversation:
            return True
        
        # End if reached message limit
        if conversation['current_message_num'] >= conversation['max_messages']:
            return True
        
        # End if explicitly marked as inactive
        if not conversation['is_active']:
            return True
        
        return False
    
    
    def end_conversation(self, session_id: str, reason: str = "completed"):
        """
        Mark conversation as ended.
        
        Args:
            session_id: Session identifier
            reason: Reason for ending ("completed", "user_left", "error")
        """
        if session_id in self.conversations:
            conversation = self.conversations[session_id]
            conversation['is_active'] = False
            conversation['ended_at'] = datetime.utcnow()
            conversation['end_reason'] = reason
            
            # Mark as complete only if reached message limit
            if conversation['current_message_num'] >= conversation['max_messages']:
                conversation['is_complete'] = True
            
            print(f"✓ Conversation ended: {session_id} (reason: {reason})")
    
    
    def get_conversation_messages(self, session_id: str) -> List[Dict]:
        """
        Get all messages from a conversation.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of message dictionaries
        """
        conversation = self.conversations.get(session_id)
        if not conversation:
            return []
        
        return conversation['messages']
    
    
    def get_conversation_duration(self, session_id: str) -> Optional[float]:
        """
        Get conversation duration in minutes.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Duration in minutes or None if conversation not ended
        """
        conversation = self.conversations.get(session_id)
        if not conversation:
            return None
        
        started_at = conversation.get('started_at')
        ended_at = conversation.get('ended_at')
        
        if started_at and ended_at:
            duration = (ended_at - started_at).total_seconds() / 60
            return round(duration, 2)
        
        return None
    
    
    def cleanup_conversation(self, session_id: str):
        """
        Remove conversation from memory after it's saved to database.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
            print(f"✓ Cleaned up conversation: {session_id}")
    
    
    def get_active_conversations_count(self) -> int:
        """
        Get count of currently active conversations.
        
        Returns:
            Number of active conversations
        """
        active_count = sum(1 for conv in self.conversations.values() if conv['is_active'])
        return active_count
    
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about all conversations.
        
        Returns:
            Dictionary with conversation statistics
        """
        total = len(self.conversations)
        active = sum(1 for conv in self.conversations.values() if conv['is_active'])
        complete = sum(1 for conv in self.conversations.values() if conv['is_complete'])
        
        return {
            'total_conversations': total,
            'active_conversations': active,
            'completed_conversations': complete,
            'incomplete_conversations': total - complete
        }