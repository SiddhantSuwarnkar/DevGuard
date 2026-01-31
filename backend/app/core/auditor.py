import os
import re
import ast

class SystemAuditor:
    def __init__(self, graph):
        self.G = graph
        # Pure logic engine. No LLM, no "magic".

    def run_compliance_check(self, file_data):
        """
        Runs the 11 Golden Rules of Readiness.
        These are binary, deterministic signals (Pass/Fail) based on Regex/AST.
        """
        violations = []
        all_files = list(file_data.keys())
        
        # 1. Configuration & Secrets
        self._check_secrets(file_data, violations)
        self._check_debug_mode(file_data, violations)
        self._check_permissive_config(file_data, violations)
        
        # 2. Dependency Hygiene
        self._check_dependencies(file_data, violations)
        self._check_docker(file_data, violations)
        
        # 3. Code Hygiene
        self._check_logging(file_data, violations)
        self._check_todos(file_data, violations)
        self._check_repo_health(all_files, violations)
            
        return violations

    def _check_secrets(self, files, issues):
        patterns = [
            (r'(?i)API_KEY\s*=\s*[\'"][a-zA-Z0-9_\-]{20,}[\'"]', "Hardcoded API Key"),
            (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID"),
            (r'sk_live_[0-9a-zA-Z]{24}', "Stripe Secret Key"),
            (r'ghp_[0-9a-zA-Z]{36}', "GitHub Personal Token")
        ]
        for fname, content in files.items():
            for pattern, label in patterns:
                if re.search(pattern, content):
                    issues.append({"severity": "CRITICAL", "file": fname, "rule": "Hardcoded Secrets", "message": f"Detected potential {label}."})

    def _check_debug_mode(self, files, issues):
        for fname, content in files.items():
            if fname.endswith(('settings.py', '.env')):
                if re.search(r'DEBUG\s*=\s*True', content):
                    issues.append({"severity": "HIGH", "file": fname, "rule": "Debug Mode Enabled", "message": "DEBUG=True leaks stack traces in production."})

    def _check_permissive_config(self, files, issues):
        for fname, content in files.items():
            if re.search(r'ALLOWED_HOSTS\s*=\s*\[[\'"]\*[\'"]\]', content):
                issues.append({"severity": "HIGH", "file": fname, "rule": "Permissive Hosts", "message": "ALLOWED_HOSTS=['*'] is dangerous."})
            if re.search(r'CORS_ORIGIN_ALLOW_ALL\s*=\s*True', content):
                issues.append({"severity": "HIGH", "file": fname, "rule": "Permissive CORS", "message": "CORS allow-all is dangerous."})

    def _check_dependencies(self, files, issues):
        for fname, content in files.items():
            if fname.endswith('requirements.txt'):
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#') and '==' not in line and '>=' not in line:
                        issues.append({"severity": "MEDIUM", "file": fname, "rule": "Unpinned Dependency", "message": f"Library '{line}' has no version."})

    def _check_docker(self, files, issues):
        for fname, content in files.items():
            if fname.endswith('Dockerfile'):
                if re.search(r'FROM\s+[\w\-\/]+:latest', content):
                    issues.append({"severity": "MEDIUM", "file": fname, "rule": "Latest Tag Used", "message": "Using :latest tag makes builds non-reproducible."})

    def _check_logging(self, files, issues):
        for fname, content in files.items():
            if fname.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                            issues.append({"severity": "LOW", "file": fname, "rule": "Console Logging", "message": "Use logger.info() instead of print()."})
                            break 
                except: pass
            elif fname.endswith(('.js', '.ts', '.tsx')):
                if 'console.log(' in content:
                    issues.append({"severity": "LOW", "file": fname, "rule": "Console Logging", "message": "Remove console.log() before production."})

    def _check_todos(self, files, issues):
        for fname, content in files.items():
            if re.search(r'#\s*(TODO|FIXME|HACK)', content) or re.search(r'//\s*(TODO|FIXME|HACK)', content):
                issues.append({"severity": "LOW", "file": fname, "rule": "Technical Debt", "message": "Leftover TODO/FIXME markers found."})

    def _check_repo_health(self, all_files, issues):
        forbidden = ['.env', 'id_rsa', 'master.key', '.DS_Store']
        for f in all_files:
            for bad in forbidden:
                if f.endswith(bad):
                    issues.append({"severity": "CRITICAL", "file": f, "rule": "Sensitive File Committed", "message": f"Never commit '{bad}' to version control."})
        
        if not any(f.lower().startswith('readme') for f in all_files):
             issues.append({"severity": "LOW", "file": "Root", "rule": "Missing Documentation", "message": "No README.md found. Project is undocumented."})