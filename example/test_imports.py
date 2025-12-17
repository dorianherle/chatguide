#!/usr/bin/env python3
"""
Test script to verify imports work correctly.
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from yaml_reader import read_yaml_to_dict
    print("[OK] yaml_reader import successful")

    from prompt import get_prompt_conversation_llm, get_prompt_sidecar_director
    print("[OK] prompt imports successful")

    from llm import talk_to_gemini, talk_to_gemini_structured
    print("[OK] llm imports successful")

    # Test reading config
    config_path = os.path.join(parent_dir, 'chatbot_config.yaml')
    if os.path.exists(config_path):
        config_dict = read_yaml_to_dict(config_path)
        print("[OK] Config file read successfully")
        print(f"  Found {len(config_dict.get('blocks', []))} blocks")
    else:
        print("[WARN] Config file not found, but imports work")

    print("\nAll imports successful! The frontend should work.")

except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Other error: {e}")
    sys.exit(1)
