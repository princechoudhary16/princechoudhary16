FORBIDDEN_OPERATIONS = {
    "delete_repo", "archive_repo", "transfer_repo",
    "change_visibility", "rewrite_history", "delete_branch",
    "delete_tag", "modify_source", "change_permissions",
}


class SafetyViolation(Exception):
    pass


def validate_operation(operation, details=""):
    if operation in FORBIDDEN_OPERATIONS:
        raise SafetyViolation(
            f"BLOCKED: '{operation}' is a forbidden operation. {details}"
        )


def validate_readme_change(current_content, proposed_content, managed_start, managed_end):
    if not current_content or not proposed_content:
        raise SafetyViolation("README content cannot be empty")
    current_outside = _extract_unmanaged(current_content, managed_start, managed_end)
    proposed_outside = _extract_unmanaged(proposed_content, managed_start, managed_end)
    if current_outside != proposed_outside:
        raise SafetyViolation(
            "Proposed change modifies content outside the managed section"
        )
    return True


def validate_proposed_changes(changes):
    for change in changes:
        if change.get("type") in FORBIDDEN_OPERATIONS:
            raise SafetyViolation(
                f"BLOCKED: proposed change includes forbidden operation '{change['type']}'"
            )
    return True


def validate_repos_exist(repo_names, available_repos):
    available = {r["name"] for r in available_repos}
    missing = set(repo_names) - available
    if missing:
        raise SafetyViolation(f"Repos not found: {missing}")
    return True


def validate_pin_count(repos, max_pins=6):
    if len(repos) > max_pins:
        raise SafetyViolation(
            f"Cannot pin {len(repos)} repos (max {max_pins})"
        )
    return True


def _extract_unmanaged(content, start_marker, end_marker):
    s = content.find(start_marker)
    e = content.find(end_marker)
    if s == -1 or e == -1:
        return content
    return content[:s] + content[e + len(end_marker):]
