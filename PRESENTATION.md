# Presentation: The Latest in (Agentic) AI on AWS

**Audience:** UC Berkeley Data Science students
**Length:** 15-20 minutes, including a live demo
**Goal:** Update students on agentic AI on AWS, grounded in a real end-to-end
app they can reason about — a Streamlit UI on ECS Fargate backed by an agentic
AI backend on Amazon Bedrock AgentCore.

> Starting-point outline for assembling slides. Timings are a guide, not a
> script. The two live tool showcases (Amazon Quick, Kiro) double as the
> evidence for capabilities #3 and #2, and the closing demo is capability #4
> made real — so each claim earns its live moment instead of being a separate
> beat.

## Arc at a glance

1. AI Portfolio — 7 skills to build agentic AI
2. Four things an organization must be good at for agentic AI adoption (the 80/20 thesis)
3. Live: Amazon Quick (the 80% — operational tasks)
4. Live: Kiro (spec-driven agentic coding — the development workflow)
5. Roadmap + solution architecture for the demo
6. Demo: the hosted agentic advisor (the 20% — expert challenges, made real)

## Suggested time budget (~16-18 min)

| Segment | Time |
| --- | --- |
| AI Portfolio (7 skills) | 1.5 min |
| Four org capabilities (80/20) | 4 min (~1 min each) |
| Amazon Quick live | 2 min |
| Kiro live | 2-3 min |
| Roadmap + architecture | 2 min |
| Demo (hosted advisor app) | 3-4 min |
| Buffer / Q&A | 1-2 min |

---

## 1. AI Portfolio — 7 skills for building agentic AI

The set of skills we recommend teams build to be effective with agentic AI.
(Show the seven; name the arc rather than reading each in full.)

_[Fill in the 7 skills.]_

## 2. What organizations must be good at for agentic AI adoption

The core thesis: **use general-purpose assistants for ~80% of operational
challenges; build custom agents for the ~20% of expert challenges.** Four
capabilities:

1. **Build a data foundation for AI.** Expose the backend so agents have real
   context to work with (knowledge bases for unstructured content, structured
   data via queryable services).

2. **Spec-driven agentic AI coding tools.** Kiro, Claude on Amazon Bedrock,
   Codex on Amazon Bedrock — define intent as specs, then let the tools build
   against them.

3. **System prompts + skills for general-purpose office assistants.** Get the
   most out of Amazon Quick, Claude, Copilot, and Gemini to solve ~80% of
   operational business challenges.

4. **Assemble custom agents with an agent framework.** Use Strands Agents with
   intentional model selection (on Amazon Bedrock) and decomposition into
   microservices (on Amazon ECS Fargate and AgentCore) to solve the ~20% of
   expert business challenges.

## 3. Live: Amazon Quick (the 80%)

Show one crisp operational task end to end with a general-purpose assistant.
This is the live evidence for capability #3. (Pre-load the context so it's
instant.)

_[Pick the one operational task to demonstrate.]_

## 4. Live: Kiro (spec-driven agentic coding)

Show how spec-driven development gets through a real development task. This is
the live evidence for capability #2 — one visible win, not a tour.

_[Pick the one dev task/win to show — e.g. the three-mode refactor or a spec
walkthrough from this very repo.]_

## 5. Roadmap + solution architecture

The demo app is capability #1 (data foundation) and capability #4 (custom
agents) made real. Frame it as: **prototype fast, then go live.**

### The three-phase roadmap (see [ROADMAP.md](ROADMAP.md))

- **Phase 1 — Prototype (thick client + Bedrock):** run the agent locally to
  iterate fast on data foundation, model, prompts, and UX. Nothing to deploy.
- **Phase 2 — Go live (thin client + AgentCore):** move the intelligence onto a
  managed runtime. Same UX, faster, less to operate.
- **Phase 3 — Production capstone (hosted):** the thin client on Amazon Cognito
  + Amazon ECS Fargate. Same agent, production-shaped.

Use the **Thick + Bedrock → Thin + AgentCore** comparison table from ROADMAP.md
as the anchor slide.

### Solution architecture (one diagram)

```
Browser
  → Amazon Cognito (auth)
  → Amazon CloudFront → ALB
  → Amazon ECS Fargate  (thin Streamlit UI — Graviton/ARM64)
  → Amazon Bedrock AgentCore Runtime  ── the agent (thick/thin boundary)
        ├── Amazon Bedrock model (Claude Sonnet)
        ├── Knowledge Base retrieval (course handbook RAG)
        ├── query_student_db tool → Athena (live student records)
        ├── AgentCore Memory (per-user, actor_id = Cognito user)
        └── MCP gateway → Lambda → DynamoDB (advisor-request write path)
```

Everything runs in **us-west-2** (region alignment matters for the audience/
customers). Fargate task is intentionally small — the thin client is I/O-bound.

## 6. Demo: the hosted agentic advisor

Open the hosted app live (URL + Cognito login — no terminal, no local setup, no
expiring credentials). Ask 1-2 prompts. This is the 20% expert challenge, made
real, and it retroactively proves capabilities #1 and #4.

**Suggested prompts (pick 2):**
- Course + prerequisite lookup (KB/RAG): "What are the prerequisites for
  Database Systems?"
- Live data + recommendation (Athena + KB): "Look up student 100033's completed
  courses, then recommend which CS courses they're eligible to take next."
- Multi-agent write path: "I'm student 100033. Request an advisor conversation
  for a course override for Data Science: Machine Learning — I completed
  equivalent prerequisites elsewhere and have a 3.8 GPA."

**Demo mechanics:**
- **Pre-warm** ~1 min before with a throwaway prompt (first invoke pays
  cold-start: Fargate task + AgentCore runtime warmup). Optionally show
  cold-vs-warm deliberately as part of the managed-runtime story.
- Fallback if the hosted app hiccups: the local thin client answers the same
  (needs credentials) — keep a terminal ready. Low risk (dedicated persistent
  account).

## Closing thought

> Prototype fast on the thick client, go live on the thin client + AgentCore,
> host it for real users on Cognito + ECS Fargate. General-purpose assistants
> handle the 80%; custom agents handle the 20%. Same UX, same agent —
> progressively less to operate yourself.
