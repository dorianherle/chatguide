#!/usr/bin/env python3
"""
Test script to verify .env file loading.
"""
import os
from dotenv import load_dotenv

# Load .env from the current directory (example folder)
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
print(f"Looking for .env file at: {env_path}")

if os.path.exists(env_path):
    print("[OK] .env file exists")
    load_dotenv(env_path)

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        print(f"[OK] GEMINI_API_KEY loaded successfully: {GEMINI_API_KEY[:10]}...")
    else:
        print("[ERROR] GEMINI_API_KEY not found in .env file")
else:
    print("[ERROR] .env file not found")
