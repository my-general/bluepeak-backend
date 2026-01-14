import os
import shutil
from git import Repo

def extract_code_from_repo(repo_url: str, user_id: str, week: int):
    # 1. SETUP TEMP DIRECTORY
    # Placing it 2 levels up so uvicorn doesn't see it and restart
    parent_dir = os.path.dirname(os.path.dirname(os.getcwd()))
    local_path = os.path.join(parent_dir, f"bluepeak_temp/sub_{user_id}_wk{week}")
    
    # Clean up any leftover files from a failed previous run
    if os.path.exists(local_path):
        shutil.rmtree(local_path, ignore_errors=True)

    try:
        # 2. CLONE REPOSITORY
        # depth=1 for speed; only need the latest code
        Repo.clone_from(repo_url, local_path, depth=1)
        
        extracted_content = []
        # Added .md for context and .tsx/.html for web-dev tracks
        allowed_extensions = ('.py', '.sql', '.js', '.ts', '.tsx', '.html', '.css', '.md') 
        ignore_dirs = {'.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build'}

        token_count_approx = 0
        max_tokens = 80000 # 80k tokens is a safe buffer for Flash models

        # 3. TRAVERSE & EXTRACT
        for root, dirs, files in os.walk(local_path):
            # Modify dirs in-place to prevent os.walk from entering ignored folders
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                if file.endswith(allowed_extensions):
                    file_path = os.path.join(root, file)
                    # Get the path relative to the repo root for better AI context
                    rel_path = os.path.relpath(file_path, local_path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Skip massive logs or minified files (safety cap)
                            if len(content) > 15000: 
                                continue 
                            
                            extracted_content.append(f"--- FILE: {rel_path} ---\n{content}\n")
                            token_count_approx += len(content) // 4
                            
                    except Exception as file_err:
                        print(f"Skipping file {file}: {file_err}")
                        continue
                
                if token_count_approx > max_tokens:
                    break

        # Join everything into a single string for Gemini
        result = "\n".join(extracted_content)
        return result if result.strip() else None

    except Exception as e:
        print(f"🔥 Extraction Error for {repo_url}: {e}")
        return None
        
    finally:
        # 4. CRITICAL CLEANUP
        # We delete the temp folder so your disk doesn't fill up
        if os.path.exists(local_path):
            shutil.rmtree(local_path, ignore_errors=True)
