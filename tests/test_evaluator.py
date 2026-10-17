import pytest
from portfolio.evaluator import score_repo, select_featured
from portfolio.config import DEFAULT_CONFIG


def _make_snapshot(**overrides):
    base = {
        "name": "test-repo",
        "description": "A test repository for ML pipelines",
        "topics": ["python", "ml", "ai"],
        "language": "Python",
        "languages": {"Python": 50000, "JavaScript": 10000},
        "stars": 2,
        "forks": 1,
        "fork": False,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-10-01T00:00:00Z",
        "pushed_at": "2026-10-01T00:00:00Z",
        "size_kb": 500,
        "has_homepage": True,
        "homepage": "https://example.com",
        "recent_commit_count": 15,
        "latest_commit_sha": "abc123",
        "readme_length": 3000,
        "readme_has_setup": True,
        "readme_has_architecture": True,
        "has_tests": True,
        "has_ci": True,
        "has_docker": True,
        "has_license": True,
        "has_env_example": True,
        "language_count": 2,
        "total_code_bytes": 60000,
        "release_count": 1,
        "file_count": 20,
    }
    base.update(overrides)
    return base


def _make_weak_snapshot(**overrides):
    base = {
        "name": "weak-repo",
        "description": "",
        "topics": [],
        "language": "",
        "languages": {},
        "stars": 0,
        "forks": 0,
        "fork": False,
        "created_at": "2026-09-01T00:00:00Z",
        "updated_at": "2026-09-01T00:00:00Z",
        "pushed_at": "2026-09-01T00:00:00Z",
        "size_kb": 5,
        "has_homepage": False,
        "homepage": "",
        "recent_commit_count": 1,
        "latest_commit_sha": "def456",
        "readme_length": 50,
        "readme_has_setup": False,
        "readme_has_architecture": False,
        "has_tests": False,
        "has_ci": False,
        "has_docker": False,
        "has_license": False,
        "has_env_example": False,
        "language_count": 0,
        "total_code_bytes": 500,
        "release_count": 0,
        "file_count": 2,
    }
    base.update(overrides)
    return base


# Test A: No new projects — current featured stays unchanged
def test_no_changes_keeps_current():
    strong = _make_snapshot(name="existing-strong")
    scored = [{"name": "existing-strong", "score": score_repo(strong, DEFAULT_CONFIG), "snapshot": strong}]
    current = [{"name": "existing-strong", "score": scored[0]["score"]}]
    featured, replaced, added = select_featured(scored, current, DEFAULT_CONFIG)
    assert len(replaced) == 0
    assert len(added) == 0
    assert any(r["name"] == "existing-strong" for r in featured)


# Test B: Weak new project does NOT displace strong existing
def test_weak_project_no_displacement():
    strong = _make_snapshot(name="strong-project")
    weak = _make_weak_snapshot(name="weak-new")
    strong_score = score_repo(strong, DEFAULT_CONFIG)
    weak_score = score_repo(weak, DEFAULT_CONFIG)
    assert strong_score["total"] > weak_score["total"] + 10

    scored = [
        {"name": "strong-project", "score": strong_score, "snapshot": strong},
        {"name": "weak-new", "score": weak_score, "snapshot": weak},
    ]
    current = [{"name": "strong-project"}]
    config = {**DEFAULT_CONFIG, "max_featured": 1}
    featured, replaced, added = select_featured(scored, current, config)
    assert any(r["name"] == "strong-project" for r in featured)
    assert not any(r["name"] == "weak-new" for r in featured)


# Test C: Strong new project replaces weakest featured
def test_strong_replaces_weakest():
    strong_new = _make_snapshot(name="strong-new")
    existing_weak = _make_weak_snapshot(name="existing-weak", description="An old project", language="HTML", languages={"HTML": 2000}, language_count=1)
    existing_strong = _make_snapshot(name="existing-strong")

    scored = [
        {"name": "existing-strong", "score": score_repo(existing_strong, DEFAULT_CONFIG), "snapshot": existing_strong},
        {"name": "existing-weak", "score": score_repo(existing_weak, DEFAULT_CONFIG), "snapshot": existing_weak},
        {"name": "strong-new", "score": score_repo(strong_new, DEFAULT_CONFIG), "snapshot": strong_new},
    ]
    current = [{"name": "existing-strong"}, {"name": "existing-weak"}]
    config = {**DEFAULT_CONFIG, "max_featured": 2}
    featured, replaced, added = select_featured(scored, current, config)
    featured_names = {r["name"] for r in featured}
    assert "strong-new" in featured_names
    assert "existing-strong" in featured_names


# Test D: Existing project improves — re-evaluated
def test_existing_project_improves():
    before = _make_weak_snapshot(name="improving-project")
    after = _make_snapshot(name="improving-project")
    score_before = score_repo(before, DEFAULT_CONFIG)
    score_after = score_repo(after, DEFAULT_CONFIG)
    assert score_after["total"] > score_before["total"]


# Test H: Insufficient confidence — keep current
def test_low_confidence_no_replacement():
    strong = _make_snapshot(name="established")
    uncertain = _make_snapshot(
        name="uncertain",
        description="",
        readme_length=0,
        recent_commit_count=0,
        total_code_bytes=0,
        language_count=0,
    )
    uncertain_score = score_repo(uncertain, DEFAULT_CONFIG)
    assert uncertain_score["confidence"] < DEFAULT_CONFIG["min_confidence"]

    scored = [
        {"name": "established", "score": score_repo(strong, DEFAULT_CONFIG), "snapshot": strong},
        {"name": "uncertain", "score": uncertain_score, "snapshot": uncertain},
    ]
    current = [{"name": "established"}]
    config = {**DEFAULT_CONFIG, "max_featured": 1}
    featured, replaced, added = select_featured(scored, current, config)
    assert not replaced
    assert "established" in {r["name"] for r in featured}


# Test J: Idempotent — same input produces same output
def test_idempotent_selection():
    repos = [_make_snapshot(name=f"repo-{i}", stars=i) for i in range(8)]
    scored = [{"name": r["name"], "score": score_repo(r, DEFAULT_CONFIG), "snapshot": r} for r in repos]
    current = [{"name": f"repo-{i}"} for i in range(4, 8)]
    f1, r1, a1 = select_featured(scored, current, DEFAULT_CONFIG)
    f2, r2, a2 = select_featured(scored, current, DEFAULT_CONFIG)
    assert {r["name"] for r in f1} == {r["name"] for r in f2}


def test_fork_penalized():
    original = _make_snapshot(name="original", fork=False)
    forked = _make_snapshot(name="forked", fork=True)
    s_original = score_repo(original, DEFAULT_CONFIG)
    s_forked = score_repo(forked, DEFAULT_CONFIG)
    assert s_original["total"] > s_forked["total"]
