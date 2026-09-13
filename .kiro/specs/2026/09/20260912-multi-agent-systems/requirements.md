# Requirements: Multi-Agent Systems on AgentCore

## Introduction

This spec covers building, deploying, and evolving the **AdmissionAgent** on
Amazon Bedrock AgentCore, following Modules 7-9 of the workshop content
(`workshop-content.md`). The work takes an already-scaffolded AgentCore project
(`AdmissionAgent/`) and:

1. **Module 7** — turns the scaffold into a single **Admission Agent** with
   Knowledge Base retrieval (`retrieve`) and Athena student-record lookups
   (`query_student_db`), tests it locally with `agentcore dev -b`, deploys it to
   AgentCore Runtime, connects a Streamlit thin client, and enables observability.
2. **Module 8** — adds **AgentCore Memory** (short-term session memory and
   long-term SEMANTIC + USER_PREFERENCE strategies) wired via
   `AgentCoreMemorySessionManager`.
3. **Module 9** — refactors the entrypoint into a **multi-agent orchestrator**
   that routes to two `@tool` specialists: the Admission Agent and a new Advisor
   Requests Agent that evaluates requests and writes to DynamoDB via an MCP server
   on AgentCore Gateway.

### Environment Facts

| Item | Value |
| --- | --- |
| Project | `AdmissionAgent/` (Strands, Bedrock, Container build) |
| Model | `us.anthropic.claude-sonnet-4-6` (cross-region inference profile) |
| Knowledge Base ID | `ONVQOQ7XJB` |
| Athena query Lambda | `education-athena-query` |
| Athena database | `education_workshop_db` |
| Advisor requests Lambda / table | `education-advisor-requests` |
| Region | `us-west-2` (this repo's actual resources; workshop docs show `us-east-1`) |

> The workshop content uses `us-east-1` in examples, but this repo's Knowledge
> Base and Lambdas live in `us-west-2`. Requirements below use the repo's actual
> region.

### Local vs Deploy Boundary

Some capabilities can only be validated after deployment (they require
provisioned AWS resources). Requirements mark each capability as **local-testable**
or **deploy-only** so the implementation can be staged accordingly.

---

## Requirements

### R1: Admission Agent tools and system prompt (Module 7, local-testable)

**User story:** As a prospective student, I want to ask the Admission Agent about
course prerequisites and my own student record, so that I get accurate answers
grounded in the course handbook and the student database.

#### Acceptance Criteria

1. WHEN the agent code is loaded THEN the system SHALL register a `retrieve` tool
   (from `strands_tools`) and a `query_student_db` tool (from
   `tools.query_student_db`) on the Strands `Agent`.
2. WHEN the agent module is imported THEN the system SHALL set
   `os.environ['STRANDS_KNOWLEDGE_BASE_ID']` from `os.environ['KNOWLEDGE_BASE_ID']`
   so the `retrieve` tool can locate the Knowledge Base.
3. THE system SHALL configure a system prompt describing a university Admission
   Advisor named "Alex" that uses `retrieve` for course handbook queries and
   `query_student_db` for student record lookups via SQL against
   `education_workshop_db`.
4. WHEN the agent starts THEN the system SHALL configure
   `logging.basicConfig(level=logging.INFO)` for runtime visibility.
5. THE system SHALL preserve the scaffold's `BedrockAgentCoreApp` entrypoint
   pattern and the `load_model()` import from the `model/` directory (it SHALL NOT
   hardcode a model string in `main.py`).
6. WHEN asked "What are the prerequisites for Database Systems?" THEN the agent
   SHALL invoke the `retrieve` tool.
7. WHEN asked "Look up student 100016 and tell me what courses they have
   completed." THEN the agent SHALL invoke the `query_student_db` tool.

### R2: Model configuration (Module 7, local-testable)

**User story:** As a developer, I want the agent to use an available Bedrock
model, so that invocations don't fail with a Marketplace access error.

#### Acceptance Criteria

1. THE system SHALL set the model ID in `app/AdmissionAgent/model/load.py` to
   `us.anthropic.claude-sonnet-4-6`.
2. IF an invocation returns an `AccessDeniedException` referencing
   `aws-marketplace:ViewSubscriptions` or `aws-marketplace:Subscribe` THEN the
   model ID in `model/load.py` SHALL be treated as misconfigured and corrected to
   the cross-region inference profile above.

### R3: Dependencies and lock file (Module 7, local-testable)

**User story:** As a developer, I want the project dependencies pinned and locked,
so that the container build (`--frozen`) and local dev use the same versions.

#### Acceptance Criteria

1. THE `app/AdmissionAgent/pyproject.toml` SHALL declare, at minimum:
   `aws-opentelemetry-distro`, `bedrock-agentcore`, `botocore[crt]`, `mcp`,
   `strands-agents`, and `strands-agents-tools`.
2. WHEN `pyproject.toml` is changed THEN the system SHALL regenerate `uv.lock` via
   `uv lock`.
3. IF the dev server reports `ModuleNotFoundError` on startup THEN the lock file
   SHALL be regenerated (`uv lock`) and the dev server restarted.

### R4: Runtime configuration — env vars and execution role (Module 7, deploy-only config)

**User story:** As an operator, I want the deployed agent to have the environment
variables and IAM role it needs, so that it can reach Bedrock, the Knowledge Base,
and the Athena Lambda in production.

#### Acceptance Criteria

1. THE `agentcore/agentcore.json` runtime entry for `AdmissionAgent` SHALL include
   an `executionRoleArn` pointing at the pre-provisioned execution role.
2. THE runtime entry SHALL include `envVars` for `KNOWLEDGE_BASE_ID`,
   `ATHENA_LAMBDA_NAME` (`education-athena-query`), and the AWS region.
3. THE `agentcore/.env.local` file SHALL contain `KNOWLEDGE_BASE_ID` and
   `ATHENA_LAMBDA_NAME` so `agentcore dev -b` injects them during local dev.
4. WHERE JSON in `agentcore.json` is edited THE change SHALL conform to the types
   in `agentcore/.llm-context/` and pass `agentcore validate`.
5. THE `agentcore.json` SHALL remain the source of truth; generated CDK code under
   `agentcore/cdk/` SHALL NOT be hand-edited to change agent behavior.

### R5: Local testing with the dev server (Module 7, local-testable)

**User story:** As a developer, I want to test the agent locally before deploying,
so that I can validate tool calls without incurring deployment cycles.

#### Acceptance Criteria

1. THE agent SHALL be runnable locally via `agentcore dev -b` (terminal/no-browser
   mode).
2. WHEN the dev server shows `Status: running` THEN the sample KB and student
   prompts (R1.6, R1.7) SHALL return grounded answers.
3. THE local dev flow SHALL NOT depend on AgentCore Memory (memory is deploy-only,
   per R6).

### R6: Short-term memory (Module 8, deploy-only)

**User story:** As a student, I want the agent to remember what we discussed
earlier in a conversation, so that I don't have to repeat context within a session.

#### Acceptance Criteria

1. THE project SHALL register a memory resource named `admission_agent_memory` via
   `agentcore add memory` (NOT `agentcore memory create`).
2. WHEN the project is deployed THEN AgentCore SHALL inject the
   `MEMORY_ADMISSION_AGENT_MEMORY_ID` environment variable into the runtime.
3. THE system SHALL provide `app/AdmissionAgent/memory/session.py` that builds an
   `AgentCoreMemorySessionManager` (from
   `bedrock_agentcore.memory.integrations.strands`) from the memory ID, session ID,
   and actor ID.
4. THE `invoke` entrypoint SHALL extract `session_id` and `actor_id` from the
   invocation payload and pass the session manager to the Strands `Agent` via the
   `session_manager` parameter.
5. WHEN a follow-up turn references an earlier turn in the same session (e.g. "Do I
   meet those prerequisites?") THEN the agent SHALL resolve the reference without
   the user repeating the earlier content.

### R7: Long-term memory strategies (Module 8, deploy-only)

**User story:** As a returning student, I want the agent to remember my stated
preferences across sessions, so that recommendations stay personalised over time.

#### Acceptance Criteria

1. THE memory resource SHALL be configured with `SEMANTIC` and `USER_PREFERENCE`
   strategies (re-added via `agentcore add memory --strategies SEMANTIC,USER_PREFERENCE`).
2. THE `memory/session.py` SHALL define a `retrieval_config` that searches both a
   semantic facts namespace and a user preferences namespace, using
   `RetrievalConfig(top_k=5, relevance_score=0.5)` for each.
3. THE namespace templates SHALL be `/users/{actor_id}/facts` (semantic) and
   `/users/{actor_id}/preferences/` (user preference).
4. WHEN a preference is stated in one session AND a new session is later started
   THEN the agent SHALL retrieve and apply that preference without being reminded
   (allowing for asynchronous extraction latency of ~10-30s).
5. THE system SHALL provide a `list_memories.py` inspection script that lists
   extracted semantic facts and user preferences for a given actor via
   `bedrock-agentcore` `list_memory_records`.

### R8: Advisor Requests MCP on AgentCore Gateway (Module 9, deploy-only)

**User story:** As a student, I want to submit advisor requests (e.g. course
overrides), so that requests are tracked for human advisors to review.

#### Acceptance Criteria

1. THE project SHALL define an AgentCore Gateway named `education-advisor-gateway`
   (authorizer type `NONE`) bound to the `AdmissionAgent` runtime.
2. THE gateway SHALL register a `lambda-function-arn` target named
   `advisor-requests` backed by the `education-advisor-requests` Lambda, using the
   pre-provisioned tool schema.
3. THE gateway SHALL expose two MCP tools: `submit_advisor_request` (write) and
   `list_advisor_requests` (read).
4. WHEN the gateway is deployed THEN the system SHALL record the MCP URL
   (`https://<gateway-id>.gateway.bedrock-agentcore.<region>.amazonaws.com/mcp`) in
   `agentcore/.env.local` (local) and in the `envVars` array of `agentcore.json`
   (production) as `ADVISOR_MCP_URL`.

### R9: Specialist agent tools (Module 9, local-testable code / deploy-only behavior)

**User story:** As a maintainer, I want each specialist encapsulated as a `@tool`,
so that the orchestrator can delegate by intent and each agent stays focused.

#### Acceptance Criteria

1. THE system SHALL provide `app/AdmissionAgent/agents/admission.py` with a
   `route_to_admission(query, student_id=None)` function decorated with `@tool`,
   which creates a Strands `Agent` (via `load_model()`) with the `retrieve` and
   `query_student_db` tools and the Admission Advisor "Alex" prompt, runs the query
   (prepending `student_id` when provided), and returns a string.
2. THE `agents/admission.py` module SHALL set `STRANDS_KNOWLEDGE_BASE_ID` from
   `KNOWLEDGE_BASE_ID` at module level.
3. THE system SHALL provide `app/AdmissionAgent/agents/advisor_requests.py` with a
   `route_to_advisor_requests(query, student_id=None)` function decorated with
   `@tool`, which builds an `MCPClient` (using `streamablehttp_client` from
   `mcp.client.streamable_http` and the `ADVISOR_MCP_URL`), obtains MCP tools via
   `list_tools_sync()`, and creates a Strands `Agent` with the MCP tools plus
   `query_student_db`.
4. THE Advisor Requests Agent prompt SHALL instruct it to (a) assess whether the
   request is reasonable and complex enough to warrant a formal request, (b) use
   `query_student_db` to check the student's record for supporting evidence, (c)
   submit via MCP only when justified, and (d) provide guidance instead of
   submitting for trivial or unsupported requests.
5. THE supported advisor request types SHALL be `course_override`,
   `advisor_meeting`, `program_change`, and `special_consideration`.

### R10: Orchestrator entrypoint (Module 9, local-testable code / deploy-only behavior)

**User story:** As a student, I want one entrypoint that understands my intent, so
that information questions and action requests are each handled by the right
specialist.

#### Acceptance Criteria

1. THE `app/AdmissionAgent/main.py` SHALL import `route_to_admission` and
   `route_to_advisor_requests` and set the orchestrator Agent's tools to
   `[route_to_admission, route_to_advisor_requests]`.
2. THE orchestrator SHALL retain the `BedrockAgentCoreApp` scaffold, `load_model()`,
   logging, the Module 8 memory session manager, and a Strands conversation
   manager.
3. THE orchestrator system prompt SHALL classify intent and route information
   lookups to the Admission Agent and action requests to the Advisor Requests
   Agent, passing `student_id` when identified.
4. WHEN a justified request is made (e.g. student 100033 with a 3.8 GPA requesting a
   course override) THEN the Advisor Requests Agent SHALL verify the record and
   submit the request.
5. WHEN a trivial request is made (e.g. a meeting to ask something answerable
   directly) THEN the Advisor Requests Agent SHALL decline and provide guidance
   instead of submitting.
6. WHEN a cross-domain query is made (e.g. GPA lookup + program change) THEN the
   orchestrator SHALL route each part to the appropriate specialist.
7. WHEN a submission succeeds THEN a corresponding item SHALL appear in the
   `education-advisor-requests` DynamoDB table with student ID, request type,
   description, and `pending` status.

### R11: Streamlit thin client (Module 7, deploy-only)

**User story:** As a user, I want the Streamlit app to talk to the deployed agent,
so that the UI is a thin client and the agent logic runs in AgentCore.

#### Acceptance Criteria

1. THE Streamlit app SHALL read `AGENTCORE_RUNTIME_ARN` from `.env` via
   `load_dotenv()`.
2. THE Streamlit app SHALL invoke the deployed runtime via the `bedrock-agentcore`
   SDK (`invoke_agent_runtime`) and SHALL NOT create a local `Agent`, import tools,
   or make direct Bedrock calls.
3. THE app SHALL extract response text from `content[0]['text']` of the AgentCore
   response dict and render it with `st.markdown()`.

### R12: Observability (Module 7, deploy-only)

**User story:** As an operator, I want logs and traces for the deployed agent, so
that I can debug behavior and see the perception-thinking-action loop.

#### Acceptance Criteria

1. THE deployed agent SHALL emit CloudWatch logs viewable via `agentcore logs`
   (including filtering by time/severity and search).
2. THE deployed agent SHALL emit distributed traces viewable via
   `agentcore traces list` / `agentcore traces get` and in the Bedrock console
   Observability view.
3. THE traces SHALL show agent, model, tool (`retrieve`, `query_student_db`), and
   memory spans as applicable to each invocation.

### R13: Deployment workflow (all modules, deploy-only)

**User story:** As a developer, I want a repeatable deploy workflow, so that
built-and-tested code goes to AgentCore Runtime reliably.

#### Acceptance Criteria

1. THE project SHALL deploy via `agentcore deploy` (CDK-backed), approving the
   one-time CDK bootstrap on first deploy.
2. THE system SHALL support previewing changes via `agentcore deploy --plan`.
3. THE deployment status SHALL be observable via `agentcore status`.
4. WHERE this repo is the transport, deployment SHALL be performed from the Amazon
   Linux 2023 Code Editor EC2 instance after code is committed and pulled there;
   local machine work stops at the point the code is ready to upload/deploy.

---

## Out of Scope

- Module 8's "Learning Support Agent" learning-profile use case (referenced only
  as future context in the workshop text).
- Provisioning the pre-existing workshop infrastructure (Knowledge Base, Athena
  Lambda, advisor-requests Lambda/DynamoDB table) — these are assumed present.
- Non-workshop features (payments, evaluators, A/B tests, policy engines) available
  in the AgentCore schema but not exercised by Modules 7-9.
