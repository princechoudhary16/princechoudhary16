#!/usr/bin/env python3
"""Main orchestrator for the portfolio management system."""

import json
import logging
import os
import subprocess
import sys
import time

from .config import load_config
from .state import load_state, save_state, record_review, get_repo_snapshot, update_repo_snapshot
from .discovery import fetch_repos, build_repo_snapshot, detect_changes
from .evaluator import score_repo, select_featured
from .updater import (
    read_current_readme, generate_project_section,
    update_readme_managed_section, compute_readme_diff,
    validate_readme, write_readme, fetch_current_pins,
)
from .safety import validate_readme_change, SafetyViolation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("portfolio.manager")


def run(config_path=None):
    log.info("=== Portfolio Manager starting ===")
    config = load_config(config_path)
    state = load_state()
    mode = config["mode"]
    username = config["username"]
    token = config["github_token"]
    errors = []
    changes_applied = False

    log.info("Mode: %s | User: %s", mode, username)

    if not token:
        log.error("GITHUB_TOKEN not set")
        _write_summary("GITHUB_TOKEN not set. Cannot proceed.", error=True)
        return False

    # --- Concurrency guard ---
    lock_file = os.path.join(os.path.dirname(__file__), ".lock")
    if os.path.exists(lock_file):
        try:
            with open(lock_file) as f:
                lock_time = float(f.read().strip())
            if time.time() - lock_time < 3600:
                log.warning("Another run is active (lock age: %.0fs). Exiting.", time.time() - lock_time)
                return False
        except (ValueError, OSError):
            pass
    with open(lock_file, "w") as f:
        f.write(str(time.time()))

    try:
        result = _run_review(config, state, username, token, mode, errors)
        changes_applied = result.get("changes_applied", False)
    except SafetyViolation as e:
        log.error("SAFETY VIOLATION: %s", e)
        errors.append(f"Safety violation: {e}")
    except Exception as e:
        log.error("Unexpected error: %s", e, exc_info=True)
        errors.append(f"Error: {e}")
    finally:
        try:
            os.remove(lock_file)
        except OSError:
            pass

    record_review(
        state,
        repos_examined=result.get("repos", []) if "result" in dir() else [],
        featured=result.get("featured", []) if "result" in dir() else [],
        scores={},
        changes_applied=changes_applied,
        errors=errors,
    )
    save_state(state)
    log.info("=== Portfolio Manager finished (changes=%s, errors=%d) ===", changes_applied, len(errors))
    return not errors


def _run_review(config, state, username, token, mode, errors):
    result = {"repos": [], "featured": [], "changes_applied": False}

    # 1. Discover repos
    log.info("Fetching repositories...")
    repos = fetch_repos(username, token)
    if not repos:
        errors.append("No repositories found or API failure")
        _write_summary("No repositories found. Check API access.", error=True)
        return result
    result["repos"] = repos

    ignored = set(config.get("ignored_repos", []))
    repos = [r for r in repos if r["name"] not in ignored and r["name"] != username]
    log.info("Found %d repos (excluding ignored and profile repo)", len(repos))

    # 2. Build snapshots and detect changes
    log.info("Building repository snapshots...")
    snapshots = {}
    changed_repos = []
    for repo in repos:
        name = repo["name"]
        snapshot = build_repo_snapshot(username, repo, token)
        snapshots[name] = snapshot
        prev = get_repo_snapshot(state, name)
        delta = detect_changes(snapshot, prev)
        if delta["is_new"] or delta["changes"]:
            changed_repos.append({"name": name, "delta": delta})
        update_repo_snapshot(state, name, {
            "latest_commit_sha": snapshot["latest_commit_sha"],
            "readme_length": snapshot["readme_length"],
            "has_tests": snapshot["has_tests"],
            "has_ci": snapshot["has_ci"],
            "release_count": snapshot["release_count"],
            "total_code_bytes": snapshot["total_code_bytes"],
            "language_count": snapshot["language_count"],
        })

    log.info("Repos with changes: %d", len(changed_repos))
    if not changed_repos and state.get("last_review_success"):
        log.info("No changes detected since last successful review. Nothing to do.")
        _write_summary("No changes detected. Portfolio unchanged.")
        return result

    # 3. Score all repos
    log.info("Scoring repositories...")
    scored = []
    for name, snapshot in snapshots.items():
        score = score_repo(snapshot, config)
        scored.append({"name": name, "score": score, "snapshot": snapshot})
    scored.sort(key=lambda x: x["score"]["total"], reverse=True)

    log.info("Top 10 scores:")
    for r in scored[:10]:
        log.info("  %s: %.1f (confidence: %.2f)", r["name"], r["score"]["total"], r["score"]["confidence"])

    # 4. Determine current featured
    current_pins = fetch_current_pins(username, token)
    current_featured = [r for r in scored if r["name"] in {p["name"] for p in current_pins}]

    # 5. Select new featured set
    featured, replaced, added = select_featured(scored, current_featured, config)
    result["featured"] = featured
    state["featured_repos"] = [r["name"] for r in featured]

    if not replaced and not added:
        log.info("No portfolio changes needed. Current selection is optimal.")
        _write_summary(_format_no_change_summary(scored, featured))
        return result

    log.info("Proposed changes:")
    for old, new in replaced:
        log.info("  REPLACE: %s → %s", old, new)
    for name in added:
        if name not in [r for _, r in replaced]:
            log.info("  ADD: %s", name)

    # 6. Generate README update
    current_readme = read_current_readme()
    start = config["readme_managed_section_start"]
    end = config["readme_managed_section_end"]

    if start in current_readme and end in current_readme:
        new_section = generate_project_section(featured)
        proposed_readme = update_readme_managed_section(current_readme, new_section, start, end)

        if proposed_readme:
            validation_errors = validate_readme(proposed_readme)
            if validation_errors:
                for err in validation_errors:
                    log.error("Validation error: %s", err)
                    errors.append(f"README validation: {err}")
                return result

            try:
                validate_readme_change(current_readme, proposed_readme, start, end)
            except SafetyViolation as e:
                errors.append(str(e))
                return result

            diff = compute_readme_diff(current_readme, proposed_readme)
            if not diff:
                log.info("No README changes needed")
            elif mode == "dry-run":
                log.info("DRY RUN: Would update README (%d lines changed)", len(diff))
                _write_summary(_format_dry_run_summary(scored, featured, replaced, added, diff))
            elif mode == "approval":
                log.info("APPROVAL MODE: Creating branch with proposed changes")
                _create_approval_branch(proposed_readme, featured, replaced, added)
                result["changes_applied"] = True
            elif mode == "automatic":
                log.info("AUTO MODE: Applying README update")
                write_readme(proposed_readme)
                _git_commit_and_push(featured, replaced, added)
                result["changes_applied"] = True
    else:
        log.warning(
            "Managed section markers not found in README. "
            "Add %s and %s markers to enable auto-updates.",
            start, end,
        )
        _write_summary(_format_dry_run_summary(scored, featured, replaced, added, None))

    return result


def _create_approval_branch(proposed_readme, featured, replaced, added):
    branch = f"portfolio-update-{time.strftime('%Y%m%d-%H%M%S')}"
    try:
        subprocess.run(["git", "checkout", "-b", branch], check=True, capture_output=True)
        write_readme(proposed_readme)
        subprocess.run(["git", "add", "README.md", "state/"], check=True, capture_output=True)
        msg = _commit_message(replaced, added)
        subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)
        subprocess.run(["git", "push", "-u", "origin", branch], check=True, capture_output=True)
        subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
        _create_pr(branch, msg, featured, replaced, added)
    except subprocess.CalledProcessError as e:
        log.error("Git operation failed: %s", e)
        subprocess.run(["git", "checkout", "main"], capture_output=True)


def _git_commit_and_push(featured, replaced, added):
    try:
        subprocess.run(["git", "add", "README.md", "state/"], check=True, capture_output=True)
        msg = _commit_message(replaced, added)
        subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        log.error("Git commit/push failed: %s", e)


def _commit_message(replaced, added):
    parts = []
    for old, new in replaced:
        parts.append(f"Replace {old} with {new}")
    for name in added:
        if name not in [r for _, r in replaced]:
            parts.append(f"Add {name}")
    if parts:
        return "Update featured projects: " + ", ".join(parts)
    return "Update portfolio"


def _create_pr(branch, title, featured, replaced, added):
    body_lines = ["## Portfolio Update Proposal\n"]
    if replaced:
        body_lines.append("### Replacements")
        for old, new in replaced:
            body_lines.append(f"- **{old}** → **{new}**")
        body_lines.append("")
    if added:
        extras = [n for n in added if n not in [r for _, r in replaced]]
        if extras:
            body_lines.append("### New Additions")
            for n in extras:
                body_lines.append(f"- **{n}**")
            body_lines.append("")
    body_lines.append("### Current Featured Set")
    for r in featured:
        body_lines.append(f"- {r['name']} (score: {r['score']['total']})")
    body = "\n".join(body_lines)
    try:
        subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", body, "--base", "main"],
            check=True, capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        log.error("PR creation failed: %s", e)


def _format_no_change_summary(scored, featured):
    lines = ["## Portfolio Review: No Changes Needed\n"]
    lines.append("The current featured set is optimal.\n")
    lines.append("### Current Featured Projects")
    for r in featured:
        lines.append(f"- **{r['name']}**: {r['score']['total']}/100 (confidence: {r['score']['confidence']})")
    lines.append("\n### Top Candidates")
    for r in scored[:8]:
        marker = " ⭐" if r["name"] in {f["name"] for f in featured} else ""
        lines.append(f"- **{r['name']}**: {r['score']['total']}/100{marker}")
    return "\n".join(lines)


def _format_dry_run_summary(scored, featured, replaced, added, diff):
    lines = ["## Portfolio Review: Dry Run\n"]
    if replaced:
        lines.append("### Proposed Replacements")
        for old, new in replaced:
            lines.append(f"- **{old}** → **{new}**")
        lines.append("")
    if added:
        extras = [n for n in added if n not in [r for _, r in replaced]]
        if extras:
            lines.append("### Proposed Additions")
            for n in extras:
                lines.append(f"- **{n}**")
            lines.append("")
    lines.append("### Proposed Featured Set")
    for r in featured:
        lines.append(f"- **{r['name']}**: {r['score']['total']}/100 (confidence: {r['score']['confidence']})")
    if diff:
        lines.append(f"\n### README Changes: {len(diff)} lines would change")
    else:
        lines.append("\n⚠️ Managed section markers not found. Add them to enable auto-updates.")
    lines.append("\n### All Scores")
    for r in scored[:15]:
        marker = " ⭐" if r["name"] in {f["name"] for f in featured} else ""
        lines.append(f"- **{r['name']}**: {r['score']['total']}/100{marker}")
    return "\n".join(lines)


def _write_summary(content, error=False):
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(content + "\n")
    if error:
        log.error(content)
    else:
        log.info("Summary:\n%s", content)


def main():
    config_path = None
    if len(sys.argv) > 1:
        from pathlib import Path
        config_path = Path(sys.argv[1])
    success = run(config_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
