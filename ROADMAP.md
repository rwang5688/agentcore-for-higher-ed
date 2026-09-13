# Roadmap: An Agentic Advisor for Higher Ed

A Strands Agents + Amazon Bedrock (Knowledge Base + model) + AgentCore demo for
Higher Education. The Peculiar University advisor is **one application with one
UX** shipped in three self-contained flavors — each a phase in the path from
rapid prototype to production.

## Overview: prototype fast, then go live

Building an agent has two very different jobs, and one architecture is not best
at both:

- **Prototype fast (Thick Client + Bedrock).** Run the whole agent locally so you
  can iterate at the speed of thought on the things that actually make an agent
  good: the **data foundation** (Knowledge Base content, the Athena/SIS schema),
  **model selection**, **system prompts**, **tools**, and the **user
  experience**. There is nothing to deploy — edit, `streamlit run`, repeat.

- **Go live (Thin Client + AgentCore).** Once the behavior is right, the local
  design does not operate or scale well. Moving the intelligence onto a managed
  AgentCore runtime is what makes it production-viable — and, as the demo shows,
  it is also simply faster and smoother.

You develop on the left and ship on the right.

### Thick Client + Bedrock → Thin Client + AgentCore

| Dimension | Thick Client + Bedrock (local) | Thin Client + AgentCore (managed) |
| --- | --- | --- |
| **Best for** | Rapid prototyping, feature testing | Going live, real users |
| **Where agent logic runs** | In-process on your machine | Managed AgentCore runtime (in-region) |
| **Startup / warmth** | Cold: rebuilds agent, model client, KB store, tools each session | Warm: runtime keeps everything initialized |
| **Tool + data latency** | Each Athena/Lambda/KB call round-trips from laptop over the internet | Calls happen inside the region, next to the runtime |
| **Conversation memory** | Full history held locally and re-sent to the model every turn | Managed AgentCore Memory (short + long term) carries context |
| **Client workload** | Model orchestration + tool marshalling compete with the UI | One `invoke_agent_runtime` call + streaming |
| **Perceived speed** | Slower, heavier on multi-tool prompts | Noticeably faster and smoother |
| **Operations** | Runs where your credentials are; you operate it | Managed runtime: scaling, observability, memory handled for you |
| **Auth** | Your shell credentials | Add Cognito in Phase 3 |
| **What you iterate on** | Data foundation, model, prompts, tools, UX | Same agent, now hosted — no client rewrite to go live |

**The takeaway:** the Thick Client is a superb lab for getting the agent *right*.
To take it *live*, you go Thin Client on AgentCore — for the warm runtime,
in-region tool calls, managed memory, and a client that does almost nothing. Same
UX, same answer quality, less to operate.

## The standard roadmap

```
  Phase 1                     Phase 2                        Phase 3
  Prototype                   Go live                        Production capstone

  streamlit-thick-client      streamlit-thin-client          deploy-streamlit-app
  + Bedrock                   + AgentCore                    (thin client hosted)
  ────────────────           ─────────────────              ──────────────────────
  local Strands agent   ──►   deployed AgentCore runtime ──► same runtime, on
  (KB + model + Athena)       (thin invoke client)           Cognito + ECS Fargate
```

### Phase 1 — Prototype: `streamlit-thick-client/` + Bedrock

The lab. The Streamlit app runs the full Strands agent **in-process**: Bedrock
model inference, Knowledge Base retrieval (course handbook RAG), and the
`query_student_db` Athena tool all execute locally with your own credentials.

- **Runs where:** your laptop. **Agent logic:** local. **Auth:** none.
- **Use it to:** iterate on data foundation, model selection, system prompts,
  tools, and UX with zero deploy friction.

### Phase 2 — Go live: `streamlit-thin-client/` + AgentCore

The same UX becomes a **thin client**. Every prompt is forwarded to the deployed
AgentCore runtime via `invoke_agent_runtime`; the UI renders the streamed
response and runs no agent logic. Model inference, KB retrieval, Athena queries,
multi-agent orchestration, and memory all live on the managed runtime.

- **Runs where:** your laptop (or anywhere) — it only calls AWS. **Agent logic:**
  the deployed runtime. **Auth:** none yet.
- **Why it's the going-live move:** warm runtime, in-region tool calls, managed
  memory, near-zero client work — faster and less to operate (see the table).

### Phase 3 — Production capstone: `deploy-streamlit-app/`

The Phase 2 thin client, wrapped for real users: **Cognito authentication** in
front, running on **ECS Fargate** behind an ALB and CloudFront, deployed with
CDK. It reuses the aws-samples Streamlit-on-Fargate shell, with the demo
inference path replaced by the thin-client logic. The authenticated Cognito
username is passed as `actor_id`, so long-term memory is scoped **per user**.

- **Runs where:** ECS Fargate (built + deployed from the EC2 Code Editor; the
  laptop has no Docker). **Agent logic:** the deployed runtime. **Auth:** Cognito.
- **Shows:** a production-shaped deployment — authenticated, hosted, per-user
  memory — with **no change to the agent** from Phase 2.

## What stays constant across phases

- **Same UX:** title, caption, sample questions, chat transcript, and
  clear-conversation control are identical in all three — the *only* thing that
  changes is where the intelligence runs.
- **Same deployed agent:** Phases 2 and 3 invoke the *same* `AdmissionAgent`
  runtime. Going from thin client to hosted requires **no agent-side change** —
  only the client gains Cognito and supplies a real `actor_id`.
- **Region:** `us-west-2` throughout (Knowledge Base, Athena Lambda, and the
  AgentCore runtime all live there).

## Directory map

| Phase | Directory | Backend | Auth | Deploy target |
| --- | --- | --- | --- | --- |
| 1 — Prototype | `streamlit-thick-client/` | Local Strands agent + Bedrock | none | laptop |
| 2 — Go live | `streamlit-thin-client/` | Deployed AgentCore runtime | none | laptop |
| 3 — Capstone | `deploy-streamlit-app/` | Deployed AgentCore runtime | Cognito | ECS Fargate |

Each directory is self-contained (its own `config.py` and app code) and carries
its own README with exact prerequisites and run commands. `src/` is kept for
backward compatibility with the earlier workshop scripts (`simple_agent`,
`kb_advisor`, `advisor_agent`, `query_student_db`), not as a shared library.

---

## Appendix: how this roadmap was built with Kiro

The raw prompt log below is the "how we got here" record — a live example of
defining and building a roadmap in conversation with Kiro.

**Prompt 1 —** Review 20260912 context; build out the three Streamlit app
options (thick = the pre-AgentCore local app, thin = the current invoke-runtime
app, deploy = Cognito + ECS Fargate from aws-samples). Split into three
directories with `src/` for older scripts; keep thick and thin self-contained
even if it means a little duplication.

**Prompt 2 —** Preferences per directory: `src/` = older workshop scripts (DRY
sharing only if it isn't pedantic); `streamlit-thick-client` = everything to run
the app before AgentCore; `streamlit-thin-client` = the invoke-AgentCore logic
that also merges into `deploy-streamlit-app/docker_app`; `deploy-streamlit-app` =
the Cognito + ECS Fargate shell, with the CDK task role revised to invoke
AgentCore.

**Prompt 3 —** Final call: three fully self-contained directories. `src/` for
backward compatibility; thick runs ALL AWS invocations locally; thin only invokes
the AgentCore backend. This is the Strands + Bedrock KB + model + AgentCore demo
for Higher Ed going forward — three app options give customers flexibility and a
live example of a three-phase roadmap.
