#!/usr/bin/env python3
"""
Script to consolidate all Python chatbot files into a single text file for easy sharing.
"""

import os
import glob

def get_all_python_files():
    """Get core Python files needed for the chatbot system."""
    python_files = []

    # Core files only
    core_files = [
        'main.py',
        'yaml_reader.py',
        'prompt.py',
        'llm.py',
        'schema.py',
        'chatbot_config.yaml',
        'data_schema.yaml',
        'requirements.txt'
    ]

    # Add core files if they exist
    for file in core_files:
        if os.path.exists(file):
            python_files.append(file)

    return python_files

def read_file_content(filepath):
    """Read file content with error handling."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading {filepath}: {str(e)}"

def create_consolidated_file(output_file="consolidated_chatbot_code.txt"):
    """Create a single consolidated text file with all Python files."""
    python_files = get_all_python_files()

    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("=" * 80 + "\n")
        outfile.write("CONSOLIDATED CHATBOT CODE\n")
        outfile.write("All Python files needed to run the chatbot system\n")
        outfile.write("=" * 80 + "\n\n")

        outfile.write("FILES INCLUDED:\n")
        for i, file in enumerate(python_files, 1):
            outfile.write(f"{i}. {file}\n")
        outfile.write("\n" + "=" * 80 + "\n\n")

        for file in python_files:
            outfile.write(f"{'='*20} {file.upper()} {'='*20}\n")
            outfile.write("-" * (40 + len(file)) + "\n\n")
            content = read_file_content(file)
            outfile.write(content)
            outfile.write("\n\n" + "=" * 80 + "\n\n")

    print(f"Consolidated file created: {output_file}")
    print(f"Total files included: {len(python_files)}")
    print("Files:")
    for file in python_files:
        print(f"  - {file}")

if __name__ == "__main__":
    create_consolidated_file()
