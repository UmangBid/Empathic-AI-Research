"""
Main Application
Participant-facing Streamlit application for empathic AI chatbot research.
"""
import sys
import streamlit as st
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Configure page FIRST before any other Streamlit commands
st.set_page_config(
    page_title="Mental Health Support Chat",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Load environment variables from .env file
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager
from src.chatbot.bot_manager import BotManager
from src.chatbot.conversation_handler import ConversationHandler
from src.ui.chat_interface import ChatInterface


def load_config(config_path: str = "config/app_config.yaml") -> dict:
    """
    Load application configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        st.stop()


def initialize_app():
    """Initialize application components."""
    # Load configuration
    config = load_config()
    
    # Initialize database manager
    db_path = config['database']['path']
    db_manager = DatabaseManager(db_path)
    
    # Initialize bot manager
    bot_manager = BotManager(db_manager, config)
    
    # Initialize conversation handler
    max_messages = config['conversation']['max_messages']
    conversation_handler = ConversationHandler(max_messages)
    
    # Initialize chat interface
    chat_interface = ChatInterface(config)
    
    return config, db_manager, bot_manager, conversation_handler, chat_interface


def main():
    """Main application function."""
    
    # Initialize components
    config, db_manager, bot_manager, conversation_handler, chat_interface = initialize_app()
    
    # Apply custom styling
    chat_interface.apply_custom_css()
    
    # Initialize session state
    chat_interface.initialize_session_state()
    
    # STAGE 1: WELCOME PAGE
    if st.session_state.show_welcome:
        # Display welcome and consent
        if chat_interface.display_welcome_page():
            # User agreed to participate
            # Create new session
            session_data = bot_manager.create_new_session()
            
            # Store in session state
            st.session_state.session_id = session_data['session_id']
            st.session_state.participant_id = session_data['participant_id']
            st.session_state.bot_type = session_data['bot_type']
            st.session_state.show_welcome = False
            st.session_state.conversation_active = True
            # Reset conversation UI state
            st.session_state.messages = []
            st.session_state.current_message_num = 0
            
            # Create participant in database (include Prolific ID if provided)
            db_manager.create_participant(
                st.session_state.participant_id,
                st.session_state.bot_type,
                prolific_id=st.session_state.get('prolific_id')
            )
            
            st.rerun()
        
        return  # Stay on welcome page until consent given
    
    # STAGE 2: CONVERSATION COMPLETE
    if st.session_state.conversation_complete:
        chat_interface.display_completion_page(st.session_state.participant_id)
        return
    
    # STAGE 3: ACTIVE CONVERSATION
    if st.session_state.conversation_active:
        
        # Display title
        st.title("Mental Health Support Chat")
        # Watermark and sticky research disclaimer (configurable)
        ui_cfg = config.get('ui') if isinstance(config.get('ui'), dict) else {}
        wm_text = ui_cfg.get('chat_watermark') if isinstance(ui_cfg, dict) else None
        chat_interface.render_watermark(wm_text)
        disclaimer = ui_cfg.get('chat_disclaimer') if isinstance(ui_cfg, dict) else None
        chat_interface.render_disclaimer(disclaimer)
        
        # Display crisis resources in sidebar
        with st.sidebar:
            st.header("Crisis Resources")
            st.markdown("""
            **If you're in crisis:**
            - 📞 Call or text **988**  
              (Suicide & Crisis Lifeline)
            - 💬 Text **HOME** to **741741**  
              (Crisis Text Line)
            - 🚨 Call **911** for emergencies
            """)
            
            st.markdown("---")
            st.caption(f"Participant ID: {st.session_state.participant_id}")
            st.caption("Your responses are anonymous")
        
        # Get conversation state (may be None due to in-memory storage, but that's OK)
        # We rely on session_state which persists across reruns
        
        # Get current message count from SESSION STATE (persists across reruns)
        current = st.session_state.current_message_num
        max_messages = config['conversation']['max_messages']
        
        # Display message counter (shows current progress)
        chat_interface.display_message_counter(current, max_messages)
        
        # Display chat history
        chat_interface.display_chat_history(st.session_state.messages)

        # Ensure BotManager has the session (Streamlit reruns recreate BotManager)
        try:
            sess_id = st.session_state.session_id
            if sess_id and sess_id not in getattr(bot_manager, 'sessions', {}):
                # Rehydrate bot session from session_state
                hist = [
                    {"role": m.get("role"), "content": m.get("content")}
                    for m in st.session_state.messages[-20:]
                    if isinstance(m, dict) and m.get("role") in ("user", "assistant")
                ]
                bot_manager.sessions[sess_id] = {
                    "participant_id": st.session_state.participant_id,
                    "bot_type": st.session_state.bot_type,
                    "history": hist,
                }
        except Exception:
            # Non-fatal; bot_manager will raise a clear error on send if needed
            pass
        
        # Check if conversation should end BEFORE taking input
        if st.session_state.current_message_num >= max_messages:
            # Mark as complete
            st.session_state.conversation_active = False
            st.session_state.conversation_complete = True
            
            # Mark participant as completed in database
            db_manager.mark_participant_completed(st.session_state.participant_id)
            
            # End bot manager session
            bot_manager.end_session(st.session_state.session_id, completed=True)
            
            st.rerun()
        
        # Get user input (disable if at limit)
        should_disable = st.session_state.current_message_num >= max_messages
        user_input = chat_interface.get_user_input(disabled=should_disable)
        
        if user_input:
            # Increment message counter IN SESSION STATE
            st.session_state.current_message_num += 1
            
            # Add user message to display
            st.session_state.messages.append({
                'role': 'user',
                'content': user_input
            })
            
            # Use session state message number for database
            message_num = st.session_state.current_message_num
            
            # Save user message to database
            db_manager.save_message(
                st.session_state.participant_id,
                message_num,
                'user',
                user_input
            )
            
            # Get bot response
            try:
                response_data = bot_manager.get_bot_response(
                    session_id=st.session_state.session_id,
                    user_message=user_input,
                    message_num=message_num
                )
                
                bot_response = response_data['bot_response']
                
                # Add bot message to display
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': bot_response
                })
                
                # Save bot message to database
                saved_msg = db_manager.save_message(
                    st.session_state.participant_id,
                    message_num,
                    'bot',
                    bot_response,
                    contains_crisis_keyword=response_data['crisis_detected']
                )
                
                # Show crisis warning if detected
                if response_data['crisis_detected']:
                    # Create a crisis flag record for admin review
                    try:
                        keyword = response_data.get('detected_keyword') or 'crisis'
                        msg_id = getattr(saved_msg, 'id', None)
                        if msg_id:
                            db_manager.create_crisis_flag(
                                participant_id=st.session_state.participant_id,
                                message_id=msg_id,
                                keyword_detected=str(keyword)
                            )
                    except Exception:
                        # Non-fatal; still show warning
                        pass
                    st.warning("⚠ Crisis resources have been provided in the response above.")
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.error("Please try sending your message again.")
            
            # Rerun to update display and counter after message processing
            st.rerun()


if __name__ == "__main__":
    # Set page config
    st.set_page_config(
        page_title="Mental Health Support Study",
        page_icon="💬",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    # Run main application
    try:
        main()
    except Exception as e:
        st.error("An unexpected error occurred. Please refresh the page.")
        st.exception(e)