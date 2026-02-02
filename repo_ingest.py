"""
github_auth.py

Authentication and integration with DevGuard API.
"""

import requests

# ============================
# Configuration
# ============================

DEVGUARD_INGEST_URL = "http://192.168.4.160:8000/api/ingest/github"
DEVGUARD_API_KEY = "devguard_local_key"


# ============================
# DevGuard API Integration
# ============================

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

    response = requests.post(DEVGUARD_INGEST_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()