import re
import ast

class SystemAuditor:
    def __init__(self, graph_engine):
        # We access the file content map from the graph engine
        self.file_map = graph_engine.file_map

    def run_audit(self):
        """
        Executes the 6 Static Analysis Checks (Items 5-10).
        These checks do NOT require the graph, just file parsing.
        """
        violations = []
        
        # We iterate through every file in the system
        for filename, content in self.file_map.items():
            # Skip irrelevant files (tests, venv, node_modules)
            if self._is_ignored(filename):
                continue

            # Check 5: Hardcoded Keys
            self._check_secrets(filename, content, violations)
            
            # Check 6: Debug Mode
            self._check_debug_mode(filename, content, violations)
            
            # Check 7: Allowed Hosts
            self._check_allowed_hosts(filename, content, violations)
            
            # Check 8: Unpinned Dependencies
            self._check_dependencies(filename, content, violations)
            
            # Check 9: Technical Debt (TODOs)
            self._check_tech_debt(filename, content, violations)
            
            # Check 10: Console Logging
            self._check_logging(filename, content, violations)

        return {"violations": violations}

    def _is_ignored(self, filename):
        return any(x in filename for x in ['test', 'spec', 'venv', 'node_modules', '.git', 'migration'])

    # --- THE 6 STATIC CHECKS ---

    def _check_secrets(self, fname, content, issues):
        """Check 5: Regex for Keys (Confidence: 100%)"""
        patterns = [
            (r'(?i)API_KEY\s*=\s*[\'"][a-zA-Z0-9_\-]{20,}[\'"]', "Hardcoded API Key"),
            (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID"),
            (r'sk_live_[0-9a-zA-Z]{24}', "Stripe Live Key"),
            (r'ghp_[0-9a-zA-Z]{36}', "GitHub Token"),
        ]
        for pattern, label in patterns:
            if re.search(pattern, content):
                issues.append({
                    "severity": "CRITICAL",
                    "file": fname,
                    "rule": label,
                    "message": "Never commit real secrets to version control.",
                    "confidence": "100% (Pattern Match)"
                })

    def _check_debug_mode(self, fname, content, issues):
        """Check 6: Django/Flask Debug Mode (Confidence: 100%)"""
        if fname.endswith(('settings.py', '.env', 'config.py')):
            if re.search(r'DEBUG\s*=\s*True', content):
                issues.append({
                    "severity": "CRITICAL",
                    "file": fname,
                    "rule": "Debug Mode Enabled",
                    "message": "Production apps must have DEBUG=False to prevent stack trace leaks.",
                    "confidence": "100% (Configuration)"
                })

    def _check_allowed_hosts(self, fname, content, issues):
        """Check 7: Permissive Security Configs (Confidence: 100%)"""
        if re.search(r'ALLOWED_HOSTS\s*=\s*\[[\'"]\*[\'"]\]', content):
            issues.append({
                "severity": "HIGH",
                "file": fname,
                "rule": "Insecure Host Config",
                "message": "ALLOWED_HOSTS=['*'] allows Host Header attacks.",
                "confidence": "100% (Configuration)"
            })
        if re.search(r'CORS_ORIGIN_ALLOW_ALL\s*=\s*True', content):
            issues.append({
                "severity": "HIGH",
                "file": fname,
                "rule": "Insecure CORS",
                "message": "Allowing all CORS origins is a security risk.",
                "confidence": "100% (Configuration)"
            })

    def _check_dependencies(self, fname, content, issues):
        """Check 8: Unpinned Dependencies (Confidence: 100%)"""
        if fname.endswith('requirements.txt'):
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '==' not in line:
                    issues.append({
                        "severity": "MEDIUM",
                        "file": fname,
                        "rule": "Unpinned Dependency",
                        "message": f"Library '{line}' has no version. Builds may break in future.",
                        "confidence": "100% (Manifest Analysis)"
                    })
        elif fname.endswith('package.json'):
             if re.search(r'"[\w\-]+":\s*"\^', content): # matches "^1.0.0"
                 issues.append({
                    "severity": "LOW",
                    "file": fname,
                    "rule": "Loose Dependency (^)",
                    "message": "Using caret (^) versions can introduce breaking changes.",
                    "confidence": "100% (Manifest Analysis)"
                })

    def _check_tech_debt(self, fname, content, issues):
        """Check 9: TODO/FIXME markers (Confidence: 100%)"""
        # We limit to 1 per file to avoid spamming the report
        if re.search(r'#\s*(TODO|FIXME|HACK)', content) or re.search(r'//\s*(TODO|FIXME|HACK)', content):
            issues.append({
                "severity": "LOW",
                "file": fname,
                "rule": "Technical Debt",
                "message": "Leftover TODO/FIXME markers found. Verify before shipping.",
                "confidence": "100% (Pattern Match)"
            })

    def _check_logging(self, fname, content, issues):
        """Check 10: Print/Console statements (Confidence: 100%)"""
        if fname.endswith('.py'):
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                        issues.append({
                            "severity": "WARNING",
                            "file": fname,
                            "rule": "Print Statement",
                            "message": "Use logger.info() instead of print() for production logs.",
                            "confidence": "100% (AST Analysis)"
                        })
                        break # Only report once per file
            except: pass
        
        elif fname.endswith(('.js', '.ts', '.tsx')):
            if 'console.log(' in content:
                issues.append({
                    "severity": "WARNING",
                    "file": fname,
                    "rule": "Console Log",
                    "message": "Remove console.log() to avoid browser performance issues.",
                    "confidence": "100% (Pattern Match)"
                })