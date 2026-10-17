import os
import yaml
from pathlib import Path

DEFAULT_CONFIG = {
    "username": "princechoudhary16",
    "schedule_days": 15,
    "mode": "dry-run",  # dry-run | approval | automatic
    "max_featured": 6,
    "min_replacement_margin": 10,
    "min_confidence": 0.80,
    "weights": {
        "technical_depth": 0.25,
        "functionality": 0.20,
        "relevance": 0.20,
        "originality": 0.15,
        "documentation": 0.10,
        "development_evidence": 0.10,
    },
    "professional_keywords": [
        "multi-agent", "ai", "ml", "machine-learning", "llm",
        "aws", "cloud", "rag", "nlp", "computer-vision",
        "scalable", "pipeline", "api", "microservices",
    ],
    "ignored_repos": [],
    "pinned_order_preference": [],
    "notification_channel": "actions-summary",
    "readme_managed_section_start": "<!-- PORTFOLIO:PROJECTS:START -->",
    "readme_managed_section_end": "<!-- PORTFOLIO:PROJECTS:END -->",
}


def load_config(config_path=None):
    config = dict(DEFAULT_CONFIG)
    if config_path is None:
        config_path = Path(__file__).parent / "config.yml"
    if config_path.exists():
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}
        _deep_merge(config, user_config)
    config["github_token"] = os.environ.get("GITHUB_TOKEN", "")
    config["mode"] = os.environ.get("PORTFOLIO_MODE", config["mode"])
    return config


def _deep_merge(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
