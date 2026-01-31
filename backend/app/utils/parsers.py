import ast
import re
import os

class CodeParser:
    @staticmethod
    def get_definitions(filename, code):
        """
        Extracts function/class definitions and imports.
        Now includes YOUR optimizations for JS/TS Regex support.
        """
        definitions = []
        imports = []
        
        # 1. Python AST Parsing (Fast & Accurate)
        if filename.endswith('.py'):
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        definitions.append({
                            "name": node.name,
                            "type": "function",
                            "code": ast.get_source_segment(code, node), # Capture source for Duplicates check
                            "lineno": node.lineno
                        })
                    elif isinstance(node, ast.ClassDef):
                        definitions.append({
                            "name": node.name,
                            "type": "class",
                            "code": ast.get_source_segment(code, node),
                            "lineno": node.lineno
                        })
                    elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                        if isinstance(node, ast.Import):
                            for n in node.names: imports.append(n.name)
                        else:
                            module = node.module if node.module else ''
                            for n in node.names: imports.append(f"{module}.{n.name}")
            except:
                pass

        # 2. JS/TS Regex Parsing (Your Optimization)
        elif filename.endswith(('.js', '.jsx', '.ts', '.tsx')):
            # Your regex for functions/consts
            func_pattern = r'(export\s+)?(function|const|class)\s+([a-zA-Z0-9_]+)\s*(=|\()'
            matches = re.findall(func_pattern, code)
            for _, type_kw, name, _ in matches:
                definitions.append({
                    "name": name,
                    "type": "component" if type_kw == 'class' or name[0].isupper() else "function",
                    "code": f"// JS Function {name} (Body extraction requires complex parsing)", 
                    "lineno": 0
                })
                
            # Regex for imports
            import_pattern = r'import\s+.*\s+from\s+[\'"](.+)[\'"]'
            import_matches = re.findall(import_pattern, code)
            for imp in import_matches:
                imports.append(imp)

        return definitions, imports