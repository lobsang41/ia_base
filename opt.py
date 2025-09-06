import os
import sys
import re
import ast

# Supported file extensions for source code
SUPPORTED_EXTENSIONS = [
    '.py', '.js', '.jsx', '.ts', '.tsx',
    '.cs', '.java', '.c', '.cpp', '.h', '.hpp'
]

# Common names for Python virtual environment directories
VIRTUAL_ENV_DIRS = {'venv', 'env', '.venv'}

def strip_python_comments(code):
    """Strip comments and minify Python code using AST."""
    try:
        tree = ast.parse(code)
        minified = ast.unparse(tree)
        minified = '\n'.join(line for line in minified.splitlines() if line.strip())
        minified = re.sub(r'^( {4})+', lambda m: '\t' * (len(m.group(0)) // 4), minified, flags=re.MULTILINE)
        return minified
    except SyntaxError as e:
        print(f"SyntaxError in Python file: {e}")
        lines = [line.split('#')[0].rstrip() for line in code.splitlines()]
        return '\n'.join(line for line in lines if line.strip())

def strip_c_style_comments(code):
    """Strip C-style comments (// and /* */) and remove blank lines."""
    try:
        code = re.sub(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/', '', code, flags=re.DOTALL)
        code = re.sub(r'//.*', '', code)
        code = '\n'.join(line.strip() for line in code.splitlines() if line.strip())
        code = re.sub(r' +', ' ', code)
        return code
    except Exception as e:
        print(f"Error processing C-style file: {e}")
        return None

def process_file(file_path):
    """Process a single file based on its extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None
    
    print(f"Processing file: {file_path}")
    if ext == '.py':
        optimized = strip_python_comments(code)
    else:
        optimized = strip_c_style_comments(code)
    
    if optimized:
        optimized = '\n'.join(line.strip() for line in optimized.splitlines() if line.strip())
        return optimized
    return None

def main(directory):
    output_file = 'optimized_source.txt'
    files_processed = 0
    try:
        with open(output_file, 'w', encoding='utf-8') as out_f:
            for root, dirs, files in os.walk(directory):
                # Exclude virtual environment directories
                dirs[:] = [d for d in dirs if d not in VIRTUAL_ENV_DIRS]
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, directory)
                    optimized = process_file(file_path)
                    if optimized:
                        out_f.write(f"### File: {rel_path}\n")
                        out_f.write(optimized)
                        out_f.write("\n\n")
                        files_processed += 1
        if files_processed == 0:
            print("No source code files found with supported extensions.")
        else:
            print(f"Optimized source code written to {output_file}. Processed {files_processed} files.")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python this_script.py /path/to/directory")
        sys.exit(1)
    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)
    print(f"Scanning directory: {directory}")
    main(directory)