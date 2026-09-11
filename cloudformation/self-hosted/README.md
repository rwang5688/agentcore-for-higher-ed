# Self-Hosted Templates

Modified CloudFormation templates for deploying in your own AWS account (e.g., Isengard dev account, customer POC). Workshop Studio dependencies have been removed.

**Region note:** All stacks deploy to us-west-2 EXCEPT Stack 5 (Identity Center), which must be in us-east-1 due to Kiro/Q Developer console requirements.

## Stack 1: Knowledge Base Buckets

**Template:** `1-knowledge-base-buckets.yaml`

**Corresponds to:** `workshop/1-knowledge-base.yaml`

**What it does:**
- Creates the KB documents bucket (`<account-id>-<region>-education-kb-docs`)
- Creates the KB supplemental bucket (`<account-id>-<region>-education-kb-supplemental`)
- Creates an S3 access logs bucket (`<account-id>-<region>-s3-access-logs`) with 90-day lifecycle
- Enables access logging on both KB buckets

**Deploy:**

```bash
aws cloudformation deploy \
  --template-file cloudformation/self-hosted/1-knowledge-base-buckets.yaml \
  --stack-name education-kb-buckets \
  --capabilities CAPABILITY_NAMED_IAM
```

**Post-deploy: Upload KB documents:**

```bash
aws s3 sync ./education-kb-docs/ s3://<account-id>-<region>-education-kb-docs/
```

**Then:** Create the Knowledge Base manually in the Bedrock console (select "Create new service role", point data source to the KB documents bucket, configure S3 Vectors, and sync).

## Stack 2: Code Editor

**Template:** `2-code-editor-full.yaml`

**Corresponds to:** `workshop/2-code-editor-full.yaml` (identical - no modifications needed)

**What it does:**
- Launches an EC2 instance (m8g.large Graviton, Amazon Linux 2023) with VS Code Server
- Bootstraps: AWS CLI, Node.js, Python 3.13, Docker, AgentCore CLI, Kiro CLI, uv, Strands Agents
- Configures Kiro CLI with workshop MCP servers (aws-docs, aws-diagrams, strands-agents)
- Puts it behind CloudFront for HTTPS access
- Creates a Secrets Manager secret for the editor password

**Deploy:**

```bash
aws cloudformation deploy \
  --template-file cloudformation/self-hosted/2-code-editor-full.yaml \
  --stack-name education-code-editor \
  --capabilities CAPABILITY_NAMED_IAM
```

**Note:** No Workshop Studio dependencies. All S3 asset paths default to empty. Deploys cleanly in any account.

## Stack 3: AgentCore Role

**Template:** `3-agentcore-role.yaml`

**What it does:**
- Creates the IAM role for AgentCore (Strands Agents)

**Deploy:**

```bash
aws cloudformation deploy \
  --template-file cloudformation/self-hosted/3-agentcore-role.yaml \
  --stack-name agentcore-role \
  --region us-west-2 \
  --capabilities CAPABILITY_NAMED_IAM
```

## Stack 4a: Athena Buckets

**Template:** `4-athena-buckets.yaml`

**What it does:**
- Creates the education-data bucket (`<account-id>-<region>-education-data`)
- Creates the education-results bucket (`<account-id>-<region>-education-results`) with 7-day lifecycle
- Enables S3 access logging on both (via ImportValue from Stack 1)

**Deploy:**

```bash
aws cloudformation deploy \
  --template-file cloudformation/self-hosted/4-athena-buckets.yaml \
  --stack-name education-athena-buckets \
  --region us-west-2
```

**Post-deploy: Upload education data:**

```bash
aws s3 sync ./education-data/ s3://<account-id>-<region>-education-data/
```

## Stack 4b: Athena Setup

**Template:** `4-athena-setup.yaml`

**Requires:** Stack 4a deployed AND education data uploaded to S3.

**What it does:**
- Creates Glue database (`education_workshop_db`) with 12 tables (schema from CSV headers)
- Creates Athena workgroup (`education_workgroup`) with results bucket
- Deploys Athena query Lambda (`education-athena-query`)
- Deploys advisor requests DynamoDB table and Lambda
- Deploys Cognito user pool and OAuth client (for gateway auth)

**Deploy:**

```bash
aws cloudformation deploy \
  --template-file cloudformation/self-hosted/4-athena-setup.yaml \
  --stack-name education-athena-setup \
  --region us-west-2 \
  --capabilities CAPABILITY_IAM
```

## Stack 5: Identity Center (us-east-1 ONLY)

**Template:** `5-identity-center-only.yaml`

**IMPORTANT:** This is the only stack deployed to us-east-1. The Kiro/Q Developer console requires IDC in us-east-1 or eu-central-1. Only one IDC instance allowed per account.

**What it does:**
- Creates an IAM Identity Center instance (`education-agents-idc`)

**Deploy:**

```bash
aws cloudformation deploy \
  --template-file cloudformation/self-hosted/5-identity-center-only.yaml \
  --stack-name identity-center-only \
  --region us-east-1
```

**Post-deploy:**
1. Disable MFA in IAM Identity Center settings
2. Create SSO user (fictitious email like `kiro-user-01@example.com` is fine)
3. Reset password > Generate one-time password
4. Navigate to Kiro console (us-east-1), enable small teams, assign user
