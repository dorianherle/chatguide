#!/usr/bin/env python3
"""Export all ChatGuide code to a single text file with detailed headers."""

import os
from pathlib import Path
from datetime import datetime

def get_code_files(directory: Path) -> list:
    """Get all code/config files recursively, sorted by path."""
    code_files = []
    # File extensions to include
    extensions = {'.py', '.yaml', '.yml', '.json', '.md', '.html', '.css', '.js', '.txt', '.sh', '.bat'}

    for root, dirs, files in os.walk(directory):
        # Skip unwanted directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'venv', 'node_modules', '.git'}]

        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                code_files.append(Path(root) / file)

    return sorted(code_files)

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

def get_file_category(file_path: Path) -> str:
    """Categorize files by type/purpose."""
    # Convert to relative path from project root for easier matching
    try:
        rel_path = file_path.relative_to(Path(__file__).parent)
    except ValueError:
        rel_path = file_path

    path_str = str(rel_path)
    # Debug: uncomment to see path strings
    # print(f"DEBUG: {path_str}")

    # Log files and generated content (check first)
    if any(pattern in file_path.name for pattern in ['_log.json', 'debug_log.json', 'simulation_', 'repro_']):
        return "DEBUG_LOGS"

    # Python package metadata
    if '.egg-info' in path_str:
        return "PACKAGE_METADATA"

    # Normalize path separators for consistent matching
    norm_path = path_str.replace('\\', '/')

    # Core ChatGuide package files
    if norm_path.startswith('python/chatguide/'):
        if norm_path.startswith('python/chatguide/core/'):
            return "CORE_ENGINE"
        elif norm_path.startswith('python/chatguide/builders/'):
            return "BUILDERS"
        elif norm_path.startswith('python/chatguide/io/'):
            return "IO_LAYER"
        elif norm_path.startswith('python/chatguide/tools/'):
            return "TOOLS"
        elif norm_path.startswith('python/chatguide/utils/'):
            return "UTILITIES"
        elif norm_path.startswith('python/chatguide/') and not norm_path.endswith('__init__.py'):
            return "CORE_PACKAGE"

    # Scripts
    if norm_path.startswith('python/scripts/'):
        return "SCRIPTS"

    # Examples
    if norm_path.startswith('examples/fastapi_app/'):
        return "WEB_EXAMPLE"
    elif norm_path.startswith('examples/'):
        return "EXAMPLES"

    # Configuration
    if norm_path.startswith('configs/'):
        return "CONFIGURATION"

    # Static assets
    if norm_path.startswith('static/'):
        return "STATIC_ASSETS"

    # Tests
    if 'test' in path_str.lower():
        return "TESTS"

    # Root level documentation and config
    if len(rel_path.parts) == 1:
        if file_path.name in ['README.md', 'pyproject.toml', 'requirements.txt', 'setup.py', 'Makefile']:
            return "PROJECT_DOCS"
        elif file_path.name.endswith('.py'):
            return "ROOT_SCRIPTS"
        elif file_path.name.endswith('.html'):
            return "DOCUMENTATION"

    return "OTHER"

def get_python_category(file_path: Path, python_dir: Path) -> str:
    """Categorize Python files in the python directory."""
    try:
        rel_path = file_path.relative_to(python_dir)
        path_str = str(rel_path)
        # Normalize path separators for consistent matching
        norm_path = path_str.replace('\\', '/')
    except ValueError:
        return "OTHER"

    # Core ChatGuide package files
    if norm_path.startswith('chatguide/'):
        if norm_path.startswith('chatguide/core/'):
            return "CORE_ENGINE"
        elif norm_path.startswith('chatguide/builders/'):
            return "BUILDERS"
        elif norm_path.startswith('chatguide/io/'):
            return "IO_LAYER"
        elif norm_path.startswith('chatguide/tools/'):
            return "TOOLS"
        elif norm_path.startswith('chatguide/utils/'):
            return "UTILITIES"
        elif norm_path.startswith('chatguide/') and not norm_path.endswith('__init__.py'):
            return "CORE_PACKAGE"

    # Scripts
    if norm_path.startswith('scripts/'):
        return "SCRIPTS"

    # Package metadata
    if '.egg-info' in norm_path:
        return "PACKAGE_METADATA"

    # Root level Python files
    if len(rel_path.parts) == 1 and rel_path.name.endswith('.py'):
        return "ROOT_SCRIPTS"

    return "OTHER"

def export_python_only():
    script_dir = Path(__file__).parent
    python_dir = script_dir / "python"
    output_file = script_dir / "chatguide_python_codebase.txt"

    if not python_dir.exists():
        print(f"Error: {python_dir} not found")
        return 1

    # Only get Python files (.py) from the python directory
    code_files = []
    for root, dirs, files in os.walk(python_dir):
        # Skip unwanted directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__'}]

        for file in files:
            if file.endswith('.py'):
                code_files.append(Path(root) / file)

    code_files = sorted(code_files)
    print(f"Found {len(code_files)} code files")

    # Group files by category (simplified for Python-only export)
    categorized_files = {}
    for file_path in code_files:
        category = get_python_category(file_path, python_dir)
        if category not in categorized_files:
            categorized_files[category] = []
        categorized_files[category].append(file_path)

    # Calculate totals
    total_size = sum(get_file_info(f)['size'] for f in code_files)
    total_lines = sum(get_file_info(f)['lines'] for f in code_files)

    content = [f"ChatGuide PYTHON Codebase Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]
    content.append("=" * 80 + "\n\n")

    content.append("SUMMARY\n")
    content.append("-" * 30 + "\n")
    content.append(f"Total Python files: {len(code_files)}\n")
    content.append(f"Total size: {total_size:,} bytes ({total_size/1024:.1f} KB)\n")
    content.append(f"Total lines: {total_lines:,}\n\n")

    # Category breakdown
    content.append("CATEGORY BREAKDOWN\n")
    content.append("-" * 30 + "\n")
    for category, files in categorized_files.items():
        cat_size = sum(get_file_info(f)['size'] for f in files)
        cat_lines = sum(get_file_info(f)['lines'] for f in files)
        content.append(f"{category}: {len(files)} files, {cat_lines} lines, {cat_size/1024:.1f} KB\n")
    content.append("\n")

    content.append("FILE DETAILS\n")
    content.append("-" * 30 + "\n")

    for category, files in categorized_files.items():
        content.append(f"\n[{category}]\n")
        content.append("-" * len(f"[{category}]") + "\n")

        for file_path in sorted(files):
            info = get_file_info(file_path)
            rel_path = file_path.relative_to(python_dir)
            content.append(f"  python/{rel_path}\n")
            content.append(f"    Size: {info['size']:,} bytes | Lines: {info['lines']} | Modified: {info['modified']}\n")

    content.append("\n\n" + "="*80 + "\n")
    content.append("SOURCE CODE\n")
    content.append("="*80 + "\n\n")

    for category, files in categorized_files.items():
        content.append(f"\n{'='*80}\n")
        content.append(f"CATEGORY: {category}\n")
        content.append(f"{'='*80}\n\n")

        for file_path in sorted(files):
            info = get_file_info(file_path)
            rel_path = file_path.relative_to(python_dir)
            print(f"  [{category}] python/{rel_path} ({info['lines']} lines)")

            content.append(f"{'-'*60}\n")
            content.append(f"FILE: python/{rel_path}\n")
            content.append(f"CATEGORY: {category}\n")
            content.append(f"STATS: {info['lines']} lines, {info['size']:,} bytes\n")
            content.append(f"MODIFIED: {info['modified']}\n")
            content.append(f"FULL PATH: {file_path}\n")
            content.append("-"*60 + "\n\n")

            try:
                file_content = file_path.read_text(encoding='utf-8')
                content.append(file_content + "\n\n")
            except UnicodeDecodeError:
                content.append("[BINARY FILE - CONTENT NOT INCLUDED]\n\n")
            except Exception as e:
                content.append(f"[ERROR READING FILE: {e}]\n\n")

            # Add separator between files
            content.append("-" * 80 + "\n\n")

    output_file.write_text(''.join(content), encoding='utf-8')
    print(f"\n[SUCCESS] Python codebase exported to: {output_file}")
    print(f"[STATS] Total: {len(code_files)} Python files, {total_lines:,} lines, {total_size/1024:.1f} KB")

if __name__ == "__main__":
    export_python_only()


