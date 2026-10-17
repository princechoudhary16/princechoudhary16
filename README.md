# Hey, I'm Prince 👋

**Software Engineer** building multi-agent AI systems, scalable ML pipelines, and cloud-native applications.

I design systems where autonomous agents collaborate, compete, and make decisions — from AI agents that date on your behalf to ML pipelines that resolve 12.5 million business entities on a laptop. Currently an SDE at [SmartBear](https://smartbear.com), AWS Solutions Architect, and VIT Vellore alum.

I care about building things that actually work at scale, not just impressive demos.

---

## What I'm Working On

### [Proxy Dating](https://github.com/princechoudhary16/proxy-dating) — Agents that date for you
An AI agent reads your LinkedIn and Instagram, builds a psychological profile, then goes on multi-turn dates with other people's agents — speaking in your voice, probing dealbreakers, and ranking compatibility.

**What makes it interesting:**
- Each agent has independent context — neither side sees the other's private dossier
- Structured outputs via Zod schemas, not parsed prose
- Two-stage matching (N² cheap swipes → N·K expensive dates) keeps cost linear-ish
- Live SSE streaming: watch scraping, analysis, and dates happen in real-time

**Stack:** Node.js, Express, Claude API (structured outputs), Apify (scraping), Zod, SSE

[Live Demo →](https://proxy-dating.onrender.com) · [See 26 agents, 52 dates →](https://proxy-dating.onrender.com/#/rankings)

---

### [Business Entity Resolution at Scale](https://github.com/princechoudhary16/amazon-ml-challenge-2026-entity-resolution) — Amazon ML Challenge 2026
Linking 12.5M noisy business records across three countries and eight Indic scripts with no shared identifiers. Qualified for the **Top-500 round**.

**What makes it interesting:**
- Learned Indic→Latin transliteration from training pairs alone (recall: 86% → 98.5%)
- Feature-hashed TF-IDF blocking reduces 10M+ comparisons to ~13 candidates per entity
- Runs entirely on a single 10-core / 16GB laptop — no GPU, no external data
- Macro F0.5: **0.9777** (out-of-fold) / **0.968** (public leaderboard)

**Stack:** Python, LightGBM, scikit-learn, pytest, GitHub Actions CI

---

### [AutoDiagnoseAI](https://github.com/princechoudhary16/AutoDiagnoseAI) — Multimodal Vehicle Diagnostics
AI copilot that diagnoses vehicle faults using photos, service history, and technical manuals. Combines vision, RAG, and structured reasoning.

**Stack:** Vue.js, TypeScript, Python, AWS Bedrock, Qdrant (vector DB), SQLite

---

### [TikTok CodeJam — Agent Launchpad](https://github.com/princechoudhary16/Tiktok_CodeJam_Hack_Track1) — Self-Healing Agent Middleware
Middleware that observes agent executions, classifies failures (transient infra, bad inputs, hallucinations), and performs automated recovery — retry, environment reset, prompt sanitization, model fallback.

**Stack:** TypeScript, Node.js, Docker, OpenTelemetry
