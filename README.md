DevGuard — The AI System Architect

Built for AIBoomi Startup Weekend 2026

“Don’t just check your code. Architect it.”

DevGuard is an AI-powered architectural reasoning system that helps developers understand how their codebase actually works, identify hidden dependencies, and predict the blast radius of changes before they break production.

Unlike linters or autocomplete tools, DevGuard operates at the system level, not the line level.

⸻

Why DevGuard Exists

Modern codebases fail not because of syntax errors, but because of silent architectural breakage.

Developers constantly ask:
	•	If I change this model, what else breaks?
	•	Why did this frontend component crash after a backend refactor?
	•	Where is the actual boundary between services?

Existing tools fall short:
	•	Linters → syntax & style only
	•	Copilot / ChatGPT → write code without system awareness
	•	Docs → outdated the moment code changes

DevGuard fills this gap by modeling your codebase as a graph, not text.

⸻

What DevGuard Does

Core Capabilities
	1.	System Topology Mapping
	•	Builds a dependency graph across the stack
	•	Frontend ↔ Backend ↔ Data models
	•	Visualizes real connections, not assumed ones
	2.	Blast Radius Simulation
	•	Simulate a change like:
“Rename user_id to uuid”
	•	DevGuard predicts which files and components will be impacted
	•	Happens before code is written or deployed
	3.	Architectural Integrity Checks
	•	Circular dependencies
	•	God objects (files with excessive coupling)
	•	Orphaned / dead code
	•	Production-readiness issues (debug flags, unsafe patterns)
	4.	Explainable AI Reasoning
	•	AI does not guess structure
	•	It explains findings based on deterministic analysis
	•	Clear “why this is risky” explanations

⸻

System Architecture

DevGuard follows a hybrid intelligence model:

Deterministic Layer (Source of Truth)
	•	Abstract Syntax Trees (AST)
	•	Dependency graphs
	•	Explicit imports, routes, schemas

AI Layer (Reasoning & Explanation)
	•	Explains risks
	•	Suggests refactors
	•	Translates graphs into human insight

This avoids hallucinations and keeps trust high.

⸻

Technology Stack

Frontend (Visualization & UX)
	•	Framework: Next.js (App Router)
	•	Styling: Tailwind CSS
	•	Visualization: react-force-graph-2d
	•	Icons: Lucide React

Backend (Core Engine)
	•	Framework: FastAPI (Python)
	•	Server: Uvicorn
	•	Graph Engine: NetworkX
	•	Static Analysis: Python ast
	•	AI Integration: LLMs (for explanation, not structure)

GitHub Integration
	•	GitHub App (CLI Helper)
	•	Authenticates securely
	•	Fetches private & public repos
	•	Normalizes code into clean documents
	•	Sends data to DevGuard Core via API key

The GitHub App is intentionally not a server or webhook listener in MVP.

⸻

Security & Access Model
	•	GitHub access via GitHub App (scoped, revocable)
	•	DevGuard ingestion protected by API key
	•	No GitHub tokens are shared with DevGuard Core
	•	Private repositories fully supported

⸻

Repository Structure

devguard/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── graph_engine.py      # Dependency graph logic
│   ├── analysis/
│   │   ├── ast_parser.py
│   │   ├── integrity_checks.py
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── styles/
│   └── package.json
│
├── devguard-github-app/
│   ├── github_auth.py       # GitHub App helper (CLI)
│   ├── repo_ingest.py       # Normalization layer
│   └── main.py              # Guardrail (not a server)
│
└── README.md


⸻

Running DevGuard Locally

Prerequisites
	•	Python 3.10+
	•	Node.js 18+
	•	GitHub App credentials (for ingestion)

⸻

Backend Setup (DevGuard Core)

cd backend
python -m venv venv
source venv/bin/activate   # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

Backend will run at:

http://localhost:8000


⸻

Frontend Setup

cd frontend
npm install
npm run dev

Frontend will run at:

http://localhost:3000


⸻

GitHub App Ingestion

cd devguard-github-app
python github_auth.py

What this does:
	•	Authenticates GitHub App
	•	Fetches repo contents
	•	Normalizes files
	•	Sends them to DevGuard Core (if running)

If DevGuard Core is not running, ingestion exits gracefully.

⸻

Demo Capabilities

In the demo you can:
	•	View the system dependency graph
	•	Select a file and see its impact radius
	•	Detect architectural smells automatically
	•	Understand risk via AI explanations

⸻

Known Limitations (MVP)
	•	No CI/CD blocking yet
	•	No webhook-based auto updates
	•	No large-scale monorepo optimization
	•	No vector embeddings (intentional)

These are planned, not missing by accident.

⸻

Roadmap

Near-Term
	•	Incremental analysis (diff-based)
	•	PR-level blast radius
	•	Better contract detection

Long-Term
	•	GitHub Actions integration
	•	Policy enforcement gates
	•	Selective embeddings for explanation
	•	Enterprise self-hosted deployments

⸻

Why This Is Different

DevGuard is not:
	•	a linter
	•	an autocomplete tool
	•	a code generator

DevGuard is:

A thinking layer that helps engineers reason about systems safely.

⸻

Built At

AIBoomi Startup Weekend 2026
24 hours. One idea. One working MVP.

⸻

License

MIT License
