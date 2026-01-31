import os
from github import Github, GithubException

class GitService:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        # Initialize GitHub client (Auth or Public)
        self.client = Github(self.token) if self.token else Github()
        
        # Filter settings
        self.IGNORED_DIRS = {'node_modules', 'venv', 'env', '.git', '__pycache__', 'dist', 'build', '.vscode', '.idea'}
        self.ACCEPTED_EXTS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.html', '.css', '.dockerfile', 'Dockerfile'}

    def get_repo_files(self, repo_url):
        """
        Fetches all relevant code files from a repo URL.
        Returns: Dict { 'path/to/file.py': 'content' }
        """
        try:
            # Parse URL to get "user/repo"
            clean_url = repo_url.strip().rstrip("/")
            if clean_url.endswith(".git"): clean_url = clean_url[:-4]
            repo_name = "/".join(clean_url.split("/")[-2:])
            
            repo = self.client.get_repo(repo_name)
            contents = repo.get_contents("")
            file_data = {}
            
            while contents:
                file_content = contents.pop(0)
                
                if file_content.type == "dir":
                    if file_content.name not in self.IGNORED_DIRS:
                        try:
                            contents.extend(repo.get_contents(file_content.path))
                        except: pass # Skip if access denied
                else:
                    # Check extension
                    _, ext = os.path.splitext(file_content.name)
                    # Special case for Dockerfile which has no extension usually
                    if ext in self.ACCEPTED_EXTS or file_content.name == 'Dockerfile':
                        try:
                            # Decode and store
                            file_data[file_content.path] = file_content.decoded_content.decode('utf-8')
                        except:
                            pass # Skip binary files

            if not file_data:
                return {"error": "Repo found, but no supported code files detected."}
            
            return file_data

        except GithubException as e:
            return {"error": f"GitHub API Error: {e.data.get('message')}"}
        except Exception as e:
            return {"error": f"Unexpected Error: {str(e)}"}