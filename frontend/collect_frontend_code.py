import os
import sys

def collect_frontend_src_code(frontend_dir):
    """
    Collects all code from the src directory within the frontend directory.
    Generates a tree structure with depth of 5 and saves all code to a single text file.
    """
    # Ensure we're in the frontend directory
    if not os.path.basename(os.path.abspath(frontend_dir)) == "frontend":
        print("Error: This script should be run from the frontend directory")
        return

    # Define the src directory
    src_dir = os.path.join(frontend_dir, "src")
    
    # Check if src directory exists
    if not os.path.exists(src_dir):
        print("Error: src directory not found in frontend directory")
        return
    
    # Output file path
    output_file = os.path.join(frontend_dir, "frontend_context_code.txt")
    
    with open(output_file, "w", encoding="utf-8") as f:
        # First, generate the tree structure with depth of 5
        f.write("# Frontend Source Code\n\n")
        f.write("## Directory Structure (depth=5)\n\n")
        f.write("```\n")
        f.write("frontend/\n")
        f.write("└── src/\n")
        
        # Collect directories and files for tree structure (up to depth 5)
        tree_structure = []
        max_depth = 5  # Max depth to display
        
        for root, dirs, files in os.walk(src_dir):
            # Calculate current depth
            rel_path = os.path.relpath(root, frontend_dir)
            depth = len(rel_path.split(os.sep)) - 1  # -1 because we start from src
            
            # Skip if we're beyond max depth
            if depth > max_depth:
                continue
            
            # Sort dirs and files for consistent output
            dirs.sort()
            files.sort()
            
            # Skip node_modules, etc.
            dirs[:] = [d for d in dirs if d not in ["node_modules", ".git", ".next"]]
            
            # Add directories to tree
            for dir_name in dirs:
                indent = "    " * depth
                tree_structure.append((depth, f"{indent}├── {dir_name}/"))
            
            # Add files to tree
            for file_name in files:
                # Skip binary files and other non-code files
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
        for root, _, files in os.walk(src_dir):
            for file_name in files:
                if is_code_file(file_name):
                    file_path = os.path.join(root, file_name)
                    rel_path = os.path.relpath(file_path, frontend_dir)
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
    
    print(f"Frontend src code collected and saved to {output_file}")

def is_code_file(filename):
    """Determine if a file is a code file based on extension."""
    code_extensions = [
        ".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".html", ".json", 
        ".md", ".svg", ".yaml", ".yml", ".graphql", ".gql", ".xml"
    ]
    
    # Get file extension
    _, ext = os.path.splitext(filename)
    
    # Check if it's a code file
    return ext.lower() in code_extensions

if __name__ == "__main__":
    # Use provided directory or current directory
    frontend_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    collect_frontend_src_code(frontend_dir)