import os
import sys

def is_text_file(file_path):
    """Simple check to determine if a file is a text file based on extension."""
    text_extensions = [
        '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.json', '.md',
        '.txt', '.csv', '.yml', '.yaml', '.xml', '.sh', '.sql', '.gitignore',
        '.env.example', '.ini', '.conf', '.cfg'
    ]
    ext = os.path.splitext(file_path)[1].lower()
    return ext in text_extensions

def collect_code(project_root):
    """Collects code from backend and frontend/src directories."""
    output_file = "project_code_collection.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("# PROJECT CODE COLLECTION\n\n")
        
        # First collect all relevant paths
        backend_paths = []
        frontend_src_paths = []
        
        # Walk backend directory
        backend_dir = os.path.join(project_root, 'backend')
        if os.path.exists(backend_dir):
            for root, dirs, files in os.walk(backend_dir):
                # Skip venv, node_modules, .git directories
                dirs[:] = [d for d in dirs if d not in ['venv', 'node_modules', '.git', '.next']]
                
                for file in files:
                    if file.endswith('.env'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    if is_text_file(file_path):
                        backend_paths.append(file_path)
        
        # Walk frontend/src directory
        frontend_src_dir = os.path.join(project_root, 'frontend', 'src')
        if os.path.exists(frontend_src_dir):
            for root, dirs, files in os.walk(frontend_src_dir):
                # Skip node_modules, .git directories
                dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '.next']]
                
                for file in files:
                    if file.endswith('.env'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    if is_text_file(file_path):
                        frontend_src_paths.append(file_path)
        
        # Sort paths
        backend_paths.sort()
        frontend_src_paths.sort()
        
        # Write tree structure
        f.write("## DIRECTORY STRUCTURE\n\n")
        f.write("```\n")
        f.write(".\n")
        
        # Write backend tree
        if backend_paths:
            f.write("├── backend/\n")
            last_parts = []
            for path in backend_paths:
                rel_path = os.path.relpath(path, project_root)
                parts = rel_path.split(os.sep)[1:]  # Skip 'backend'
                
                # Print directories
                for i in range(len(last_parts)):
                    if i >= len(parts) - 1 or parts[i] != last_parts[i]:
                        break
                
                for j in range(i, len(parts) - 1):
                    indent = "│   " * (j + 1)
                    f.write(f"{indent}├── {parts[j]}/\n")
                
                # Print file
                indent = "│   " * len(parts)
                f.write(f"{indent}├── {parts[-1]}\n")
                
                last_parts = parts
        
        # Write frontend/src tree
        if frontend_src_paths:
            f.write("├── frontend/\n")
            f.write("│   ├── src/\n")
            last_parts = []
            for path in frontend_src_paths:
                rel_path = os.path.relpath(path, project_root)
                parts = rel_path.split(os.sep)[2:]  # Skip 'frontend/src'
                
                # Print directories
                for i in range(len(last_parts)):
                    if i >= len(parts) - 1 or parts[i] != last_parts[i]:
                        break
                
                for j in range(i, len(parts) - 1):
                    indent = "│   " * (j + 3)  # +3 for frontend/src nesting
                    f.write(f"{indent}├── {parts[j]}/\n")
                
                # Print file
                indent = "│   " * (len(parts) + 2)  # +2 for frontend/src
                f.write(f"{indent}├── {parts[-1]}\n")
                
                last_parts = parts
        
        f.write("```\n\n")
        
        # Write file contents
        f.write("## FILE CONTENTS\n\n")
        
        # Process backend files
        if backend_paths:
            f.write("### BACKEND FILES\n\n")
            for file_path in backend_paths:
                rel_path = os.path.relpath(file_path, project_root)
                f.write(f"#### {rel_path}\n\n")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as code_file:
                        content = code_file.read()
                        f.write("```\n")
                        f.write(content)
                        f.write("\n```\n\n")
                except Exception as e:
                    f.write(f"[Error reading file: {str(e)}]\n\n")
                
                f.write("-" * 80 + "\n\n")
        
        # Process frontend/src files
        if frontend_src_paths:
            f.write("### FRONTEND SRC FILES\n\n")
            for file_path in frontend_src_paths:
                rel_path = os.path.relpath(file_path, project_root)
                f.write(f"#### {rel_path}\n\n")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as code_file:
                        content = code_file.read()
                        f.write("```\n")
                        f.write(content)
                        f.write("\n```\n\n")
                except Exception as e:
                    f.write(f"[Error reading file: {str(e)}]\n\n")
                
                f.write("-" * 80 + "\n\n")
    
    return output_file

if __name__ == "__main__":
    # Use provided directory or current directory
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    output = collect_code(project_root)
    print(f"Code collection complete. Output saved to: {output}")
    print("Only included text files from backend/ and frontend/src/ directories.")
    print("Excluded .env files and binary files.")