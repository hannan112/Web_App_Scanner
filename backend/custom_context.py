import logging
import os
import sys

logger = logging.getLogger(__name__)


def is_binary_file(file_path):
    """Check if a file is binary by reading the first few KB."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(8192)
            if b"\x00" in chunk:
                return True
            try:
                chunk.decode("utf-8")
                return False
            except UnicodeDecodeError:
                return True
    except Exception:
        return True


def should_exclude_file(file_name):
    """Check if file should be excluded based on name or extension."""
    excluded_exts = [
        ".env",
        ".db",
        ".sqlite",
        ".sqlite3",
        ".sql3",
        ".db3",
        ".pyc",
        ".so",
        ".dll",
        ".exe",
        ".bin",
    ]
    return any(file_name.endswith(ext) for ext in excluded_exts)


def is_code_file(filename):
    """Determine if a file is a code file based on extension."""
    code_extensions = [
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".css",
        ".scss",
        ".html",
        ".json",
        ".md",
        ".txt",
        ".yml",
        ".yaml",
        ".xml",
        ".sh",
        ".bat",
        ".conf",
    ]
    return os.path.splitext(filename)[1].lower() in code_extensions


def collect_code_from_modules(base_dir, modules_to_include, output_filename):
    """Collect code from specified modules and save to a file."""
    output_file = os.path.join(base_dir, output_filename)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Collected Backend Source Code\n\n")

        for module in modules_to_include:
            module_path = os.path.join(base_dir, module)
            if not os.path.isdir(module_path):
                logger.warning(f"Module path not found: {module_path}, skipping.")
                continue

            f.write(f"## Module: {module}\n\n")
            f.write("### Directory Tree\n\n```\n")
            for root, dirs, files in os.walk(module_path):
                # Exclude unwanted dirs
                dirs[:] = [
                    d
                    for d in dirs
                    if d not in ["venv", ".git", "__pycache__", "node_modules", ".next"]
                ]
                depth = len(os.path.relpath(root, module_path).split(os.sep))
                indent = "    " * depth
                f.write(f"{indent}{os.path.basename(root)}/\n")
                for file in sorted(files):
                    if should_exclude_file(file) or is_binary_file(
                        os.path.join(root, file)
                    ):
                        continue
                    f.write(f"{indent}    {file}\n")
            f.write("```\n\n")

            f.write("### Source Code\n\n")
            for root, _, files in os.walk(module_path):
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    if (
                        should_exclude_file(file)
                        or is_binary_file(file_path)
                        or not is_code_file(file)
                    ):
                        continue
                    rel_path = os.path.relpath(file_path, base_dir)
                    f.write(f"#### {rel_path}\n\n```\n")
                    try:
                        with open(file_path, "r", encoding="utf-8") as code_file:
                            f.write(code_file.read())
                    except Exception as e:
                        f.write(f"[Error reading file: {str(e)}]")
                    f.write("\n```\n\n" + "-" * 80 + "\n\n")

    logger.info(f"Code saved to: {output_file}")


def prompt_user_choice():
    """Prompt user for collection choice."""
    print("Choose an option:")
    print("1. Collect entire backend")
    print("2. Collect specific module(s) only")

    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        return "all", []
    elif choice == "2":
        modules_input = input(
            "Enter module names separated by spaces (e.g., scanning auth): "
        ).strip()
        modules = modules_input.split()
        return "partial", modules
    else:
        print("Invalid choice. Please try again.")
        return prompt_user_choice()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    base_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

    mode, modules = prompt_user_choice()

    if mode == "all":
        # Include everything under backend/
        modules_to_include = [
            d
            for d in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, d))
            and d not in ["venv", ".git", "__pycache__", "node_modules", ".next"]
        ]
        output_name = "full_backend_context_code.txt"
    else:
        modules_to_include = modules
        output_name = "selected_modules_context_code.txt"

    collect_code_from_modules(base_dir, modules_to_include, output_name)
