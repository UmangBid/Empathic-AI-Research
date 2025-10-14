"""
Admin Dashboard Streamlit App
Direct dashboard for viewing research data.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables (DATABASE_URL, etc.)
load_dotenv()
from src.database.db_manager import DatabaseManager
from src.ui.admin_dashboard import run_admin_dashboard

# Initialize database manager
db_manager = DatabaseManager("data/database/conversations.db")

# Run dashboard
if __name__ == "__main__":
    # Simple password gate to avoid exposing admin publicly
    admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password:
        import streamlit as st
        st.set_page_config(page_title="Admin Login", page_icon="🔒")
        st.title("🔒 Admin Dashboard Login")
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            if pwd == admin_password:
                run_admin_dashboard(db_manager)
            else:
                st.error("Invalid password")
    else:
        # If no password configured, run directly
        run_admin_dashboard(db_manager)