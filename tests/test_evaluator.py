import pytest
from portfolio.evaluator import score_repo, select_featured, _score_portfolio_impact
from portfolio.config import DEFAULT_CONFIG


def _make_readme_signals(**overrides):
    base = {
        "has_metrics": True, "metric_count": 3,
        "has_quality_comparison": True, "quality_comparison_count": 2,
        "has_competition": False, "architecture_depth": 3,
        "tech_sophistication": 4, "has_live_demo": True,
        "has_scale_numbers": False, "has_images": True,
        "section_count": 5, "list_item_count": 10,
        "code_block_count": 3, "has_table": False,
    }
    base.update(overrides)
    return base


def _make_structure(**overrides):
    base = {
        "max_depth": 3, "dir_count": 8, "config_variety": 4,
        "has_src_structure": True, "has_test_dir": True,
        "has_docs_dir": False, "has_ci_dir": True, "total_files": 25,
    }
    base.update(overrides)
    return base


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
        "readme_signals": _make_readme_signals(),
        "structure": _make_structure(),
        "commit_quality": {"substantive_ratio": 0.6, "avg_message_length": 45, "total_analyzed": 15},
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
        "readme_signals": _make_readme_signals(
            has_metrics=False, metric_count=0,
            has_quality_comparison=False, quality_comparison_count=0,
            has_competition=False, architecture_depth=0,
            tech_sophistication=0, has_live_demo=False,
            has_scale_numbers=False, has_images=False,
            section_count=0, list_item_count=0,
            code_block_count=0, has_table=False,
        ),
        "structure": _make_structure(
            max_depth=0, dir_count=0, config_variety=0,
            has_src_structure=False, has_test_dir=False,
            has_docs_dir=False, has_ci_dir=False, total_files=2,
        ),
        "commit_quality": {"substantive_ratio": 0.0, "avg_message_length": 10, "total_analyzed": 1},
    }
    base.update(overrides)
    return base


def test_no_changes_keeps_current():
    strong = _make_snapshot(name="existing-strong")
    scored = [{"name": "existing-strong", "score": score_repo(strong, DEFAULT_CONFIG), "snapshot": strong}]
    current = [{"name": "existing-strong", "score": scored[0]["score"]}]
    featured, replaced, added = select_featured(scored, current, DEFAULT_CONFIG)
    assert len(replaced) == 0
    assert len(added) == 0
    assert any(r["name"] == "existing-strong" for r in featured)


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


def test_strong_replaces_weakest():
    strong_new = _make_snapshot(name="strong-new")
    existing_weak = _make_weak_snapshot(
        name="existing-weak", description="An old project",
        language="HTML", languages={"HTML": 2000}, language_count=1,
    )
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


def test_existing_project_improves():
    before = _make_weak_snapshot(name="improving-project")
    after = _make_snapshot(name="improving-project")
    score_before = score_repo(before, DEFAULT_CONFIG)
    score_after = score_repo(after, DEFAULT_CONFIG)
    assert score_after["total"] > score_before["total"]


def test_low_confidence_no_replacement():
    strong = _make_snapshot(name="established")
    uncertain = _make_snapshot(
        name="uncertain",
        description="",
        readme_length=0,
        recent_commit_count=0,
        total_code_bytes=0,
        language_count=0,
        readme_signals=_make_readme_signals(
            has_metrics=False, metric_count=0, section_count=0,
            has_quality_comparison=False, quality_comparison_count=0,
        ),
        structure=_make_structure(total_files=2, max_depth=0, dir_count=0, config_variety=0,
                                  has_src_structure=False, has_test_dir=False),
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


def test_portfolio_impact_rewards_benchmarks():
    with_benchmarks = _make_snapshot(
        name="ml-project",
        readme_signals=_make_readme_signals(
            has_metrics=True, metric_count=5,
            has_quality_comparison=True, quality_comparison_count=3,
            has_competition=True, has_scale_numbers=True,
        ),
    )
    without = _make_snapshot(
        name="crud-app",
        readme_signals=_make_readme_signals(
            has_metrics=False, metric_count=0,
            has_quality_comparison=False, quality_comparison_count=0,
            has_competition=False, has_scale_numbers=False,
            architecture_depth=0, tech_sophistication=0,
        ),
    )
    impact_with = _score_portfolio_impact(with_benchmarks)
    impact_without = _score_portfolio_impact(without)
    assert impact_with > impact_without + 20


def test_portfolio_impact_penalizes_tiny_repos():
    tiny = _make_snapshot(
        name="tiny",
        total_code_bytes=500,
        readme_signals=_make_readme_signals(
            has_metrics=False, metric_count=0,
            has_quality_comparison=False, quality_comparison_count=0,
        ),
    )
    impact = _score_portfolio_impact(tiny)
    assert impact < 80


def test_score_includes_portfolio_impact():
    snap = _make_snapshot()
    score = score_repo(snap, DEFAULT_CONFIG)
    assert "portfolio_impact" in score["breakdown"]
    assert score["breakdown"]["portfolio_impact"] > 0
