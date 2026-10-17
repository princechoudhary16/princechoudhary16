import logging
import time

log = logging.getLogger(__name__)


def score_repo(snapshot, config):
    weights = config["weights"]
    keywords = config.get("professional_keywords", [])

    td = _score_technical_depth(snapshot)
    fn = _score_functionality(snapshot)
    rl = _score_relevance(snapshot, keywords)
    og = _score_originality(snapshot)
    dc = _score_documentation(snapshot)
    de = _score_development_evidence(snapshot)

    raw = (
        td * weights["technical_depth"]
        + fn * weights["functionality"]
        + rl * weights["relevance"]
        + og * weights["originality"]
        + dc * weights["documentation"]
        + de * weights["development_evidence"]
    )
    confidence = _compute_confidence(snapshot)
    return {
        "total": round(raw, 2),
        "confidence": round(confidence, 2),
        "breakdown": {
            "technical_depth": round(td, 2),
            "functionality": round(fn, 2),
            "relevance": round(rl, 2),
            "originality": round(og, 2),
            "documentation": round(dc, 2),
            "development_evidence": round(de, 2),
        },
    }


def _score_technical_depth(s):
    score = 0
    lang_count = s.get("language_count", 0)
    score += min(lang_count * 8, 30)
    code_bytes = s.get("total_code_bytes", 0)
    if code_bytes > 100_000:
        score += 25
    elif code_bytes > 30_000:
        score += 18
    elif code_bytes > 10_000:
        score += 12
    elif code_bytes > 3_000:
        score += 6
    if s.get("has_docker"):
        score += 10
    if s.get("has_tests"):
        score += 15
    if s.get("has_ci"):
        score += 10
    if s.get("file_count", 0) > 15:
        score += 10
    elif s.get("file_count", 0) > 5:
        score += 5
    return min(score, 100)


def _score_functionality(s):
    score = 0
    if s.get("has_homepage") or s.get("homepage"):
        score += 25
    if s.get("readme_has_setup"):
        score += 15
    if s.get("readme_has_architecture"):
        score += 15
    if s.get("release_count", 0) > 0:
        score += 15
    if s.get("has_env_example"):
        score += 10
    code_bytes = s.get("total_code_bytes", 0)
    if code_bytes > 50_000:
        score += 20
    elif code_bytes > 10_000:
        score += 10
    return min(score, 100)


def _score_relevance(s, keywords):
    score = 0
    searchable = " ".join([
        s.get("description", ""),
        " ".join(s.get("topics", [])),
        s.get("language", ""),
        " ".join(s.get("languages", {}).keys()),
    ]).lower()
    matches = sum(1 for kw in keywords if kw.lower() in searchable)
    score += min(matches * 15, 60)
    primary = s.get("language", "").lower()
    if primary in ("python", "typescript", "javascript"):
        score += 20
    elif primary in ("c++", "java", "go", "rust"):
        score += 10
    if s.get("topics"):
        score += min(len(s["topics"]) * 5, 20)
    return min(score, 100)


def _score_originality(s):
    score = 50
    if s.get("fork"):
        score -= 40
    if s.get("description") and len(s["description"]) > 30:
        score += 15
    if s.get("stars", 0) > 0:
        score += min(s["stars"] * 5, 20)
    if s.get("forks", 0) > 0:
        score += min(s["forks"] * 5, 15)
    return min(max(score, 0), 100)


def _score_documentation(s):
    score = 0
    readme_len = s.get("readme_length", 0)
    if readme_len > 2000:
        score += 35
    elif readme_len > 500:
        score += 20
    elif readme_len > 100:
        score += 10
    if s.get("readme_has_setup"):
        score += 20
    if s.get("readme_has_architecture"):
        score += 15
    if s.get("has_license"):
        score += 10
    if s.get("has_env_example"):
        score += 10
    if s.get("description") and len(s.get("description", "")) > 20:
        score += 10
    return min(score, 100)


def _score_development_evidence(s):
    score = 0
    commits = s.get("recent_commit_count", 0)
    if commits > 20:
        score += 30
    elif commits > 10:
        score += 22
    elif commits > 5:
        score += 15
    elif commits > 0:
        score += 8
    if s.get("has_ci"):
        score += 15
    if s.get("release_count", 0) > 0:
        score += 15
    pushed = s.get("pushed_at", "")
    if pushed:
        try:
            pushed_ts = time.mktime(time.strptime(pushed[:19], "%Y-%m-%dT%H:%M:%S"))
            days_ago = (time.time() - pushed_ts) / 86400
            if days_ago < 30:
                score += 25
            elif days_ago < 90:
                score += 15
            elif days_ago < 180:
                score += 8
        except (ValueError, OverflowError):
            pass
    if s.get("has_tests"):
        score += 15
    return min(score, 100)


def _compute_confidence(s):
    factors = 0
    total = 0
    if s.get("readme_length", 0) > 100:
        factors += 1
        total += 1
    else:
        total += 1
    if s.get("description"):
        factors += 1
        total += 1
    else:
        total += 1
    if s.get("recent_commit_count", 0) > 2:
        factors += 1
        total += 1
    else:
        total += 1
    if s.get("total_code_bytes", 0) > 1000:
        factors += 1
        total += 1
    else:
        total += 1
    if s.get("language_count", 0) > 0:
        factors += 1
        total += 1
    else:
        total += 1
    return factors / total if total > 0 else 0


def select_featured(scored_repos, current_featured, config):
    max_featured = config["max_featured"]
    margin = config["min_replacement_margin"]
    min_confidence = config["min_confidence"]

    current_set = {r["name"] for r in current_featured}
    candidates = sorted(scored_repos, key=lambda x: x["score"]["total"], reverse=True)

    featured = []
    replaced = []
    added = []

    current_scores = {r["name"]: r["score"]["total"] for r in scored_repos if r["name"] in current_set}
    if not current_set:
        for c in candidates[:max_featured]:
            if c["score"]["confidence"] >= min_confidence:
                featured.append(c)
                added.append(c["name"])
        return featured, replaced, added

    current_weakest = min(current_scores.values()) if current_scores else 0
    weakest_name = min(current_scores, key=current_scores.get) if current_scores else None

    for r in scored_repos:
        if r["name"] in current_set:
            featured.append(r)

    for candidate in candidates:
        if candidate["name"] in current_set:
            continue
        if len(featured) >= max_featured:
            if candidate["score"]["confidence"] < min_confidence:
                continue
            weakest_in_featured = min(featured, key=lambda x: x["score"]["total"])
            if candidate["score"]["total"] - weakest_in_featured["score"]["total"] >= margin:
                replaced.append((weakest_in_featured["name"], candidate["name"]))
                featured.remove(weakest_in_featured)
                featured.append(candidate)
                added.append(candidate["name"])
        else:
            if candidate["score"]["confidence"] >= min_confidence:
                featured.append(candidate)
                added.append(candidate["name"])

    return featured, replaced, added
