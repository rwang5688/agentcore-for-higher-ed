# AgentCore for Higher Education - Workshop Templates

CloudFormation templates and knowledge base documents from the **Building Agents for Higher Education** AWS Workshop, with self-hosted equivalents for deploying in your own AWS account.

## Workshop References

- [Workshop Studio](https://studio.us-east-1.prod.workshops.aws/workshops/public/4277be71-fc3e-4ec3-a6e2-8c8f20db36a8)
- [Workshop Content](https://catalog.us-east-1.prod.workshops.aws/workshops/4277be71-fc3e-4ec3-a6e2-8c8f20db36a8/en-US)

## Repository Structure

```
.
├── cloudformation/
│   ├── workshop/       # Original CloudFormation templates from the workshop (as-is)
│   └── self-hosted/    # Modified templates for deploying in your own AWS account
├── data/               # Test data for the agents (e.g. students.json)
├── education-data/     # Structured CSV datasets (Athena/Glue student information source)
├── education-kb-docs/  # Knowledge Base source documents (Peculiar U course catalog)
├── iam/                # IAM policy documents
├── notes/              # Workshop observations, issues, and feedback
├── README.md
├── requirements.txt
└── src/                # Strands agent scripts (simple_agent, kb_advisor, streamlit_advisor)
```

## Purpose

1. **Workshop templates** (`cloudformation/workshop/`) - Capture the CloudFormation templates provided by the workshop exactly as they are, for reference and traceability. These depend on Workshop Studio infrastructure.

2. **Self-hosted templates** (`cloudformation/self-hosted/`) - Adapted versions with Workshop Studio dependencies removed. Ready to deploy in any AWS account (Isengard, customer POC, etc.).

3. **KB documents** (`education-kb-docs/`) - The Peculiar University course catalog markdown files used as the Bedrock Knowledge Base data source.

4. **Education data** (`education-data/`) - Structured CSV datasets (12 tables, 987 students) used as the Athena/Glue data source for the student information system.

## Local Runbook: Run the Streamlit advisor

```powershell
# 1. Check AWS credentials (must print your Isengard ARN, not an error)
aws sts get-caller-identity

# 2. Activate the venv and launch the app (one shot)
.\venv\Scripts\Activate.ps1; streamlit run src\streamlit_advisor.py
```

Opens at http://localhost:8501. If step 1 errors, refresh your credentials before step 2.

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

Streamlit chat interface (opens in your browser at http://localhost:8501):

```powershell
.\venv\Scripts\Activate.ps1; streamlit run src\streamlit_advisor.py
```

## Notes

- Templates will be added as we work through the workshop modules.
- See `notes/workshop-issues.md` for observations and workarounds.

**Kiro and IDE Setup:** The workshop uses a VS Code Server instance with Kiro CLI for development. A next step is to switch to a local Kiro IDE installation for day-to-day development, using the remote Code Editor only for AgentCore CLI commands (`agentcore build`, `agentcore deploy`).

**Education datasets:** The education-data tables share the same schema as the [AWS Data EDU](https://github.com/aws-samples/data-edu) Student Information System databases, but the content appears to be re-written and aligned with education-kb-docs. Do not assume prior familiarity with Data EDU transfers here.
