# Hey, I'm Prince 👋

**MSc AI student at [NTU Singapore](https://www.ntu.edu.sg)** building multi-agent AI systems, scalable ML pipelines, and cloud-native applications.

I design systems where autonomous agents collaborate, compete, and make decisions — from AI agents that date on your behalf to ML pipelines that resolve 12.5 million business entities on a laptop. Previously an SDE at SmartBear, AWS Certified Solutions Architect, and VIT alum.

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

---

## Technical Skills

**Languages:** Python · JavaScript · TypeScript · C++ · SQL · Dart

**AI & ML:** LLM APIs (Claude, Gemini) · Structured Outputs · Multi-Agent Systems · RAG · LightGBM · Computer Vision · NLP

**Cloud & Infrastructure:** AWS (Bedrock, Lambda, S3, Rekognition, SNS, Amplify, CloudWatch) · Docker · GitHub Actions · Render

**Frameworks:** Node.js · Express · Vue.js · React · Flask · LangChain

**Data:** Qdrant · SQLite · FAISS · Pandas · NumPy

---

## Competitions & Hackathons

| Event | What I Built | Result |
|---|---|---|
| **Amazon ML Challenge 2026** | Entity resolution pipeline for 12.5M records | Top-500 |
| **TikTok CodeJam** | Self-healing middleware for agent workflows | Hackathon submission |

---

## Background

- **MSc in Artificial Intelligence at NTU Singapore** — Director of Career and Academic at CCDS Graduate Students' Club
- **Ex-SDE at SmartBear** — 2 years building developer tools (SDE → Associate Software Developer → Intern)
- **Ex-Intern at Swiggy** — software engineering
- **Amazon ML Summer School** alumni
- **AWS Certified Solutions Architect** · **iSAQB CPSA-FL**
- **B.Tech in Computer Science from VIT** (2020–2024)

---

## Let's Connect

I'm interested in multi-agent AI, ML systems, and building tools that make complex systems reliable.

- **LinkedIn:** [prince-choudhary-b34407245](https://linkedin.com/in/prince-choudhary-b34407245)
- **Email:** pc16oct@gmail.com
- **GitHub:** You're already here — explore the repos below ↓

---

<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github-readme-stats.vercel.app/api?username=princechoudhary16&show_icons=true&theme=github_dark&hide_border=true&count_private=true&hide_title=true" />
  <source media="(prefers-color-scheme: light)" srcset="https://github-readme-stats.vercel.app/api?username=princechoudhary16&show_icons=true&theme=default&hide_border=true&count_private=true&hide_title=true" />
  <img src="https://github-readme-stats.vercel.app/api?username=princechoudhary16&show_icons=true&theme=default&hide_border=true&count_private=true&hide_title=true" alt="GitHub Stats" />
</picture>
</p>

<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github-readme-stats.vercel.app/api/top-langs/?username=princechoudhary16&layout=compact&theme=github_dark&hide_border=true&langs_count=8" />
  <source media="(prefers-color-scheme: light)" srcset="https://github-readme-stats.vercel.app/api/top-langs/?username=princechoudhary16&layout=compact&theme=default&hide_border=true&langs_count=8" />
  <img src="https://github-readme-stats.vercel.app/api/top-langs/?username=princechoudhary16&layout=compact&theme=default&hide_border=true&langs_count=8" alt="Top Languages" />
</picture>
</p>

<p align="center"><i>If a project interests you, open an issue or reach out — I'm always up for a good technical conversation.</i></p>
