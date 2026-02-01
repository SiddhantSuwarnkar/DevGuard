import json
from ..services.llm_service import LLMService

class IntentAdvisor:
    def __init__(self, graph_engine):
        self.ge = graph_engine
        self.llm = LLMService()

    def analyze_intent(self, user_intent: str):
        """
        Step 2: The Reality Check.
        Compares 'What the user wants' vs 'What the code actually does'.
        """
        
        # 1. Gather Evidence from the Graph (The Reality)
        # We summarize the codebase into a concise context for the LLM
        system_summary = {
            "files": [n for n, d in self.ge.G.nodes(data=True) if d.get('type') == 'file'],
            "models": [d.get('label') for n, d in self.ge.G.nodes(data=True) if d.get('type') == 'model'],
            "apis": [d.get('label') for n, d in self.ge.G.nodes(data=True) if d.get('type') == 'url'],
            "technologies": self.ge.tech_report  # Python, React, etc.
        }

        # 2. Construct the Prompt
        prompt = f"""
        Act as a Senior Software Architect performing a Gap Analysis.

        USER INTENT (The Requirement):
        "{user_intent}"

        ACTUAL IMPLEMENTATION (The Codebase):
        {json.dumps(system_summary, indent=2)}

        TASK:
        Compare the Intent against the Reality.
        1. Identify features mentioned in Intent but missing in Code.
        2. Identify logic that seems incomplete (e.g. Frontend exists, Backend missing).
        3. Assign a CONFIDENCE SCORE to your assessment.

        OUTPUT JSON format:
        {{
            "alignment_score": <0-100>,
            "verdict": "Aligned" | "Partial" | "Misaligned",
            "gaps": [
                {{
                    "feature": "Name of missing feature",
                    "observation": "Explain what is missing (e.g., 'Found Login.tsx but no auth API')",
                    "impact": "Why this matters"
                }}
            ],
            "confidence_score": "High" | "Medium" | "Low",
            "reasoning": "Brief explanation of confidence level (e.g. 'High because no Stripe SDK found')"
        }}
        """

        # 3. Get AI Verdict
        try:
            result = self.llm.generate_json(prompt)
            
            # Fallback if LLM fails
            if not result:
                return self._get_fallback_response()
                
            return result
            
        except Exception as e:
            print(f"⚠️ Intent Advisor Error: {e}")
            return self._get_fallback_response()

    def _get_fallback_response(self):
        return {
            "alignment_score": 0,
            "verdict": "Unknown",
            "gaps": [],
            "confidence_score": "Low",
            "reasoning": "Analysis failed due to LLM timeout."
        }