import logging
import time
import requests

log = logging.getLogger(__name__)

API_BASE = "https://api.github.com"
MAX_RETRIES = 3
BACKOFF_BASE = 2


def _headers(token):
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _api_get(url, token, params=None):
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=_headers(token), params=params, timeout=30)
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait = max(reset - time.time(), 1)
                log.warning("Rate limited, waiting %.0fs", wait)
                time.sleep(min(wait, 120))
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                delay = BACKOFF_BASE ** (attempt + 1)
                log.warning("API error (attempt %d): %s, retrying in %ds", attempt + 1, e, delay)
                time.sleep(delay)
            else:
                raise
    return None


def fetch_repos(username, token):
    repos = []
    page = 1
    while True:
        data = _api_get(
            f"{API_BASE}/users/{username}/repos",
            token,
            params={"per_page": 100, "page": page, "type": "owner", "sort": "updated"},
        )
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def fetch_repo_details(username, repo_name, token):
    return _api_get(f"{API_BASE}/repos/{username}/{repo_name}", token)


def fetch_repo_languages(username, repo_name, token):
    return _api_get(f"{API_BASE}/repos/{username}/{repo_name}/languages", token)


def fetch_recent_commits(username, repo_name, token, since=None):
    params = {"per_page": 30}
    if since:
        params["since"] = since
    try:
        return _api_get(f"{API_BASE}/repos/{username}/{repo_name}/commits", token, params)
    except Exception:
        return []


def fetch_repo_contents(username, repo_name, token, path=""):
    try:
        return _api_get(f"{API_BASE}/repos/{username}/{repo_name}/contents/{path}", token)
    except Exception:
        return []


def fetch_readme_content(username, repo_name, token):
    try:
        resp = requests.get(
            f"{API_BASE}/repos/{username}/{repo_name}/readme",
            headers={**_headers(token), "Accept": "application/vnd.github.raw+json"},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return ""


def fetch_releases(username, repo_name, token):
    try:
        return _api_get(f"{API_BASE}/repos/{username}/{repo_name}/releases", token, {"per_page": 5})
    except Exception:
        return []


def fetch_workflows(username, repo_name, token):
    try:
        return _api_get(f"{API_BASE}/repos/{username}/{repo_name}/actions/workflows", token)
    except Exception:
        return {"total_count": 0, "workflows": []}


def build_repo_snapshot(username, repo, token):
    name = repo["name"]
    languages = fetch_repo_languages(username, name, token) or {}
    commits = fetch_recent_commits(username, name, token) or []
    contents = fetch_repo_contents(username, name, token) or []
    readme = fetch_readme_content(username, name, token)
    releases = fetch_releases(username, name, token) or []
    workflows = fetch_workflows(username, name, token)

    content_names = [c["name"].lower() for c in contents if isinstance(c, dict)]
    has_tests = any(
        n in ("tests", "test", "__tests__", "spec", "test.py", "test_", "pytest.ini", "jest.config")
        or n.startswith("test_") or n.endswith("_test.py") or n.endswith(".test.js") or n.endswith(".test.ts")
        for n in content_names
    )
    has_ci = bool(workflows.get("total_count", 0))
    has_docker = any(n in ("dockerfile", "docker-compose.yml", "docker-compose.yaml") for n in content_names)
    has_license = any(n in ("license", "license.md", "license.txt") for n in content_names)
    has_env_example = any(n in (".env.example", "env.example") for n in content_names)

    return {
        "name": name,
        "description": repo.get("description") or "",
        "topics": repo.get("topics") or [],
        "language": repo.get("language") or "",
        "languages": languages,
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "fork": repo.get("fork", False),
        "created_at": repo.get("created_at", ""),
        "updated_at": repo.get("updated_at", ""),
        "pushed_at": repo.get("pushed_at", ""),
        "size_kb": repo.get("size", 0),
        "has_homepage": bool(repo.get("homepage")),
        "homepage": repo.get("homepage", ""),
        "recent_commit_count": len(commits),
        "latest_commit_sha": commits[0]["sha"] if commits else "",
        "readme_length": len(readme),
        "readme_has_setup": any(kw in readme.lower() for kw in ["setup", "install", "getting started", "usage"]),
        "readme_has_architecture": any(kw in readme.lower() for kw in ["architecture", "how it works", "design"]),
        "has_tests": has_tests,
        "has_ci": has_ci,
        "has_docker": has_docker,
        "has_license": has_license,
        "has_env_example": has_env_example,
        "language_count": len(languages),
        "total_code_bytes": sum(languages.values()),
        "release_count": len(releases),
        "file_count": len(contents),
    }


def detect_changes(current_snapshot, previous_snapshot):
    if not previous_snapshot:
        return {"is_new": True, "changes": ["new_repo"]}
    changes = []
    if current_snapshot.get("latest_commit_sha") != previous_snapshot.get("latest_commit_sha"):
        changes.append("new_commits")
    if current_snapshot.get("readme_length", 0) > previous_snapshot.get("readme_length", 0) * 1.2:
        changes.append("readme_expanded")
    if current_snapshot.get("has_tests") and not previous_snapshot.get("has_tests"):
        changes.append("tests_added")
    if current_snapshot.get("has_ci") and not previous_snapshot.get("has_ci"):
        changes.append("ci_added")
    if current_snapshot.get("release_count", 0) > previous_snapshot.get("release_count", 0):
        changes.append("new_release")
    if current_snapshot.get("language_count", 0) > previous_snapshot.get("language_count", 0):
        changes.append("languages_added")
    if current_snapshot.get("total_code_bytes", 0) > previous_snapshot.get("total_code_bytes", 0) * 1.5:
        changes.append("substantial_code_growth")
    return {"is_new": False, "changes": changes}
