import networkx as nx
import json
from ..services.llm_service import LLMService

class BlastRadiusSimulator:
    def __init__(self, graph, model):
        self.G = graph
        self.llm = model

    def identify_surface_area(self, target_file):
        """
        Identifies the 'Impact Surface' (Direct Dependencies).
        Returns a list of files that directly import or call the target file.
        """
        impacted = set()
        # Find all nodes belonging to this file (functions, classes, or the file itself)
        file_nodes = [n for n in self.G.nodes if str(n).startswith(f"{target_file}")]
        if target_file in self.G: file_nodes.append(target_file)

        for node in file_nodes:
            if node in self.G:
                # Find predecessors (who calls me?)
                for p in self.G.predecessors(node):
                    p_file = p.split("::")[0] if "::" in str(p) else str(p)
                    # Don't list the file itself as an external dependency
                    if p_file != target_file:
                        impacted.add(p_file)
        return list(impacted)

    def assess_risk(self, target_file, intent, dependents, file_contents):
        """
        Evaluates the risk of breaking contracts (interfaces, APIs, props).
        Does NOT predict runtime behavior.
        """
        if not dependents: return None

        # Build context from dependent files (limited to save tokens)
        context = ""
        for dep in dependents[:3]: 
            content = file_contents.get(dep, '')[:1500]
            context += f"\n--- DEPENDENT: {dep} ---\n{content}\n"

        prompt = f"""
        Act as a Technical Lead reviewing a proposed code change.
        
        TARGET FILE: '{target_file}'
        CHANGE INTENT: "{intent}"
        
        DEPENDENT FILES (Callers/Importers):
        {context}
        
        TASK:
        Assess the risk of breaking Data Contracts (Function signatures, API schemas, Prop types).
        Do NOT predict functionality or runtime logic. Focus strictly on Interface Compatibility.
        
        Output JSON:
        {{
            "risk_level": "High/Medium/Low",
            "potential_breaks": [
                "Specific risk (e.g., 'Renaming user_id breaks UserProfile.tsx which expects 'user_id'')"
            ],
            "mitigation_steps": [
                "Specific fix (e.g., 'Update UserProfile.tsx interface to match new schema')"
            ]
        }}
        """
        return self.llm.generate_json(prompt)