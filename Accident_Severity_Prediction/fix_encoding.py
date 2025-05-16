import os
import codecs
import re

def fix_encoding():
    """Fix encoding issues in Python files"""
    print("Fixing encoding issues in Python files...")
    
    # Find all Python files in the current directory and subdirectories
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    for file_path in python_files:
        print(f"Processing {file_path}...")
        
        # Try to read the file with different encodings
        encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'windows-1252']
        content = None
        
        for encoding in encodings_to_try:
            try:
                with codecs.open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"  Successfully read using {encoding} encoding")
                break
            except UnicodeDecodeError:
                print(f"  Failed to read using {encoding} encoding")
                continue
        
        if content is None:
            print(f"  WARNING: Could not read {file_path} with any encoding. Skipping file.")
            continue
        
        # Replace problematic characters
        replacements = {
            'e': 'e', 'e': 'e', 'e': 'e', 'e': 'e',
            'a': 'a', 'a': 'a', 'c': 'c',
            'u': 'u', 'u': 'u', 'u': 'u',
            'i': 'i', 'i': 'i',
            'o': 'o', 'o': 'o',
            'E': 'E', 'E': 'E', 'E': 'E', 'E': 'E',
            'A': 'A', 'A': 'A', 'C': 'C',
            'U': 'U', 'U': 'U', 'U': 'U',
            'I': 'I', 'I': 'I',
            'O': 'O', 'O': 'O'
        }
        
        for old_char, new_char in replacements.items():
            content = content.replace(old_char, new_char)
        
        # Write back the file with UTF-8 encoding
        with codecs.open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Saved {file_path} with UTF-8 encoding")

if __name__ == "__main__":
    fix_encoding()
    print("Encoding fixes complete!")