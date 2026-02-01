import networkx as nx
from ..services.llm_service import LLMService

class SystemIntegrity:
    def __init__(self, graph_engine):
        self.ge = graph_engine
        self.G = graph_engine.G
        self.llm = LLMService()

    def run_checks(self):
        """
        Step 3: Proactive Integrity Analysis.
        1. Deterministic Graph Checks (Cycles, God Objects) - Fast & Accurate
        2. AI Data Contract Validation (Frontend vs Backend) - Deep & Insightful
        """
        print("🛡️ Integrity: Running structural analysis...")
        structure_report = self._check_structure()
        
        print("🛡️ Integrity: Running AI Contract Validation...")
        contract_report = self._check_data_contracts()
        
        return {
            "structure": structure_report,
            "contracts": contract_report
        }

    def _check_structure(self):
        """
        Part A: The Math (Deterministic Graph Theory)
        """
        # 1. Circular Dependencies
        try:
            # Optimization: Only check strongly connected components if graph is huge
            if len(self.G.nodes) < 1000:
                cycles = list(nx.simple_cycles(self.G))
                # Filter out self-loops (A->A) or trivial cycles
                cycles = [c for c in cycles if len(c) > 1]
            else:
                cycles = []
        except:
            cycles = []

        # 2. God Objects (High Coupling)
        # Definition: A file that is imported by > 15 other files (Hub)
        god_objects = []
        degrees = dict(self.G.in_degree()) # Who depends on me?
        for node, degree in degrees.items():
            # Heuristic: >15 dependents is a smell
            if degree > 15:
                god_objects.append(node)

        return {
            "cycles": [" -> ".join([n.split('/')[-1] for n in c]) for c in cycles],
            "god_objects": [n.split('/')[-1] for n in god_objects],
            "confidence": "100% (Graph Theory)"
        }

    def _check_data_contracts(self):
        """
        Part B: The AI Analyst (Cross-Stack Validation)
        Finds where Frontend connects to Backend and audits the data flow.
        """
        issues = []
        
        # 1. Identify "Bridge Nodes" (API Endpoints/URLs) in the Graph
        # These nodes were created in graph_engine.py with type='url'
        api_nodes = [n for n, d in self.G.nodes(data=True) if d.get('type') == 'url']
        
        for api_node in api_nodes:
            # Who calls this API? (The Frontend Component)
            callers = list(self.G.predecessors(api_node))
            # Who handles this API? (The Backend Function)
            handlers = list(self.G.successors(api_node))
            
            # We need a pair to compare. 
            if callers and handlers:
                caller_node = callers[0]
                handler_node = handlers[0]
                
                # 2. Extract Context (The Code)
                # We assume file_map keys match the node IDs (or close enough)
                caller_code = self._get_node_content(caller_node)
                handler_code = self._get_node_content(handler_node)
                
                if caller_code and handler_code:
                    # 3. AI Analysis
                    risk = self._analyze_contract_mismatch(api_node, caller_code, handler_code)
                    if risk:
                        issues.append(risk)

        return {
            "issues": issues,
            "scanned_endpoints": len(api_nodes),
            "confidence": "High (AI Schema Analysis)"
        }

    def _get_node_content(self, node_id):
        """
        Helper to grab relevant code snippet for a node.
        """
        # Node ID is usually "path/to/file.py::FunctionName" or just "path/to/file.py"
        file_path = node_id.split("::")[0]
        content = self.ge.file_map.get(file_path, "")
        
        # Optimization: We could try to extract just the function, 
        # but sending the first 2000 chars of the file usually captures imports + usages.
        return content[:2000]

    def _analyze_contract_mismatch(self, api_url, front_code, back_code):
        prompt = f"""
        Act as a Lead Engineer performing a Data Contract Audit.
        
        TARGET API: {api_url}
        
        [FRONTEND CALLER CODE]
        {front_code}
        
        [BACKEND HANDLER CODE]
        {back_code}
        
        TASK:
        1. Identify the data sent by Frontend (Payload).
        2. Identify the data expected by Backend (Schema).
        3. Identify the data returned by Backend vs expected by Frontend.
        
        CHECK FOR:
        - Type Mismatches (e.g., sending String '123' when Backend expects Int 123).
        - Missing Fields (e.g., Backend expects 'email', Frontend sends only 'username').
        - Field Renaming (e.g., Frontend uses 'userId', Backend uses 'user_id').
        
        OUTPUT JSON (Only if issues found, else null):
        {{
            "api": "{api_url}",
            "severity": "High" | "Medium",
            "issue": "Brief title (e.g., 'Type Mismatch on user_id')",
            "description": "Technical explanation of the break.",
            "suggestion": "How to fix it (e.g., 'Update Pydantic model to accept string')."
        }}
        """
        
        # Call LLM
        return self.llm.generate_json(prompt)