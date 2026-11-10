from portfolio.discovery import (
    detect_changes, analyze_readme_content, analyze_commit_messages,
    analyze_project_structure,
)


def test_no_changes_when_identical():
    current = {"latest_commit_sha": "abc", "readme_length": 100, "has_tests": True,
               "has_ci": True, "release_count": 1, "language_count": 2, "total_code_bytes": 5000}
    previous = dict(current)
    result = detect_changes(current, previous)
    assert not result["is_new"]
    assert result["changes"] == []


def test_new_repo_detected():
    current = {"latest_commit_sha": "abc"}
    result = detect_changes(current, None)
    assert result["is_new"]
    assert "new_repo" in result["changes"]


def test_new_commits_detected():
    current = {"latest_commit_sha": "new", "readme_length": 100, "has_tests": False,
               "has_ci": False, "release_count": 0, "language_count": 1, "total_code_bytes": 5000}
    previous = {"latest_commit_sha": "old", "readme_length": 100, "has_tests": False,
                "has_ci": False, "release_count": 0, "language_count": 1, "total_code_bytes": 5000}
    result = detect_changes(current, previous)
    assert "new_commits" in result["changes"]


def test_tests_added_detected():
    current = {"latest_commit_sha": "abc", "readme_length": 100, "has_tests": True,
               "has_ci": False, "release_count": 0, "language_count": 1, "total_code_bytes": 5000}
    previous = {"latest_commit_sha": "abc", "readme_length": 100, "has_tests": False,
                "has_ci": False, "release_count": 0, "language_count": 1, "total_code_bytes": 5000}
    result = detect_changes(current, previous)
    assert "tests_added" in result["changes"]


def test_ci_added_detected():
    current = {"latest_commit_sha": "abc", "readme_length": 100, "has_tests": False,
               "has_ci": True, "release_count": 0, "language_count": 1, "total_code_bytes": 5000}
    previous = {"latest_commit_sha": "abc", "readme_length": 100, "has_tests": False,
                "has_ci": False, "release_count": 0, "language_count": 1, "total_code_bytes": 5000}
    result = detect_changes(current, previous)
    assert "ci_added" in result["changes"]


def test_substantial_growth_detected():
    current = {"latest_commit_sha": "abc", "readme_length": 100, "has_tests": False,
               "has_ci": False, "release_count": 0, "language_count": 1, "total_code_bytes": 20000}
    previous = {"latest_commit_sha": "abc", "readme_length": 100, "has_tests": False,
                "has_ci": False, "release_count": 0, "language_count": 1, "total_code_bytes": 5000}
    result = detect_changes(current, previous)
    assert "substantial_code_growth" in result["changes"]


# --- README content analysis ---

def test_readme_detects_metrics():
    readme = "Our model achieves Macro F0.5: 0.9777 with accuracy: 95.2%"
    signals = analyze_readme_content(readme)
    assert signals["has_metrics"] is True
    assert signals["metric_count"] >= 2


def test_readme_detects_competition():
    readme = "Built for the Amazon ML Challenge 2026. Top-500 qualifier on the leaderboard."
    signals = analyze_readme_content(readme)
    assert signals["has_competition"] is True


def test_readme_detects_architecture():
    readme = """
    # How It Works
    The pipeline orchestrates multiple agents in a multi-agent workflow.
    Each component handles a specific module in the data flow.
    """
    signals = analyze_readme_content(readme)
    assert signals["architecture_depth"] >= 3


def test_readme_detects_tech_sophistication():
    readme = "Uses RAG with vector database embeddings and LLM inference for autonomous agent reasoning."
    signals = analyze_readme_content(readme)
    assert signals["tech_sophistication"] >= 3


def test_readme_detects_live_demo():
    readme = "[Live Demo](https://myapp.onrender.com)"
    signals = analyze_readme_content(readme)
    assert signals["has_live_demo"] is True


def test_readme_detects_scale():
    readme = "Processes 12.5M records across three countries"
    signals = analyze_readme_content(readme)
    assert signals["has_scale_numbers"] is True


def test_readme_empty():
    signals = analyze_readme_content("")
    assert signals["has_metrics"] is False
    assert signals["tech_sophistication"] == 0


def test_readme_detects_structure():
    readme = """# Title
## Setup
- Step one
- Step two
## Architecture
| Col1 | Col2 |
|------|------|
```python
code here
```
![diagram](img.png)
"""
    signals = analyze_readme_content(readme)
    assert signals["section_count"] >= 2
    assert signals["list_item_count"] >= 2
    assert signals["has_table"] is True
    assert signals["has_images"] is True
    assert signals["code_block_count"] >= 1


# --- Commit quality analysis ---

def test_commit_quality_substantive():
    commits = [
        {"commit": {"message": "Implement causal fault attribution with structured evidence collection"}},
        {"commit": {"message": "Add budget-aware recovery orchestration for failed agents"}},
        {"commit": {"message": "Fix edge case in deterministic tool enforcement layer"}},
    ]
    result = analyze_commit_messages(commits)
    assert result["substantive_ratio"] >= 0.6
    assert result["total_analyzed"] == 3


def test_commit_quality_trivial():
    commits = [
        {"commit": {"message": "update"}},
        {"commit": {"message": "fix"}},
        {"commit": {"message": "initial commit"}},
        {"commit": {"message": "wip"}},
    ]
    result = analyze_commit_messages(commits)
    assert result["substantive_ratio"] == 0.0


def test_commit_quality_empty():
    result = analyze_commit_messages([])
    assert result["substantive_ratio"] == 0.0
    assert result["total_analyzed"] == 0


# --- Project structure analysis ---

def test_structure_deep_project():
    tree = [
        {"path": "src", "type": "tree"},
        {"path": "src/core", "type": "tree"},
        {"path": "src/core/engine.py", "type": "blob"},
        {"path": "src/utils/helpers.py", "type": "blob"},
        {"path": "tests", "type": "tree"},
        {"path": "tests/test_engine.py", "type": "blob"},
        {"path": "Dockerfile", "type": "blob"},
        {"path": "pyproject.toml", "type": "blob"},
        {"path": "requirements.txt", "type": "blob"},
        {"path": ".github/workflows/ci.yml", "type": "blob"},
    ]
    result = analyze_project_structure(tree)
    assert result["max_depth"] >= 2
    assert result["has_src_structure"] is True
    assert result["has_test_dir"] is True
    assert result["has_ci_dir"] is True
    assert result["config_variety"] >= 2


def test_structure_flat_project():
    tree = [
        {"path": "main.py", "type": "blob"},
        {"path": "README.md", "type": "blob"},
    ]
    result = analyze_project_structure(tree)
    assert result["max_depth"] == 0
    assert result["has_src_structure"] is False
    assert result["total_files"] == 2


def test_structure_empty():
    result = analyze_project_structure([])
    assert result["max_depth"] == 0
    assert result["dir_count"] == 0
