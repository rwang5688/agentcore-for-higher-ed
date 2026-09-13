# AgentCore for Higher Education - Workshop Templates

CloudFormation templates and knowledge base documents from the **Building Agents for Higher Education** AWS Workshop, with self-hosted equivalents for deploying in your own AWS account.

## Workshop References

- [Workshop Studio](https://studio.us-east-1.prod.workshops.aws/workshops/public/4277be71-fc3e-4ec3-a6e2-8c8f20db36a8)
- [Workshop Content](https://catalog.us-east-1.prod.workshops.aws/workshops/4277be71-fc3e-4ec3-a6e2-8c8f20db36a8/en-US)

## Repository Structure

```
.
├── cloudformation/
│   ├── self-hosted/    # Modified templates for deploying in your own AWS account
│   └── workshop/       # Original CloudFormation templates from the workshop (as-is)
├── data/               # Test data for the agents (e.g. students.json)
├── deploy-streamlit-app/   # App mode 3: thin client on ECS Fargate + Cognito (CDK)
├── education-data/     # Structured CSV datasets (Athena/Glue student information source)
├── education-kb-docs/  # Knowledge Base source documents (Peculiar U course catalog)
├── iam/                # IAM policy documents
├── notes/              # Workshop observations, issues, and feedback
├── src/                # Older standalone Strands scripts (simple_agent, kb_advisor, advisor_agent, query_student_db)
├── streamlit-thick-client/ # App mode 1: runs the Strands agent locally (all AWS calls local)
├── streamlit-thin-client/  # App mode 2: invokes the deployed AgentCore runtime (thin client)
├── README.md
└── requirements.txt
```

## Streamlit advisor — three app modes

The advisor UI ships in three self-contained flavors, one per phase of the demo
roadmap (see `ROADMAP.md`). Pick the one that matches what you want to show:

| Directory | Mode | Where agent logic runs | Auth | Run |
| --- | --- | --- | --- | --- |
| `streamlit-thick-client/` | Local Strands agent | In-process (Bedrock + KB + Athena, your creds) | none | `streamlit run app.py` |
| `streamlit-thin-client/` | Managed backend | Deployed AgentCore runtime | none | `streamlit run app.py` |
| `deploy-streamlit-app/` | Hosted thin client | Deployed AgentCore runtime | Cognito | `cdk deploy` (EC2) |

Each directory is self-contained (its own `config.py`/app code) and carries its
own README with exact prerequisites and run commands:

- Local modes (thick + thin): see "Runbook: Run the local Streamlit advisor" below.
- Hosted mode: **[`deploy-streamlit-app/README.md`](deploy-streamlit-app/README.md)**
  has the full EC2 `cdk deploy` runbook (build, Cognito user, CloudFront test)
  and the `cdk destroy` teardown.

See `ROADMAP.md` for why you prototype on the thick client and go live on the
thin client + AgentCore.

## Purpose

1. **Workshop templates** (`cloudformation/workshop/`) - Capture the CloudFormation templates provided by the workshop exactly as they are, for reference and traceability. These depend on Workshop Studio infrastructure.

2. **Self-hosted templates** (`cloudformation/self-hosted/`) - Adapted versions with Workshop Studio dependencies removed. Ready to deploy in any AWS account (Isengard, customer POC, etc.).

3. **KB documents** (`education-kb-docs/`) - The Peculiar University course catalog markdown files used as the Bedrock Knowledge Base data source.

4. **Education data** (`education-data/`) - Structured CSV datasets (12 tables, 987 students) used as the Athena/Glue data source for the student information system.

## Deployment

### Prerequisites

- An AWS account with permissions to deploy CloudFormation stacks and create Bedrock resources.
- The [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) installed and configured with credentials (`aws configure` or `aws sso login`).
- Amazon Bedrock model access enabled in your target region for the model the agents use (`us.anthropic.claude-sonnet-4-6`).

### Self-Hosted Deployment

#### Stack 1: Knowledge Base Buckets

```bash
aws cloudformation deploy \
  --template-file cloudformation/self-hosted/1-knowledge-base-buckets.yaml \
  --stack-name education-kb-buckets \
  --capabilities CAPABILITY_NAMED_IAM
```

Then upload the KB documents:

```bash
aws s3 sync ./education-kb-docs/ s3://<account-id>-<region>-education-kb-docs/
```

Then create the Knowledge Base manually in the Bedrock console. Note the resulting Knowledge Base ID; you will need it for the environment configuration below.

## Environment Configuration

The agent scripts read configuration from a `.env` file at the repo root. Nothing will run until this is set up. Copy the template and fill in your values:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

| Variable | Description |
| --- | --- |
| `AWS_REGION` | Region where your Bedrock model and Knowledge Base live (e.g. `us-east-1`). |
| `BEDROCK_MODEL_ID` | Model ID the agents use (default `us.anthropic.claude-sonnet-4-6`). |
| `KNOWLEDGE_BASE_ID` | The Bedrock Knowledge Base ID from the deployment step above. Required. |

`.env` is git-ignored so your values are never committed. Valid AWS credentials with Bedrock access in the configured region are also required.

## Runbook: Run the local Streamlit advisor

Two local modes (both open at http://localhost:8501). Check credentials first:

```powershell
# Must print your Isengard ARN, not an error
aws sts get-caller-identity
```

Thick client — runs the Strands agent locally (Bedrock + KB + Athena):

```powershell
.\venv\Scripts\Activate.ps1; streamlit run streamlit-thick-client\app.py
```

Thin client — invokes the deployed AgentCore runtime (needs
`AGENTCORE_RUNTIME_ARN` in `.env`):

```powershell
.\venv\Scripts\Activate.ps1; streamlit run streamlit-thin-client\app.py
```

If the credentials check errors, refresh your credentials before launching. For
the hosted (Cognito + ECS Fargate) mode, see `deploy-streamlit-app/README.md`.

## Runbook: Deploy the AgentCore agent (from the EC2 Code Editor)

The `AdmissionAgent/` AgentCore project is built and deployed from the Amazon
Linux 2023 Code Editor EC2 instance (Docker + instance-profile credentials). The
laptop has NO Docker, so it is used only for code edits and review — all
container build, local test, and deploy happen on EC2.

**The change cycle (who does what, in order):**

1. **Laptop:** make code edits; upload the changed files to the EC2 instance.
2. **EC2:** `git add` / commit + push the changes.
3. **Laptop / WorkSpaces:** `git pull` and review.
4. **EC2:** local test — `agentcore dev --logs` (Terminal 1) +
   `agentcore dev "<prompt>"` (Terminal 2).
5. **EC2:** `agentcore deploy`, then `agentcore invoke` to verify.

The by-hand EC2 steps (env recreate, local test, deploy, verify) are below.

```bash
# 0. From the repo root on EC2, pull the latest
git pull

# A. Recreate the gitignored local environments (from committed lockfiles)
cd AdmissionAgent/app/AdmissionAgent && uv sync && cd -
cd AdmissionAgent/agentcore/cdk && npm install && cd -

# B. Recreate .env.local for local dev (gitignored; does NOT travel via git)
cd AdmissionAgent
grep -E 'KNOWLEDGE_BASE_ID|ATHENA_LAMBDA_NAME' ../.env >> agentcore/.env.local
echo "AWS_DEFAULT_REGION=us-west-2" >> agentcore/.env.local
cat agentcore/.env.local            # verify all three present

# C. Fill values that need live credentials (executionRoleArn in agentcore.json)
aws sts get-caller-identity --query Account --output text
#   -> edit agentcore/agentcore.json: set
#      "executionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/agentcore-agent-role"
agentcore validate

# D. Local test on EC2 (instance profile provides credentials)
#   Use TWO terminals. Do NOT use the `agentcore dev -b` TUI (output can't be
#   copied, hard to exit). This is the only local-test path we use.
#
#   ALWAYS clean up old dev servers/containers first so you don't creep up ports
#   (8081, 8082...). pkill alone may leave the Docker container holding the port:
#     pkill -f "agentcore dev"
#     docker rm -f $(docker ps -aq --filter "name=agentcore-dev") 2>/dev/null
#     docker ps            # should be empty
#
#   TERMINAL 1 — start the dev server and leave it running:
#     cd AdmissionAgent
#     agentcore dev --logs
#     # Note the port it prints (uses 8081 if 8080 is busy).
#     # OpenTelemetry "host.docker.internal:4318" connection errors are NOISE —
#     # ignore them. Wait for "Application startup complete".
#
#   TERMINAL 2 — send prompts (copyable output). Match --port to Terminal 1.
#   These are the two acceptance tests (both VERIFIED working 2026-09-13):
#     cd AdmissionAgent
agentcore dev "What are the prerequisites for Database Systems?" --port 8081                         # KB retrieval -> returns COMP-3210/3450/3620 prereqs
agentcore dev "Look up student 100016 and tell me what courses they have completed." --port 8081     # Athena query_student_db -> returns Mateo Jackson's 8 courses
#
#   Stop the server: Ctrl+C in Terminal 1. If a stray server/container lingers,
#   run the cleanup block above again.

# E. Deploy
agentcore deploy                    # first run: approve one-time CDK bootstrap (Y)
#   preview only:  agentcore deploy --plan
agentcore status                    # runtime should reach ACTIVE

# F. Test the production endpoint
agentcore invoke "What are the prerequisites for Database Systems?"
agentcore invoke "Look up student 100016 and tell me what courses they have completed."

# G. Observability
agentcore logs
agentcore traces list
```

### Adding the Advisor Requests Gateway (Module 9) — 2 deploys

The advisor MCP URL doesn't exist until the gateway is deployed, and the agent
needs that URL — so this is 2 deploys. Backend Lambda `education-advisor-requests`
must already exist (stack 4). On EC2:

```bash
cd AdmissionAgent
# 1. define gateway + target (target = the existing Lambda ARN + our tools.json)
agentcore add gateway --name education-advisor-gateway --authorizer-type NONE --runtimes AdmissionAgent
agentcore add gateway-target \
  --name advisor-requests \
  --type lambda-function-arn \
  --lambda-arn $(aws lambda get-function --function-name education-advisor-requests --query 'Configuration.FunctionArn' --output text) \
  --tool-schema-file ../mcp/tools.json \
  --gateway education-advisor-gateway

# 2. deploy #1 — creates the gateway (agent's advisor tool is inert until URL set)
agentcore deploy

# 3. get the gateway URL
agentcore status    # note the gateway id
#   ADVISOR_MCP_URL = https://<gateway-id>.gateway.bedrock-agentcore.us-west-2.amazonaws.com/mcp

# 4. set the URL in BOTH places, then deploy #2
#    - agentcore/.env.local:   ADVISOR_MCP_URL=<url>
#    - agentcore/agentcore.json envVars ADVISOR_MCP_URL value
agentcore deploy

# 5. verify
agentcore invoke "I'm student 100033. Submit a course override for Data Science: Machine Learning; I have a 3.8 GPA and completed equivalent prereqs." --session-id gwtest-0001-0001-0001-000000000001
```

Commit `agentcore.json` + `.cli/deployed-state.json` after each deploy.

### Adding AgentCore Memory (Module 8) — order matters

We go straight to memory with **both** long-term strategies (SEMANTIC +
USER_PREFERENCE). One memory resource with strategies also stores short-term
session events, so this is a superset of the workshop's short-term-only step —
no need to do that intermediate step separately.

Provision memory FIRST so `agentcore deploy` injects
`MEMORY_ADMISSION_AGENT_MEMORY_ID`, THEN change app code to use it. Two rounds:

1. **Provision with strategies (EC2):**
   ```bash
   agentcore remove memory --name admission_agent_memory   # only if a prior short-term-only one exists
   agentcore add memory --name admission_agent_memory --strategies SEMANTIC,USER_PREFERENCE
   agentcore deploy
   ```
   Commit `agentcore/agentcore.json` + `agentcore/.cli/deployed-state.json`, push.
2. **Use it (laptop→EC2):** pull; add `memory/session.py` (short + long-term
   retrieval_config) + wire `main.py`; commit, push; pull to EC2; `agentcore deploy`.

> Region for this repo is **us-west-2** (KB `ONVQOQ7XJB` + `education-athena-query`
> Lambda), not the workshop's us-east-1 examples.

## Local Development

### Activate the virtual environment (PowerShell)

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks the script with an execution-policy error, run this once for the session, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

You'll know it worked when your prompt shows `(venv)`. Run `deactivate` to exit.

### Install dependencies

```powershell
pip install -r requirements.txt
```

### Run the agent scripts

All commands are run from the repo root with the virtual environment activated. Each script is a separate entry point; run whichever one you want.

Basic Strands agent (no tools):

```powershell
python src\simple_agent.py
```

Knowledge Base advisor agent (course handbook + student_profile tool):

```powershell
python src\kb_advisor.py
```

Streamlit chat interface (opens in your browser at http://localhost:8501) — see
the "three app modes" section above; e.g. the local thick client:

```powershell
.\venv\Scripts\Activate.ps1; streamlit run streamlit-thick-client\app.py
```

## Notes

- Templates will be added as we work through the workshop modules.
- See `notes/workshop-issues.md` for observations and workarounds.

**Kiro and IDE Setup:** The workshop uses a VS Code Server instance with Kiro CLI for development. A next step is to switch to a local Kiro IDE installation for day-to-day development, using the remote Code Editor only for AgentCore CLI commands (`agentcore build`, `agentcore deploy`).

**Education datasets:** The education-data tables share the same schema as the [AWS Data EDU](https://github.com/aws-samples/data-edu) Student Information System databases, but the content appears to be re-written and aligned with education-kb-docs. Do not assume prior familiarity with Data EDU transfers here.
