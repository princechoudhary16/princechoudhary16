from portfolio.discovery import detect_changes


# Test A: No changes detected
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


# Test D: Existing project improvement detected
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
