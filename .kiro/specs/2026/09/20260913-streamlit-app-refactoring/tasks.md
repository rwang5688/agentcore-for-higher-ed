# Tasks: Streamlit App Refactoring (Three Modes)

All tasks are `[local]` (laptop, no Docker/creds needed to write code) unless
tagged `[deploy]` (EC2/Docker, human-run). Each task cites requirements.

## Phase 1 — streamlit-thick-client/ (R1, R3, R6) — DONE

- [x] 1.1 `[local]` Create `streamlit-thick-client/` with self-contained copies:
  `config.py` (thick-relevant fields), `advisor_agent.py` (create_agent +
  SYSTEM_PROMPT), `query_student_db.py` (@tool). Adjust imports so they resolve
  within the directory and read repo-root `.env`. (R1.1, R1.2)
- [x] 1.2 `[local]` Write `streamlit-thick-client/app.py`: Streamlit UI that
  builds ONE agent per browser session (cached in `st.session_state`), calls
  `agent(prompt)` per turn, renders the reply. Sidebar states "Thick client →
  local Strands agent". Same title/caption/samples/clear-control as thin. (R1.3, R3)
- [x] 1.3 `[local]` `streamlit-thick-client/requirements.txt` (streamlit,
  strands-agents, boto3, python-dotenv) + `README.md` with run command. (R6, D6)
- [x] 1.4 `[local]` Import-smoke: config/advisor_agent/query_student_db import
  cleanly from the directory. VERIFIED (`thick imports OK`).

## Phase 2 — streamlit-thin-client/ (R2, R3, R6) — DONE

- [x] 2.1 `[local]` Create `streamlit-thin-client/`; move `src/streamlit_advisor.py`
  content into `app.py`; self-contained `config.py` (agentcore_runtime_arn,
  aws_region). Preserves session-id >=33, SSE parsing, missing-ARN guard. (R2.1-R2.4)
- [x] 2.2 `[local]` `streamlit-thin-client/requirements.txt` (streamlit, boto3,
  python-dotenv) + `README.md` with run command. (R6, D6)
- [x] 2.3 `[local]` Import-smoke of config.py. VERIFIED (`thin config OK`).

## Phase 3 — src/ cleanup (R5) — DONE

- [x] 3.1 `[local]` Removed `src/streamlit_advisor.py` (now lives in both client
  dirs). `src/` holds only: simple_agent, kb_advisor, advisor_agent,
  query_student_db, config, __init__. (R5)
- [x] 3.2 `[local]` No code imports `src.streamlit_advisor` (grep: docs only).
  Repo `README.md` updated: repo-structure tree, new "three app modes" table,
  and both `streamlit run` runbooks now point to thick/thin dirs. `ROADMAP.md`
  rewritten: Overview ("prototype fast, then go live") + Thick+Bedrock ->
  Thin+AgentCore comparison table + three-phase roadmap + prompt-log appendix.
  (`prompt.txt` was renamed to `ROADMAP.md`.) (R5, R6)

## Phase 4 — deploy-streamlit-app/ (R4) — DONE (laptop portion)

- [x] 4.1 `[local]` Added `docker_app/utils/agentcore.py`: `AgentCoreClient`
  (invoke_agent_runtime + SSE parsing, thin-client logic), reads runtime ARN +
  region from `config_file.py`, accepts `actor_id`. (R4.1)
- [x] 4.2 `[local]` Rewrote `docker_app/app.py`: Cognito login gate kept; after
  login renders advisor chat UI; per prompt calls the util with
  `actor_id = authenticator.get_username()`. Claude-v2 demo path removed. (R4.1, R4.3)
- [x] 4.3 `[local]` Retired `docker_app/utils/llm.py` (deleted). (R4.1)
- [x] 4.4 `[local]` `config_file.py`: `DEPLOYMENT_REGION = "us-west-2"`, added
  `AGENTCORE_RUNTIME_ARN` (real deployed ARN), dropped BEDROCK_REGION/claude-v2. (R4.4)
- [x] 4.5 `[local]` `cdk/cdk_stack.py`: swapped task-role IAM from
  `bedrock:InvokeModel` to `bedrock-agentcore:InvokeAgentRuntime` scoped to the
  runtime ARN (+ `/*` for endpoints). (R4.2)
- [x] 4.6 `[local]` `docker_app/requirements.txt`: streamlit, boto3,
  streamlit-cognito-auth (claude-v2 assumptions dropped). (D6)
- [x] 4.7 `[local]` Updated `deploy-streamlit-app/README.md`: advisor use case,
  what-changed-from-baseline, us-west-2, EC2 `cdk deploy` runbook (human-run),
  local-dev instructions, baseline limitations. (R6)
- [x] 4.8 `[local]` Smoke tests VERIFIED:
  - `config_file` + `utils/agentcore` import clean; region=us-west-2, real ARN.
  - `py_compile` OK for `docker_app/app.py`, `utils/auth.py`, `cdk/cdk_stack.py`
    (all parse; no syntax errors).
  - NOTE: `streamlit-cognito-auth` is a container-only dep (not in laptop venv),
    so a full runtime `import app` can't run here — expected. `cdk synth` needs
    Docker (image asset) so it's an EC2 step, not a laptop check.

## Phase 5 — deploy (EC2/Docker, human-run) (R4, R7) — NOT STARTED (CP-D handoff)

Laptop work is complete; these are EC2/Docker steps for the human. Full runbook
is in `deploy-streamlit-app/README.md`.

- [ ] 5.1 `[deploy]` On EC2 with Docker: `cdk bootstrap` (if needed) +
  `cdk deploy` from `deploy-streamlit-app/`.
- [ ] 5.2 `[deploy]` Create a Cognito user; open the CloudFront URL; log in;
  verify the advisor answers via the deployed runtime with per-user memory.

## Local verification summary (all `[local]` phases) — VERIFIED

- All three apps import cleanly (thick: config/advisor_agent/query_student_db;
  thin: config; deploy: config_file + utils/agentcore).
- `py_compile` OK for every `app.py` + `cdk/cdk_stack.py`.
- Final layout confirmed: `src/` = older scripts only; thick/thin self-contained;
  `deploy/docker_app/utils/` has `agentcore.py` (llm.py removed), `auth.py` kept.
- CANNOT verify on laptop (documented, not failures): `import app` for deploy
  (needs container-only `streamlit-cognito-auth`), `cdk synth`/deploy (needs
  Docker). These are Phase 5 / user-run.

## INTEGRATION TESTS PASSED (laptop + credentials, 2026-09-13)

Real `streamlit run` with AWS credentials — the true test for a refactor (only
syntax/import/organization could break, since functionality already worked).

- **thick** (`streamlit run streamlit-thick-client\app.py`): came up on :8501;
  student 100033 prompt ran `query_student_db` (Athena, 26 courses) + KB store
  retrieval locally and produced a full next-course recommendation. PASS.
- **thin** (`streamlit run streamlit-thin-client\app.py`): launched with correct
  runtime ARN + 33-char session id. Advisor-request prompt (student 100033)
  routed through the deployed runtime: orchestrator -> advisor-requests agent ->
  MCP gateway -> Lambda -> DynamoDB (new Request ID minted; existing pending
  override recalled from memory). PASS.

No syntax/import/organization issues found — refactor confirmed good.

## Notes
- Phases 1-4 are laptop-only code edits; no AWS creds/Docker needed to WRITE
  them. Running the apps (`streamlit run`) hits real AWS with laptop creds.
- Phase 5 is the only EC2/Docker part — stop at CP-C after Phase 4, hand off.
- R7: no edits to `AdmissionAgent/app/**` or `agentcore.json` anywhere.
