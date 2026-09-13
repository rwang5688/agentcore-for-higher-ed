# Session Notes - 2026-09-13

## Environment
- Machine: work laptop (Windows, PowerShell, local Kiro IDE)
- venv: `venv\` at repo root, Python 3.13.11
- Region: us-west-2 (this repo's real KB + Lambdas)

## Where We Are (start of session)
- Workshop Modules 7-9 are DONE + deployed + verified in us-west-2 (see
  20260912 notes): AgentCore runtime, Memory, multi-agent orchestrator, MCP
  gateway write path. Demo path = Streamlit thin client on the laptop.
- Specs were flat under `.kiro/specs/`; reorganized on EC2 into the
  `YYYY/MM/YYYYMMDD-name/` convention, committed, pushed, pulled down here.
  Verified layout:
  - `2026/08/20260808-harden-code-editor`
  - `2026/08/20260809-split-athena-setup`
  - `2026/08/20260819-streamlit-advisor`
  - `2026/09/20260912-multi-agent-systems`

## Change of Plan (this morning)
Instead of stopping at "thin client only", build out ALL THREE Streamlit app
modes as first-class, self-contained options:

1. **streamlit-thick-client** — the PRE-AgentCore app: runs the Strands agent
   locally (Bedrock model + KB store + `query_student_db` Athena tool). This is
   what `src/streamlit_advisor.py` was BEFORE we switched to invoking the
   deployed runtime.
2. **streamlit-thin-client** — the CURRENT app: no local agent; calls the
   deployed AgentCore runtime via `invoke_agent_runtime` and renders the stream.
3. **deploy-streamlit-app** — the thin client wrapped with Cognito auth and
   deployed on ECS Fargate (ALB + CloudFront) via CDK. Reuses the aws-samples
   `deploy-streamlit-app-main` baseline the user just dropped into the repo.

## Structure Decision (user directive)
- Three self-contained top-level directories: `streamlit-thick-client/`,
  `streamlit-thin-client/`, `deploy-streamlit-app/`.
- `src/` keeps ONLY the older standalone scripts (simple_agent, kb_advisor,
  advisor_agent, query_student_db, config).
- Prefer self-contained apps even if it means a bit of code duplication between
  thick and thin. Explicit user preference: keep them independent.

## Baseline Reviewed (aws-samples deploy-streamlit-app)
- `docker_app/app.py` — Streamlit + Cognito auth (`utils/auth.py` reads Cognito
  params from Secrets Manager) + `utils/llm.py` (direct Bedrock invoke_model).
- `cdk/cdk_stack.py` — Cognito user pool + client, Secrets Manager secret, VPC,
  ECS Fargate service, ALB (custom-header gated), CloudFront distribution,
  Bedrock IAM. Python CDK.
- `config_file.py` — STACK_NAME, CUSTOM_HEADER_VALUE, SECRETS_MANAGER_ID,
  DEPLOYMENT_REGION/BEDROCK_REGION (us-east-1 defaults in baseline).
- Reuse plan: keep the CDK/auth/CloudFront scaffolding; replace the demo
  `llm.py` invoke with our thin-client `invoke_agent_runtime` call to the
  deployed AgentCore runtime; add IAM for `bedrock-agentcore:InvokeAgentRuntime`
  instead of `bedrock:InvokeModel`; pass Cognito `sub` as `actor_id`.

## Plan
- Create spec `.kiro/specs/2026/09/20260913-streamlit-app-refactoring/`
  (requirements, design, tasks). Get user approval before implementing.
- Then build the three directories.

## Next Steps
- Author the spec trilogy; review with user.
- Implement thick, thin, deploy in that order.

## Open Questions
- deploy-streamlit-app region: baseline defaults us-east-1; we need us-west-2
  (KB/Lambda/runtime live there). Confirm during spec.
- How much of the aws-samples CDK to keep vs slim (CloudFront needed for demo?).

## COMPLETED — three self-contained Streamlit app modes built (laptop portion)

Decision locked: three fully self-contained dirs, no `src/` imports; `src/`
untouched (backward compat).

- **streamlit-thick-client/** — local Strands agent (config.py, advisor_agent.py,
  query_student_db.py, app.py, requirements.txt, README.md). All AWS calls local.
- **streamlit-thin-client/** — invokes deployed AgentCore runtime (config.py with
  just runtime ARN + region, app.py, requirements.txt, README.md). Moved out of
  `src/streamlit_advisor.py` (which was deleted).
- **deploy-streamlit-app/** — thin client merged into the aws-samples Fargate +
  Cognito shell:
  - `docker_app/utils/agentcore.py` (new) = `AgentCoreClient.invoke` (invoke +
    SSE parse, `actor_id` in payload).
  - `docker_app/app.py` rewritten: Cognito gate + advisor chat UI, `actor_id =
    authenticator.get_username()`.
  - `docker_app/utils/llm.py` deleted (was direct claude-v2 Bedrock demo).
  - `config_file.py`: STACK_NAME=AdvisorStreamlit, DEPLOYMENT_REGION=us-west-2,
    AGENTCORE_RUNTIME_ARN=<deployed AdmissionAgent runtime ARN>.
  - `cdk/cdk_stack.py`: task-role IAM swapped `bedrock:InvokeModel` →
    `bedrock-agentcore:InvokeAgentRuntime` scoped to [ARN, ARN/*].
  - `requirements.txt`: boto3, streamlit, streamlit-cognito-auth.
  - `README.md` rewritten (advisor use case, us-west-2, EC2 cdk deploy runbook).

### Verification (laptop, no Docker/creds)
- All three apps import cleanly; `py_compile` OK for all app.py + cdk_stack.py.
- Final dir layout confirmed correct.
- NOT verifiable on laptop (documented): live behavior (creds), deploy `import
  app` (container-only streamlit-cognito-auth), `cdk synth`/deploy (Docker).

### Docs
- Repo `README.md`: repo-structure tree updated, new "three app modes" table,
  both `streamlit run` runbooks repointed to thick/thin dirs.
- `ROADMAP.md`: appended a formatted three-phase roadmap section below the raw
  prompt log (Phase 1 thick / Phase 2 thin / Phase 3 hosted).
- Spec `tasks.md`: Phases 1-4 marked done with verification notes; Phase 5 is the
  EC2 `cdk deploy` handoff (CP-D).

### Left as-is (intentional)
- `src/config.py` still has the orphaned `agentcore_runtime_arn` field — kept per
  "src untouched / backward compat" directive.
- `notes/6-connecting-to-live-data.md` still references `src/streamlit_advisor.py`
  — historical workshop notes, not touched.

## Next Steps
- Phase 5 (EC2, human): `cdk deploy` from `deploy-streamlit-app/`, create a
  Cognito user, verify via CloudFront URL.
- `prompt.txt` was renamed to `ROADMAP.md` (no separate file to remove).

## READY TO UPLOAD (CP-C, 2026-09-13)
All laptop work done + integration-verified (thick + thin PASS). Docs current:
- `ROADMAP.md` rewritten (Overview + Thick->Thin comparison table + 3-phase
  roadmap + prompt-log appendix). User will refine for slides tonight.
- Repo `README.md`, spec `tasks.md`, these session notes all current.
Files to upload: streamlit-thick-client/, streamlit-thin-client/,
deploy-streamlit-app/ (docker_app + cdk changes), src/ (streamlit_advisor.py
deleted), README.md, ROADMAP.md, .kiro specs + session notes.
Next after pull-down: user review, then Phase 5 EC2 `cdk deploy`.

## INTEGRATION TESTS PASSED (real streamlit run + creds, 2026-09-13)

- **thick**: student 100033 prompt -> local query_student_db (Athena, 26 courses)
  + KB retrieval -> full recommendation. All AWS calls local. PASS.
- **thin**: advisor-request prompt -> deployed runtime orchestrator ->
  advisor-requests agent -> MCP gateway -> Lambda -> DynamoDB (new Request ID;
  existing pending override recalled from memory). PASS.
- Both launched clean (no syntax/import errors); side-by-side terminal output is
  a strong teaching point (thick shows local tool calls; thin shows one
  invoke_agent_runtime). Refactor confirmed good.

Ready for CP-C: commit + upload to EC2 for Phase 5 `cdk deploy`.
