import logging
import re
import requests
import time
from pathlib import Path

from .safety import validate_readme_change, validate_pin_count, validate_repos_exist

log = logging.getLogger(__name__)

API_BASE = "https://api.github.com"
README_PATH = Path(__file__).parent.parent / "README.md"


def _headers(token):
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def read_current_readme():
    if README_PATH.exists():
        return README_PATH.read_text(encoding="utf-8")
    return ""


def generate_project_section(featured_repos):
    lines = ["", "<table>"]
    for i, repo in enumerate(featured_repos):
        if i % 2 == 0:
            lines.append("<tr>")

        s = repo.get("snapshot", {})
        name = s.get("name", repo.get("name", ""))
        desc = s.get("description", "")
        lang = s.get("language", "")
        homepage = s.get("homepage", "")
        url = f"https://github.com/princechoudhary16/{name}"

        lines.append('<td width="50%" valign="top">')
        lines.append("")
        lines.append(f"#### [{name}]({url})")
        if desc:
            lines.append(desc)
        lines.append("")
        tech = []
        if lang:
            tech.append(lang)
        langs = s.get("languages", {})
        for l in list(langs.keys())[:4]:
            if l != lang and l not in tech:
                tech.append(l)
        if tech:
            lines.append(" ".join(f"`{t}`" for t in tech))
        if homepage:
            lines.append(f"\n[Live Demo →]({homepage})")
        lines.append("")
        lines.append("</td>")

        if i % 2 == 1 or i == len(featured_repos) - 1:
            if i % 2 == 0:
                lines.append('<td width="50%"></td>')
            lines.append("</tr>")

    lines.append("</table>")
    lines.append("")
    return "\n".join(lines)


def update_readme_managed_section(current_content, new_section, start_marker, end_marker):
    s = current_content.find(start_marker)
    e = current_content.find(end_marker)
    if s == -1 or e == -1:
        log.warning("Managed section markers not found in README")
        return None
    before = current_content[: s + len(start_marker)]
    after = current_content[e:]
    proposed = before + "\n" + new_section + "\n" + after
    return proposed


def compute_readme_diff(current, proposed):
    if current == proposed:
        return None
    current_lines = current.splitlines()
    proposed_lines = proposed.splitlines()
    changes = []
    for i, (c, p) in enumerate(zip(current_lines, proposed_lines)):
        if c != p:
            changes.append({"line": i + 1, "old": c, "new": p})
    if len(proposed_lines) > len(current_lines):
        for i in range(len(current_lines), len(proposed_lines)):
            changes.append({"line": i + 1, "old": "", "new": proposed_lines[i]})
    elif len(current_lines) > len(proposed_lines):
        for i in range(len(proposed_lines), len(current_lines)):
            changes.append({"line": i + 1, "old": current_lines[i], "new": ""})
    return changes


def validate_readme(content):
    errors = []
    links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', content)
    for text, url in links:
        if url.startswith("http") and not url.startswith(("https://", "http://")):
            errors.append(f"Malformed URL: {url}")
    if "PORTFOLIO:PROJECTS:START" in content and "PORTFOLIO:PROJECTS:END" not in content:
        errors.append("Managed section start marker found without end marker")
    if len(content) > 50_000:
        errors.append("README exceeds 50KB")
    return errors


def write_readme(content):
    README_PATH.write_text(content, encoding="utf-8")


def fetch_current_pins(username, token):
    query = """
    query($login: String!) {
      user(login: $login) {
        pinnedItems(first: 6) {
          nodes {
            ... on Repository {
              id
              name
              url
            }
          }
        }
      }
    }
    """
    try:
        resp = requests.post(
            "https://api.github.com/graphql",
            headers=_headers(token),
            json={"query": query, "variables": {"login": username}},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        nodes = data.get("data", {}).get("user", {}).get("pinnedItems", {}).get("nodes", [])
        return [n for n in nodes if n]
    except Exception as e:
        log.error("Failed to fetch pins: %s", e)
        return []


def update_pins(username, token, desired_repo_names, all_repos):
    validate_pin_count(desired_repo_names)
    validate_repos_exist(
        [{"name": n} for n in desired_repo_names],
        all_repos,
    )
    log.info(
        "Pin update requested: %s (pin management via API is limited; "
        "use the web reorder form endpoint if auth supports it)",
        desired_repo_names,
    )
    return {"status": "pin_update_logged", "desired": desired_repo_names}
