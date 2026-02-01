import networkx as nx
from ..services.llm_service import LLMService

class BlastRadiusSimulator:
    def __init__(self, graph_engine):
        self.G = graph_engine.G
        self.file_map = graph_engine.file_map
        self.llm = LLMService()

    def simulate_change(self, target_file, intent="Refactoring"):
        """
        Step 4: The Simulation.
        Orchestrates the Graph Traversal + AI Impact Analysis.
        """
        # 1. Identify the Blast Radius (Surface Area)
        # Who imports or calls the target file?
        dependents = self._identify_surface_area(target_file)
        
        # 2. Extract Context for AI
        # We need to show the AI the code that *might* break.
        context = self._build_context(target_file, dependents)
        
        # 3. AI Risk Assessment
        if not dependents:
            return {
                "impacted_files": [],
                "risk_assessment": {
                    "risk_level": "Low",
                    "confidence": "100%",
                    "potential_breaks": ["No direct dependencies found. Safe to modify."],
                    "mitigation_steps": []
                }
            }

        risk_report = self._assess_risk_with_ai(target_file, intent, context, len(dependents))
        
        # Merge results
        return {
            "impacted_files": dependents,
            "risk_assessment": risk_report
        }

    def _identify_surface_area(self, target_file):
        """
        Graph Theory: Find all 'Predecessors' (Reverse Dependencies).
        """
        impacted = set()
        
        # Helper: Find graph nodes that belong to this file
        # (e.g., 'utils.py', 'utils.py::calculate_tax')
        target_nodes = [n for n in self.G.nodes if str(n).startswith(target_file)]
        
        for node in target_nodes:
            # Who calls this node?
            if node in self.G:
                callers = self.G.predecessors(node)
                for caller in callers:
                    # Extract filename from node ID (e.g. 'views.py::get_user' -> 'views.py')
                    caller_file = caller.split("::")[0]
                    
                    # Ignore self-references
                    if caller_file != target_file:
                        impacted.add(caller_file)
                        
        return list(impacted)

    def _build_context(self, target_file, dependents):
        """
        Optimized Context Builder.
        Pulls the Target File code + Snippets of Dependent Files.
        """
        # 1. Get Target Code (Limit size)
        target_code = self.file_map.get(target_file, "")[:1000]
        
        # 2. Get Dependent Code (Limit to top 3 to save tokens)
        dep_context = ""
        for dep in dependents[:3]:
            content = self.file_map.get(dep, "")[:800] # First 800 chars usually contain imports/usage
            dep_context += f"\n--- DEPENDENT FILE: {dep} ---\n{content}\n"
            
        return f"""
        [TARGET FILE CODE]:
        {target_code}
        
        [DEPENDENT FILES SAMPLE]:
        {dep_context}
        """

    def _assess_risk_with_ai(self, target_file, intent, context, dep_count):
        prompt = f"""
        Act as a QA Automation Architect. Perform a Regression Risk Analysis.
        
        SCENARIO:
        Developer wants to modify: '{target_file}'
        Change Intent: "{intent}"
        Total Dependent Files: {dep_count}
        
        CODE CONTEXT (Target + Dependents):
        {context}
        
        TASK:
        Predict what will break in the DEPENDENT files based on the INTENT.
        1. If Intent is "Rename X to Y", look for usages of X in dependents.
        2. If Intent is "Change return type", look for logic expecting the old type.
        
        OUTPUT JSON:
        {{
            "risk_level": "High" | "Medium" | "Low",
            "confidence": "High" | "Medium",
            "potential_breaks": [
                "Technical description of break (e.g. 'auth.py calls login() which is being renamed')"
            ],
            "mitigation_steps": [
                "Actionable fix (e.g. 'Update imports in auth.py')"
            ]
        }}
        """
        return self.llm.generate_json(prompt)