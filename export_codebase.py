#!/usr/bin/env python3
"""Export all ChatGuide Python code to a single text file with detailed headers."""

import os
from pathlib import Path
from datetime import datetime

def get_python_files(directory: Path) -> list:
    """Get all Python files recursively, sorted by path."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip pycache and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    return sorted(python_files)

def get_file_info(file_path: Path) -> dict:
    """Get detailed information about a file."""
    stat = file_path.stat()
    content = file_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    return {
        'path': file_path,
        'size': stat.st_size,
        'lines': len(lines),
        'non_empty_lines': len([line for line in lines if line.strip()]),
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    }

def export():
    script_dir = Path(__file__).parent
    chatguide_dir = script_dir / "python" / "chatguide"
    output_file = script_dir / "chatguide_codebase.txt"

    if not chatguide_dir.exists():
        print(f"Error: {chatguide_dir} not found")
        return 1

    python_files = get_python_files(chatguide_dir)
    print(f"Found {len(python_files)} Python files")

    # Calculate totals
    total_size = sum(get_file_info(f)['size'] for f in python_files)
    total_lines = sum(get_file_info(f)['lines'] for f in python_files)

    content = [f"ChatGuide Codebase Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]
    content.append("=" * 60 + "\n\n")

    content.append("SUMMARY\n")
    content.append("-" * 20 + "\n")
    content.append(f"Total files: {len(python_files)}\n")
    content.append(f"Total size: {total_size:,} bytes ({total_size/1024:.1f} KB)\n")
    content.append(f"Total lines: {total_lines:,}\n\n")

    content.append("FILE DETAILS\n")
    content.append("-" * 20 + "\n")

    for file_path in python_files:
        info = get_file_info(file_path)
        rel_path = file_path.relative_to(script_dir / "python")
        content.append(f"[FILE] {rel_path}\n")
        content.append(f"   Size: {info['size']:,} bytes | Lines: {info['lines']} | Modified: {info['modified']}\n")
        content.append(f"   Path: {file_path}\n\n")

    content.append("SOURCE CODE\n")
    content.append("=" * 60 + "\n\n")

    for file_path in python_files:
        info = get_file_info(file_path)
        rel_path = file_path.relative_to(script_dir / "python")
        print(f"  [FILE] {rel_path} ({info['lines']} lines)")

        content.append(f"{'='*60}\n")
        content.append(f"FILE: {rel_path}\n")
        content.append(f"STATS: {info['lines']} lines, {info['size']:,} bytes\n")
        content.append(f"MODIFIED: {info['modified']}\n")
        content.append("="*60 + "\n\n")

        file_content = file_path.read_text(encoding='utf-8')
        content.append(file_content + "\n\n")

        # Add separator
        content.append("-" * 80 + "\n\n")

    output_file.write_text(''.join(content), encoding='utf-8')
    print(f"\n[SUCCESS] Exported to: {output_file}")
    print(f"[STATS] Total: {len(python_files)} files, {total_lines:,} lines, {total_size/1024:.1f} KB")

if __name__ == "__main__":
    export()

