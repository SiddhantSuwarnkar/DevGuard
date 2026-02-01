from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil

# --- FIXED IMPORTS (MATCHING YOUR "app" FOLDER STRUCTURE) ---
from app.services.git_service import GitService
from app.core.graph_engine import GraphEngine       # Feature 1
from app.core.advisor import IntentAdvisor          # Feature 2
from app.core.integrity import SystemIntegrity      # Feature 3
from app.core.simulator import BlastRadiusSimulator # Feature 4
from app.core.auditor import SystemAuditor          # Feature 5

API_KEY = os.getenv("DEVGUARD_API_KEY", "devguard_local_key")
app = FastAPI()

# Allow React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL STATE ---
CURRENT_REPO_PATH = "temp_repo"
graph_engine = None

# --- DATA MODELS ---
class AnalyzeRequest(BaseModel):
    repo_url: str

class IntentRequest(BaseModel):
    intent: str

class ImpactRequest(BaseModel):
    target_file: str
    intent: str

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "active", "version": "2.1 (Nested Structure)"}

# 1. ANALYZE (Step 1)
@app.post("/api/analyze")
async def analyze_repo(request: AnalyzeRequest):
    global graph_engine
    
    if os.path.exists(CURRENT_REPO_PATH): 
        try:
            shutil.rmtree(CURRENT_REPO_PATH)
        except PermissionError:
            pass 
    
    GitService.clone_repo(request.repo_url, CURRENT_REPO_PATH)
    
    graph_engine = GraphEngine(CURRENT_REPO_PATH)
    G = graph_engine.build_graph() 
    
    return {"status": "analyzed", "nodes": G.number_of_nodes()}

@app.get("/api/graph")
async def get_graph():
    if not graph_engine: return {"nodes": [], "edges": []}
    return graph_engine.get_graph_data()

# 2. INTENT ADVISOR (Step 2)
@app.post("/api/intent")
async def analyze_intent(request: IntentRequest):
    if not graph_engine: raise HTTPException(400, "Analyze repo first")
    advisor = IntentAdvisor(graph_engine)
    return advisor.analyze_intent(request.intent)

# 3. INTEGRITY CHECKS (Step 3)
@app.get("/api/integrity")
async def check_integrity():
    if not graph_engine: raise HTTPException(400, "Analyze repo first")
    integrity = SystemIntegrity(graph_engine)
    return integrity.run_checks()

# 4. BLAST RADIUS (Step 4)
@app.post("/api/impact")
async def calculate_impact(request: ImpactRequest):
    if not graph_engine: raise HTTPException(400, "Analyze repo first")
    simulator = BlastRadiusSimulator(graph_engine)
    # UPDATED: Passing 'intent' so AI knows if it's a Rename vs Logic Change
    return simulator.simulate_change(request.target_file, request.intent)

# 5. READINESS AUDIT (Step 5)
@app.get("/api/readiness")
async def check_readiness():
    if not graph_engine: raise HTTPException(400, "Analyze repo first")
    auditor = SystemAuditor(graph_engine)
    return auditor.run_audit()



@app.get("/health")
def health():
    return {"status": "ok"}


class GitHubIngestRequest(BaseModel):
    repo: dict
    files: list

from fastapi import HTTPException

@app.post("/api/ingest/github")
async def ingest_from_github(payload: dict):
    print("🔥 /api/ingest/github HIT")

    files = payload.get("files", [])
    if not files:
        raise HTTPException(status_code=400, detail="No files received")

    # Build file_data dict expected by GraphEngine
    file_data = {
        f["path"]: f.get("content", "")
        for f in files
        if "path" in f
    }

    print("Files received:", len(file_data))

    global graph_engine
    graph_engine = GraphEngine(repo_path="github_ingest")

    G, tech_report = graph_engine.build_graph(file_data)

    print("Graph built successfully")
    print("Nodes:", len(G.nodes))
    print("Edges:", len(G.edges))

    return {
        "status": "ingested",
        "files_received": len(file_data),
        "nodes": len(G.nodes),
        "edges": len(G.edges),
        "tech_stack": tech_report,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)