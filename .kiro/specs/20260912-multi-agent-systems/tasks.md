# Tasks: Multi-Agent Systems on AgentCore

Implementation plan for the AdmissionAgent build-out (Modules 7-9). Tasks are
grouped so all **local-testable** coding/config happens first (up to the point the
code is ready to upload/deploy), followed by **deploy-only** steps performed on the
Amazon Linux 2023 Code Editor EC2 instance.

Legend: **[local]** = doable and verifiable on this laptop; **[deploy]** = requires
provisioned AWS resources, run from the Code Editor EC2 instance.

---

## Phase 0: Environment activation (local)

- [ ] 0.1 Repopulate the CDK Node environment: `npm install` under
  `AdmissionAgent/agentcore/cdk/`. _(R13)_
- [ ] 0.2 Repopulate the Python env: `uv sync` under
  `AdmissionAgent/app/AdmissionAgent/`. _(R3)_
- [ ] 0.3 Confirm `agentcore --version` (0.29.0) and `agentcore validate` runs
  clean against the untouched scaffold. _(R4.4)_

## Phase 1: Module 7 — Admission Agent (local-testable)

- [x] 1.1 **[local]** Add the Athena tool at
  `app/AdmissionAgent/tools/query_student_db.py` (+ `tools/__init__.py`). Adapt
  from `src/query_student_db.py`: read `ATHENA_LAMBDA_NAME` and region from
  `os.environ` (fallback `AWS_DEFAULT_REGION`/`AWS_REGION`) instead of
  `config.get_config()`; keep the full docstring and the list/`{"error":...}`
  return contract. _(R1.1, R1.7)_ — DONE
- [x] 1.2 **[local]** Update `app/AdmissionAgent/model/load.py` to
  `model_id="us.anthropic.claude-sonnet-4-6"`. _(R2.1, R2.2)_ — DONE
- [x] 1.2b **[local]** Pin `runtimeVersion` in `agentcore.json` from the scaffold
  default `PYTHON_3_14` to `PYTHON_3_13` (3.14 too new). Logged in ISSUES.md. — DONE
- [x] 1.3 **[local]** Update `app/AdmissionAgent/main.py`: logging;
  `STRANDS_KNOWLEDGE_BASE_ID` from `KNOWLEDGE_BASE_ID`; import `retrieve` +
  `query_student_db`; `tools = [retrieve, query_student_db]`; "Alex" system prompt;
  removed example ExaAI MCP client and `add_numbers`; kept `BedrockAgentCoreApp`,
  `load_model()`, session cache, streaming, `_extract_prompt`/`strip_trailing_tool_use`.
  _(R1.1-R1.5)_ — DONE
- [x] 1.4 **[local]** Update `pyproject.toml` (added `strands-agents-tools`); ran
  `uv lock`. _(R3.1, R3.2)_ — DONE. NOTE: `strands-agents-tools` pulls a large
  transitive tree (slack-sdk, pillow, sympy, markdownify, rich, ...) though we only
  use `retrieve`. Flagged for possible slimming (see session notes / open question).
- [x] 1.5 **[local]** Created `agentcore/.env.local` with
  `KNOWLEDGE_BASE_ID=ONVQOQ7XJB`, `ATHENA_LAMBDA_NAME=education-athena-query`,
  `AWS_DEFAULT_REGION=us-west-2`. _(R4.3, R5)_ — DONE
- [x] 1.6 **[local]** Edit `agentcore/agentcore.json` runtime entry: added
  `envVars` (`KNOWLEDGE_BASE_ID=ONVQOQ7XJB`, `ATHENA_LAMBDA_NAME=education-athena-query`,
  `AWS_DEFAULT_REGION=us-west-2`) and
  `executionRoleArn=arn:aws:iam::331773567763:role/agentcore-agent-role`;
  `agentcore validate` → **Valid**. _(R4.1, R4.2, R4.4, R4.5)_ — DONE
- [x] 1.7 **[EC2 only]** Local test via two-terminal `agentcore dev --logs` +
  `agentcore dev "<prompt>"` (NOT the TUI; laptop has no Docker). **PASSED on EC2
  2026-09-13:**
  - "What are the prerequisites for Database Systems?" → KB retrieval returned
    real handbook prereqs (COMP-3210/3450/3620).
  - "Look up student 100016 ..." → `query_student_db` returned Mateo Jackson's 8
    completed courses from Athena.
  _(R1.6, R1.7, R3.3, R5.1, R5.2)_ — DONE
- [x] 1.8 **[local]** Replaced deprecated `retrieve`/`strands-agents-tools` with
  core `BedrockKnowledgeBaseStore` + `MemoryManager` (matches `src/advisor_agent.py`).
  Dropped the bloat and the `STRANDS_KNOWLEDGE_BASE_ID` var; single
  `KNOWLEDGE_BASE_ID`. — DONE

**Phase 1 (Module 7 local) COMPLETE.** Agent verified locally on EC2.

## Phase 5: Module 7 deploy + verify (EC2) — DONE
- [x] 5.1 `agentcore deploy` succeeded (CDK bootstrap approved). Runtime READY:
  `arn:aws:bedrock-agentcore:us-west-2:331773567763:runtime/AdmissionAgent_AdmissionAgent-zc7w8t847K`.
- [x] 5.1b IAM fix: deployed KB retrieval hit AccessDenied on
  `bedrock:GetKnowledgeBase` (BedrockKnowledgeBaseStore needs it; the deprecated
  retrieve tool did not). Added that action to `cloudformation/self-hosted/3-agentcore-role.yaml`
  and updated the role stack via console (in-place, no replacement).
- [x] 5.2 `agentcore invoke` PASSED in production for BOTH prompts (KB prereqs +
  student 100016 Athena lookup). Real data returned.
- [x] 5.3 Streamlit thin client — DONE. `src/streamlit_advisor.py` now calls the
  deployed runtime via `invoke_agent_runtime` (no local agent). Added
  `AGENTCORE_RUNTIME_ARN` to config/.env; session id `session-<uuid>` (>=33 chars
  for the API). Sidebar + terminal log prove it's calling AgentCore (ARN, session,
  prompt). Verified on laptop against the deployed runtime. Sets up ECS Fargate later.
- [ ] 5.4 Observability (`agentcore logs`/`traces`) — optional, not yet run.

**MODULE 7 COMPLETE (deployed + verified, incl. Streamlit thin client).**

## Phase 2 + 6: Module 8 Memory — DONE
- [x] Provisioned memory with BOTH strategies in one shot (skipped the
  short-term-only step): `agentcore add memory --strategies SEMANTIC,USER_PREFERENCE`
  → `admission_agent_memory` ACTIVE.
- [x] `memory/session.py`: AgentCoreMemorySessionManager from
  MEMORY_ADMISSION_AGENT_MEMORY_ID; long-term retrieval over
  /users/{actor}/facts + /preferences/; async_mode; None locally (graceful).
- [x] `main.py`: per-session session_manager (falls back to conversation_manager
  locally); actor_id from payload.
- [x] `list_memories.py`: workshop inspection script (annotated as optional
  fluff — console shows the same).
- [x] Deployed + VERIFIED (2026-09-13): two `agentcore invoke` with the SAME
  `--session-id` → turn 2 ("Do I meet those...") correctly resolved "those" to
  the DATA-3300 prereqs from turn 1. Short-term memory works. (Each invoke
  without a shared --session-id gets a NEW session → no memory; must pass
  --session-id to chain.)

**MODULE 8 COMPLETE.** Next: Phase 3 (Module 9 multi-agent).

## Phase 2: Module 8 — Memory wiring (code local, provisioning deploy)

- [ ] 2.1 **[local]** Create `app/AdmissionAgent/memory/session.py` with
  `build_session_manager(session_id, actor_id)` returning an
  `AgentCoreMemorySessionManager` built from
  `MEMORY_ADMISSION_AGENT_MEMORY_ID`. _(R6.3)_
- [ ] 2.2 **[local]** Add long-term `retrieval_config` to `session.py`: namespaces
  `/users/{actor_id}/facts` (SEMANTIC) and `/users/{actor_id}/preferences/`
  (USER_PREFERENCE), each `RetrievalConfig(top_k=5, relevance_score=0.5)`. _(R7.2,
  R7.3)_
- [ ] 2.3 **[local]** Wire memory into `main.py`: extract `session_id`/`actor_id`
  from payload; build the session manager and pass `session_manager=` to the
  `Agent`. Degrade gracefully (skip session manager) when
  `MEMORY_ADMISSION_AGENT_MEMORY_ID` is unset so `agentcore dev -b` still runs.
  _(R6.4, R5.3)_
- [ ] 2.4 **[local]** Add `list_memories.py` inspection script
  (`bedrock-agentcore` `list_memory_records` over the facts/preferences
  namespaces). _(R7.5)_
- [ ] 2.5 **[local]** Re-run `agentcore dev -b` to confirm the agent still starts
  without deployed memory. _(R5.3)_

## Phase 3: Module 9 — Multi-agent code (local-testable code)

- [ ] 3.1 **[local]** Create `app/AdmissionAgent/agents/__init__.py` and
  `agents/admission.py` with `route_to_admission(query, student_id=None)` (`@tool`)
  — Strands `Agent` via `load_model()`, tools `[retrieve, query_student_db]`, "Alex"
  prompt; set `STRANDS_KNOWLEDGE_BASE_ID` from `KNOWLEDGE_BASE_ID` at module level.
  _(R9.1, R9.2)_
- [ ] 3.2 **[local]** Create `agents/advisor_requests.py` with
  `route_to_advisor_requests(query, student_id=None)` (`@tool`) — `MCPClient` over
  `streamablehttp_client(ADVISOR_MCP_URL)` used as a context manager,
  `list_tools_sync()`, Strands `Agent` with MCP tools + `query_student_db`, and the
  evaluate-then-act prompt (request types: `course_override`, `advisor_meeting`,
  `program_change`, `special_consideration`). _(R9.3, R9.4, R9.5)_
- [ ] 3.3 **[local]** Refactor `main.py` into the orchestrator: tools
  `[route_to_admission, route_to_advisor_requests]`; keep `BedrockAgentCoreApp`,
  `load_model()`, logging, Module 8 session manager; add a Strands conversation
  manager; intent-routing system prompt that passes `student_id`. _(R10.1, R10.2,
  R10.3)_
- [ ] 3.4 **[local]** Add `ADVISOR_MCP_URL` placeholder handling: read from env in
  the specialist; document that the real value is filled after the gateway is
  deployed (Phase 5). Confirm modules import cleanly and the orchestrator
  constructs with both tools. _(R8.4, R9.3)_
- [ ] 3.5 **[local]** Final local validation: `agentcore validate` clean;
  `agentcore dev -b` starts; Admission routing works locally (advisor-request
  routing is validated post-deploy since it needs the gateway). _(R5, R10)_

## Phase 4: Prepare for transport (local)

- [ ] 4.1 **[local]** Confirm `.env.local`, `.venv/`, `node_modules/` remain
  gitignored; only source/config is tracked. _(R13.4)_
- [ ] 4.2 **[local]** Commit the AdmissionAgent changes (source + `agentcore.json`
  + `uv.lock`) — user performs the commit/push; Kiro does not commit or push.
  _(R13.4)_

---

## Deploy-only (run on the Amazon Linux 2023 Code Editor EC2 instance)

> These require provisioned AWS resources and are executed from the EC2 instance
> after pulling the committed baseline. Listed for completeness of the workshop
> scope.

## Phase 5: Module 7 deploy + verify

- [ ] 5.1 **[deploy]** `agentcore deploy` (approve one-time CDK bootstrap);
  `agentcore status` shows the runtime `ACTIVE`. _(R13.1, R13.3)_
- [ ] 5.2 **[deploy]** `agentcore invoke` the KB and student prompts; optionally
  `--stream`. _(R1.6, R1.7)_
- [ ] 5.3 **[deploy]** Streamlit thin client: add `AGENTCORE_RUNTIME_ARN` to
  `.env`; refactor the app to `invoke_agent_runtime` and render
  `content[0]['text']` via `st.markdown()`; remove local Agent/tool/Bedrock usage.
  _(R11.1, R11.2, R11.3)_
- [ ] 5.4 **[deploy]** Observability: `agentcore logs` (with filters) and
  `agentcore traces list/get`; confirm agent/model/tool spans. _(R12.1, R12.2,
  R12.3)_

## Phase 6: Module 8 deploy + verify

- [ ] 6.1 **[deploy]** `agentcore add memory --name admission_agent_memory`; then
  `agentcore deploy`; `agentcore status` shows memory `ACTIVE` and
  `MEMORY_ADMISSION_AGENT_MEMORY_ID` injected. _(R6.1, R6.2)_
- [ ] 6.2 **[deploy]** Verify short-term memory: multi-turn reference resolution in
  one session. _(R6.5)_
- [ ] 6.3 **[deploy]** Re-add memory with strategies
  (`--strategies SEMANTIC,USER_PREFERENCE`); `agentcore deploy`. _(R7.1)_
- [ ] 6.4 **[deploy]** Verify long-term memory: state a preference, wait ~30s, start
  a new session, confirm recall; run `list_memories.py`. _(R7.4, R7.5)_

## Phase 7: Module 9 deploy + verify

- [ ] 7.1 **[deploy]** `agentcore add gateway --name education-advisor-gateway
  --authorizer-type NONE --runtimes AdmissionAgent`. _(R8.1)_
- [ ] 7.2 **[deploy]** `agentcore add gateway-target --name advisor-requests --type
  lambda-function-arn --lambda-arn <education-advisor-requests ARN>
  --tool-schema-file <tools.json> --gateway education-advisor-gateway`; then
  `agentcore deploy`. _(R8.2, R8.3)_
- [ ] 7.3 **[deploy]** Construct the MCP URL from `agentcore status`; set
  `ADVISOR_MCP_URL` in `.env.local` and in `agentcore.json` `envVars`;
  `agentcore deploy -y`. _(R8.4, R10.2)_
- [ ] 7.4 **[deploy]** Verify routing with the workshop prompts: information lookup
  → admission; justified request (student 100033, 3.8 GPA) → submitted; trivial
  request → declined with guidance; cross-domain → both specialists. _(R10.3-R10.6)_
- [ ] 7.5 **[deploy]** Confirm the DynamoDB `education-advisor-requests` item
  (student ID, type, description, `pending`). _(R10.7)_

---

## Notes

- Tonight's local session targets **Phases 0-4** (all `[local]` tasks), stopping at
  the point the code is committed and ready to pull to EC2. Phases 5-7 (`[deploy]`)
  run on the Code Editor EC2 instance.
- Behavioral routing in Module 9 (advisor-requests path) can only be fully verified
  after the gateway is deployed (Phase 7), so Phase 3 verifies code
  construction/imports and the Admission path locally.
- Region is `us-west-2` throughout (this repo's real resources), not the workshop's
  `us-east-1` examples.
