# 🛡️ DevGuard: Your Intelligent AI Architect

> **Built for AIBoomi Startup Weekend 2026**

DevGuard is an intelligent AI agent that acts as a "Senior Engineer" for your codebase. It maps your entire system architecture, analyzes hidden dependencies, and predicts the "blast radius" of code changes before they happen.

---

## 🚀 Project Overview

### The Problem
In modern software development, systems are complex and tightly coupled. Developers often hesitate to refactor code because they ask: **"If I change this variable here, what breaks over there?"**
* Documentation is always out of date.
* Static analysis tools miss cross-stack dependencies (e.g., Frontend API calls matching Backend Endpoints).
* Architectural debt (Circular dependencies, God objects) accumulates silently.

### The Solution
**DevGuard** solves this by treating your codebase as a Knowledge Graph, not just text files.
1.  **Visualizes Topology:** Automatically maps how frontend components, backend services, and databases connect.
2.  **Predicts Impact:** Simulates code changes (like renaming an API field) and warns you which frontend components will crash.
3.  **Enforces Integrity:** continuously scans for architectural smells (cycles, god objects) and production readiness risks (secrets, debug flags).

---

## 🛠️ Technology Stack

We built DevGuard using a modern, graph-based architecture:

### Frontend (Visualization & UI)
* **Framework:** Next.js (App Router)
* **Styling:** Tailwind CSS (Glassmorphism & Clean UI)
* **Visualization:** `react-force-graph-2d` for the interactive system map.
* **Icons:** Lucide React.

### Backend (The Brain)
* **Framework:** FastAPI (Python) & Uvicorn.
* **Graph Engine:** NetworkX (Builds the Dependency Graph).
* **Analysis:** Python `ast` module (Abstract Syntax Trees) for deep code parsing.
* **AI Integration:** Large Language Models (LLMs) to explain risks and suggest refactors.

---

## 🎥 Product Demo

> **[🔴 WATCH THE DEMO VIDEO HERE]** > *(Replace this text with your YouTube/Loom link or a link to your hosted Vercel app)*

### Key Features Showcased:
1.  **System Topology Map:** Interactive visualization of the codebase.
2.  **Blast Radius Simulator:** Typing "Rename user_id" shows exactly which 5 files will break.
3.  **Integrity Dashboard:** detecting "God Objects" and Circular Dependencies.

---

## ⚙️ How to Run Locally

If you want to spin up the AI Architect on your own machine:

### 1. Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
