from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Import your engines (Adjust paths if needed)
from app.services.git_service import GitService
from app.core.graph_engine import GraphEngine
from app.core.auditor import SystemAuditor
from app.core.advisor import CodeAdvisor
from app.core.simulator import BlastRadiusSimulator

load_dotenv()
app = FastAPI()

# Allow React Frontend to talk to this Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- IN-MEMORY CACHE (Replaces Session State) ---
# NOTE: In Phase 2, this will become a Database.
# Structure: { "repo_url": { "graph": G, "files": {...} } }
SESSION_STORE = {}

# --- DATA MODELS ---
class AnalyzeRequest(BaseModel):
    repo_url: str
    intent: str = ""

class ImpactRequest(BaseModel):
    repo_url: str
    target_file: str
    change_intent: str

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "active", "version": "2.0"}

@app.post("/api/analyze")
def analyze_repo(request: AnalyzeRequest):
    """
    1. Clones Repo
    2. Builds Graph
    3. Stores in Memory
    4. Returns Basic Stats
    """
    try:
        git = GitService()
        files = git.get_repo_files(request.repo_url)
        
        if "error" in files:
            raise HTTPException(status_code=400, detail=files['error'])
            
        engine = GraphEngine()
        G, tech_report = engine.build_graph(files)
        
        # Save to Cache
        SESSION_STORE[request.repo_url] = {
            "graph": G,
            "files": files,
            "tech": tech_report,
            "context": request.intent
        }
        
        return {
            "message": "Analysis Complete",
            "file_count": len(files),
            "node_count": len(G.nodes),
            "tech_stack": tech_report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graph/{repo_url_encoded:path}")
def get_graph_data(repo_url_encoded: str):
    """
    Returns nodes and edges for the React Graph Visualization.
    """
    # Simple decode/lookup (in real app, use IDs)
    data = SESSION_STORE.get(repo_url_encoded)
    if not data:
        raise HTTPException(status_code=404, detail="Repo not analyzed yet")
    
    G = data['graph']
    nodes = [{"id": n, "label": d.get('label', n), "type": d.get('type', 'file')} 
             for n, d in G.nodes(data=True)]
    edges = [{"source": u, "target": v, "type": d.get('relation')} 
             for u, v, d in G.edges(data=True)]
    
    return {"nodes": nodes, "edges": edges}

@app.post("/api/audit")
def run_audit(request: AnalyzeRequest):
    data = SESSION_STORE.get(request.repo_url)
    if not data: raise HTTPException(status_code=404, detail="Repo not found")
    
    auditor = SystemAuditor(data['graph'])
    violations = auditor.run_compliance_check(data['files'])
    
    # Also run Structure Check from Advisor
    advisor = CodeAdvisor(data['graph'])
    structure = advisor.check_structure()
    
    return {"violations": violations, "structure": structure}

@app.post("/api/impact")
def run_impact_analysis(request: ImpactRequest):
    data = SESSION_STORE.get(request.repo_url)
    if not data: raise HTTPException(status_code=404, detail="Repo not found")
    
    advisor = CodeAdvisor(data['graph'])
    simulator = BlastRadiusSimulator(data['graph'], advisor.llm)
    
    impacted_files = simulator.identify_surface_area(request.target_file)
    risk_assessment = simulator.assess_risk(
        request.target_file, 
        request.change_intent, 
        impacted_files, 
        data['files']
    )
    
    return {
        "impacted_files": impacted_files,
        "risk_assessment": risk_assessment
    }