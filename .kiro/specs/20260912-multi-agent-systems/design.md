# Design: Multi-Agent Systems on AgentCore

## Overview

This design turns the scaffolded `AdmissionAgent/` AgentCore project into a
multi-agent student-services system, implemented in three incremental layers that
map to workshop Modules 7-9:

- **Layer 1 (Module 7):** A single Admission Agent with `retrieve` (Knowledge
  Base) and `query_student_db` (Athena) tools, testable locally with
  `agentcore dev -b`, deployable to AgentCore Runtime, fronted by a Streamlit thin
  client.
- **Layer 2 (Module 8):** AgentCore Memory (short-term session + long-term
  SEMANTIC/USER_PREFERENCE) wired through `AgentCoreMemorySessionManager`.
- **Layer 3 (Module 9):** An orchestrator entrypoint that delegates to two
  `@tool` specialists — the Admission Agent and a new Advisor Requests Agent that
  writes to DynamoDB via an MCP server on AgentCore Gateway.

The design deliberately keeps each layer independently deployable, matching the
AgentCore flat-resource model described in `AdmissionAgent/AGENTS.md`: agents,
memories, and gateways are independent top-level resources in `agentcore.json`,
discovered at runtime via environment variables.

### Guiding constraints (from AGENTS.md)

- **Schema-first authority:** `agentcore.json` / `aws-targets.json` are the source
  of truth. Do not hand-edit generated CDK under `agentcore/cdk/`.
- **Resource identity:** the `name` field is the CloudFormation logical ID.
  Renaming destroys/recreates; other field edits update in place.
- **Invocation input:** validate payloads; require prompt text to be a string;
  normalize a caller-supplied message-history tail with `strip_trailing_tool_use()`
  (already present in the scaffold's `main.py`).

---

## Architecture

### Target architecture (end state, Module 9)

```text
                         ┌─────────────────────────────────────────┐
                         │         AgentCore Runtime                │
   invoke ─────────────► │  main.py  (Orchestrator Agent)           │
   {prompt, session_id,  │   ├─ system prompt: intent routing        │
    actor_id}            │   ├─ session_manager (Memory)             │
                         │   └─ tools:                                │
                         │        ├─ route_to_admission (@tool)       │
                         │        └─ route_to_advisor_requests (@tool)│
                         └───────┬───────────────────────┬───────────┘
                                 │                        │
              ┌──────────────────▼─────┐        ┌─────────▼───────────────────┐
              │ Admission Agent (@tool)│        │ Advisor Requests Agent (@tool)│
              │  tools:                │        │  tools:                       │
              │   ├─ retrieve (KB)     │        │   ├─ MCP tools (via Gateway)  │
              │   └─ query_student_db  │        │   └─ query_student_db         │
              └───────┬────────┬───────┘        └──────┬─────────────┬─────────┘
                      │        │                       │             │
             ┌────────▼──┐  ┌──▼─────────┐      ┌───────▼──────┐  ┌───▼──────────┐
             │ Bedrock   │  │ Athena     │      │ AgentCore    │  │ Athena       │
             │ KB        │  │ Lambda     │      │ Gateway (MCP)│  │ Lambda       │
             │ ONVQOQ7XJB│  │ education- │      │ education-   │  │ (validation) │
             │           │  │ athena-    │      │ advisor-     │  └──────────────┘
             └───────────┘  │ query      │      │ gateway      │
                            └────────────┘      └──────┬───────┘
                                                       │
                                              ┌────────▼─────────┐
                                              │ Lambda           │
                                              │ education-       │
                                              │ advisor-requests │
                                              │  └─ DynamoDB      │
                                              │     education-    │
                                              │     advisor-      │
                                              │     requests      │
                                              └──────────────────┘

  AgentCore Memory (short-term events + long-term SEMANTIC/USER_PREFERENCE)
  ── injected via MEMORY_ADMISSION_AGENT_MEMORY_ID; read/written by session_manager
```

### Incremental delivery

| Layer | Entrypoint shape | New code | New AgentCore resources |
| --- | --- | --- | --- |
| Module 7 | Single Admission Agent | `tools/query_student_db.py`, updated `main.py`, `model/load.py` | runtime `envVars`, `executionRoleArn` |
| Module 8 | + memory session manager | `memory/session.py` | `admission_agent_memory` |
| Module 9 | Orchestrator + 2 specialists | `agents/admission.py`, `agents/advisor_requests.py`, orchestrator `main.py` | `education-advisor-gateway` + target |

---

## Components and Interfaces

### C1: `tools/query_student_db.py` (Athena tool)

**Purpose:** Strands `@tool` that runs read-only SQL against
`education_workshop_db` by invoking the `education-athena-query` Lambda.

**Design decision — adapt, don't copy verbatim.** The existing repo tool
(`src/query_student_db.py`) depends on this repo's `config.get_config()` module,
which does not exist inside the AgentCore app package. The AgentCore app reads
configuration from environment variables directly. Therefore the ported tool will:

- Read `ATHENA_LAMBDA_NAME` and the region from `os.environ` (with the region
  falling back to `AWS_DEFAULT_REGION` / `AWS_REGION`), instead of `get_config()`.
- Keep the rich docstring (schema + SQL notes) verbatim — it is the tool contract
  the LLM relies on to generate correct SQL.
- Keep the lazy boto3 client and the same return contract (list of row dicts on
  success; `{"error": ...}` on failure).

**Interface:**

```python
@tool
def query_student_db(sql: str) -> list | dict: ...
```

Shared by the Admission Agent and (in Module 9) the Advisor Requests Agent for
record validation.

### C2: `model/load.py` (model loader)

**Purpose:** Provide `load_model() -> BedrockModel`.

**Change:** The scaffold currently returns
`BedrockModel(model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0")`. Per
R2, set `model_id="us.anthropic.claude-sonnet-4-6"` (the cross-region inference
profile that avoids the Marketplace subscription error). The `load_model()`
signature and call sites are unchanged.

### C3: `main.py` — Module 7 form (single agent)

**Purpose:** `BedrockAgentCoreApp` entrypoint hosting one Admission Agent.

Building on the scaffold's structure (which already includes `strip_trailing_tool_use`,
`_extract_prompt`, the per-session agent cache, and the streaming `invoke`
entrypoint), the Module 7 changes are:

- `import os, logging`; `logging.basicConfig(level=logging.INFO)`.
- At import: `os.environ["STRANDS_KNOWLEDGE_BASE_ID"] = os.environ["KNOWLEDGE_BASE_ID"]`.
- `from strands_tools import retrieve` and
  `from tools.query_student_db import query_student_db`.
- Replace the placeholder `add_numbers` tool; set `tools = [retrieve, query_student_db]`.
- Replace `DEFAULT_SYSTEM_PROMPT` with the "Alex" Admission Advisor prompt.
- Keep `load_model()`, the session-scoped agent cache, and streaming.

**Prompt (Alex):** university Admission Advisor; use `retrieve` for course-handbook
questions; use `query_student_db` for live student-record lookups via SQL against
`education_workshop_db`; be accurate and cite what the tools return.

### C4: `memory/session.py` — Module 8

**Purpose:** Build an `AgentCoreMemorySessionManager` for short-term (and later
long-term) memory.

**Interface:**

```python
from bedrock_agentcore.memory.integrations.strands import (
    AgentCoreMemorySessionManager, AgentCoreMemoryConfig, RetrievalConfig,
)

def build_session_manager(session_id: str, actor_id: str) -> AgentCoreMemorySessionManager:
    memory_id = os.environ["MEMORY_ADMISSION_AGENT_MEMORY_ID"]
    ...
```

- **Short-term (Ex 1):** config from `memory_id`, `session_id`, `actor_id`.
- **Long-term (Ex 2):** add a `retrieval_config` searching two namespaces —
  `/users/{actor_id}/facts` (SEMANTIC) and `/users/{actor_id}/preferences/`
  (USER_PREFERENCE) — each `RetrievalConfig(top_k=5, relevance_score=0.5)`.

**Wiring in `main.py`:** extract `session_id` and `actor_id` from the payload
(with sensible defaults), build the session manager, and pass it to the `Agent`
via `session_manager=...`. Because memory is deploy-only, `main.py` must degrade
gracefully when `MEMORY_ADMISSION_AGENT_MEMORY_ID` is absent (local dev): if the
env var is missing, skip the session manager so `agentcore dev -b` still runs.

### C5: `agents/admission.py` — Module 9 specialist

**Purpose:** Encapsulate the Admission Agent as a delegable tool.

```python
os.environ["STRANDS_KNOWLEDGE_BASE_ID"] = os.environ["KNOWLEDGE_BASE_ID"]  # module level

@tool
def route_to_admission(query: str, student_id: str | None = None) -> str:
    agent = Agent(model=load_model(),
                  tools=[retrieve, query_student_db],
                  system_prompt=ADMISSION_PROMPT)
    text = query if not student_id else f"[student_id={student_id}] {query}"
    return str(agent(text))
```

This reuses the same "Alex" prompt and tool set as the Module 7 single agent — in
effect the Module 7 agent becomes a callable specialist.

### C6: `agents/advisor_requests.py` — Module 9 specialist

**Purpose:** Evaluate-then-act agent that writes advisor requests via MCP.

```python
@tool
def route_to_advisor_requests(query: str, student_id: str | None = None) -> str:
    mcp_client = MCPClient(lambda: streamablehttp_client(os.environ["ADVISOR_MCP_URL"]))
    with mcp_client:
        mcp_tools = mcp_client.list_tools_sync()
        agent = Agent(model=load_model(),
                      tools=[*mcp_tools, query_student_db],
                      system_prompt=ADVISOR_PROMPT)
        text = query if not student_id else f"[student_id={student_id}] {query}"
        return str(agent(text))
```

- Transport: `streamablehttp_client` from `mcp.client.streamable_http`; `MCPClient`
  from `strands.tools.mcp`; must be used as a context manager.
- Prompt enforces **evaluation before action**: assess reasonableness/complexity,
  check the student record via `query_student_db`, submit via MCP only when
  justified, otherwise give guidance.
- Request types: `course_override`, `advisor_meeting`, `program_change`,
  `special_consideration`.

### C7: `main.py` — Module 9 orchestrator

**Purpose:** Classify intent and delegate to specialists.

- Tools become `[route_to_admission, route_to_advisor_requests]`.
- Keep `BedrockAgentCoreApp`, `load_model()`, logging, the Module 8 session
  manager, and add a Strands conversation manager.
- System prompt: route information lookups → admission; action requests → advisor
  requests; pass `student_id` when identified; support cross-domain queries by
  calling both tools.

### C8: `agentcore/agentcore.json` — runtime configuration

- Runtime `AdmissionAgent` gains `executionRoleArn` and `envVars`
  (`KNOWLEDGE_BASE_ID`, `ATHENA_LAMBDA_NAME`, region, and later `ADVISOR_MCP_URL`).
- Memory resource `admission_agent_memory` (Module 8) with strategies `SEMANTIC`,
  `USER_PREFERENCE` (added via CLI, provisioned by deploy).
- Gateway `education-advisor-gateway` with a `lambda-function-arn` target
  `advisor-requests` (Module 9, added via CLI).
- All edits validated with `agentcore validate` against `.llm-context/` types.

### C9: `agentcore/.env.local` — local dev environment

Holds `KNOWLEDGE_BASE_ID`, `ATHENA_LAMBDA_NAME` (Module 7), and later
`ADVISOR_MCP_URL` (Module 9) so `agentcore dev -b` injects them into the local
container. Never committed (gitignored).

### C10: Streamlit thin client (Module 7, Ex 5)

Existing `streamlit_advisor` app is refactored to: load `AGENTCORE_RUNTIME_ARN`
from `.env`; call `invoke_agent_runtime` via the `bedrock-agentcore` SDK; remove
local `Agent`/tool/Bedrock usage; render `content[0]['text']` with `st.markdown()`.

### C11: `list_memories.py` (Module 8, Ex 2 Step 4)

Standalone inspection script using `boto3.client("bedrock-agentcore")` and
`list_memory_records` over the facts and preferences namespaces for an actor.

---

## Data Flow

### Module 7 — information query

1. Client invokes runtime with `{prompt}` (or validated `messages`).
2. `main.py` validates the payload, resolves/creates the session agent.
3. Agent reasons; for a handbook question it calls `retrieve` (KB `ONVQOQ7XJB`);
   for a record question it calls `query_student_db` (Athena Lambda).
4. Tool results feed back into the model; the agent streams the final answer.

### Module 8 — memory-augmented turn

1. `invoke` extracts `session_id` + `actor_id`; builds the session manager.
2. On each turn the session manager loads short-term events and (long-term)
   retrieves facts/preferences from the actor's namespaces, injecting them into
   context.
3. After the turn, events are written; strategies asynchronously extract long-term
   records (~10-30s later).

### Module 9 — action request (evaluate-then-act)

1. Orchestrator classifies intent; an action request routes to
   `route_to_advisor_requests`.
2. That specialist opens the MCP client to the Gateway, lists MCP tools, and
   validates the student's record via `query_student_db`.
3. If justified, it calls `submit_advisor_request` (MCP → Lambda → DynamoDB);
   otherwise it returns guidance.
4. Cross-domain queries cause the orchestrator to call both specialists and merge
   results.

---

## Error Handling

- **Payload validation:** reuse the scaffold's `_extract_prompt` /
  `strip_trailing_tool_use`; reject non-string prompts and malformed tool results
  with `ValueError`.
- **Athena tool:** `query_student_db` returns `{"error": ...}` on Lambda failure or
  non-200 status rather than raising, so the agent can react and retry with
  corrected SQL.
- **Model access:** if invocations raise `AccessDeniedException` mentioning
  `aws-marketplace:*`, the model ID in `model/load.py` is wrong (must be
  `us.anthropic.claude-sonnet-4-6`).
- **Missing memory env var (local dev):** `main.py` skips the session manager when
  `MEMORY_ADMISSION_AGENT_MEMORY_ID` is unset, so `agentcore dev -b` runs without
  deployed memory.
- **MCP connectivity:** the Advisor Requests specialist wraps MCP usage in the
  client context manager; a missing/invalid `ADVISOR_MCP_URL` surfaces as a tool
  error the orchestrator reports back.
- **Lock drift:** `ModuleNotFoundError` at dev-server start → `uv lock` and
  restart.

---

## Testing Strategy

Per the project convention, tests are not auto-added unless requested. Validation
here is primarily manual/behavioral, matching the workshop's acceptance prompts.

### Local (before upload/deploy)

- `agentcore validate` passes after each `agentcore.json` edit.
- `agentcore dev -b` starts cleanly (no `ModuleNotFoundError`).
- KB prompt ("prerequisites for Database Systems") → `retrieve` span/tool call.
- Record prompt ("Look up student 100016 ...") → `query_student_db` call returning
  real rows.
- Module 9 specialist code imports cleanly and the orchestrator constructs with
  both tools (behavioral routing is validated post-deploy).

### Deploy-time (on the Code Editor EC2 instance)

- `agentcore deploy` (approve one-time CDK bootstrap); `agentcore status` shows the
  runtime (and memory/gateway) `ACTIVE`.
- Memory: multi-turn reference resolution in one session; cross-session preference
  recall after ~30s; `list_memories.py` shows extracted facts/preferences.
- Multi-agent: justified request submits (DynamoDB item with `pending`); trivial
  request declined with guidance; cross-domain query routes to both specialists.
- Observability: `agentcore logs` and `agentcore traces list/get` show
  agent/model/tool/memory spans.
- Streamlit thin client returns the same answers via `invoke_agent_runtime`.

---

## Key Design Decisions

1. **Adapt `query_student_db` to env-var config** rather than importing the repo's
   `config` module, because the AgentCore app package is self-contained and reads
   configuration from injected environment variables. Preserve the docstring
   verbatim (it is the LLM's tool contract).
2. **Reuse the Module 7 agent as the Module 9 `route_to_admission` specialist** —
   same prompt and tools — so Module 9 is a refactor, not a rewrite.
3. **Graceful memory degradation in local dev** so the Module 8 wiring can live in
   `main.py` without breaking `agentcore dev -b` (memory is deploy-only).
4. **Region = `us-west-2`** to match this repo's actual KB/Lambda locations, not
   the workshop's `us-east-1` examples.
5. **Keep the schema-first model:** all resource changes go through
   `agentcore.json` + CLI `add`/`remove`; never hand-edit generated CDK.
6. **Stop at "ready to deploy" locally:** all deploy-only steps (memory, gateway,
   production `envVars`/role, Streamlit ARN wiring) are prepared in code/config but
   executed from the Code Editor EC2 instance per the transport workflow.

## Requirements Traceability

| Requirement | Design components |
| --- | --- |
| R1 Admission tools/prompt | C1, C3 |
| R2 Model config | C2 |
| R3 Dependencies/lock | C8 (pyproject), build flow |
| R4 Runtime env/role | C8, C9 |
| R5 Local dev | C3, C9, Testing (local) |
| R6 Short-term memory | C4, C7 |
| R7 Long-term memory | C4, C11 |
| R8 Gateway/MCP | C8 |
| R9 Specialist tools | C5, C6 |
| R10 Orchestrator | C7 |
| R11 Streamlit thin client | C10 |
| R12 Observability | Testing (deploy), C7 |
| R13 Deploy workflow | C8, Key Decision 6 |
