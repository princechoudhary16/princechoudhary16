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
