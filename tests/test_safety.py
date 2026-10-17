import pytest
from portfolio.safety import (
    validate_operation, validate_readme_change,
    validate_pin_count, SafetyViolation,
)


# Test I: Forbidden operations are rejected
def test_delete_repo_blocked():
    with pytest.raises(SafetyViolation, match="BLOCKED"):
        validate_operation("delete_repo")


def test_archive_repo_blocked():
    with pytest.raises(SafetyViolation, match="BLOCKED"):
        validate_operation("archive_repo")


def test_transfer_repo_blocked():
    with pytest.raises(SafetyViolation, match="BLOCKED"):
        validate_operation("transfer_repo")


def test_change_visibility_blocked():
    with pytest.raises(SafetyViolation, match="BLOCKED"):
        validate_operation("change_visibility")


def test_rewrite_history_blocked():
    with pytest.raises(SafetyViolation, match="BLOCKED"):
        validate_operation("rewrite_history")


def test_modify_source_blocked():
    with pytest.raises(SafetyViolation, match="BLOCKED"):
        validate_operation("modify_source")


def test_safe_operations_allowed():
    validate_operation("update_readme")
    validate_operation("update_pins")
    validate_operation("read_repo")


# Test G: Conflicting manual edit detected
def test_readme_unmanaged_content_protected():
    current = "# Hello\n<!-- PORTFOLIO:PROJECTS:START -->\nold\n<!-- PORTFOLIO:PROJECTS:END -->\nfooter"
    proposed_bad = "# Changed\n<!-- PORTFOLIO:PROJECTS:START -->\nnew\n<!-- PORTFOLIO:PROJECTS:END -->\nfooter"
    with pytest.raises(SafetyViolation, match="outside the managed section"):
        validate_readme_change(current, proposed_bad,
                              "<!-- PORTFOLIO:PROJECTS:START -->",
                              "<!-- PORTFOLIO:PROJECTS:END -->")


def test_readme_managed_content_allowed():
    current = "# Hello\n<!-- PORTFOLIO:PROJECTS:START -->\nold\n<!-- PORTFOLIO:PROJECTS:END -->\nfooter"
    proposed = "# Hello\n<!-- PORTFOLIO:PROJECTS:START -->\nnew content\n<!-- PORTFOLIO:PROJECTS:END -->\nfooter"
    assert validate_readme_change(current, proposed,
                                  "<!-- PORTFOLIO:PROJECTS:START -->",
                                  "<!-- PORTFOLIO:PROJECTS:END -->")


# Test K: Pin count validated
def test_pin_count_over_limit():
    with pytest.raises(SafetyViolation, match="max"):
        validate_pin_count(["a", "b", "c", "d", "e", "f", "g"])


def test_pin_count_within_limit():
    assert validate_pin_count(["a", "b", "c", "d", "e", "f"])


def test_empty_readme_rejected():
    with pytest.raises(SafetyViolation, match="empty"):
        validate_readme_change("", "new content",
                              "<!-- START -->", "<!-- END -->")
