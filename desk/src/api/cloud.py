import requests
from services.state import AppState

CLOUD_API = "https://cloud-server.example.com/api"

def login_cloud(username, password):
    r = requests.post(f"{CLOUD_API}/token", data={"username": username, "password": password})
    r.raise_for_status()
    token = r.json()["access_token"]
    AppState().set_token(token)
    return token

def _headers():
    token = AppState().token
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def get_patients():
    r = requests.get(f"{CLOUD_API}/patients", headers=_headers())
    r.raise_for_status()
    return r.json()

def get_sessions(patient_id):
    r = requests.get(f"{CLOUD_API}/patients/{patient_id}/sessions", headers=_headers())
    r.raise_for_status()
    return r.json()

def create_session(patient_id, description):
    r = requests.post(
        f"{CLOUD_API}/patients/{patient_id}/sessions",
        headers=_headers(),
        json={"description": description}
    )
    r.raise_for_status()
    return r.json()

def delete_session(session_id):
    r = requests.delete(f"{CLOUD_API}/sessions/{session_id}", headers=_headers())
    r.raise_for_status()
    return r.json()

def get_session_results(session_id):
    r = requests.get(f"{CLOUD_API}/sessions/{session_id}/results", headers=_headers())
    r.raise_for_status()
    return r.json()
