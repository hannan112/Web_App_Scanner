import os
import sys

def is_binary_file(file_path):
    """Check if a file is binary by reading the first few KB."""
    try:
        with open(file_path, 'rb') as f:
            # Read first 8KB
            chunk = f.read(8192)
            # Check for null bytes (common in binary files)
            if b'\x00' in chunk:
                return True
            # Try to decode as text
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except Exception:
        # If we can't open or read the file, skip it
        return True

def should_exclude_file(file_name):
    """Check if file should be excluded based on name or extension."""
    # Exclude environment files
    if file_name.endswith('.env') or file_name == '.env':
        return True
    
    # Exclude database files
    db_extensions = ['.db', '.sqlite', '.sqlite3', '.sql3', '.db3']
    if any(file_name.endswith(ext) for ext in db_extensions):
        return True
    
    # Exclude other common binaries
    binary_extensions = ['.pyc', '.so', '.dll', '.exe', '.bin']
    if any(file_name.endswith(ext) for ext in binary_extensions):
        return True
    
    return False

def is_code_file(filename):
    """Determine if a file is a code file based on extension."""
    code_extensions = [
        ".py", ".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".html", ".json", 
        ".md", ".txt", ".yml", ".yaml", ".xml", ".sh", ".bat", ".conf"
    ]
    
    # Get file extension
    _, ext = os.path.splitext(filename)
    
    # Check if it's a code file
    return ext.lower() in code_extensions

def collect_backend_code(backend_dir):
    """
    Collects all code from the backend directory.
    Generates a tree structure with depth of 5 and saves all code to a single text file.
    Excludes binary files, database files, .env files, and certain directories.
    """
    # Ensure we're in the backend directory
    if not os.path.basename(os.path.abspath(backend_dir)) == "backend":
        print("Error: This script should be run from the backend directory")
        return

    # Output file path
    output_file = os.path.join(backend_dir, "backend_context_code.txt")
    
    with open(output_file, "w", encoding="utf-8") as f:
        # First, generate the tree structure with depth of 5
        f.write("# Backend Source Code\n\n")
        f.write("## Directory Structure (depth=5)\n\n")
        f.write("```\n")
        f.write("backend/\n")
        
        # Collect directories and files for tree structure (up to depth 5)
        tree_structure = []
        max_depth = 5  # Max depth to display
        
        for root, dirs, files in os.walk(backend_dir):
            # Calculate current depth
            rel_path = os.path.relpath(root, backend_dir)
            if rel_path == ".":
                depth = 0
            else:
                depth = len(rel_path.split(os.sep))
            
            # Skip if we're beyond max depth
            if depth > max_depth:
                continue
            
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ["venv", ".git", "__pycache__", "node_modules", ".next"]]
            
            # Sort dirs and files for consistent output
            dirs.sort()
            files.sort()
            
            # Add directories to tree (except at root level)
            if depth > 0:
                for dir_name in dirs:
                    indent = "    " * depth
                    tree_structure.append((depth, f"{indent}├── {dir_name}/"))
            
            # Add files to tree
            for file_name in files:
                # Skip excluded and binary files
                file_path = os.path.join(root, file_name)
                if should_exclude_file(file_name) or is_binary_file(file_path):
                    continue
                
                if is_code_file(file_name):
                    indent = "    " * depth
                    tree_structure.append((depth, f"{indent}├── {file_name}"))
        
        # Write tree structure
        for _, line in tree_structure:
            f.write(line + "\n")
        
        f.write("```\n\n")
        
        # Now collect and write all the code
        f.write("## Source Code\n\n")
        
        # Collect all code files
        code_files = []
        for root, _, files in os.walk(backend_dir):
            # Skip certain directories
            if any(skip_dir in root.split(os.sep) for skip_dir in ["venv", ".git", "__pycache__", "node_modules", ".next"]):
                continue
            
            for file_name in files:
                # Skip excluded files
                if should_exclude_file(file_name):
                    continue
                    
                file_path = os.path.join(root, file_name)
                
                # Skip binary files
                if is_binary_file(file_path):
                    continue
                    
                if is_code_file(file_name):
                    rel_path = os.path.relpath(file_path, backend_dir)
                    code_files.append((rel_path, file_path))
        
        # Sort for consistent output
        code_files.sort()
        
        # Write all code contents
        for rel_path, file_path in code_files:
            f.write(f"### {rel_path}\n\n")
            try:
                with open(file_path, "r", encoding="utf-8") as code_file:
                    content = code_file.read()
                    f.write("```\n")
                    f.write(content)
                    f.write("\n```\n\n")
                    f.write("-" * 80 + "\n\n")
            except Exception as e:
                f.write(f"[Error reading file: {str(e)}]\n\n")
    
    print(f"Backend code collected and saved to {output_file}")
    print("Binary files, database files, and .env files were excluded.")

if __name__ == "__main__":
    # Use provided directory or current directory
    backend_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    collect_backend_code(backend_dir)