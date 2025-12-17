#!/usr/bin/env python3
"""
Simple runner script for the ChatGuide frontend example.
"""
import os
import sys

# Change to the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(script_dir))

# Import and run the app
from app import app

if __name__ == "__main__":
    import uvicorn
    print("Starting ChatGuide Frontend...")
    print("[OK] Using .env file from example directory")
    print("Server will be available at: http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
