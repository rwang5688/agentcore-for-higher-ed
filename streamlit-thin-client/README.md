# streamlit-thin-client

Phase 2 of the demo roadmap: the Peculiar University advisor as a **thin client**
over a managed backend. This app runs no agent logic locally. It forwards each
prompt to the deployed AgentCore runtime via `invoke_agent_runtime` and renders
the streamed response.

All the intelligence — model inference, Knowledge Base retrieval, Athena
queries, multi-agent orchestration, and memory — runs on the AgentCore backend
(the `AdmissionAgent` runtime), not here.

## Self-contained

This directory carries its own `config.py` (just the runtime ARN + region) and
`app.py`. It does not import from `src/` or the other client directories. The
`invoke_agent` logic here is the same business logic that gets merged into
`deploy-streamlit-app/docker_app` for the hosted (Cognito + ECS Fargate)
Phase 3.

## Prerequisites

- Python 3.13, the repo-root `venv` (or a fresh venv with `requirements.txt`).
- AWS credentials in the shell with `bedrock-agentcore:InvokeAgentRuntime` on
  the deployed runtime, in `us-west-2`.
- Repo-root `.env` with `AGENTCORE_RUNTIME_ARN` (from `agentcore status`) and
  optionally `AWS_REGION`.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then ask about courses, prerequisites, a specific student, or submit an advisor
request (name the student ID, e.g. "student 100033").
