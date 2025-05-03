#!/usr/bin/env python3
import os
import subprocess
import re
from pathlib import Path

def is_binary_file(file_path):
    """Check if file is binary"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return False
    except UnicodeDecodeError:
        return True

def contains_secrets(file_path):
    """Check if file might contain secrets"""
    secret_patterns = [
        r'SECRET_KEY\s*=',
        r'API_KEY\s*=',
        r'PASSWORD\s*=',
        r'TOKEN\s*=',
        r'ACCESS_KEY\s*=',
        r'PRIVATE_KEY',
        r'\.env',
        r'credentials',
    ]
    
    # Skip checking binary files
    if is_binary_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            for pattern in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return False

def collect_code(output_file="context_for_LLMs.txt"):
    # Directories to ignore
    ignore_dirs = ['.next', 'node_modules', '.git', 'public', '__pycache__', 'venv', 'migrations']
    
    # File extensions to ignore
    ignore_extensions = ['.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.log', '.cache', '.sqlite3']
    
    # Specific files to ignore
    ignore_files = ['package-lock.json', '.env.local']
    
    # Get directory tree first (max depth 5)
    try:
        tree_cmd = ['tree', '-I', '|'.join(ignore_dirs), '-L', '5']
        tree_output = subprocess.check_output(tree_cmd, universal_newlines=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        tree_output = "Could not generate tree structure. Make sure 'tree' command is installed."
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write tree structure first
        f.write("# Project Structure\n")
        f.write("```\n")
        f.write(tree_output)
        f.write("```\n\n")
        
        # Collect and write code
        f.write("# Code Files\n\n")
        
        for root, dirs, files in os.walk('.'):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Skip ignored file extensions
                if any(file.endswith(ext) for ext in ignore_extensions):
                    continue
                
                # Skip specifically ignored files
                if file in ignore_files:
                    print(f"Skipping explicitly ignored file: {file_path}")
                    continue
                
                # Skip binary files
                if is_binary_file(file_path):
                    continue
                
                # Skip files that may contain secrets
                if contains_secrets(file_path):
                    print(f"Skipping file that may contain sensitive data: {file_path}")
                    continue
                
                # Write file path as heading
                f.write(f"## {file_path}\n")
                f.write("```\n")
                
                # Write file content
                try:
                    with open(file_path, 'r', encoding='utf-8') as code_file:
                        f.write(code_file.read())
                except Exception as e:
                    f.write(f"Error reading file: {e}")
                
                f.write("\n```\n\n")

if __name__ == "__main__":
    collect_code()
    print("Code collection complete! Output written to context_for_LLMs.txt")