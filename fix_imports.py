"""
Script to fix all import paths from 'app.' to 'backend.app.'
"""

import os
import re

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace 'from app.' with 'from backend.app.'
        updated_content = re.sub(r'from app\.', 'from backend.app.', content)
        
        # Replace 'import app.' with 'import backend.app.'
        updated_content = re.sub(r'import app\.', 'import backend.app.', updated_content)
        
        if content != updated_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"Fixed imports in: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def fix_all_imports():
    """Fix imports in all Python files in the backend directory."""
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    fixed_count = 0
    
    for root, dirs, files in os.walk(backend_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_imports_in_file(file_path):
                    fixed_count += 1
    
    print(f"Fixed imports in {fixed_count} files.")

if __name__ == "__main__":
    fix_all_imports()
