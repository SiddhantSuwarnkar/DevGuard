import networkx as nx
import os
import json
import ast
from ..services.llm_service import LLMService
from ..services.git_service import GitService  # <--- Import GitService

class GraphEngine:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        # Load files immediately using the service
        self.file_map = GitService.get_repo_files(repo_path)
        
        self.G = nx.DiGraph()
        self.llm = LLMService()
        self.api_knowledge_base = {} 
        self.tech_report = {}
        # Maps ClassName -> NodeID (e.g. "User" -> "backend/models.py::User")
        self.class_index = {} 

    def build_graph(self):
        """
        Builds the graph using the loaded self.file_map.
        No arguments needed anymore.
        """
        print("🏗️  GraphEngine: Starting Hybrid Analysis (AST + LLM)...")
        
        file_data = self.file_map
        
        # 1. Tech Stack Detection
        self._detect_tech_stack(list(file_data.keys()))
        
        # 2. HARD PARSING (AST) - Index Nodes & Definitions
        relevant_files = [] 
        for f, code in file_data.items():
            if self._is_ignored(f): continue
            
            try:
                # Add File Node
                self.G.add_node(f, type='file', label=os.path.basename(f), group=f, info="Source File")
                relevant_files.append(f)
                
                # Analyze Definitions (Classes/Functions)
                if f.endswith('.py'):
                    self._analyze_python_ast(f, code)
                # (Add JS/TS parsing here in Phase 2 if needed)
                
            except Exception as e:
                print(f"⚠️  Parser Error in {f}: {e}")

        # 3. HARD LINKING (AST) - Connect Usages to Definitions
        for f in relevant_files:
            if f.endswith('.py'):
                self._link_python_dependencies(f, file_data[f])

        print(f"✅ GraphEngine: Mapped {len(relevant_files)} files & {len(self.G.nodes)} nodes.")

        # 4. SOFT LINKING (AI Layer) - Identify Implicit Edges (API calls, etc)
        backend_files = {k: v for k, v in file_data.items() if k in relevant_files and k.endswith('.py')}
        frontend_files = {k: v for k, v in file_data.items() if k in relevant_files and k.endswith(('.tsx', '.ts', '.js', '.jsx'))}

        if backend_files:
            self._map_backend_logic(backend_files)

        if frontend_files:
            self._map_frontend_logic(frontend_files)

        return self.G

    def _is_ignored(self, filename):
        ignore_patterns = ['test', 'spec', 'migration', 'config', 'venv', 'node_modules', 'build', 'dist', 'json', 'md', '.git']
        return any(x in filename for x in ignore_patterns)

    # --- AST LOGIC (Deterministic) ---

    def _analyze_python_ast(self, file_path, code):
        """Extracts Classes (Models) and Functions with Docstrings."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                
                # 1. Detect Classes (Likely Models)
                if isinstance(node, ast.ClassDef):
                    node_id = f"{file_path}::{node.name}"
                    
                    # Heuristic: Is it a DB Model?
                    base_classes = [b.id for b in node.bases if isinstance(b, ast.Name)]
                    is_model = any(b in ['BaseModel', 'Model', 'db.Model'] for b in base_classes)
                    node_type = "model" if is_model else "class"
                    
                    # Extract Docstring for Sidebar
                    doc = ast.get_docstring(node) or "No description."
                    
                    self.G.add_node(node_id, type=node_type, label=node.name, group=file_path, info=doc)
                    self.G.add_edge(file_path, node_id, relation="contains")
                    
                    # Register for Linking
                    self.class_index[node.name] = node_id

                # 2. Detect Functions
                elif isinstance(node, ast.FunctionDef):
                    node_id = f"{file_path}::{node.name}"
                    doc = ast.get_docstring(node) or "Function definition."
                    
                    self.G.add_node(node_id, type='function', label=node.name, group=file_path, info=doc)
                    self.G.add_edge(file_path, node_id, relation="contains")

        except SyntaxError:
            pass

    def _link_python_dependencies(self, file_path, code):
        """Connects file usage to specific Class/Model nodes."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # Handle 'from models import User'
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        # Link to specific Class Node if it exists
                        if alias.name in self.class_index:
                            target_node = self.class_index[alias.name]
                            self.G.add_edge(file_path, target_node, relation="imports_model")
        except SyntaxError:
            pass

    # --- LLM LOGIC (Soft Linking) ---

    def _detect_tech_stack(self, file_list):
        candidates = [f for f in file_list if not self._is_ignored(f)]
        file_str = "\n".join(candidates[:100])
        prompt = f"""
        Identify Backend/Frontend frameworks.
        Files: {file_str}
        Output JSON: {{ "backend": "...", "frontend": "...", "missing_files": [] }}
        """
        data = self.llm.generate_json(prompt)
        if data: self.tech_report = data

    def _map_backend_logic(self, files):
        print(f"🤖 GraphEngine: AI analyzing {len(files)} Backend files for connections...")
        
        combined_code = ""
        for name, content in files.items():
            combined_code += f"\n--- FILE: {name} ---\n{content[:3000]}\n"

        prompt = f"""
        Analyze this Python Backend. Map Views, Models, URLs, and INTERNAL CALLS.
        Output strictly valid JSON:
        {{
            "apis": [ 
                {{"url": "api/endpoint", "mapped_to": "path/to/view::function_name"}} 
            ],
            "internal_calls": [ 
                {{"source": "path/to/file::caller_func", "target": "path/to/file::callee_func"}} 
            ]
        }}
        Code:
        {combined_code}
        """
        
        data = self.llm.generate_json(prompt)
        if not data: return

        # Process API Routes
        for api in data.get('apis', []):
            self.api_knowledge_base[api['url']] = api.get('mapped_to')
            url_node = f"API::{api['url']}"
            
            if url_node not in self.G.nodes:
                self.G.add_node(url_node, type='url', label=api['url'], group="Endpoints", info="API Endpoint")
            
            target = self._fuzzy_find_node(api.get('mapped_to'))
            if target:
                self.G.add_edge(url_node, target, relation="routes_to")
                # Link urls.py
                urls_file = next((n for n in self.G.nodes if 'urls.py' in str(n)), None)
                if urls_file:
                    self.G.add_edge(urls_file, url_node, relation="defines")

        # Process Internal Calls
        for call in data.get('internal_calls', []):
            source = self._fuzzy_find_node(call.get('source'))
            target = self._fuzzy_find_node(call.get('target'))
            if source and target and source != target:
                self.G.add_edge(source, target, relation="calls")

    def _map_frontend_logic(self, files):
        print(f"🤖 GraphEngine: AI analyzing {len(files)} Frontend files for connections...")
        
        combined_code = ""
        for name, content in files.items():
            combined_code += f"\n--- FILE: {name} ---\n{content[:3000]}\n"

        api_context = json.dumps(self.api_knowledge_base)

        prompt = f"""
        You are a Frontend Architect.
        Backend APIs available: {api_context}
        Task: Map Components to APIs AND other Components.
        Output strictly valid JSON:
        {{
            "links": [ 
                {{"source": "path/to/file::Component", "target_url": "api/endpoint"}},
                {{"source": "path/to/file::Component", "target_component": "path/to/other::Component"}}
            ]
        }}
        Code:
        {combined_code}
        """

        data = self.llm.generate_json(prompt)
        if not data: return

        for link in data.get('links', []):
            source = self._fuzzy_find_node(link.get('source'))
            if not source: continue

            if 'target_url' in link:
                url_node = f"API::{link['target_url']}"
                if url_node not in self.G.nodes:
                    self.G.add_node(url_node, type='url', label=link['target_url'], group="External", info="External API")
                self.G.add_edge(source, url_node, relation="calls_api")

            elif 'target_component' in link:
                target = self._fuzzy_find_node(link['target_component'])
                if target and target != source:
                    self.G.add_edge(source, target, relation="imports")

    # --- UTILS ---

    def _fuzzy_find_node(self, identifier):
        if not identifier: return None
        if identifier in self.G.nodes: return identifier
        
        suffix = identifier.split("::")[-1]
        matches = []
        for n in self.G.nodes:
            if n.endswith(f"::{suffix}"): return n
            if n.endswith(f"/{suffix}") or n == suffix: matches.append(n)
        
        if matches: return matches[0]
        return None

    def get_graph_data(self):
        nodes = []
        for n in self.G.nodes:
            data = self.G.nodes[n]
            # Ensure 'info' is always present for the sidebar
            nodes.append({
                "id": n,
                "label": data.get("label", n),
                "type": data.get("type", "file"),
                "info": data.get("info", "No details available.") 
            })
            
        links = [{"source": u, "target": v} for u, v in self.G.edges]
        return {"nodes": nodes, "edges": links}