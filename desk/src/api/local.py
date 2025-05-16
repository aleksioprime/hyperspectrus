import requests

LOCAL_API = "http://localhost:8000"

def get_patient_names(ids: list[int]):
    r = requests.post(f"{LOCAL_API}/patients/names", json={"ids": ids})
    r.raise_for_status()
    return r.json()  # {id: ФИО}

def add_job_to_queue(session_id, spectra):
    r = requests.post(
        f"{LOCAL_API}/queue/",
        json={"session_id": session_id, "spectra": spectra}
    )
    r.raise_for_status()
    return r.json()

def get_jobs(status="new"):
    r = requests.get(f"{LOCAL_API}/queue/", params={"status": status})
    r.raise_for_status()
    return r.json()
