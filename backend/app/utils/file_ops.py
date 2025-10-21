import json
import os
from typing import Dict, List

RUNS_DIR = os.path.join(os.path.dirname(__file__), "..", "runs")
os.makedirs(RUNS_DIR, exist_ok=True)

def save_run(record: Dict) -> Dict:
    run_id = record.get("run_id")
    path = os.path.join(RUNS_DIR, f"run_{run_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    return record

def list_runs() -> List[str]:
    files = [f for f in os.listdir(RUNS_DIR) if f.startswith("run_") and f.endswith(".json")]
    files.sort(reverse=True)
    return files

def load_run(run_id: str) -> Dict:
    path = os.path.join(RUNS_DIR, f"run_{run_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(run_id)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
