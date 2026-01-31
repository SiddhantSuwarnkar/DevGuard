import networkx as nx
import json
import os
from ..services.llm_service import LLMService

class CodeAdvisor:
    def __init__(self, graph):
        self.G = graph
        self.llm = LLMService()

    # --- 1. INTENT ALIGNMENT (AI-Powered) ---
    def analyze_intent_alignment(self, app_context):
        """
        AI looks at the 'Intent' vs 'Code Summary' to find gaps.
        """
        features = [n.split("::")[-1] for n, d in self.G.nodes(data=True) if d.get('type') in ['function', 'component']]
        summary = ", ".join(features[:200]) 

        prompt = f"""
        Act as a Senior Software Architect.
        USER INTENT: "{app_context}"
        VISIBLE CODE IMPLEMENTATION: [{summary}]
        
        Task: Highlight potential alignment gaps.
        Constraint: Be suggestive, not accusatory. Use phrases like "No evidence found for...".
        
        Output JSON:
        {{
            "alignment_gaps": [
                {{"area": "Category", "observation": "Observed gap", "recommendation": "Verify implementation of X"}}
            ]
        }}
        """
        return self.llm.generate_json(prompt)

    # --- 2. ARCHITECTURAL SMELLS (Graph-Powered) ---
    def check_structure(self):
        """
        Analyzes the Graph for structural smells.
        1. Circular Dependencies (Loops)
        2. God Objects (High Coupling)
        3. Orphans (Dead Code)
        4. Redundancy (API Overlap)
        """
        report = {
            "cycles": [], 
            "god_objects": [], 
            "orphans": [], 
            "redundancy": []
        }
        
        # A. Circular Dependencies
        try:
            if len(self.G.nodes) < 500: # Safety limit for large graphs
                cycles = list(nx.simple_cycles(self.G))
                for cycle in cycles:
                    if len(cycle) > 1:
                        clean = [n.split("::")[-1] for n in cycle]
                        report["cycles"].append(" -> ".join(clean))
        except: pass

        # B. God Objects (High Coupling)
        degrees = dict(self.G.degree())
        if degrees:
            avg = sum(degrees.values()) / len(degrees)
            for node, deg in degrees.items():
                # If a node has >4x average connections and at least 10 links
                if deg > avg * 4 and deg > 10:
                   report["god_objects"].append(f"{node.split('::')[-1]} ({deg} links)")

        # C. Orphans (Dead Code)
        ignored = ['urls.py', 'App.tsx', 'main.py', 'index.js', 'manage.py', 'wsgi.py']
        for node, data in self.G.nodes(data=True):
            if data.get('type') in ['component', 'function', 'class']:
                # Incoming edges that are NOT just 'file contains function'
                callers = [u for u, v, d in self.G.in_edges(node, data=True) if d.get('relation') != 'contains']
                if not callers:
                    fname = os.path.basename(data.get('file', ''))
                    if fname not in ignored and not fname.startswith('test'):
                         report["orphans"].append(node.split('::')[-1])

        # D. Architectural Redundancy (Components using identical APIs)
        comp_api_map = {}
        for node, data in self.G.nodes(data=True):
            if data.get('type') in ['component', 'function']:
                # Find outgoing API calls
                apis = [n for n in self.G.successors(node) if 'API::' in str(n)]
                if apis:
                    # Create a signature of APIs used
                    sig = tuple(sorted(apis))
                    if sig not in comp_api_map: comp_api_map[sig] = []
                    comp_api_map[sig].append(node)
        
        # Check for overlaps
        for apis, nodes in comp_api_map.items():
            if len(nodes) > 1:
                clean_nodes = [n.split("::")[-1] for n in nodes]
                clean_apis = [a.replace("API::", "") for a in apis]
                report["redundancy"].append({
                    "files": clean_nodes,
                    "apis": clean_apis
                })

        return report

    # --- 3. CROSS-STACK INTEGRITY (AI-Powered) ---
    def check_contracts(self, file_data):
        """
        Checks if Frontend calls match Backend handlers.
        """
        issues = []
        for node in self.G.nodes():
            if 'API::' in str(node):
                callers = list(self.G.predecessors(node))
                handlers = list(self.G.successors(node))
                if callers and handlers:
                    # We compare the first caller and handler found
                    src = self._get_code(callers[0], file_data)
                    tgt = self._get_code(handlers[0], file_data)
                    if src and tgt:
                        risk = self._analyze_contract(node, src, tgt)
                        if risk: issues.append(risk)
        return issues

    def _analyze_contract(self, api, front, back):
        prompt = f"""
        Analyze Data Contract for API: {api}
        Frontend Call: {front[:500]}
        Backend Handler: {back[:500]}
        
        Task: Check for Schema Mismatches (e.g. Frontend sends 'id', Backend expects 'uuid').
        If mismatch, Output JSON: {{ "risk": "High", "message": "Technical explanation of mismatch" }}
        else null
        """
        return self.llm.generate_json(prompt)

    def _get_code(self, node, file_data):
        return file_data.get(node.split("::")[0], "")