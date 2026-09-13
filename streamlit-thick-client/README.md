# streamlit-thick-client

Phase 1 of the demo roadmap: the Peculiar University advisor running the
**Strands agent locally**. Every AWS service call happens in-process with your
own credentials:

- Bedrock model inference (Claude Sonnet)
- Bedrock Knowledge Base retrieval (course handbook RAG)
- `query_student_db` tool → Athena query Lambda (`education-athena-query`)

No AgentCore runtime is involved. This is the "before" state: the same advisor
UX as the thin client, but all the intelligence lives here.

## Self-contained

This directory carries its own copies of `config.py`, `advisor_agent.py`, and
`query_student_db.py` on purpose. It does not import from `src/` or the other
client directories.

## Prerequisites

- Python 3.13, the repo-root `venv` (or a fresh venv with `requirements.txt`).
- AWS credentials in the shell with access to Bedrock (model + KB
  `Retrieve`/`GetKnowledgeBase`) and `lambda:InvokeFunction` on the Athena
  query Lambda, all in `us-west-2`.
- Repo-root `.env` with `KNOWLEDGE_BASE_ID` (and optionally `AWS_REGION`,
  `BEDROCK_MODEL_ID`, `ATHENA_LAMBDA_NAME`).

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then ask about courses, prerequisites, or a specific student (name the student
ID, e.g. "student 100033").
