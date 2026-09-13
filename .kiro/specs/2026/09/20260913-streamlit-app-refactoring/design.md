# Design: Streamlit App Refactoring (Three Modes)

## Target Layout

```
repo/
├── src/                         # older standalone scripts ONLY (R5)
│   ├── simple_agent.py
│   ├── kb_advisor.py            # CLI that builds the local agent
│   ├── advisor_agent.py         # create_agent() factory + SYSTEM_PROMPT
│   ├── query_student_db.py      # @tool
│   ├── config.py                # get_config()
│   └── __init__.py
│
├── streamlit-thick-client/      # MODE 1: local Strands agent (R1)
│   ├── app.py                   # Streamlit UI + create_agent(), agent per session
│   ├── advisor_agent.py         # own copy (self-contained)
│   ├── query_student_db.py      # own copy
│   ├── config.py                # own copy
│   ├── requirements.txt
│   └── README.md
│
├── streamlit-thin-client/       # MODE 2: invoke deployed runtime (R2)
│   ├── app.py                   # Streamlit UI + invoke_agent_runtime
│   ├── config.py                # own copy (agentcore_runtime_arn, region)
│   ├── requirements.txt
│   └── README.md
│
└── deploy-streamlit-app/        # MODE 3: thin client on ECS Fargate (R4)
    ├── app.py                   # CDK app entry (existing)
    ├── cdk/cdk_stack.py         # Cognito + VPC + ECS + ALB + CloudFront (adapted)
    ├── docker_app/
    │   ├── app.py               # Streamlit + Cognito auth + thin-client invoke
    │   ├── config_file.py       # STACK_NAME, region us-west-2, runtime ARN
    │   ├── utils/auth.py        # Cognito (reused as-is)
    │   ├── utils/agentcore.py   # NEW: invoke_agent_runtime (replaces llm.py)
    │   ├── requirements.txt
    │   └── Dockerfile
    └── README.md
```

## Key Decisions

### D1 — Self-contained over shared module (user directive)
Thick and thin each carry their own `config.py` (and thick its `advisor_agent.py`
+ `query_student_db.py`). We deliberately duplicate rather than import from
`src/`. Rationale: the user wants each app to stand alone so it can be copied,
deployed, or reasoned about without cross-directory imports. `src/` is legacy
reference, not a shared library.

### D2 — Thick client = today's `advisor_agent.create_agent()` in a Streamlit UI
The thick client is the pre-AgentCore design. `create_agent()` already builds the
agent with `BedrockKnowledgeBaseStore` + `MemoryManager` + `query_student_db`.
The app instantiates one agent per browser session (cached in `st.session_state`)
and calls `agent(prompt)` per turn. UI (title, caption, samples, transcript,
clear button) mirrors the thin client so they're interchangeable (R3).

Note: local KB retrieval needs `bedrock:GetKnowledgeBase` + `Retrieve` on the
caller's credentials (same permission lesson from the deployed agent). The
laptop's Isengard Admin role has this.

### D3 — Thin client = today's `src/streamlit_advisor.py`, moved and trimmed
Move the current thin-client file into `streamlit-thin-client/app.py` with its
own `config.py` (only the fields it needs: `agentcore_runtime_arn`,
`aws_region`). Behavior unchanged: `invoke_agent_runtime`, `session-<uuid>` id
(>=33 chars), SSE `data:` parsing for `contentBlockDelta.delta.text`.

### D4 — deploy-streamlit-app = thin client + Cognito on Fargate
Reuse the aws-samples baseline's CDK (Cognito user pool/client, Secrets Manager,
VPC, ECS Fargate, ALB with custom-header gate, CloudFront). Replace the demo
inference path:
- Delete/retire `docker_app/utils/llm.py` (direct `bedrock invoke_model`,
  claude-v2).
- Add `docker_app/utils/agentcore.py` — the thin-client `invoke_agent_runtime`
  logic (same SSE parsing), reading the runtime ARN + region from `config_file.py`.
- `docker_app/app.py`: keep Cognito login gate; after login, render the advisor
  chat UI; on each prompt call the agentcore util, passing
  `actor_id = authenticator.get_username()` (Cognito sub/username) so memory is
  per-user (R4.3).
- `cdk/cdk_stack.py`: swap the Bedrock IAM policy from `bedrock:InvokeModel` to
  `bedrock-agentcore:InvokeAgentRuntime` scoped to the runtime ARN (R4.2);
  region → us-west-2 (R4.4).
- `config_file.py`: set `DEPLOYMENT_REGION = "us-west-2"`, add
  `AGENTCORE_RUNTIME_ARN` (and drop unused `BEDROCK_REGION`/claude-v2 bits).

### D5 — actor_id from Cognito
The deployed agent's `main.py` already reads `actor_id` from the invoke payload
(defaults to `default-actor`). The thick and thin local apps can keep the
default; only deploy-streamlit-app supplies a real per-user `actor_id` from the
Cognito identity. No agent-side change (R7).

### D6 — Requirements pinning
- Thick client: `streamlit`, `strands-agents`, `boto3`, `python-dotenv` (matches
  what the local agent already uses). No `strands-agents-tools` (we use the core
  KB store, per the Module 7 cleanup decision).
- Thin client: `streamlit`, `boto3`, `python-dotenv` only (no strands).
- deploy-streamlit-app docker: `streamlit`, `boto3`, `streamlit-cognito-auth`
  (drop the claude-v2 demo assumptions).

## Data Flow

### Thick client (Mode 1)
```
browser → Streamlit app.py → Strands Agent (local)
   ├── BedrockKnowledgeBaseStore → Bedrock KB Retrieve/GetKnowledgeBase (us-west-2)
   ├── query_student_db tool → Lambda education-athena-query → Athena
   └── Bedrock model invoke (claude-sonnet-4-6)
```

### Thin client (Mode 2)
```
browser → Streamlit app.py → invoke_agent_runtime(ARN, session) → AgentCore runtime
   (all agent logic server-side) → streamed SSE → app parses delta.text
```

### deploy-streamlit-app (Mode 3)
```
browser → CloudFront → ALB (custom header) → ECS Fargate task (Streamlit)
   → Cognito login gate (auth.py + Secrets Manager)
   → utils/agentcore.py invoke_agent_runtime(actor_id=cognito sub) → AgentCore runtime
```

## Error Handling
- Thin client: missing `AGENTCORE_RUNTIME_ARN` → `st.error` + `st.stop` (R2.2).
- Thick client: missing `KNOWLEDGE_BASE_ID` → fail fast via `get_config()`
  (`os.environ[...]` KeyError), surfaced as a Streamlit error.
- Both parse defensively: if a streamed/raw body isn't the expected shape, fall
  back to rendering the raw text.

## Testing (laptop, no Docker)
- Thick: import-smoke (`python -c "import app"` won't run Streamlit, so verify
  `advisor_agent`/`query_student_db`/`config` import cleanly) + optional
  `streamlit run` by the user (hits real AWS with laptop creds).
- Thin: import-smoke of `app.py` + `config.py`; user can `streamlit run`.
- deploy: `cdk synth` is EC2/Docker territory; on the laptop we only verify
  Python imports of `docker_app/app.py` + `utils/agentcore.py` + `config_file.py`
  and that `cdk_stack.py` is syntactically valid. Actual `cdk deploy` is an EC2
  step (documented in README, human-run).

## Traceability
| Requirement | Design |
| --- | --- |
| R1 thick self-contained | D1, D2, D6; thick dir |
| R2 thin self-contained | D1, D3, D6; thin dir |
| R3 parity | D2, D3 (shared UI shape) |
| R4 deploy wraps thin | D4, D5 |
| R5 src reduced | Target Layout; move streamlit_advisor.py out |
| R6 docs | READMEs per dir + repo README |
| R7 no agent regression | D5 (payload-only), no AdmissionAgent edits |
