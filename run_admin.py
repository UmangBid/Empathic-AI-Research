"""
Admin Dashboard Launcher
Starts the researcher dashboard for monitoring and data export.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()
from src.database.db_manager import DatabaseManager


def create_admin_script():
    """
    Create temporary admin script for Streamlit to run.
    """
    admin_script = """import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager
from src.ui.admin_dashboard import run_admin_dashboard

# Initialize database manager
db_manager = DatabaseManager("data/database/conversations.db")

# Run dashboard
run_admin_dashboard(db_manager)
"""
    
    # Write to temp file
    temp_file = project_root / 'temp_admin.py'
    with open(temp_file, 'w') as f:
        f.write(admin_script)
    
    return temp_file


def main():
    """Main launcher function."""
    print("=" * 60)
    print("EMPATHIC AI RESEARCH - ADMIN DASHBOARD")
    print("=" * 60)
    print()
    
    # Check if database exists
    db_path = project_root / 'data' / 'database' / 'conversations.db'
    if not db_path.exists():
        print("⚠️  No database found. Run the main app first to create data.")
        print()
        return
    
    print("✓ Database found")
    print("✓ Starting admin dashboard...")
    print()
    print("The dashboard will open in your default web browser.")
    print("Press Ctrl+C to stop the dashboard.")
    print()
    print("=" * 60)
    print()
    
    # Create temp admin script
    temp_script = create_admin_script()
    
    try:
        # Run Streamlit with admin script (quote path to handle spaces)
        # Use the current Python interpreter to ensure correct environment
        os.system(f'"{sys.executable}" -m streamlit run "{temp_script}" --server.port 8502')
    finally:
        # Clean up temp file
        if temp_script.exists():
            temp_script.unlink()


if __name__ == "__main__":
    main()