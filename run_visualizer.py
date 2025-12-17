#!/usr/bin/env python3
"""
Launcher script for the Gearbox Chatbot Visualizer
"""

import subprocess
import sys
import os

def main():
    print("🚀 Starting Gearbox Chatbot Visualizer...")

    # Check if streamlit is available
    try:
        import streamlit
    except ImportError:
        print("❌ Streamlit not found. Please install with: pip install streamlit")
        sys.exit(1)

    # Check if required files exist
    required_files = ["data_schema.yaml", "chatbot_visualizer.py"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Required file '{file}' not found.")
            sys.exit(1)

    # Check for API key
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not found in .env file.")
        sys.exit(1)

    print("✅ All checks passed. Starting Streamlit server...")

    # Launch streamlit
    cmd = ["streamlit", "run", "chatbot_visualizer.py", "--server.headless", "true"]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Visualizer stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start visualizer: {e}")

if __name__ == "__main__":
    main()

