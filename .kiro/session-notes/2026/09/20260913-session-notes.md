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

## PHASE 5 DEPLOYED + VERIFIED — deploy-streamlit-app live (2026-09-13)

`cdk deploy` from EC2 succeeded. Stack `AdvisorStreamlit` (us-west-2), ~7.5 min.
- CloudFrontDistributionURL = d2oez7aqlzbdec.cloudfront.net
- CognitoPoolId = us-west-2_ibTcOAKpA
- Cognito user `streamlit-user`; login OK; student-100033 recommendation streamed
  from the deployed runtime (KB + Athena). All three roadmap phases now live.

### Deploy gotchas found + fixed (folded into deploy README runbook)
1. **CDK CLI missing** — `cdk` command not installed (only Python aws-cdk-lib
   was). Fixed: `npm install -g aws-cdk`. AgentCore wraps CDK internally so the
   agent side never needed a global cdk; this plain CDK app does. Runbook now has
   the install + a CLI-vs-library note + Docker/creds preflight.
2. **Graviton / ARM64** — baseline Dockerfile pinned `FROM --platform=linux/amd64`
   -> "exec /bin/sh: exec format error" on the ARM64 Code Editor at the pip layer.
   Fixed (2 coordinated changes): Dockerfile drop the platform pin +
   cdk_stack.py Fargate `runtime_platform=ARM64/LINUX`. Native Graviton build,
   cheaper Fargate, consistent with the ARM64 AgentCore runtime.

### Demo note
- First response is slower = cold start (Fargate task + AgentCore runtime warmup).
  Pre-warm with a throwaway prompt ~1 min before presenting. Can also be shown
  deliberately as part of the managed-runtime story.

### Teardown reminder
- Stack bills hourly (NAT gateway + ALB especially). `cdk destroy` from
  deploy-streamlit-app/ when done. Does NOT touch the AgentCore runtime/KB/Lambda.

## SESSION WRAP-UP (2026-09-13)

Goal (set this morning): build out all three Streamlit app modes as
self-contained directories. DONE and verified end to end.

### Final state — three roadmap phases live
1. **streamlit-thick-client/** (Phase 1, prototype) — local Strands agent
   (Bedrock + KB + Athena). Verified locally.
2. **streamlit-thin-client/** (Phase 2, go live) — invokes deployed AgentCore
   runtime; no local agent. Verified locally + on EC2.
3. **deploy-streamlit-app/** (Phase 3, production capstone) — thin client on
   Cognito + ECS Fargate (Graviton/ARM64), behind ALB + CloudFront. LIVE at
   d2oez7aqlzbdec.cloudfront.net; verified (recommendation + advisor-request
   multi-agent write path). `src/` untouched for backward compat.

### Why this matters (the demo story)
The hosted app is production-quality end to end: no local setup, no expiring
credentials, no Code Editor — just a URL + Cognito login. Same UX and same agent
across all three phases; only the backend location changes. Prototype on thick,
go live on thin + AgentCore, host it on Fargate + Cognito.

### Cold-start = expected (my gotcha to remember; NOT in ISSUES.md)
First prompt after idle is slower (Fargate task + AgentCore runtime warmup);
warm calls are fast. Thin client is I/O-bound, so the tiny 256/512 task is
correct — not undersized. I run the demo, so I'll pre-warm with a throwaway
prompt ~1 min before presenting. Documented in deploy-streamlit-app/README.md.

### Docs to commit before pulling to the laptop tonight
- `deploy-streamlit-app/README.md` — CDK CLI install + preflight + Graviton +
  teardown + cold-start gotcha.
- `.kiro/specs/2026/09/20260913-streamlit-app-refactoring/tasks.md` — Phase 5 DONE.
- this session-notes file.
Suggested commit: `docs: record Phase 5 deploy success + CDK CLI/Graviton/cold-start gotchas`

### For slides tonight (laptop)
- Refine ROADMAP.md (Overview + thick->thin comparison table are the anchor).
- Talking points: thin-client latency drop, cold-vs-warm, per-user memory via
  Cognito sub as actor_id, Graviton cost/consistency, "one URL, no setup".

### Teardown when done demoing
`cdk destroy` from deploy-streamlit-app/ (NAT + ALB bill hourly). Does NOT touch
the AgentCore runtime / KB / Athena Lambda.

## Demo environment + flow (locked 2026-09-13)

### Environment
- Account: Isengard `wangrob-agentcore-for-higher-ed-01`, dedicated to hosting
  the whole setup. Stack is PERSISTENT (not a spin-up-for-the-session thing) —
  no teardown pressure before the demo. `cdk destroy` only if deliberately
  pausing NAT/ALB spend during long idle; not a demo risk.
- Region: **us-west-2 everywhere** — deliberate, and the primary reason is
  customer fit: this is SLG/EDU **West** — those customers want us-west-2, and any
  us-east-1 resource in the demo would invite "why isn't this in our region?"
  questions that distract from the agent story. Pinning us-west-2 also forces KB,
  Athena Lambda, AgentCore runtime, and the Fargate app all in-region and removes
  any accidental us-east-1 fallback (incl. Kiro). Region discipline as customer
  empathy + a "self-contained regional deployment" talking point.
- Tooling: local Kiro (Windows laptop) for code/specs; EC2 Code Editor only for
  Docker build + deploy.

### Demo flow (decided)
- Go STRAIGHT to the hosted app (Phase 3) live: open the CloudFront URL, Cognito
  login, ask a question, get an answer — no terminal, no creds, no Code Editor.
  Leads with the "real product" payoff.
- Narrate Phases 1-2 as lead-in (slides/talk, NOT live app-switching):
  thick = local prototype lab; thin = managed backend, same UX, faster; hosted =
  that thin client + Cognito on Fargate, same agent, production-shaped.
- ROADMAP.md Overview + thick->thin comparison table = backbone of the talk.
- Pre-warm ~1 min before (throwaway prompt); optionally show cold-vs-warm as a
  live teaching beat for the managed-runtime story.
- Fallback if CloudFront/Cognito hiccups live: local thin client (same answers,
  needs creds) — keep a terminal ready. (Low risk given dedicated account.)
