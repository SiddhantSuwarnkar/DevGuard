import os
import time
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables once at module level
load_dotenv()

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("❌ GOOGLE_API_KEY not found in .env file")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate_json(self, prompt, retries=3):
        """
        Generates content and forces a JSON return. 
        Includes exponential backoff for rate limits.
        """
        wait_time = 2  # Start with 2 seconds wait
        
        for attempt in range(retries):
            try:
                response = self.model.generate_content(prompt)
                return self._clean_json(response.text)
            
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    print(f"⚠️ Rate limit hit. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    wait_time *= 2  # Exponential backoff
                else:
                    print(f"❌ LLM Error: {e}")
                    return None
        
        return None

    def _clean_json(self, text):
        """Helper to extract JSON from Markdown code blocks."""
        try:
            # Remove ```json and ``` wrapping
            clean = text.replace("```json", "").replace("```", "").strip()
            # Try parsing directly
            return json.loads(clean)
        except json.JSONDecodeError:
            # Fallback: Regex extraction if model adds extra text
            match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
            return None