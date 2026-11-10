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
    pi = _score_portfolio_impact(snapshot)

    raw = (
        td * weights.get("technical_depth", 0.20)
        + fn * weights.get("functionality", 0.15)
        + rl * weights.get("relevance", 0.15)
        + og * weights.get("originality", 0.10)
        + dc * weights.get("documentation", 0.10)
        + de * weights.get("development_evidence", 0.10)
        + pi * weights.get("portfolio_impact", 0.20)
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
            "portfolio_impact": round(pi, 2),
        },
    }


def _score_technical_depth(s):
    score = 0
    lang_count = s.get("language_count", 0)
    score += min(lang_count * 8, 25)

    code_bytes = s.get("total_code_bytes", 0)
    if code_bytes > 100_000:
        score += 20
    elif code_bytes > 30_000:
        score += 15
    elif code_bytes > 10_000:
        score += 10
    elif code_bytes > 3_000:
        score += 5

    if s.get("has_docker"):
        score += 8
    if s.get("has_tests"):
        score += 12
    if s.get("has_ci"):
        score += 8

    structure = s.get("structure", {})
    depth = structure.get("max_depth", 0)
    if depth >= 4:
        score += 10
    elif depth >= 2:
        score += 5

    config_variety = structure.get("config_variety", 0)
    score += min(config_variety * 3, 12)

    if structure.get("has_src_structure"):
        score += 5
    if structure.get("has_test_dir"):
        score += 5

    return min(score, 100)


def _score_functionality(s):
    score = 0
    if s.get("has_homepage") or s.get("homepage"):
        score += 20

    readme_signals = s.get("readme_signals", {})
    if readme_signals.get("has_live_demo"):
        score += 15

    if s.get("readme_has_setup"):
        score += 12
    if s.get("readme_has_architecture"):
        score += 12

    if s.get("release_count", 0) > 0:
        score += 10
    if s.get("has_env_example"):
        score += 8

    code_bytes = s.get("total_code_bytes", 0)
    if code_bytes > 50_000:
        score += 15
    elif code_bytes > 10_000:
        score += 8

    structure = s.get("structure", {})
    if structure.get("total_files", 0) > 30:
        score += 8
    elif structure.get("total_files", 0) > 15:
        score += 4

    return min(score, 100)


def _score_relevance(s, keywords):
    score = 0
    searchable = " ".join([
        s.get("description", ""),
        " ".join(s.get("topics", [])),
        s.get("language", ""),
        " ".join(s.get("languages", {}).keys()),
    ]).lower()

    readme_signals = s.get("readme_signals", {})
    tech_soph = readme_signals.get("tech_sophistication", 0)
    score += min(tech_soph * 5, 25)

    matches = sum(1 for kw in keywords if kw.lower() in searchable)
    score += min(matches * 12, 40)

    primary = s.get("language", "").lower()
    if primary in ("python", "typescript", "javascript"):
        score += 15
    elif primary in ("c++", "java", "go", "rust"):
        score += 8

    if s.get("topics"):
        score += min(len(s["topics"]) * 4, 15)

    return min(score, 100)


def _score_originality(s):
    score = 40
    if s.get("fork"):
        score -= 35

    if s.get("description") and len(s["description"]) > 30:
        score += 12
    if s.get("stars", 0) > 0:
        score += min(s["stars"] * 5, 20)
    if s.get("forks", 0) > 0:
        score += min(s["forks"] * 5, 15)

    readme_signals = s.get("readme_signals", {})
    if readme_signals.get("has_quality_comparison"):
        score += 10
    if readme_signals.get("has_scale_numbers"):
        score += 8

    return min(max(score, 0), 100)


def _score_documentation(s):
    score = 0
    readme_len = s.get("readme_length", 0)
    if readme_len > 2000:
        score += 25
    elif readme_len > 500:
        score += 15
    elif readme_len > 100:
        score += 8

    if s.get("readme_has_setup"):
        score += 12
    if s.get("readme_has_architecture"):
        score += 10
    if s.get("has_license"):
        score += 5
    if s.get("has_env_example"):
        score += 5

    if s.get("description") and len(s.get("description", "")) > 20:
        score += 8

    readme_signals = s.get("readme_signals", {})
    sections = readme_signals.get("section_count", 0)
    score += min(sections * 3, 12)

    if readme_signals.get("has_images"):
        score += 5
    if readme_signals.get("code_block_count", 0) > 0:
        score += 5
    if readme_signals.get("has_table"):
        score += 3

    list_items = readme_signals.get("list_item_count", 0)
    score += min(list_items, 10)

    return min(score, 100)


def _score_development_evidence(s):
    score = 0
    commits = s.get("recent_commit_count", 0)
    if commits > 20:
        score += 25
    elif commits > 10:
        score += 18
    elif commits > 5:
        score += 12
    elif commits > 0:
        score += 6

    if s.get("has_ci"):
        score += 12
    if s.get("release_count", 0) > 0:
        score += 10

    pushed = s.get("pushed_at", "")
    if pushed:
        try:
            pushed_ts = time.mktime(time.strptime(pushed[:19], "%Y-%m-%dT%H:%M:%S"))
            days_ago = (time.time() - pushed_ts) / 86400
            if days_ago < 30:
                score += 20
            elif days_ago < 90:
                score += 12
            elif days_ago < 180:
                score += 6
        except (ValueError, OverflowError):
            pass

    if s.get("has_tests"):
        score += 10

    commit_quality = s.get("commit_quality", {})
    ratio = commit_quality.get("substantive_ratio", 0)
    if ratio >= 0.5:
        score += 10
    elif ratio >= 0.3:
        score += 5

    structure = s.get("structure", {})
    if structure.get("has_ci_dir"):
        score += 5

    return min(score, 100)


def _score_portfolio_impact(s):
    score = 0
    readme_signals = s.get("readme_signals", {})

    if readme_signals.get("has_metrics"):
        score += 18
        score += min(readme_signals.get("metric_count", 0) * 2, 8)

    if readme_signals.get("has_quality_comparison"):
        score += 12
        score += min(readme_signals.get("quality_comparison_count", 0) * 2, 6)

    if readme_signals.get("has_competition"):
        score += 12

    if readme_signals.get("has_scale_numbers"):
        score += 8

    if readme_signals.get("has_live_demo"):
        score += 8

    arch_depth = readme_signals.get("architecture_depth", 0)
    score += min(arch_depth * 3, 12)

    tech_soph = readme_signals.get("tech_sophistication", 0)
    score += min(tech_soph * 2, 12)

    structure = s.get("structure", {})
    if structure.get("has_src_structure") and structure.get("has_test_dir"):
        score += 5
    if structure.get("config_variety", 0) >= 3:
        score += 5

    if not s.get("fork"):
        score += 4

    if s.get("total_code_bytes", 0) < 2000:
        score -= 10

    desc = s.get("description", "")
    if len(desc) > 50:
        score += 4

    return min(max(score, 0), 100)


def _compute_confidence(s):
    factors = 0
    total = 7

    if s.get("readme_length", 0) > 100:
        factors += 1
    if s.get("description"):
        factors += 1
    if s.get("recent_commit_count", 0) > 2:
        factors += 1
    if s.get("total_code_bytes", 0) > 1000:
        factors += 1
    if s.get("language_count", 0) > 0:
        factors += 1

    readme_signals = s.get("readme_signals", {})
    if readme_signals.get("section_count", 0) >= 2:
        factors += 1

    structure = s.get("structure", {})
    if structure.get("total_files", 0) > 5:
        factors += 1

    return factors / total


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
