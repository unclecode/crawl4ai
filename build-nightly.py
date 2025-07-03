#!/usr/bin/env python3
"""
Build script for creating nightly versions of Crawl4AI.
This script temporarily modifies pyproject.toml to build the nightly package.
"""

import shutil
import sys
import os
import tempfile
from pathlib import Path

def modify_files_for_nightly():
    """Modify pyproject.toml and __version__.py for nightly package."""
    
    from datetime import datetime
    
    # Generate date-based version: YY.M.D.HHMMSS
    now = datetime.utcnow()
    nightly_version = f"{now.year % 100}.{now.month}.{now.day}.{now.strftime('%H%M%S')}"
    
    # 1. Modify pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found!")
        sys.exit(1)
    
    with open(pyproject_path, 'r') as f:
        content = f.read()
    
    # Create backup
    pyproject_backup = pyproject_path.with_suffix('.toml.backup')
    shutil.copy2(pyproject_path, pyproject_backup)
    print(f"Created backup: {pyproject_backup}")
    
    # Modify content for nightly build
    modified_content = content.replace(
        'name = "Crawl4AI"',
        'name = "crawl4ai-nightly"'
    )
    
    # Also update the description
    modified_content = modified_content.replace(
        'description = "🚀🤖 Crawl4AI: Open-source LLM Friendly Web Crawler & scraper"',
        'description = "🚀🤖 Crawl4AI: Open-source LLM Friendly Web Crawler & scraper (Nightly Build)"'
    )
    
    # Update the version attribute to use __nightly_version__
    modified_content = modified_content.replace(
        'version = {attr = "crawl4ai.__version__.__version__"}',
        'version = {attr = "crawl4ai.__version__.__nightly_version__"}'
    )
    
    # Write modified content
    with open(pyproject_path, 'w') as f:
        f.write(modified_content)
    print("Modified pyproject.toml for nightly build")
    
    # 2. Update __nightly_version__ in __version__.py
    version_path = Path("crawl4ai/__version__.py")
    if not version_path.exists():
        print("Error: crawl4ai/__version__.py not found!")
        sys.exit(1)
    
    with open(version_path, 'r') as f:
        version_content = f.read()
    
    # Create backup
    version_backup = version_path.with_suffix('.py.backup')
    shutil.copy2(version_path, version_backup)
    print(f"Created backup: {version_backup}")
    
    # Update __nightly_version__
    modified_version_content = version_content.replace(
        '__nightly_version__ = None',
        f'__nightly_version__ = "{nightly_version}"'
    )
    
    # Write modified content
    with open(version_path, 'w') as f:
        f.write(modified_version_content)
    print(f"Set nightly version: {nightly_version}")
    
    return pyproject_backup, version_backup

def restore_files(pyproject_backup, version_backup):
    """Restore original files from backups."""
    # Restore pyproject.toml
    pyproject_path = Path("pyproject.toml")
    shutil.move(pyproject_backup, pyproject_path)
    print("Restored original pyproject.toml")
    
    # Restore __version__.py
    version_path = Path("crawl4ai/__version__.py")
    shutil.move(version_backup, version_path)
    print("Restored original __version__.py")

def main():
    """Main function to handle build process."""
    # Set environment variable for nightly versioning
    os.environ['CRAWL4AI_NIGHTLY'] = '1'
    
    try:
        # Modify files for nightly
        pyproject_backup, version_backup = modify_files_for_nightly()
        
        print("\nReady for nightly build!")
        print("Run your build command now (e.g., 'python -m build')")
        print(f"\nTo restore original files, run:")
        print(f"  python build-nightly.py --restore")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def restore_mode():
    """Restore original files from backups."""
    pyproject_backup = Path("pyproject.toml.backup")
    version_backup = Path("crawl4ai/__version__.py.backup")
    
    if pyproject_backup.exists() and version_backup.exists():
        restore_files(pyproject_backup, version_backup)
    else:
        if pyproject_backup.exists():
            shutil.move(pyproject_backup, Path("pyproject.toml"))
            print("Restored pyproject.toml")
        if version_backup.exists():
            shutil.move(version_backup, Path("crawl4ai/__version__.py"))
            print("Restored __version__.py")
        if not pyproject_backup.exists() and not version_backup.exists():
            print("No backups found. Nothing to restore.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        restore_mode()
    else:
        main()