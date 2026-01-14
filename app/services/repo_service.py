import os
import shutil
from git import Repo, GitCommandError

def extract_code_from_repo(repo_url: str, user_id: str, week: int):
    # 1. MOVE TEMP OUTSIDE: Use /tmp or a folder outside your project root
    # This prevents Uvicorn from restarting when it detects the cloned files
    parent_dir = os.path.dirname(os.path.dirname(os.getcwd())) # Goes 2 levels up
    local_path = os.path.join(parent_dir, f"bluepeak_temp/sub_{user_id}_wk{week}")
    
    if os.path.exists(local_path):
        shutil.rmtree(local_path, ignore_errors=True)

    try:
        Repo.clone_from(repo_url, local_path, depth=1)
        
        extracted_content = []
        # Keep this list tight to save tokens
        allowed_extensions = ('.py', '.sql', '.js') 
        ignore_dirs = {'.git', 'node_modules', 'tests', 'venv', 'goldens', 'samples'}

        token_count_approx = 0
        max_tokens = 100000 # Safety cap (well under 250k)

        for root, dirs, files in os.walk(local_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                # ONLY take root files or small files to start
                if file.endswith(allowed_extensions):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Simple check: Don't send massive files
                        if len(content) > 10000: continue 
                        
                        extracted_content.append(f"--- FILE: {file} ---\n{content}\n")
                        token_count_approx += len(content) // 4
                
                if token_count_approx > max_tokens:
                    break

        return "\n".join(extracted_content)

    except Exception as e:
        print(f"Extraction Error: {e}")
        return None
    finally:
        if os.path.exists(local_path):
            shutil.rmtree(local_path, ignore_errors=True)