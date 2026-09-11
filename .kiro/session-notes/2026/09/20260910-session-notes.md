# Session Notes - 2026-09-10

## Environment
- Machine: work laptop (Windows, local Kiro IDE)
- AWS: Isengard dev account, KB + Athena Lambda in us-west-2, IDC in us-east-1

## What We're Working On

Building out the rest of the AgentCore for Higher Ed workshop into a
presentation-ready showcase for a **UC Berkeley Data Science course**
("Agentic AI on AWS" update). The narrative and target architecture:

### Presentation thesis
- Old package-software era: ERP/CRM codified ~50% of backend processes.
- General-purpose agents ($20-40/user/month) are NOT economical for answering
  ~50% of expert office-worker questions.
- More economical: invest AI budget in a **Data Foundation for AI** and
  **Custom Agents** to maximize value per dollar.

### Two key trends to demo
1. **Data Foundation for AI** - Bedrock Knowledge Base + an MCP server running
   on Amazon Bedrock AgentCore (exposes the Data Foundation to agents).
2. **Custom Agents** - a Strands Agents **agent swarm** that routes student
   questions and handles requests for an advisor (advisor appointments).

### Target hosting architecture
- **Amazon Bedrock AgentCore**: hosts the agent swarm + MCP backend(s).
- **ECS Fargate**: deploys a thin Streamlit front-end app.
- **Amazon Cognito**: identity management for the Streamlit app.

## Current State (from prior sessions / streamlit-advisor spec)

- Local Strands advisor already works end-to-end:
  - `src/advisor_agent.py` (shared: SYSTEM_PROMPT + create_agent)
  - `src/config.py` (explicit get_config, lru_cache, no import side effects)
  - `src/query_student_db.py` (Athena query via `education-athena-query` Lambda)
  - `src/kb_advisor.py` (CLI), `src/streamlit_advisor.py` (local UI),
    `src/simple_agent.py` (starter)
- Bedrock Managed KB: `university-handbooks-kb` (ID: ONVQOQ7XJB), us-west-2
- Athena: `education_workshop_db`, 12 Glue tables, 987 students, query Lambda
- CloudFormation self-hosted stacks 1-5 deployed (KB buckets, code editor,
  agentcore role, athena buckets/setup, identity center in us-east-1)
- streamlit-advisor spec task 22 (final Streamlit acceptance test) still open;
  task 23 (migrate agent to AgentCore) is the future work we're starting now.

## Work Completed This Session

### Git housekeeping (committed + pushed to origin/main)
- `51e43f6` Standardize steering docs across workspaces; move runbook in README
  - Replaced terse `.kiro/steering/session-notes.md` with standardized
    management docs shared across Kiro workspaces: `session-notes-management.md`,
    `specs-management.md`, `build-warnings-workflow.md`.
  - Moved `database-schema.md` from `.kiro/steering/` -> `data/` (content
    unchanged; git tracked it as a 100% rename).
  - Moved Streamlit runbook below repo structure in README, renamed
    "Local Runbook".
  - Added this session-notes file.
- `372092d` Drop inert steering front-matter from `data/database-schema.md`
  - Removed `inclusion: always` front-matter. It is dataset documentation, not
    a Kiro steering file, so the front-matter was inert. Kept under `data/`
    (NOT `education-data/`, which holds actual CSV load files).

### Decision: database-schema.md is documentation, not steering
- Lives at `data/database-schema.md` as plain docs.
- No longer auto-included in Kiro context. Runtime agent does NOT depend on it
  (schema is embedded in the `query_student_db` tool docstring in
  `src/query_student_db.py`).
- To pull it into Kiro context on demand: reference `#data/database-schema.md`
  in chat, or add a steering file that points at it via
  `#[[file:data/database-schema.md]]`.

## AgentCore Build-Out: Plan + Handoff

### Goal
Build the AgentCore project (Strands agent swarm + MCP backend) to showcase:
1. Data Foundation for AI = Bedrock KB + MCP server on AgentCore.
2. Custom Agents = Strands agent swarm that routes student questions and
   handles advisor-appointment requests.
Front-end: thin Streamlit app on ECS Fargate, Cognito for identity.

### Where the work happens (IMPORTANT constraint)
- User is doing the scaffold + build on a **standalone Code Editor EC2 instance**
  (Linux + Docker, needed for `agentcore build` / `agentcore launch`).
- **That EC2 box has NO GitLab connectivity.** So git CANNOT be the transport
  between EC2 and this repo.
- Decision: user will **scaffold and build entirely on EC2**, then bring the
  code back down into THIS repo later for tracking. Kiro (laptop/WorkSpaces)
  did NOT scaffold anything this session, at the user's request.

### Transport plan (EC2 -> this repo), since GitLab is unreachable from EC2
- Options discussed: `git bundle` (preferred, keeps history), plain SCP/rsync
  of the folder, or zip + upload via Code Editor UI / stage through S3.
- Target location in repo once code comes down: new top-level `agentcore/`
  folder. Will need a `.gitignore` for Docker/build artifacts when integrating.

### Architecture questions STILL OPEN (needed before scaffolding/integration)
- **Region** for AgentCore — recommended `us-west-2` (co-locate with KB
  `ONVQOQ7XJB` + `education-athena-query` Lambda). Not confirmed.
- **Swarm topology** — full router + specialists (course/handbook,
  student-record, advisor-appointment) vs leaner single agent with those as
  tools. Not confirmed. (Multi-agent sells the "Custom Agents" trend harder.)
- **Advisor appointments** — real DynamoDB backend vs mocked for the demo.
  Not confirmed.
- **MCP server** — expose Data Foundation (KB search + Athena query) as a
  separate MCP server on AgentCore (matches the "MCP backend" trend) vs start
  as in-process Strands tools and split out later. Not confirmed.
- **CDK language** for ECS Fargate + Cognito infra — Python vs TypeScript, or
  skip CDK and use the `agentcore` CLI packaging. Not confirmed.

## Next Steps (for WorkSpaces / next session)
- User returns with AgentCore code built on EC2.
- Help integrate it into this repo under `agentcore/` (placement, `.gitignore`
  for build artifacts, README + session-notes updates).
- Create the spec under `.kiro/specs/2026/09/` (e.g.
  `20260910-agentcore-swarm-showcase/`) once architecture answers are known;
  reconcile the as-built EC2 code with requirements/design/tasks.
- Note: streamlit-advisor spec (`.kiro/specs/20260819-streamlit-advisor/`)
  task 22 (final local Streamlit acceptance test) is still open; task 23
  (migrate agent to AgentCore) is the work now in progress on EC2.

## Open Questions
- The five architecture questions above (region, topology, appointments, MCP
  server split, CDK language).
- Same repo vs separate repo for the AgentCore project — current intent is
  SAME repo (this one), under `agentcore/`.
