#!/usr/bin/env python3
"""
Launch script for DCF Web Interface
Simple script to launch the Streamlit web interface.
"""

import subprocess
import sys
import os

def main():
    """Launch the DCF web interface."""
    print("🚀 Launching DCF Web Interface...")
    print("=" * 50)
    
    # Check if streamlit is installed
    try:
        import streamlit
        print(" Streamlit is installed")
    except ImportError:
        print(" Streamlit not found. Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_web.txt"])
        print(" Dependencies installed")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    web_interface_path = os.path.join(script_dir, "dcf_web_interface.py")
    
    # Check if the web interface file exists
    if not os.path.exists(web_interface_path):
        print(f" Web interface file not found: {web_interface_path}")
        return
    
    print(" Starting web server...")
    print(" The interface will open in your default browser")
    print(" If it doesn't open automatically, go to: http://localhost:8501")
    print("=" * 50)
    
    # Launch streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            web_interface_path,
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Web interface stopped by user")
    except Exception as e:
        print(f" Error launching web interface: {e}")

if __name__ == "__main__":
    main()
