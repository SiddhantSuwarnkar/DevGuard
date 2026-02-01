import os
import shutil
import git  # Requires: pip install gitpython

class GitService:
    @staticmethod
    def clone_repo(repo_url: str, target_dir: str):
        """
        Clones a remote git repository to a local directory.
        Used by main.py to setup the environment for GraphEngine.
        """
        # 1. Clean up existing directory if it exists
        if os.path.exists(target_dir):
            try:
                # Helper to handle Windows read-only files (like .git objects)
                def on_rm_error(func, path, exc_info):
                    os.chmod(path, 0o777)
                    func(path)
                    
                shutil.rmtree(target_dir, onerror=on_rm_error)
            except Exception as e:
                print(f"⚠️ Warning: Could not clean {target_dir}: {e}")

        # 2. Create directory
        os.makedirs(target_dir, exist_ok=True)

        # 3. Clone
        print(f"⬇️ Cloning {repo_url} into {target_dir}...")
        try:
            git.Repo.clone_from(repo_url, target_dir)
            print("✅ Clone successful.")
        except Exception as e:
            # Cleanup on fail
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir, ignore_errors=True)
            raise Exception(f"Failed to clone repo: {str(e)}")

    @staticmethod
    def get_repo_files(target_dir: str):
        """
        Walks the local directory to return a dictionary of {filepath: content}.
        This replaces the old API-based method.
        """
        file_map = {}
        ignored_dirs = {'.git', 'node_modules', 'venv', 'env', '__pycache__', 'dist', 'build'}
        accepted_exts = {'.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.html', '.css', 'Dockerfile', '.dockerfile'}

        for root, dirs, files in os.walk(target_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            
            for file in files:
                _, ext = os.path.splitext(file)
                if ext in accepted_exts or file == 'Dockerfile':
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            # Store relative path as key (e.g., "src/main.py")
                            rel_path = os.path.relpath(full_path, target_dir)
                            file_map[rel_path] = f.read()
                    except Exception:
                        pass # Skip binary or unreadable files
        
        return file_map