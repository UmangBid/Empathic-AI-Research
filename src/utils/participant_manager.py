"""
Participant Manager
Handles participant ID generation and session management.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict
from src.database.db_manager import DatabaseManager


class ParticipantManager:
    """
    Manages participant identification and session tracking.
    Generates unique IDs and tracks active sessions.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize participant manager.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        self.active_sessions = {}  # In-memory storage of active sessions
    
    
    def generate_participant_id(self, prefix: str = "P") -> str:
        """
        Generate unique participant ID.
        Format: P001, P002, P003, etc.
        
        Args:
            prefix: Letter prefix for ID (default "P" for Participant)
            
        Returns:
            Unique participant ID string
        """
        # Get total number of participants to determine next ID number
        stats = self.db_manager.get_statistics()
        next_number = stats['total_participants'] + 1
        
        # Format with leading zeros (e.g., P001, P002)
        participant_id = f"{prefix}{next_number:03d}"
        
        return participant_id
    
    
    def generate_session_id(self) -> str:
        """
        Generate unique session ID using UUID.
        Used for tracking individual browser sessions.
        
        Returns:
            Unique session ID string
        """
        return str(uuid.uuid4())
    
    
    def create_session(self, bot_type: str) -> Dict:
        """
        Create new participant session.
        Generates IDs and initializes session data.
        
        Args:
            bot_type: Which bot type assigned to this participant
            
        Returns:
            Dictionary with session information
        """
        # Generate IDs
        participant_id = self.generate_participant_id()
        session_id = self.generate_session_id()
        
        # Create participant in database
        participant = self.db_manager.create_participant(participant_id, bot_type)
        
        # Create session data
        session_data = {
            'session_id': session_id,
            'participant_id': participant_id,
            'bot_type': bot_type,
            'created_at': datetime.utcnow(),
            'message_count': 0,
            'conversation_complete': False
        }
        
        # Store in active sessions (in-memory)
        self.active_sessions[session_id] = session_data
        
        print(f"✓ Created session for participant {participant_id} with {bot_type} bot")
        
        return session_data
    
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve session data by session ID.
        
        Args:
            session_id: The session's unique ID
            
        Returns:
            Session data dictionary or None if not found
        """
        return self.active_sessions.get(session_id)
    
    
    def update_session_message_count(self, session_id: str):
        """
        Increment message count for a session.
        
        Args:
            session_id: The session's unique ID
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['message_count'] += 1
    
    
    def mark_session_complete(self, session_id: str):
        """
        Mark session as completed (reached 20 messages or ended).
        
        Args:
            session_id: The session's unique ID
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session['conversation_complete'] = True
            
            # Update database
            participant_id = session['participant_id']
            self.db_manager.update_participant_completion(participant_id, completed=True)
            
            print(f"✓ Session {session_id} marked complete")
    
    
    def end_session(self, session_id: str):
        """
        End and cleanup a session.
        Removes from active sessions memory.
        
        Args:
            session_id: The session's unique ID
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            participant_id = session['participant_id']
            
            # Ensure database is updated
            self.db_manager.update_participant_completion(
                participant_id, 
                completed=session['conversation_complete']
            )
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            print(f"✓ Ended session {session_id}")
    
    
    def get_active_session_count(self) -> int:
        """
        Get count of currently active sessions.
        
        Returns:
            Number of active sessions
        """
        return len(self.active_sessions)
    
    
    def cleanup_stale_sessions(self, timeout_hours: int = 2):
        """
        Remove sessions that have been inactive for too long.
        
        Args:
            timeout_hours: Hours of inactivity before session is considered stale
        """
        current_time = datetime.utcnow()
        stale_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            created_at = session_data['created_at']
            hours_elapsed = (current_time - created_at).total_seconds() / 3600
            
            if hours_elapsed > timeout_hours:
                stale_sessions.append(session_id)
        
        # Remove stale sessions
        for session_id in stale_sessions:
            self.end_session(session_id)
            print(f"⚠ Removed stale session: {session_id}")
        
        if stale_sessions:
            print(f"✓ Cleaned up {len(stale_sessions)} stale sessions")
    
    
    def get_participant_info(self, participant_id: str) -> Optional[Dict]:
        """
        Get comprehensive information about a participant.
        
        Args:
            participant_id: The participant's ID
            
        Returns:
            Dictionary with participant information
        """
        # Get from database
        participant = self.db_manager.get_participant(participant_id)
        
        if not participant:
            return None
        
        # Get conversation messages
        messages = self.db_manager.get_conversation(participant_id)
        
        # Compile information
        info = {
            'participant_id': participant.id,
            'bot_type': participant.bot_type,
            'start_time': participant.start_time,
            'end_time': participant.end_time,
            'total_messages': participant.total_messages,
            'completed': participant.completed,
            'crisis_flagged': participant.crisis_flagged,
            'message_count': len(messages)
        }
        
        return info