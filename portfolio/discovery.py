import logging
import re
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


def fetch_repo_tree(username, repo_name, token):
    try:
        data = _api_get(
            f"{API_BASE}/repos/{username}/{repo_name}/git/trees/HEAD",
            token,
            params={"recursive": "1"},
        )
        if data and "tree" in data:
            return data["tree"]
    except Exception:
        pass
    return []


def analyze_readme_content(readme_text):
    if not readme_text:
        return _empty_readme_signals()

    text = readme_text.lower()

    metrics_patterns = [
        r"\d+\.?\d*\s*%",
        r"f[0-9][\s:=]+[\d.]",
        r"accuracy[\s:=]+[\d.]",
        r"precision[\s:=]+[\d.]",
        r"recall[\s:=]+[\d.]",
        r"auc[\s:=]+[\d.]",
        r"macro[\s_-]f",
        r"mse[\s:=]+[\d.]",
        r"rmse[\s:=]+[\d.]",
        r"bleu[\s:=]+[\d.]",
        r"rouge[\s:=]+[\d.]",
    ]
    metric_hits = sum(1 for p in metrics_patterns if re.search(p, text))

    quality_keywords = [
        "benchmark", "baseline", "outperform", "state-of-the-art",
        "sota", "ablation", "evaluation", "compared to", "beats",
    ]
    quality_hits = sum(1 for kw in quality_keywords if kw in text)

    competition_keywords = [
        "hackathon", "challenge", "competition", "top-", "winner",
        "finalist", "people's choice", "first place", "runner-up",
        "qualified", "qualifier", "leaderboard", "codejam", "code jam",
    ]

    arch_keywords = [
        "architecture", "pipeline", "how it works", "system design",
        "workflow", "data flow", "component", "module", "middleware",
        "orchestrat", "multi-agent", "microservice", "event-driven",
    ]

    tech_keywords = [
        "rag", "vector database", "embedding", "transformer", "attention",
        "reinforcement learning", "fine-tun", "inference", "llm",
        "distributed", "concurrent", "async", "streaming", "sse",
        "websocket", "grpc", "graphql", "rest api",
        "kubernetes", "terraform", "infrastructure as code",
        "oauth", "jwt", "authentication", "authorization",
        "cache", "indexing", "optimization", "profiling",
        "causal", "fault", "recovery", "self-healing",
        "agent", "autonomous", "reasoning", "chain-of-thought",
    ]

    scale_pattern = r"(\d+[\.,]?\d*)\s*[MmKkBb]\+?\s*(record|entit|user|request|row|transaction|document|item|node|pair|sample|image|token)"

    return {
        "has_metrics": metric_hits > 0,
        "metric_count": metric_hits,
        "has_quality_comparison": quality_hits > 0,
        "quality_comparison_count": quality_hits,
        "has_competition": any(kw in text for kw in competition_keywords),
        "architecture_depth": sum(1 for kw in arch_keywords if kw in text),
        "tech_sophistication": sum(1 for kw in tech_keywords if kw in text),
        "has_live_demo": any(kw in text for kw in [
            "live demo", "deployed at", "try it", ".onrender.com",
            ".vercel.app", ".netlify.app", ".herokuapp.com",
            "hosted at", "available at",
        ]),
        "has_scale_numbers": bool(re.search(scale_pattern, text)),
        "has_images": bool(re.search(r"!\[.*?\]\(.*?\)", readme_text)),
        "section_count": len(re.findall(r"^#{1,3}\s+", readme_text, re.MULTILINE)),
        "list_item_count": len(re.findall(r"^\s*[-*]\s+", readme_text, re.MULTILINE)),
        "code_block_count": len(re.findall(r"```", readme_text)) // 2,
        "has_table": bool(re.search(r"\|.*\|.*\|", readme_text)),
    }


def _empty_readme_signals():
    return {
        "has_metrics": False, "metric_count": 0,
        "has_quality_comparison": False, "quality_comparison_count": 0,
        "has_competition": False, "architecture_depth": 0,
        "tech_sophistication": 0, "has_live_demo": False,
        "has_scale_numbers": False, "has_images": False,
        "section_count": 0, "list_item_count": 0,
        "code_block_count": 0, "has_table": False,
    }


def analyze_commit_messages(commits):
    if not commits:
        return {"substantive_ratio": 0.0, "avg_message_length": 0, "total_analyzed": 0}

    messages = []
    for c in commits:
        if isinstance(c, dict):
            msg = c.get("commit", {}).get("message", "")
            if msg:
                messages.append(msg)

    if not messages:
        return {"substantive_ratio": 0.0, "avg_message_length": 0, "total_analyzed": 0}

    trivial_starts = [
        "update readme", "update", "initial commit", "first commit",
        "wip", "temp", "fix typo", "minor", "cleanup", "clean up",
        "merge branch", "merge pull request",
    ]
    substantive = 0
    for msg in messages:
        first_line = msg.strip().split("\n")[0].lower()
        if len(first_line) > 15 and not any(first_line.startswith(t) for t in trivial_starts):
            substantive += 1

    return {
        "substantive_ratio": round(substantive / len(messages), 2),
        "avg_message_length": round(sum(len(m) for m in messages) / len(messages)),
        "total_analyzed": len(messages),
    }


def analyze_project_structure(tree):
    if not tree:
        return _empty_structure()

    paths = []
    dirs = set()
    for item in tree:
        if not isinstance(item, dict):
            continue
        p = item.get("path", "")
        paths.append(p.lower())
        if item.get("type") == "tree":
            dirs.add(p.lower())

    max_depth = max((p.count("/") for p in paths), default=0)

    config_indicators = [
        "dockerfile", "docker-compose", ".eslintrc", ".prettierrc",
        "tsconfig.json", "pyproject.toml", "setup.py", "setup.cfg",
        "jest.config", "pytest.ini", ".flake8", "mypy.ini",
        "webpack.config", "vite.config", "next.config",
        "makefile", "procfile", "tox.ini", ".pre-commit-config",
        "requirements.txt", "package.json", "cargo.toml", "go.mod",
        "poetry.lock", "pipfile", "yarn.lock", "pnpm-lock",
    ]
    config_variety = sum(1 for cf in config_indicators if any(cf in p for p in paths))

    has_src = any(p.startswith("src/") or p.startswith("lib/") or p.startswith("app/") for p in paths)
    has_test_dir = any(p.startswith("tests/") or p.startswith("test/") or p.startswith("__tests__/") or p.startswith("spec/") for p in paths)
    has_docs = any(p.startswith("docs/") or p.startswith("doc/") for p in paths)
    has_ci_dir = any(".github/workflows" in p for p in paths)

    file_count = sum(1 for item in tree if isinstance(item, dict) and item.get("type") == "blob")

    return {
        "max_depth": max_depth,
        "dir_count": len(dirs),
        "config_variety": config_variety,
        "has_src_structure": has_src,
        "has_test_dir": has_test_dir,
        "has_docs_dir": has_docs,
        "has_ci_dir": has_ci_dir,
        "total_files": file_count,
    }


def _empty_structure():
    return {
        "max_depth": 0, "dir_count": 0, "config_variety": 0,
        "has_src_structure": False, "has_test_dir": False,
        "has_docs_dir": False, "has_ci_dir": False, "total_files": 0,
    }


def build_repo_snapshot(username, repo, token):
    name = repo["name"]
    languages = fetch_repo_languages(username, name, token) or {}
    commits = fetch_recent_commits(username, name, token) or []
    contents = fetch_repo_contents(username, name, token) or []
    readme = fetch_readme_content(username, name, token)
    releases = fetch_releases(username, name, token) or []
    workflows = fetch_workflows(username, name, token)
    tree = fetch_repo_tree(username, name, token)

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

    readme_signals = analyze_readme_content(readme)
    commit_quality = analyze_commit_messages(commits)
    structure = analyze_project_structure(tree)

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
        # Deep analysis fields
        "readme_signals": readme_signals,
        "commit_quality": commit_quality,
        "structure": structure,
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
