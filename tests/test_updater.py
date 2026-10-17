from portfolio.updater import (
    update_readme_managed_section, compute_readme_diff, validate_readme,
)


START = "<!-- PORTFOLIO:PROJECTS:START -->"
END = "<!-- PORTFOLIO:PROJECTS:END -->"


def test_managed_section_replaced():
    current = f"# Title\n\n{START}\nold content\n{END}\n\n## Footer"
    new_section = "### New Project\nDescription"
    result = update_readme_managed_section(current, new_section, START, END)
    assert "### New Project" in result
    assert "old content" not in result
    assert "# Title" in result
    assert "## Footer" in result


def test_no_markers_returns_none():
    current = "# Title\nno markers here"
    result = update_readme_managed_section(current, "new", START, END)
    assert result is None


def test_diff_detects_changes():
    current = "line1\nline2\nline3"
    proposed = "line1\nchanged\nline3"
    diff = compute_readme_diff(current, proposed)
    assert diff is not None
    assert len(diff) == 1
    assert diff[0]["line"] == 2


def test_diff_identical():
    content = "same\ncontent"
    diff = compute_readme_diff(content, content)
    assert diff is None


# Test L: README validation
def test_validate_catches_orphan_marker():
    content = "text\n<!-- PORTFOLIO:PROJECTS:START -->\nno end"
    errors = validate_readme(content)
    assert any("marker" in e.lower() for e in errors)


def test_validate_passes_good_readme():
    content = f"# Title\n{START}\ncontent\n{END}\n[link](https://example.com)"
    errors = validate_readme(content)
    assert errors == []
