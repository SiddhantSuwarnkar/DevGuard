import jwt
import time
import requests
from pathlib import Path
from repo_ingest import normalize_files


# ===== CONFIG =====
APP_ID = "2766398"  # <-- your GitHub App ID (from settings)
PRIVATE_KEY_PATH = Path("dev-arch-guard.2026-01-31.private-key.pem")

# ===== DEVGUARD INGESTION CONFIG =====
DEVGUARD_INGEST_URL = "http://192.168.4.160:8000/api/ingest/github"
DEVGUARD_API_KEY = "devguard_local_key"

def who_am_i():
    
    jwt_token = generate_jwt()
    r = requests.get(
        "https://api.github.com/app",
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json"
        }
    )
    print(r.status_code)
    print(r.json())

# ==================

def generate_jwt():
    private_key = PRIVATE_KEY_PATH.read_text()

    payload = {
        "iat": int(time.time()) - 60,
        "exp": int(time.time()) + (10 * 60),
        "iss": APP_ID
    }

    encoded_jwt = jwt.encode(
        payload,
        private_key,
        algorithm="RS256"
    )

    return encoded_jwt


def list_installations():
    jwt_token = generate_jwt()
    url = "https://api.github.com/app/installations"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_installation_access_token(installation_id: int):
    jwt_token = generate_jwt()

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.post(url, headers=headers)
    if response.status_code == 404:
        print(f"Error 404: Installation ID {installation_id} not found. This may mean the installation ID does not belong to this GitHub App or the App was reinstalled.")
    response.raise_for_status()
    return response.json()["token"]

def list_repositories(installation_token: str):
    url = "https://api.github.com/installation/repositories"
    headers = {
        "Authorization": f"token {installation_token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


# --- New function: list_branches ---
def list_branches(installation_token: str, owner: str, repo: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/branches"
    headers = {
        "Authorization": f"token {installation_token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


# --- New helper function: get_branch_commit_sha ---
def get_branch_commit_sha(installation_token: str, owner: str, repo: str, branch: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
    headers = {
        "Authorization": f"token {installation_token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["commit"]["sha"]


# --- New helper function: get_repo_tree ---
def get_repo_tree(installation_token: str, owner: str, repo: str, commit_sha: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{commit_sha}?recursive=1"
    headers = {
        "Authorization": f"token {installation_token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["tree"]

# --- New helper function: get_blob_content ---
import base64

def get_blob_content(installation_token: str, owner: str, repo: str, blob_sha: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{blob_sha}"
    headers = {
        "Authorization": f"token {installation_token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    # GitHub returns blob content base64-encoded
    content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
    return content

# --- DevGuard ingestion helper ---
def send_to_devguard(documents):
    headers = {
        "Authorization": f"Bearer {DEVGUARD_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "repo": {
            "name": documents[0]["repo"] if documents else "",
            "branch": documents[0]["branch"] if documents else "",
            "commit": documents[0]["commit"] if documents else ""
        },
        "files": [
            {
                "path": d["path"],
                "content": d["content"],
                "language": d["language"]
            }
            for d in documents
        ]
    }

    try:
        response = requests.post(
            DEVGUARD_INGEST_URL,
            json=payload,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        print("⚠️ DevGuard core is not running at", DEVGUARD_INGEST_URL)
        print(f"✔ Documents prepared for ingestion: {len(documents)}")
        return {
            "status": "skipped",
            "reason": "devguard_core_not_running",
            "documents": len(documents),
        }

if __name__ == "__main__":
    installations = list_installations()
    print("Installations:", installations)
    if not installations:
        raise Exception("No installations found. The GitHub App is not installed on any repositories.")

    installation_id = installations[0]["id"]
    print(f"Using installation ID: {installation_id}")

    token = get_installation_access_token(installation_id)
    print("Installation access token acquired")

    owner = "VIVEKBSUTAR"
    repo = "API-Cost-Optimizer"
    branch = "main"

    commit_sha = get_branch_commit_sha(token, owner, repo, branch)
    print("Commit SHA for branch:", commit_sha)

    tree = get_repo_tree(token, owner, repo, commit_sha)

    raw_files = []
    for item in tree:
        if item["type"] == "blob":
            content = get_blob_content(token, owner, repo, item["sha"])
            raw_files.append(
                {
                    "path": item["path"],
                    "content": content,
                }
            )

    documents = normalize_files(
        repo=repo,
        branch=branch,
        commit=commit_sha,
        files=raw_files,
    )

    print(f"Normalized documents count: {len(documents)}")

    print("Sending normalized documents to DevGuard...")
    result = send_to_devguard(documents)
    print("DevGuard ingestion response:", result)