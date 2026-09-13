# deploy-streamlit-app

Phase 3 of the demo roadmap: the Peculiar University advisor as a **hosted thin
client** — the Streamlit UI behind Cognito authentication, running on ECS
Fargate (ALB + CloudFront), invoking the deployed AgentCore runtime.

This is the same thin-client business logic as `streamlit-thin-client/`, merged
into the aws-samples ECS Fargate + Cognito shell. All agent intelligence (model,
Knowledge Base retrieval, Athena queries, multi-agent orchestration, memory)
runs on the AgentCore backend. The authenticated Cognito username is passed as
`actor_id`, so long-term memory is scoped per user.

## Components

- Streamlit app in ECS/Fargate, behind an ALB and CloudFront.
- A Cognito user pool for authentication (manage users from the console).
- The Fargate task role granted `bedrock-agentcore:InvokeAgentRuntime` on the
  deployed runtime (NOT `bedrock:InvokeModel` — this is a thin client).

## What changed from the aws-samples baseline

- `docker_app/utils/agentcore.py` (new) — `AgentCoreClient.invoke()` calls the
  deployed runtime via `invoke_agent_runtime` and parses the streamed response
  (same logic as `streamlit-thin-client`).
- `docker_app/app.py` — after the Cognito login gate, renders the advisor chat
  UI and calls the AgentCore client with `actor_id = authenticator.get_username()`.
- `docker_app/utils/llm.py` — removed (was a direct claude-v2 Bedrock demo).
- `docker_app/config_file.py` — `DEPLOYMENT_REGION = "us-west-2"` and
  `AGENTCORE_RUNTIME_ARN` (the deployed `AdmissionAgent` runtime).
- `cdk/cdk_stack.py` — task-role IAM swapped to
  `bedrock-agentcore:InvokeAgentRuntime` scoped to the runtime ARN.

## Prerequisites

- The `AdmissionAgent` AgentCore runtime already deployed in `us-west-2` (see
  the repo's `AdmissionAgent/` and `agentcore status`).
- Docker, AWS CLI, and AWS CDK on the deploy host.
- Bedrock/AgentCore access in `us-west-2`.

NOTE: the laptop has NO Docker, so build/synth/deploy happen on the Amazon Linux
2023 Code Editor EC2 instance, not the laptop. Laptop work stops at code edits +
import smoke tests.

## Configure

Edit `docker_app/config_file.py`:

- `STACK_NAME` / `CUSTOM_HEADER_VALUE` — change if deploying a second instance.
- `AGENTCORE_RUNTIME_ARN` — must match the deployed runtime
  (`agentcore status`, or `AdmissionAgent/agentcore/.cli/deployed-state.json`).
- `DEPLOYMENT_REGION` — keep `us-west-2` (matches the runtime/KB/Lambda).

## Deploy runbook (EC2 Code Editor, human-run)

```bash
# From deploy-streamlit-app/ on the EC2 instance (Docker available):
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cdk bootstrap        # first time in the account/region only
cdk deploy           # ~5-10 min; builds the docker_app image and pushes to ECR
```

Note the stack outputs: the CloudFront distribution URL and the Cognito user
pool id.

Then:

1. In the Cognito user pool (AWS console), create a user.
2. Open the CloudFront URL in a browser (use a pop-out window, not an embedded
   preview, so session cookies persist).
3. Log in with the Cognito user.
4. Ask the advisor a question (name a student ID, e.g. "student 100033"). The
   response comes from the deployed AgentCore runtime, with memory scoped to
   your Cognito user.

## Run locally for development (EC2, no Docker)

After the Cognito user pool exists (post-`cdk deploy`), you can run the Streamlit
app directly against it:

```bash
cd docker_app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8080
```

You still need AWS credentials with `bedrock-agentcore:InvokeAgentRuntime` and
`secretsmanager:GetSecretValue` on the Cognito secret.

## Limitations (from the aws-samples baseline)

- CloudFront-to-ALB traffic is HTTP, not TLS. For real use, bring your own domain
  and certificate to the ALB.
- This is demo/starter code. Vet third-party deps (Streamlit,
  streamlit-cognito-auth), harden the Cognito configuration (password policy,
  MFA, advanced security), and add WAF/Shield/network controls before production.

## Acknowledgments

Inspired by:

- https://github.com/tzaffi/streamlit-cdk-fargate.git
- https://github.com/aws-samples/build-scale-generative-ai-applications-with-amazon-bedrock-workshop/

## License

Licensed under the MIT-0 License. See the LICENSE file.
