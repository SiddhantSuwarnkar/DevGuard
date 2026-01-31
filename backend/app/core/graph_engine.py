import networkx as nx
import os
import json
from ..services.llm_service import LLMService
from ..utils.parsers import CodeParser

class GraphEngine:
    def __init__(self):
        self.G = nx.DiGraph()
        self.llm = LLMService()
        self.api_knowledge_base = {} 
        self.tech_report = {}

    def build_graph(self, file_data):
        print("🏗️  GraphEngine: Starting Hybrid Analysis...")
        
        # 1. Tech Stack Detection
        self._detect_tech_stack(list(file_data.keys()))
        
        # 2. HARD PARSING (AST/Regex) - Identify Nodes
        relevant_files = [] 
        for f, code in file_data.items():
            if any(x in f for x in ['test', 'spec', 'migration', 'config', 'venv', 'node_modules', 'build', 'dist', 'json', 'md']):
                continue
                
            defs, imports = CodeParser.get_definitions(f, code)
            if defs:
                relevant_files.append(f)
                self.G.add_node(f, type='file', label=os.path.basename(f), group=f)
                for d in defs:
                    node_id = f"{f}::{d['name']}"
                    self.G.add_node(node_id, type=d['type'], label=d['name'], group=f)
                    self.G.add_edge(f, node_id, relation="contains")

        print(f"   GraphEngine: AST mapped {len(relevant_files)} files & {len(self.G.nodes)} nodes.")

        # 3. SOFT LINKING (AI Layer) - Identify Edges
        backend_files = {k: v for k, v in file_data.items() if k in relevant_files and k.endswith('.py')}
        frontend_files = {k: v for k, v in file_data.items() if k in relevant_files and k.endswith(('.tsx', '.ts', '.js', '.jsx'))}

        if backend_files:
            self._map_backend_logic(backend_files)

        if frontend_files:
            self._map_frontend_logic(frontend_files)

        return self.G, self.tech_report

    def _detect_tech_stack(self, file_list):
        candidates = [f for f in file_list if not any(x in f for x in ['node_modules', 'venv', '.git'])]
        file_str = "\n".join(candidates[:100])
        prompt = f"""
        Identify Backend/Frontend frameworks.
        Files: {file_str}
        Output JSON: {{ "backend": "...", "frontend": "...", "missing_files": [] }}
        """
        data = self.llm.generate_json(prompt)
        if data: self.tech_report = data

    def _map_backend_logic(self, files):
        print(f"   GraphEngine: AI analyzing {len(files)} Backend files for connections...")
        
        # We send more context now to capture internal calls
        combined_code = ""
        for name, content in files.items():
            # Context window optimization: limit large files
            combined_code += f"\n--- FILE: {name} ---\n{content[:3000]}\n"

        # RESTORED FULL PROMPT FROM MAPPER.PY
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

        # 1. Process API Routes (External Edges)
        for api in data.get('apis', []):
            self.api_knowledge_base[api['url']] = api.get('mapped_to')
            url_node = f"API::{api['url']}"
            
            if url_node not in self.G.nodes:
                self.G.add_node(url_node, type='url', label=api['url'], group="Endpoints")
            
            # Find what function this URL maps to
            target = self._fuzzy_find_node(api.get('mapped_to'))
            if target:
                self.G.add_edge(url_node, target, relation="routes_to")
                
                # Also link the urls.py file if possible
                urls_file = next((n for n in self.G.nodes if 'urls.py' in str(n)), None)
                if urls_file:
                    self.G.add_edge(urls_file, url_node, relation="defines")

        # 2. Process Internal Calls (Internal Edges)
        for call in data.get('internal_calls', []):
            source = self._fuzzy_find_node(call.get('source'))
            target = self._fuzzy_find_node(call.get('target'))
            
            if source and target and source != target:
                self.G.add_edge(source, target, relation="calls")

    def _map_frontend_logic(self, files):
        print(f"   GraphEngine: AI analyzing {len(files)} Frontend files for connections...")
        
        combined_code = ""
        for name, content in files.items():
            combined_code += f"\n--- FILE: {name} ---\n{content[:3000]}\n"

        api_context = json.dumps(self.api_knowledge_base)

        # RESTORED FULL PROMPT FROM MAPPER.PY
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

            # Case A: Component calls API
            if 'target_url' in link:
                url_node = f"API::{link['target_url']}"
                if url_node not in self.G.nodes:
                    self.G.add_node(url_node, type='url', label=link['target_url'], group="External")
                self.G.add_edge(source, url_node, relation="calls_api")

            # Case B: Component calls Component (Import/Render)
            elif 'target_component' in link:
                target = self._fuzzy_find_node(link['target_component'])
                if target and target != source:
                    self.G.add_edge(source, target, relation="imports")

    def _fuzzy_find_node(self, identifier):
        """Helper to find a node even if LLM gets the path slightly wrong."""
        if not identifier: return None
        # 1. Exact Match
        if identifier in self.G.nodes: return identifier
        
        # 2. Suffix Match (e.g. LLM says 'views::get_user', Node is 'backend/views.py::get_user')
        suffix = identifier.split("::")[-1]
        
        # 3. File Name Match (e.g. LLM says 'UserProfile', Node is 'frontend/UserProfile.tsx')
        matches = []
        for n in self.G.nodes:
            if n.endswith(f"::{suffix}"): 
                return n
            if n.endswith(f"/{suffix}") or n == suffix: # Component file match
                matches.append(n)
        
        if matches: return matches[0] # Return best guess
        return None