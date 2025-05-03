#!/usr/bin/env python3

import os
import subprocess
import re
import logging
import time
import magic  # pip install python-magic
import json
from pathlib import Path
from tqdm import tqdm  # pip install tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("context_collection.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuration for file collection
MAX_FILE_SIZE_MB = 5  # Skip files larger than this size
MAX_TOTAL_SIZE_MB = 100  # Increased to capture more project files
CHUNK_FILES = True  # Whether to split large output into multiple files

def is_binary_file(file_path):
    """
    Check if file is binary using multiple methods for accuracy,
    only reading a small sample of the file
    """
    # First, check file extension as a quick filter
    _, ext = os.path.splitext(file_path.lower())
    known_binary_exts = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.pdf', 
                         '.zip', '.gz', '.tar', '.exe', '.dll', '.so', '.pyc']
    if ext in known_binary_exts:
        return True
    
    # Use python-magic for file type detection (only reads file header)
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        if 'text/' not in file_type and 'application/json' not in file_type:
            return True
    except Exception as e:
        logger.warning(f"Magic library failed for {file_path}: {e}, falling back to manual check")
        # Fallback to manual binary check - only read a sample
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(1024)  # Read just the first 1KB
                # Check for null bytes which indicate binary content
                if b'\x00' in sample:
                    return True
                # Try to decode as text
                sample.decode('utf-8')
                return False
        except UnicodeDecodeError:
            return True
        
    return False

def contains_secrets(file_path):
    """
    Enhanced check if file might contain secrets or sensitive information,
    using efficient streaming to avoid loading large files entirely
    """
    secret_patterns = [
        # API and access keys
        r'SECRET_KEY\s*=',
        r'SECRET[-_]?KEY["\']\s*:',
        r'API[-_]?KEY\s*=',
        r'API[-_]?KEY["\']\s*:',
        r'ACCESS[-_]?KEY\s*=',
        r'ACCESS[-_]?KEY["\']\s*:',
        
        # Passwords and tokens
        r'PASSWORD\s*=',
        r'PASSWORD["\']\s*:',
        r'TOKEN\s*=',
        r'TOKEN["\']\s*:',
        
        # JWT and private keys
        r'JWT[-_]?SECRET',
        r'PRIVATE[-_]?KEY',
        r'-----BEGIN .* PRIVATE KEY-----',
        
        # Config files likely to contain secrets
        r'\.env',
        r'credentials\.json',
        r'client_secret',
        r'\.pem$',
        
        # Database connection strings
        r'DATABASE_URL',
        r'mongodb(\+srv)?://[^/\s]+:[^/\s]+@',
        r'postgres://[^/\s]+:[^/\s]+@',
        r'mysql://[^/\s]+:[^/\s]+@',
        
        # AWS specific
        r'AKIA[0-9A-Z]{16}',  # AWS Access Key ID format
        r'aws_access_key_id',
        r'aws_secret_access_key',
    ]
    
    # Skip binary files
    if is_binary_file(file_path):
        return False
    
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
    if file_size > MAX_FILE_SIZE_MB:
        logger.info(f"Skipping large file ({file_size:.2f} MB): {file_path}")
        return True
    
    try:
        # Use line-by-line reading instead of reading the whole file
        with open(file_path, 'r', encoding='utf-8') as f:
            # Check file in chunks to avoid loading it all at once
            chunk_size = 50  # lines per chunk
            lines = []
            
            for i, line in enumerate(f):
                lines.append(line)
                
                # When we've read enough lines, check them and clear buffer
                if (i + 1) % chunk_size == 0:
                    chunk_text = ''.join(lines)
                    
                    for pattern in secret_patterns:
                        if re.search(pattern, chunk_text, re.IGNORECASE):
                            logger.info(f"Potential secrets detected in {file_path}")
                            return True
                    
                    # Clear buffer for next chunk
                    lines = []
            
            # Check any remaining lines
            if lines:
                chunk_text = ''.join(lines)
                for pattern in secret_patterns:
                    if re.search(pattern, chunk_text, re.IGNORECASE):
                        logger.info(f"Potential secrets detected in {file_path}")
                        return True
            
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return True  # Skip files that can't be properly checked
        
    return False

def is_relevant_file(file_path, file_extensions=None):
    """
    Enhanced check if file is relevant for code context
    """
    if file_extensions is None:
        file_extensions = [
            # Code files
            '.py', '.js', '.jsx', '.ts', '.tsx', 
            '.java', '.c', '.cpp', '.h', '.hpp',
            '.go', '.rb', '.php', '.html', '.css',
            '.scss', '.json', '.yaml', '.yml',
            
            # Config files
            '.toml', '.ini', '.conf',
            
            # Documentation
            '.md', '.txt', '.rst',
            
            # Templates
            '.j2', '.jinja', '.mustache', '.hbs'
        ]
    
    # Check file path for critical components
    critical_patterns = [
        # Authentication
        r'/authentication/models\.py',
        r'/authentication/views\.py',
        r'/auth/',
        
        # Frontend components
        r'/components/auth/',
        r'/components/projects/',
        r'/components/scanning/',
        
        # API integration
        r'/lib/api/',
        
        # Testing
        r'test\.py',
        r'tests\.py',
    ]
    
    # Prioritize files that match critical patterns
    for pattern in critical_patterns:
        if re.search(pattern, file_path):
            return True
    
    # Check if file has relevant extension
    return any(file_path.endswith(ext) for ext in file_extensions)

def prioritize_files(file_paths):
    """
    Prioritize files to ensure critical components are included first
    when size limits apply
    """
    priority_patterns = {
        # Highest priority - Core models and system components
        'highest': [
            r'/models\.py$',
            r'/settings\.py$',
            r'/urls\.py$',
            r'/authentication/.*\.py$',
            r'/scanning/scanner/.*\.py$',
        ],
        # High priority - Views, serializers, and frontend components
        'high': [
            r'/views\.py$',
            r'/serializers\.py$',
            r'/components/.*\.tsx$',
            r'/app/.*\.tsx$',
            r'/lib/api/.*\.ts$',
        ],
        # Medium priority - Configuration files and tests
        'medium': [
            r'\.json$',
            r'\.yml$',
            r'\.yaml$',
            r'/tests\.py$',
            r'test_.*\.py$',
        ],
        # Default priority - Everything else
        'default': [r'.*'],
    }
    
    # Sort files by priority
    priority_files = {
        'highest': [],
        'high': [],
        'medium': [],
        'default': [],
    }
    
    for file_path in file_paths:
        matched = False
        for priority, patterns in priority_patterns.items():
            if not matched:
                for pattern in patterns:
                    if re.search(pattern, file_path):
                        priority_files[priority].append(file_path)
                        matched = True
                        break
        
        # If no priority matched, add to default
        if not matched:
            priority_files['default'].append(file_path)
    
    # Combine all priorities in order
    prioritized = (
        priority_files['highest'] + 
        priority_files['high'] + 
        priority_files['medium'] + 
        priority_files['default']
    )
    
    return prioritized

def get_git_info():
    """
    Get basic Git repository information if available
    """
    git_info = {
        "is_git_repo": False,
        "remote_url": None,
        "current_branch": None,
        "last_commit": None
    }
    
    try:
        # Check if it's a git repo
        subprocess.check_output(["git", "rev-parse", "--is-inside-work-tree"], stderr=subprocess.DEVNULL)
        git_info["is_git_repo"] = True
        
        # Get remote URL
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], 
                                           stderr=subprocess.DEVNULL, universal_newlines=True).strip()
        git_info["remote_url"] = remote_url
        
        # Get current branch
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                                       stderr=subprocess.DEVNULL, universal_newlines=True).strip()
        git_info["current_branch"] = branch
        
        # Get last commit info
        last_commit = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%h - %s (%an, %ar)"],
            stderr=subprocess.DEVNULL, universal_newlines=True
        ).strip()
        git_info["last_commit"] = last_commit
        
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.debug(f"Git information not available: {e}")
        
    return git_info

def get_project_summary():
    """
    Generate a more detailed project summary by analyzing the codebase
    """
    file_counts = {}
    total_lines = 0
    top_directories = {}
    framework_indicators = {
        'django': 0,
        'react': 0,
        'next.js': 0,
        'tailwind': 0
    }
    
    try:
        for root, dirs, files in os.walk('.'):
            if any(ignore in root for ignore in ['.git', 'node_modules', '__pycache__', 'venv']):
                continue
                
            dir_name = root.lstrip('./\\')
            if not dir_name:
                dir_name = "root"
            
            top_directories[dir_name] = top_directories.get(dir_name, 0) + len(files)
            
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1]
                
                if not is_binary_file(file_path) and is_relevant_file(file_path):
                    file_counts[ext] = file_counts.get(ext, 0) + 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            line_count = content.count('\n') + 1
                            total_lines += line_count
                            
                            # Check for framework indicators
                            if 'django' in content.lower():
                                framework_indicators['django'] += 1
                            if 'react' in content.lower():
                                framework_indicators['react'] += 1
                            if 'next' in content.lower() and ('app' in content.lower() or 'pages' in content.lower()):
                                framework_indicators['next.js'] += 1
                            if 'tailwind' in content.lower():
                                framework_indicators['tailwind'] += 1
                    except:
                        pass
        
        # Sort and keep only top directories
        top_dirs = dict(sorted(top_directories.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Determine primary frameworks
        frameworks_used = []
        for framework, count in framework_indicators.items():
            if count > 0:
                frameworks_used.append(framework)
        
        return {
            "file_counts_by_type": dict(sorted(file_counts.items(), key=lambda x: x[1], reverse=True)),
            "total_files": sum(file_counts.values()),
            "total_lines": total_lines,
            "top_directories": top_dirs,
            "frameworks": frameworks_used
        }
        
    except Exception as e:
        logger.error(f"Error generating project summary: {e}")
        return {"error": str(e)}

def analyze_code_completeness(file_paths):
    """
    Analyze the codebase for completeness by checking for key file components
    and their implementations
    """
    components = {
        'backend': {
            'authentication': {
                'files': ['models.py', 'views.py', 'serializers.py'],
                'found': []
            },
            'projects': {
                'files': ['models.py', 'views.py', 'serializers.py'],
                'found': []
            },
            'scanning': {
                'files': ['models.py', 'views.py', 'serializers.py', 'scanner/engine.py', 
                          'scanner/crawler.py', 'scanner/analyzers.py', 'scanner/passive.py'],
                'found': []
            }
        },
        'frontend': {
            'auth': {
                'files': ['LoginForm.tsx', 'RegisterForm.tsx', 'ProtectedRoute.tsx'],
                'found': []
            },
            'projects': {
                'files': ['ProjectList.tsx', 'ProjectDetail.tsx', 'ProjectForm.tsx'],
                'found': []
            },
            'scanning': {
                'files': ['ScanResults.tsx'],
                'found': []
            },
            'api': {
                'files': ['auth.ts', 'projects.ts', 'scans.ts'],
                'found': []
            }
        }
    }
    
    # Check which files exist
    for file_path in file_paths:
        for section, subsections in components.items():
            for subsection, details in subsections.items():
                for file in details['files']:
                    if f'/{subsection}/{file}' in file_path:
                        if file not in details['found']:
                            details['found'].append(file)
                        break
    
    # Calculate completeness percentage for each section
    completeness = {}
    missing_components = []
    
    for section, subsections in components.items():
        completeness[section] = {}
        
        for subsection, details in subsections.items():
            total = len(details['files'])
            found = len(details['found'])
            percentage = (found / total) * 100 if total > 0 else 0
            
            completeness[section][subsection] = {
                'percentage': round(percentage, 2),
                'found': found,
                'total': total
            }
            
            # Add missing components to the list
            missing = [f'{section}/{subsection}/{file}' for file in details['files'] if file not in details['found']]
            if missing:
                missing_components.extend(missing)
    
    # Calculate overall completeness
    total_files = sum(len(details['files']) for section in components.values() for details in section.values())
    total_found = sum(len(details['found']) for section in components.values() for details in section.values())
    overall_percentage = (total_found / total_files) * 100 if total_files > 0 else 0
    
    return {
        'overall_percentage': round(overall_percentage, 2),
        'details': completeness,
        'missing_components': missing_components[:10] if len(missing_components) > 10 else missing_components
    }

def find_missing_modules(file_paths):
    """
    Identify potentially important modules that are missing from the collected files,
    using line-by-line processing for efficiency
    """
    # Dictionary of patterns to find imported modules
    import_patterns = {
        'python': r'^\s*(?:import|from)\s+([a-zA-Z0-9_.]+)',
        'javascript': r'(?:import|require)\s*\(?[\'"]([^\'"]*)[\'"]\)?',
        'typescript': r'(?:import|require)\s*\(?[\'"]([^\'"]*)[\'"]\)?',
    }
    
    # Map file extensions to language
    extension_to_lang = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript'
    }
    
    # Track modules imported and files collected
    imported_modules = set()
    collected_modules = set()
    
    for file_path in file_paths:
        ext = os.path.splitext(file_path)[1]
        lang = extension_to_lang.get(ext)
        
        if not lang:
            continue
            
        # Add this file's module to collected set
        module_path = os.path.dirname(file_path).replace(os.sep, '.')
        if module_path.startswith('.'):
            module_path = module_path[1:]
        if module_path:
            collected_modules.add(module_path)
        
        # Find imports in this file - only read the first 100 lines
        # since imports are typically at the top of files
        pattern = import_patterns.get(lang)
        if not pattern:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Only read enough lines to find imports (typically at the top)
                for i, line in enumerate(f):
                    if i > 100:  # Stop after 100 lines
                        break
                        
                    match = re.search(pattern, line)
                    if match:
                        module_name = match.group(1)
                        # Filter out third-party packages
                        if (lang == 'python' and '.' in module_name and not module_name.startswith(('django', 'rest_framework'))) or \
                           (lang in ['javascript', 'typescript'] and module_name.startswith('./')):
                            imported_modules.add(module_name)
                        
        except Exception as e:
            logger.debug(f"Error analyzing imports in {file_path}: {e}")
    
    # Find what's missing
    missing = imported_modules - collected_modules
    return list(missing)

def collect_code(output_file="context_for_LLMs.txt", output_dir=None):
    """
    Collect code files and create a context file for LLMs
    """
    start_time = time.time()
    logger.info("Starting code collection process")
    
    # Directories to ignore
    ignore_dirs = [
        '.next', 'node_modules', '.git', 'public', '__pycache__', 
        'venv', 'env', '.venv', '.env', 'migrations', 'dist', 'build',
        'coverage', 'fixtures'
    ]
    
    # File extensions to ignore
    ignore_extensions = [
        '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.log', '.cache', 
        '.sqlite3', '.db', '.DS_Store', '.jpeg', '.jpg', '.png', '.gif', 
        '.bmp', '.ico', '.svg', '.mp4', '.mp3', '.mov', '.pdf', '.zip',
        '.tar.gz', '.rar'
    ]
    
    # Specific files to ignore
    ignore_files = [
        'package-lock.json', '.env.local', '.env', 'yarn.lock',
        'client_secret.json', 'credentials.json', 'service-account.json'
    ]
    
    # Get git info if available
    git_info = get_git_info()
    
    # Setup output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, output_file)
    
    # Get directory tree first (max depth 5)
    try:
        ignore_pattern = '|'.join(ignore_dirs)
        tree_cmd = ['tree', '-I', ignore_pattern, '-L', '5']
        tree_output = subprocess.check_output(tree_cmd, universal_newlines=True)
    except Exception as e:
        logger.warning(f"Could not generate tree structure: {e}")
        tree_output = "Could not generate tree structure. Make sure 'tree' command is installed."
    
    # Collect all valid files first
    valid_files = []
    total_size = 0
    
    logger.info("Scanning for relevant files...")
    for root, dirs, files in os.walk('.'):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip ignored file extensions and specific files
            if any(file.endswith(ext) for ext in ignore_extensions) or file in ignore_files:
                continue
                
            # Skip if not a relevant file type
            if not is_relevant_file(file_path):
                continue
                
            # Skip binary files
            if is_binary_file(file_path):
                continue
                
            # Skip files that may contain secrets
            if contains_secrets(file_path):
                logger.info(f"Skipping file that may contain sensitive data: {file_path}")
                continue
                
            # Check file size
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            if file_size > MAX_FILE_SIZE_MB:
                logger.info(f"Skipping large file ({file_size:.2f} MB): {file_path}")
                continue
                
            valid_files.append(file_path)
            total_size += file_size
    
    logger.info(f"Found {len(valid_files)} relevant files (total size: {total_size:.2f} MB)")
    
    # Prioritize files to ensure important components are captured
    logger.info("Prioritizing files...")
    valid_files = prioritize_files(valid_files)
    
    # Check for completeness
    logger.info("Analyzing code completeness...")
    completeness = analyze_code_completeness(valid_files)
    
    # Enforce size limit if necessary
    if total_size > MAX_TOTAL_SIZE_MB:
        logger.warning(f"Total size exceeds limit ({total_size:.2f} MB > {MAX_TOTAL_SIZE_MB} MB)")
        
        # Keep files up to size limit
        size_limited_files = []
        current_size = 0
        
        for file_path in valid_files:
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            if current_size + file_size <= MAX_TOTAL_SIZE_MB:
                size_limited_files.append(file_path)
                current_size += file_size
            else:
                logger.info(f"Skipping {file_path} due to size limit")
                
        valid_files = size_limited_files
        total_size = current_size
        logger.info(f"Reduced to {len(valid_files)} files (total size: {total_size:.2f} MB)")
    
    # Find potentially missing modules
    logger.info("Analyzing imports and dependencies...")
    missing_modules = find_missing_modules(valid_files)
    
    # Generate project summary
    logger.info("Generating project summary...")
    project_summary = get_project_summary()
    
    # Determine if we need to split into multiple files
    num_chunks = 1
    if CHUNK_FILES and total_size > MAX_TOTAL_SIZE_MB:
        num_chunks = int(total_size / MAX_TOTAL_SIZE_MB) + 1
        files_per_chunk = len(valid_files) // num_chunks
        logger.info(f"Splitting output into {num_chunks} files")
    
    # Write content to output file(s)
    current_chunk = 1
    files_written = 0
    
    def get_output_filename(chunk=None):
        if chunk and chunk > 1:
            base, ext = os.path.splitext(output_file)
            return f"{base}_{chunk}{ext}"
        return output_file
    
    logger.info(f"Writing to {get_output_filename(current_chunk)}...")
    with open(get_output_filename(current_chunk), 'w', encoding='utf-8') as f:
        # Write summary information
        f.write("# Project Context for LLMs\n\n")
        
        # Write Git info if available
        if git_info["is_git_repo"]:
            f.write("## Repository Information\n")
            f.write(f"Remote URL: {git_info['remote_url']}\n")
            f.write(f"Branch: {git_info['current_branch']}\n")
            f.write(f"Last commit: {git_info['last_commit']}\n\n")
        
        # Write project summary
        f.write("## Project Summary\n")
        f.write(f"Total files: {project_summary['total_files']}\n")
        f.write(f"Total lines of code: {project_summary['total_lines']}\n")
        
        if 'frameworks' in project_summary and project_summary['frameworks']:
            f.write(f"\nFrameworks: {', '.join(project_summary['frameworks'])}\n")
        
        f.write("\nFile types:\n")
        for ext, count in list(project_summary['file_counts_by_type'].items())[:10]:
            f.write(f"- {ext}: {count} files\n")
            
        f.write("\nTop directories:\n")
        for directory, count in project_summary['top_directories'].items():
            f.write(f"- {directory}: {count} files\n")
        
        # Write completeness analysis
        f.write("\n## Code Completeness\n")
        f.write(f"Overall completeness: {completeness['overall_percentage']}%\n\n")
        
        f.write("Component completeness:\n")
        for section, subsections in completeness['details'].items():
            f.write(f"- {section.capitalize()}:\n")
            for subsection, details in subsections.items():
                f.write(f"  - {subsection}: {details['percentage']}% ({details['found']}/{details['total']})\n")
        
        if completeness['missing_components']:
            f.write("\nMissing components (up to 10):\n")
            for component in completeness['missing_components']:
                f.write(f"- {component}\n")
        
        f.write("\n")
        
        # Write tree structure
        f.write("## Project Structure\n")
        f.write("```\n")
        f.write(tree_output)
        f.write("```\n\n")
        
        # Write note about potentially missing modules
        if missing_modules:
            f.write("## Potentially Missing Modules\n")
            f.write("These modules are imported but not included in the collected files:\n")
            for module in missing_modules:
                f.write(f"- {module}\n")
            f.write("\n")
        
        # Write code files
        f.write("## Code Files\n\n")
        
        for i, file_path in enumerate(tqdm(valid_files, desc="Collecting files")):
            # Check if we need to start a new chunk
            if CHUNK_FILES and num_chunks > 1 and i > 0 and i % files_per_chunk == 0:
                current_chunk += 1
                f.close()
                logger.info(f"Starting new chunk: {get_output_filename(current_chunk)}...")
                f = open(get_output_filename(current_chunk), 'w', encoding='utf-8')
                f.write(f"# Project Context for LLMs (Part {current_chunk}/{num_chunks})\n\n")
                f.write("## Code Files (Continued)\n\n")
            
            # Write file path as heading
            f.write(f"### {file_path}\n")
            f.write("```\n")
            
            # Write file content using line-by-line reading
            try:
                with open(file_path, 'r', encoding='utf-8') as code_file:
                    # Read and write line by line instead of the whole file at once
                    for line in code_file:
                        f.write(line)
                files_written += 1
            except Exception as e:
                f.write(f"Error reading file: {e}")
                logger.error(f"Error reading {file_path}: {e}")
                
            f.write("\n```\n\n")
    
    # Create a manifest file if using multiple chunks
    if num_chunks > 1:
        manifest = {
            "total_chunks": num_chunks,
            "total_files": len(valid_files),
            "files_written": files_written,
            "total_size_mb": round(total_size, 2),
            "chunk_files": [get_output_filename(i) for i in range(1, num_chunks + 1)],
            "collection_time": round(time.time() - start_time, 2),
            "completeness": {
                "overall_percentage": completeness['overall_percentage'],
                "missing_components_count": len(completeness['missing_components'])
            }
        }
        
        manifest_path = os.path.join(output_dir or '.', "context_manifest.json")
        logger.info(f"Writing manifest to {manifest_path}...")
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Code collection complete! {files_written} files written to {output_file}")
    logger.info(f"Total size: {total_size:.2f} MB, Collection time: {elapsed_time:.2f} seconds")
    
    return {
        "output_file": output_file,
        "files_collected": files_written,
        "total_size_mb": round(total_size, 2),
        "collection_time": round(elapsed_time, 2),
        "completeness": completeness['overall_percentage']
    }

# Add this code to call the collect_code function when the script is run directly
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect code context for LLMs")
    parser.add_argument("--output", "-o", default="context_for_LLMs.txt", help="Output file name")
    parser.add_argument("--output-dir", "-d", help="Output directory")
    parser.add_argument("--max-file-size", "-m", type=int, default=5, help="Maximum file size in MB")
    parser.add_argument("--max-total-size", "-t", type=int, default=100, help="Maximum total size in MB")
    parser.add_argument("--no-chunk", action="store_true", help="Disable chunking large output")
    
    args = parser.parse_args()
    
    # Set global configuration based on arguments
    global MAX_FILE_SIZE_MB, MAX_TOTAL_SIZE_MB, CHUNK_FILES
    MAX_FILE_SIZE_MB = args.max_file_size
    MAX_TOTAL_SIZE_MB = args.max_total_size
    CHUNK_FILES = not args.no_chunk
    
    result = collect_code(args.output, args.output_dir)
    print(f"\nCollection completed successfully!")
    print(f"Files collected: {result['files_collected']}")
    print(f"Total size: {result['total_size_mb']} MB")
    print(f"Collection time: {result['collection_time']} seconds")
    print(f"Code completeness: {result['completeness']}%")
    print(f"Output file: {result['output_file']}")