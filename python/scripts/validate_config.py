#!/usr/bin/env python3
"""
ChatGuide Config Validator

Validates YAML configuration files and tests ChatGuide initialization.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to path for imports
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))

from chatguide.utils.config_loader import load_config_file, validate_config


def main():
    """Main validation function."""
    if len(sys.argv) < 2:
        print("Usage: python validate_config.py <config_file> [--test-init]")
        print("\nOptions:")
        print("  --test-init    Test ChatGuide initialization (requires GEMINI_API_KEY)")
        sys.exit(1)

    config_path = sys.argv[1]
    test_init = "--test-init" in sys.argv

    print(f"[INFO] Validating config: {config_path}")

    try:
        # Load and validate config
        data = load_config_file(config_path)
        errors = validate_config(data)

        if errors:
            print("[ERROR] Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("[SUCCESS] Configuration is valid!")

        # Print summary
        plan = data.get("plan", [])
        tasks = data.get("tasks", {})
        print(f"\nConfig Summary:")
        print(f"  - {len(plan)} blocks in plan")
        print(f"  - {len(tasks)} tasks defined")
        total_expected = sum(len(tasks.get(tid, {}).get("expects", [])) for block in plan for tid in block if isinstance(tid, str))
        print(f"  - {total_expected} total expected values")

        # Test initialization if requested
        if test_init:
            print("\nTesting ChatGuide initialization...")
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("[ERROR] GEMINI_API_KEY not set, skipping initialization test")
                sys.exit(1)

            try:
                from chatguide import ChatGuide
                cg = ChatGuide(api_key=api_key, config=config_path)
                print("[SUCCESS] ChatGuide initialized successfully!")
                print(f"  - Progress: {cg.get_progress()}")

                # Test first chat turn
                reply = cg.chat()
                print(f"  - First reply: {reply.text[:100]}...")

            except Exception as e:
                print(f"[ERROR] ChatGuide initialization failed: {e}")
                sys.exit(1)

    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
