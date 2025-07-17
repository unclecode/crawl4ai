#!/usr/bin/env python3
"""
Dependency checker for Crawl4AI
Analyzes imports in the codebase and shows which files use them
"""

import ast
import os
import sys
from pathlib import Path
from typing import Set, Dict, List, Tuple
from collections import defaultdict
import re
import toml

# Standard library modules to ignore
STDLIB_MODULES = {
    'abc', 'argparse', 'asyncio', 'base64', 'collections', 'concurrent', 'contextlib',
    'copy', 'datetime', 'decimal', 'email', 'enum', 'functools', 'glob', 'hashlib',
    'http', 'importlib', 'io', 'itertools', 'json', 'logging', 'math', 'mimetypes',
    'multiprocessing', 'os', 'pathlib', 'pickle', 'platform', 'pprint', 'random',
    're', 'shutil', 'signal', 'socket', 'sqlite3', 'string', 'subprocess', 'sys',
    'tempfile', 'threading', 'time', 'traceback', 'typing', 'unittest', 'urllib',
    'uuid', 'warnings', 'weakref', 'xml', 'zipfile', 'dataclasses', 'secrets',
    'statistics', 'textwrap', 'queue', 'csv', 'gzip', 'tarfile', 'configparser',
    'inspect', 'operator', 'struct', 'binascii', 'codecs', 'locale', 'gc',
    'atexit', 'builtins', 'html', 'errno', 'fcntl', 'pwd', 'grp', 'resource',
    'termios', 'tty', 'pty', 'select', 'selectors', 'ssl', 'zlib', 'bz2',
    'lzma', 'types', 'copy', 'pydoc', 'profile', 'cProfile', 'timeit',
    'trace', 'doctest', 'pdb', 'contextvars', 'dataclasses', 'graphlib',
    'zoneinfo', 'tomllib', 'cgi', 'wsgiref', 'fileinput', 'linecache',
    'tokenize', 'tabnanny', 'compileall', 'dis', 'pickletools', 'formatter',
    '__future__', 'array', 'ctypes', 'heapq', 'bisect', 'array', 'weakref',
    'types', 'copy', 'pprint', 'repr', 'numbers', 'cmath', 'fractions',
    'statistics', 'itertools', 'functools', 'operator', 'pathlib', 'fileinput',
    'stat', 'filecmp', 'tempfile', 'glob', 'fnmatch', 'linecache', 'shutil',
    'pickle', 'copyreg', 'shelve', 'marshal', 'dbm', 'sqlite3', 'zlib', 'gzip',
    'bz2', 'lzma', 'zipfile', 'tarfile', 'configparser', 'netrc', 'xdrlib',
    'plistlib', 'hashlib', 'hmac', 'secrets', 'os', 'io', 'time', 'argparse',
    'getopt', 'logging', 'getpass', 'curses', 'platform', 'errno', 'ctypes',
    'threading', 'multiprocessing', 'concurrent', 'subprocess', 'sched', 'queue',
    'contextvars', 'asyncio', 'socket', 'ssl', 'email', 'json', 'mailcap',
    'mailbox', 'mimetypes', 'base64', 'binhex', 'binascii', 'quopri', 'uu',
    'html', 'xml', 'webbrowser', 'cgi', 'cgitb', 'wsgiref', 'urllib', 'http',
    'ftplib', 'poplib', 'imaplib', 'nntplib', 'smtplib', 'smtpd', 'telnetlib',
    'uuid', 'socketserver', 'xmlrpc', 'ipaddress', 'audioop', 'aifc', 'sunau',
    'wave', 'chunk', 'colorsys', 'imghdr', 'sndhdr', 'ossaudiodev', 'gettext',
    'locale', 'turtle', 'cmd', 'shlex', 'tkinter', 'typing', 'pydoc', 'doctest',
    'unittest', 'test', '2to3', 'distutils', 'venv', 'ensurepip', 'zipapp',
    'py_compile', 'compileall', 'dis', 'pickletools', 'pdb', 'timeit', 'trace',
    'tracemalloc', 'warnings', 'faulthandler', 'pdb', 'dataclasses', 'cgi', 
    'cgitb', 'chunk', 'crypt', 'imghdr', 'mailcap', 'nis', 'nntplib', 'optparse',
    'ossaudiodev', 'pipes', 'smtpd', 'sndhdr', 'spwd', 'sunau', 'telnetlib',
    'uu', 'xdrlib', 'msilib', 'pstats', 'rlcompleter', 'tkinter', 'ast'
}

# Known package name mappings (import name -> package name)
PACKAGE_MAPPINGS = {
    'bs4': 'beautifulsoup4',
    'PIL': 'pillow',
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'yaml': 'PyYAML',
    'OpenSSL': 'pyOpenSSL',
    'sqlalchemy': 'SQLAlchemy',
    'playwright': 'playwright',
    'patchright': 'patchright',
    'dotenv': 'python-dotenv',
    'fake_useragent': 'fake-useragent',
    'playwright_stealth': 'tf-playwright-stealth',
    'sentence_transformers': 'sentence-transformers',
    'rank_bm25': 'rank-bm25',
    'snowballstemmer': 'snowballstemmer',
    'PyPDF2': 'PyPDF2',
    'pdf2image': 'pdf2image',
}


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract imports from Python files"""
    
    def __init__(self):
        self.imports = {}  # Changed to dict to store line numbers
        self.from_imports = {}
    
    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            if module_name not in self.imports:
                self.imports[module_name] = []
            self.imports[module_name].append(node.lineno)
    
    def visit_ImportFrom(self, node):
        if node.module and node.level == 0:  # absolute imports only
            module_name = node.module.split('.')[0]
            if module_name not in self.from_imports:
                self.from_imports[module_name] = []
            self.from_imports[module_name].append(node.lineno)


def extract_imports_from_file(filepath: Path) -> Dict[str, List[int]]:
    """Extract all imports from a Python file with line numbers"""
    all_imports = {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        visitor = ImportVisitor()
        visitor.visit(tree)
        
        # Merge imports and from_imports
        for module, lines in visitor.imports.items():
            if module not in all_imports:
                all_imports[module] = []
            all_imports[module].extend(lines)
            
        for module, lines in visitor.from_imports.items():
            if module not in all_imports:
                all_imports[module] = []
            all_imports[module].extend(lines)
        
    except Exception as e:
        # Silently skip files that can't be parsed
        pass
    
    return all_imports


def get_codebase_imports_with_files(root_dir: Path) -> Dict[str, List[Tuple[str, List[int]]]]:
    """Get all imports from the crawl4ai library and docs folders with file locations and line numbers"""
    import_to_files = defaultdict(list)
    
    # Only scan crawl4ai library folder and docs folder
    target_dirs = [
        root_dir / 'crawl4ai',
        root_dir / 'docs'
    ]
    
    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
            
        for py_file in target_dir.rglob('*.py'):
            # Skip __pycache__ directories
            if '__pycache__' in py_file.parts:
                continue
            
            # Skip setup.py and similar files
            if py_file.name in ['setup.py', 'setup.cfg', 'conf.py']:
                continue
                
            imports = extract_imports_from_file(py_file)
            
            # Map each import to the file and line numbers
            for imp, line_numbers in imports.items():
                relative_path = py_file.relative_to(root_dir)
                import_to_files[imp].append((str(relative_path), sorted(line_numbers)))
    
    return dict(import_to_files)


def get_declared_dependencies() -> Set[str]:
    """Get declared dependencies from pyproject.toml and requirements.txt"""
    declared = set()
    
    # Read from pyproject.toml
    if Path('pyproject.toml').exists():
        with open('pyproject.toml', 'r') as f:
            data = toml.load(f)
        
        # Get main dependencies
        deps = data.get('project', {}).get('dependencies', [])
        for dep in deps:
            # Parse dependency string (e.g., "numpy>=1.26.0,<3")
            match = re.match(r'^([a-zA-Z0-9_-]+)', dep)
            if match:
                pkg_name = match.group(1).lower()
                declared.add(pkg_name)
        
        # Get optional dependencies
        optional = data.get('project', {}).get('optional-dependencies', {})
        for group, deps in optional.items():
            for dep in deps:
                match = re.match(r'^([a-zA-Z0-9_-]+)', dep)
                if match:
                    pkg_name = match.group(1).lower()
                    declared.add(pkg_name)
    
    # Also check requirements.txt as backup
    if Path('requirements.txt').exists():
        with open('requirements.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    match = re.match(r'^([a-zA-Z0-9_-]+)', line)
                    if match:
                        pkg_name = match.group(1).lower()
                        declared.add(pkg_name)
    
    return declared


def normalize_package_name(name: str) -> str:
    """Normalize package name for comparison"""
    # Handle known mappings first
    if name in PACKAGE_MAPPINGS:
        return PACKAGE_MAPPINGS[name].lower()
    
    # Basic normalization
    return name.lower().replace('_', '-')


def check_missing_dependencies():
    """Main function to check for missing dependencies"""
    print("🔍 Analyzing crawl4ai library and docs folders...\n")
    
    # Get all imports with their file locations
    root_dir = Path('.')
    import_to_files = get_codebase_imports_with_files(root_dir)
    
    # Get declared dependencies
    declared_deps = get_declared_dependencies()
    
    # Normalize declared dependencies
    normalized_declared = {normalize_package_name(dep) for dep in declared_deps}
    
    # Categorize imports
    external_imports = {}
    local_imports = {}
    
    # Known local packages
    local_packages = {'crawl4ai'}
    
    for imp, file_info in import_to_files.items():
        # Skip standard library
        if imp in STDLIB_MODULES:
            continue
            
        # Check if it's a local import
        if any(imp.startswith(local) for local in local_packages):
            local_imports[imp] = file_info
        else:
            external_imports[imp] = file_info
    
    # Check which external imports are not declared
    not_declared = {}
    declared_imports = {}
    
    for imp, file_info in external_imports.items():
        normalized_imp = normalize_package_name(imp)
        
        # Check if import is covered by declared dependencies
        found = False
        for declared in normalized_declared:
            if normalized_imp == declared or normalized_imp.startswith(declared + '.') or declared.startswith(normalized_imp):
                found = True
                break
        
        if found:
            declared_imports[imp] = file_info
        else:
            not_declared[imp] = file_info
    
    # Print results
    print(f"📊 Summary:")
    print(f"  - Total unique imports: {len(import_to_files)}")
    print(f"  - External imports: {len(external_imports)}")
    print(f"  - Declared dependencies: {len(declared_deps)}")
    print(f"  - External imports NOT in dependencies: {len(not_declared)}\n")
    
    if not_declared:
        print("❌ External imports NOT declared in pyproject.toml or requirements.txt:\n")
        
        # Sort by import name
        for imp in sorted(not_declared.keys()):
            file_info = not_declared[imp]
            print(f"  📦 {imp}")
            if imp in PACKAGE_MAPPINGS:
                print(f"     → Package name: {PACKAGE_MAPPINGS[imp]}")
            
            # Show up to 3 files that use this import
            for i, (file_path, line_numbers) in enumerate(file_info[:3]):
                # Format line numbers for clickable output
                if len(line_numbers) == 1:
                    print(f"     - {file_path}:{line_numbers[0]}")
                else:
                    # Show first few line numbers
                    line_str = ','.join(str(ln) for ln in line_numbers[:3])
                    if len(line_numbers) > 3:
                        line_str += f"... ({len(line_numbers)} imports)"
                    print(f"     - {file_path}: lines {line_str}")
            
            if len(file_info) > 3:
                print(f"     ... and {len(file_info) - 3} more files")
            print()
    
    # Check for potentially unused dependencies
    print("\n🔎 Checking declared dependencies usage...\n")
    
    # Get all used external packages
    used_packages = set()
    for imp in external_imports.keys():
        normalized = normalize_package_name(imp)
        used_packages.add(normalized)
    
    # Find unused
    unused = []
    for dep in declared_deps:
        normalized_dep = normalize_package_name(dep)
        
        # Check if any import uses this dependency
        found_usage = False
        for used in used_packages:
            if used == normalized_dep or used.startswith(normalized_dep) or normalized_dep.startswith(used):
                found_usage = True
                break
        
        if not found_usage:
            # Some packages are commonly unused directly
            indirect_deps = {'wheel', 'setuptools', 'pip', 'colorama', 'certifi', 'packaging', 'urllib3'}
            if normalized_dep not in indirect_deps:
                unused.append(dep)
    
    if unused:
        print("⚠️  Declared dependencies with NO imports found:")
        for dep in sorted(unused):
            print(f"  - {dep}")
        print("\n  Note: These might be used indirectly or by other dependencies")
    else:
        print("✅ All declared dependencies have corresponding imports")
    
    print("\n" + "="*60)
    print("💡 How to use this report:")
    print("  1. Check each ❌ import to see if it's legitimate")
    print("  2. If legitimate, add the package to pyproject.toml")
    print("  3. If it's an internal module or typo, fix the import")
    print("  4. Review unused dependencies - remove if truly not needed")
    print("="*60)


if __name__ == '__main__':
    check_missing_dependencies()