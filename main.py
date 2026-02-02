DEVGUARD_INGEST_URL = "http://192.168.4.160:8000/api/ingest/github"
DEVGUARD_API_KEY = "devguard_local_key"

def send_to_devguard(documents):
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
    # rest of the function remains unchanged