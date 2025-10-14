"""
Diagnostic Script - Check for Duplicate Participant Bug
Shows each participant and their message count to identify the issue.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.database.db_manager import DatabaseManager
from src.database.models import Participant, Message

def diagnose():
    db_manager = DatabaseManager("data/database/conversations.db")
    session = db_manager.get_session()
    
    try:
        # Get all participants
        participants = session.query(Participant).order_by(Participant.start_time.desc()).all()
        
        print("\n" + "="*80)
        print("PARTICIPANT DIAGNOSIS")
        print("="*80)
        print(f"\nTotal Participants: {len(participants)}")
        print("\nRecent Participants (last 10):")
        print("-"*80)
        
        for i, p in enumerate(participants[:10], 1):
            # Count messages for this participant
            msg_count = session.query(Message).filter_by(participant_id=p.id).count()
            
            print(f"\n{i}. Participant ID: {p.id}")
            print(f"   Prolific ID: {p.prolific_id or 'N/A'}")
            print(f"   Bot Type: {p.bot_type}")
            print(f"   Messages: {msg_count}")
            print(f"   Started: {p.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Completed: {'✓' if p.completed else '✗'}")
            
            # Get first few messages to show pattern
            messages = session.query(Message).filter_by(participant_id=p.id).order_by(Message.message_num).limit(3).all()
            if messages:
                print(f"   First messages:")
                for msg in messages:
                    sender_icon = "👤" if msg.sender == "user" else "🤖"
                    content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                    print(f"      {sender_icon} #{msg.message_num} {msg.sender}: {content_preview}")
        
        # Check for the bug pattern
        print("\n" + "="*80)
        print("BUG DETECTION")
        print("="*80)
        
        # Count participants with only 1-2 messages (sign of the bug)
        single_msg_participants = [p for p in participants if session.query(Message).filter_by(participant_id=p.id).count() <= 2]
        
        if len(single_msg_participants) > 5:
            print(f"\n⚠️  WARNING: Found {len(single_msg_participants)} participants with ≤2 messages")
            print("   This suggests the 'duplicate participant per message' bug is active!")
        else:
            print(f"\n✅ Looks OK: Only {len(single_msg_participants)} participants with ≤2 messages")
            print("   (Some early dropouts are normal)")
        
        # Check for same Prolific ID appearing multiple times
        prolific_ids = [p.prolific_id for p in participants if p.prolific_id]
        if len(prolific_ids) != len(set(prolific_ids)):
            from collections import Counter
            duplicates = {pid: count for pid, count in Counter(prolific_ids).items() if count > 1}
            print(f"\n⚠️  WARNING: Found duplicate Prolific IDs:")
            for pid, count in duplicates.items():
                print(f"   - {pid}: {count} participants")
                print("   This indicates the bug created multiple participant entries!")
        else:
            print("\n✅ No duplicate Prolific IDs found")
        
        print("\n" + "="*80)
        
    finally:
        session.close()

if __name__ == "__main__":
    diagnose()
