import os
import shutil
import tempfile
from git import Repo, GitCommandError

def extract_code_from_repo(repo_url: str, user_id: str, week: int):
    """
    Clones a GitHub repo into a temp directory, extracts technical files,
    and cleans up immediately to save cloud disk space.
    """
    # 1. Use tempfile to ensure a unique, writable path in Render's /tmp folder
    temp_dir = tempfile.mkdtemp(prefix=f"bp_sub_{user_id}_wk{week}_")
    
    try:
        # 2. Clone with depth=1 (shallow clone) to save time and bandwidth
        Repo.clone_from(repo_url, temp_dir, depth=1)
        
        extracted_content = []
        # technical files allowed for review
        allowed_extensions = ('.py', '.js', '.ts', '.tsx', '.sql', '.md', '.json') 
        # folders to skip to avoid token bloat and irrelevant data
        ignore_dirs = {'.git', 'node_modules', 'tests', 'venv', 'env', '__pycache__'}

        token_count_approx = 0
        max_tokens_cap = 80000  # Conservative cap for Gemini prompt context

        # 3. Walk through the directory
        for root, dirs, files in os.walk(temp_dir):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                if file.endswith(allowed_extensions):
                    file_path = os.path.join(root, file)
                    
                    try:
                        # Open with ignore to prevent crashing on binary or weird encodings
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Skip massive files (e.g., package-lock.json or data dumps)
                            if len(content) > 15000:
                                continue
                            
                            relative_path = os.path.relpath(file_path, temp_dir)
                            extracted_content.append(f"--- File: {relative_path} ---\n{content}\n")
                            
                            # Approximate tokens (4 chars per token)
                            token_count_approx += len(content) // 4
                            
                    except Exception as file_err:
                        print(f"Skipping {file}: {file_err}")
                        continue
                
                # Stop if we hit the token safety limit
                if token_count_approx > max_tokens_cap:
                    break
        
        return "\n".join(extracted_content) if extracted_content else None

    except GitCommandError as git_err:
        print(f"Git Clone Error: {git_err}")
        return None
    except Exception as e:
        print(f"General Extraction Error: {e}")
        return None
    finally:
        # 4. CRITICAL: Clean up the folder after extraction to save disk space on Render
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
