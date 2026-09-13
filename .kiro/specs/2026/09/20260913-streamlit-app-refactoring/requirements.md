# Requirements: Streamlit App Refactoring (Three Modes)

## Overview

Today the repo has a single Streamlit app at `src/streamlit_advisor.py` that is a
**thin client** (calls the deployed AgentCore runtime). Earlier in its history
the same file was a **thick client** (ran the Strands agent locally). We want
both approaches to coexist as first-class, runnable options, plus a third option
that deploys the thin client to ECS Fargate behind Cognito auth.

Split the work into three self-contained top-level directories:

1. `streamlit-thick-client/` — runs the Strands agent locally (Bedrock + KB +
   Athena tool). No AgentCore runtime needed.
2. `streamlit-thin-client/` — no local agent; invokes the deployed AgentCore
   runtime and renders the streamed response.
3. `deploy-streamlit-app/` — the thin client wrapped with Cognito auth and
   deployed on ECS Fargate (ALB + CloudFront) via CDK, reusing the aws-samples
   baseline already dropped into the repo.

`src/` is reduced to the older standalone scripts only.

## Environment Facts

| Fact | Value |
| --- | --- |
| Region | `us-west-2` (KB, Athena Lambda, AgentCore runtime all live here) |
| Account | `331773567763` |
| KB id | `KNOWLEDGE_BASE_ID` env (repo `.env`) |
| Athena query Lambda | `education-athena-query` (`ATHENA_LAMBDA_NAME`) |
| Model | `us.anthropic.claude-sonnet-4-6` |
| Deployed runtime | `AdmissionAgent_AdmissionAgent-zc7w8t847K` (ARN in `.env` as `AGENTCORE_RUNTIME_ARN`) |
| Laptop constraint | NO Docker; Fargate build/deploy is EC2-only |

## Requirements

### R1 — Self-contained thick client [local-testable]
WHEN a developer runs the thick-client app THE SYSTEM SHALL run the full Strands
advisor agent in-process (Bedrock model + `BedrockKnowledgeBaseStore` KB
retrieval + `query_student_db` Athena tool) without invoking any deployed
AgentCore runtime.
- R1.1 The directory SHALL be self-contained: it carries its own copy of the
  agent code, tool, config, and system prompt (duplication over `src/` is
  acceptable and intended).
- R1.2 It SHALL read configuration (region, model, KB id, Athena Lambda name)
  from the repo-root `.env`.
- R1.3 It SHALL keep one agent instance per browser session for multi-turn
  context.

### R2 — Self-contained thin client [local-testable]
WHEN a developer runs the thin-client app THE SYSTEM SHALL forward each prompt to
the deployed AgentCore runtime via `bedrock-agentcore` `invoke_agent_runtime`
and render the streamed assistant text, running no agent logic locally.
- R2.1 The directory SHALL be self-contained (own copy of client + config).
- R2.2 It SHALL require `AGENTCORE_RUNTIME_ARN` and fail with a clear message if
  unset.
- R2.3 It SHALL use a runtime session id >= 33 chars, one per browser session,
  so server-side memory carries across turns.
- R2.4 It SHALL parse the streamed SSE `data:` frames and extract assistant text
  from `contentBlockDelta.delta.text`.

### R3 — Behavior parity of thick and thin [local-testable]
The two apps SHALL present the same advisor UX (title, caption, sample
questions, chat transcript, clear-conversation control) so they are
interchangeable from the user's point of view; only the backend differs and each
app SHALL make its mode obvious in the sidebar.

### R4 — deploy-streamlit-app wraps the thin client [deploy-only]
WHEN deployed to ECS Fargate THE SYSTEM SHALL serve the thin-client advisor UI
behind Cognito authentication, invoking the deployed AgentCore runtime (NOT a
direct Bedrock `invoke_model`).
- R4.1 It SHALL replace the aws-samples demo `llm.py` (direct Bedrock invoke)
  with the thin-client `invoke_agent_runtime` call.
- R4.2 The task role SHALL grant `bedrock-agentcore:InvokeAgentRuntime` on the
  runtime (not `bedrock:InvokeModel`).
- R4.3 It SHALL pass the authenticated Cognito user's `sub` as `actor_id` in the
  invoke payload, so per-user memory is scoped correctly (the deployed agent
  already accepts `actor_id`).
- R4.4 Region SHALL be `us-west-2` to match the runtime, KB, and Lambda.
- R4.5 Cognito auth, Secrets Manager wiring, VPC/ECS/ALB/CloudFront scaffolding
  from the aws-samples baseline SHALL be reused.

### R5 — src/ reduced to older scripts [local-testable]
`src/` SHALL contain ONLY the older standalone scripts: `simple_agent.py`,
`kb_advisor.py`, `advisor_agent.py`, `query_student_db.py`, `config.py`,
`__init__.py`. The Streamlit entry point (`streamlit_advisor.py`) SHALL move out
of `src/` into the two client directories.

### R6 — Each directory is documented and runnable [local-testable]
Each of the three directories SHALL include a README with its exact run command
and prerequisites. The repo README SHALL point to all three modes and explain
when to use each.

### R7 — No regression to the deployed agent [deploy-only]
This refactor SHALL NOT modify any `AdmissionAgent/app/**` source or
`agentcore.json`. The deployed runtime, memory, and gateway stay as-is.

## Out of Scope
- Changing the deployed AgentCore agent, memory, or gateway.
- Running Fargate build/deploy from the laptop (no Docker) — that is an EC2 step.
- HTTPS between CloudFront and ALB (baseline limitation, noted not fixed).
