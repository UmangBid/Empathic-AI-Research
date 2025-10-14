"""
Admin Dashboard
Researcher interface for monitoring conversations, exporting data, and viewing statistics.
"""

import streamlit as st
import pandas as pd
from typing import Dict
from datetime import datetime

from src.database.db_manager import DatabaseManager
from src.database.models import Message
from src.database.csv_exporter import CSVExporter


class AdminDashboard:
    """
    Researcher dashboard for monitoring and managing the research study.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize admin dashboard.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        self.csv_exporter = CSVExporter(db_manager)
    
    
    def display_dashboard(self):
        """Main dashboard display function."""
        st.set_page_config(
            page_title="Research Dashboard",
            page_icon="📊",
            layout="wide"
        )
        
        st.title("📊 Empathic AI Research Dashboard")
        st.markdown("---")
        
        # Sidebar navigation
        page = st.sidebar.selectbox(
            "Navigation",
            ["Overview", "Participants", "Data Export", "Crisis Flags", "Bot Comparison"]
        )
        
        # Display selected page
        if page == "Overview":
            self.display_overview()
        elif page == "Participants":
            self.display_participants()
        elif page == "Data Export":
            self.display_data_export()
        elif page == "Crisis Flags":
            self.display_crisis_flags()
        elif page == "Bot Comparison":
            self.display_bot_comparison()
    
    
    def display_overview(self):
        """Display overview statistics."""
        st.header("Study Overview")
        
        # Get statistics
        stats = self.db_manager.get_statistics()
        
        # Display key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Participants", stats['total_participants'])
        
        with col2:
            st.metric("Completed Conversations", stats['completed_conversations'])
        
        with col3:
            st.metric("Total Messages", stats['total_messages'])
        
        with col4:
            st.metric("Crisis Flags", stats['crisis_flags'])
        
        st.markdown("---")
        
        # Bot distribution
        st.subheader("Participant Distribution by Bot Type")
        
        dist_data = stats.get('bot_distribution', {})
        df_dist = pd.DataFrame({'Bot Type': list(dist_data.keys()), 'Count': list(dist_data.values())})
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.bar_chart(df_dist.set_index('Bot Type'))
        
        with col2:
            st.dataframe(df_dist, hide_index=True)
        
        # Completion rate
        if stats.get('total_participants', 0) > 0:
            completion_rate = (stats['completed_conversations'] / stats['total_participants']) * 100
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    
    def display_participants(self):
        """Display participant list and details."""
        st.header("Participant Management")
        
        # Get all participants
        participants = self.db_manager.get_all_participants()
        
        if not participants:
            st.info("No participants yet.")
            return
        
        # Create dataframe
        data = []
        for p in participants:
            duration = None
            if p.end_time and p.start_time:
                duration = (p.end_time - p.start_time).total_seconds() / 60
            
            data.append({
                'ID': p.id,
                'Prolific ID': getattr(p, 'prolific_id', None) or '',
                'Bot Type': p.bot_type,
                'Messages': p.total_messages,
                'Completed': '✓' if p.completed else '✗',
                'Crisis': '⚠' if p.crisis_flagged else '',
                'Duration (min)': f"{duration:.1f}" if duration else 'N/A',
                'Start Time': p.start_time.strftime("%Y-%m-%d %H:%M")
            })
        
        df = pd.DataFrame(data)
        
        # Display table
        st.dataframe(df, hide_index=True, use_container_width=True)
        
        # View individual conversation
        st.markdown("---")
        st.subheader("View Conversation")
        
        participant_ids = [p.id for p in participants]
        selected_id = st.selectbox("Select Participant", participant_ids)
        
        if st.button("Load Conversation"):
            self.display_conversation(selected_id)
    
    
    def display_conversation(self, participant_id: str):
        """
        Display full conversation for a participant.
        
        Args:
            participant_id: Participant's ID
        """
        messages = self.db_manager.get_conversation(participant_id)
        
        if not messages:
            st.warning("No messages found.")
            return
        
        st.markdown(f"**Conversation: {participant_id}**")
        
        for msg in messages:
            sender_label = "👤 User" if msg.sender == "user" else "🤖 Bot"
            timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S") if msg.timestamp else ""
            
            with st.expander(f"{sender_label} - Message {msg.message_num} ({timestamp})"):
                st.write(msg.content)
                if msg.contains_crisis_keyword:
                    st.error("⚠ Contains crisis keyword")
    
    
    def display_data_export(self):
        """Display data export options."""
        st.header("Data Export")
        
        st.markdown("""
        Export conversation data for analysis in Excel, SPSS, R, or other tools.
        All exports are saved to the `data/exports/` directory.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Individual Exports")
            
            if st.button("📄 Export All Conversations", use_container_width=True):
                with st.spinner("Exporting..."):
                    filepath = self.csv_exporter.export_all_conversations()
                    st.success(f"✓ Exported to: {filepath}")
            
            if st.button("👥 Export Participant Summary", use_container_width=True):
                with st.spinner("Exporting..."):
                    filepath = self.csv_exporter.export_participant_summary()
                    st.success(f"✓ Exported to: {filepath}")
            
            if st.button("⚠ Export Crisis Flags", use_container_width=True):
                with st.spinner("Exporting..."):
                    filepath = self.csv_exporter.export_crisis_flags()
                    st.success(f"✓ Exported to: {filepath}")
            
            if st.button("📊 Export Bot Comparison", use_container_width=True):
                with st.spinner("Exporting..."):
                    filepath = self.csv_exporter.export_bot_comparison()
                    st.success(f"✓ Exported to: {filepath}")
        
        with col2:
            st.subheader("Complete Export")
            
            if st.button("📦 Export All Data", type="primary", use_container_width=True):
                with st.spinner("Exporting all data..."):
                    exports = self.csv_exporter.export_all()
                    st.success("✓ All data exported successfully!")
                    
                    for export_type, filepath in exports.items():
                        st.write(f"- {export_type}: `{filepath}`")
    
    
    def display_crisis_flags(self):
        """Display crisis flag monitoring."""
        st.header("Crisis Flag Monitoring")
        
        # Get unreviewed flags
        unreviewed_flags = self.db_manager.get_unreviewed_crisis_flags()
        
        if not unreviewed_flags:
            st.success("No unreviewed crisis flags")
            return
        
        st.warning(f"⚠ {len(unreviewed_flags)} unreviewed crisis flags")
        
        # Display each flag
        for flag in unreviewed_flags:
            with st.expander(f"Participant {flag.participant_id} - {flag.keyword_detected}"):
                st.write(f"**Timestamp:** {flag.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**Keyword Detected:** {flag.keyword_detected}")
                
                # Get the message content
                session = self.db_manager.get_session()
                try:
                    message = session.query(Message).filter_by(id=flag.message_id).first()
                    if message:
                        st.write("**Message:**")
                        st.info(message.content)
                finally:
                    session.close()
                
                # Mark as reviewed
                if st.button("Mark as Reviewed", key=f"review_{flag.id}"):
                    try:
                        self.db_manager.mark_crisis_flag_reviewed(flag.id)
                        st.success("Marked as reviewed")
                    except Exception as e:
                        st.error(f"Failed to mark as reviewed: {e}")
    
    
    def display_bot_comparison(self):
        """Display bot type comparison statistics."""
        st.header("Bot Type Comparison")
        
        # Get statistics by bot type
        stats = self.db_manager.get_statistics()
        bot_dist = stats.get('bot_distribution', {})
        
        # Create comparison data
        comparison_data = []
        
        # Use dynamic bot types from DB; fallback to common list
        try:
            bot_types = self.db_manager.get_distinct_bot_types() or ['emotional', 'cognitive', 'motivational', 'neutral', 'control']
        except Exception:
            bot_types = ['emotional', 'cognitive', 'motivational', 'neutral', 'control']

        for bot_type in bot_types:
            # Get participants for this bot type
            session = self.db_manager.get_session()
            try:
                from src.database.models import Participant
                participants = session.query(Participant).filter_by(bot_type=bot_type).all()
                
                if participants:
                    total = len(participants)
                    completed = sum(1 for p in participants if p.completed)
                    total_msgs = sum(p.total_messages for p in participants)
                    avg_msgs = total_msgs / total if total > 0 else 0
                    crisis = sum(1 for p in participants if p.crisis_flagged)
                    completion_pct = (completed/total*100) if total > 0 else 0.0
                    
                    comparison_data.append({
                        'Bot Type': bot_type.capitalize(),
                        'Participants': total,
                        'Completed': completed,
                        'Completion %': f"{completion_pct:.1f}",
                        'Completion_Pct': round(completion_pct, 1),
                        'Avg Messages': f"{avg_msgs:.1f}",
                        'Crisis Flags': crisis
                    })
            finally:
                session.close()
        
        # Display as table
        if comparison_data:
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            # Visualizations
            st.subheader("Visual Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Completion Rates**")
                # Use numeric percentage for accurate charting
                completion_df = df[['Bot Type', 'Completion_Pct']].set_index('Bot Type')
                st.bar_chart(completion_df)
            
            with col2:
                st.write("**Crisis Flags**")
                crisis_df = df[['Bot Type', 'Crisis Flags']].set_index('Bot Type')
                st.bar_chart(crisis_df)
        else:
            st.info("No data available for comparison yet.")


def run_admin_dashboard(db_manager: DatabaseManager):
    """
    Run the admin dashboard application.
    
    Args:
        db_manager: DatabaseManager instance
    """
    dashboard = AdminDashboard(db_manager)
    dashboard.display_dashboard()