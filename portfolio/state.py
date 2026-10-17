import json
import time
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent / "state" / "last_review.json"

EMPTY_STATE = {
    "last_review_timestamp": None,
    "last_update_timestamp": None,
    "last_review_success": False,
    "featured_repos": [],
    "repo_snapshots": {},
    "review_history": [],
}


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
        for key, default in EMPTY_STATE.items():
            state.setdefault(key, default)
        return state
    return dict(EMPTY_STATE)


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def record_review(state, repos_examined, featured, scores, changes_applied, errors=None):
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repos_examined": len(repos_examined),
        "featured": [r["name"] for r in featured],
        "top_scores": {r["name"]: round(s, 2) for r, s in sorted(
            scores.items(), key=lambda x: x[1], reverse=True
        )[:10]} if scores else {},
        "changes_applied": changes_applied,
        "errors": errors or [],
    }
    state["review_history"] = state.get("review_history", [])[-19:]
    state["review_history"].append(entry)
    state["last_review_timestamp"] = entry["timestamp"]
    state["last_review_success"] = not errors
    if changes_applied:
        state["last_update_timestamp"] = entry["timestamp"]
    return entry


def get_repo_snapshot(state, repo_name):
    return state.get("repo_snapshots", {}).get(repo_name)


def update_repo_snapshot(state, repo_name, snapshot):
    if "repo_snapshots" not in state:
        state["repo_snapshots"] = {}
    state["repo_snapshots"][repo_name] = snapshot
