# Requirements: Streamlit Admission Advisor

## Overview

A Strands-based admission advisor agent for Peculiar University, runnable both
as a CLI script and as a Streamlit chat interface. The agent answers questions
about courses and programs from a Bedrock Knowledge Base and looks up live
student records by querying the Student Information System through Athena.

This document describes the final state of the local Streamlit advisor app.

## Context

- Model: `us.anthropic.claude-sonnet-4-6` (Amazon Bedrock)
- Region: `us-west-2` (KB and Athena Lambda both live here)
- Knowledge Base: Peculiar University course handbook (Bedrock Knowledge Base)
- Live student data: 12-table Student Information System in the
  `education_workshop_db` Athena database, queried via the
  `education-athena-query` Lambda
- Config is supplied via `.env` (git-ignored), documented in `.env.example`
- A later phase moves the agent onto Amazon Bedrock AgentCore in its own CDK
  project/repo, so naming here must not collide with "AgentCore".

## Functional Requirements

### R1: Simple starter agent
- A minimal Strands agent with no tools, used as a learning/reference example.
- WHEN run, THEN it answers a sample prompt as a university admission assistant.

### R2: Knowledge Base search
- The agent SHALL search the course handbook Knowledge Base before answering
  course/program/prerequisite questions.
- The agent SHALL cite retrieved details and say plainly when the KB has no
  answer rather than guessing.
- The KB integration SHALL use the current Strands memory API
  (`MemoryManager` + `BedrockKnowledgeBaseStore`, read-only), not the
  deprecated `retrieve` tool.

### R3: Live database query tool
- A tool `query_student_db` SHALL accept a `sql` string and query the
  `education_workshop_db` Athena database by invoking the `education-athena-query`
  Lambda via boto3 (`InvocationType='RequestResponse'`, payload `{"sql": <query>}`).
- The tool SHALL parse the Lambda response contract
  `{"statusCode": 200, "body": "<json string>"}`, where `body` parses to
  `{"result": [<row dicts>]}`, and SHALL return the `result` list.
- WHEN `statusCode` is not 200 (or the invoke fails), THEN the tool SHALL return
  the error rather than raising.
- The Lambda name SHALL come from the `ATHENA_LAMBDA_NAME` environment variable.
- The tool's docstring SHALL include a schema summary so the model can generate
  correct Athena (Presto/Trino) SQL at runtime.
- The full schema SHALL also be provided to Kiro as an always-included steering
  file at `.kiro/steering/database-schema.md`, derived from the `education-data/`
  CSVs.
- The agent's system prompt SHALL tell it that it can look up real student
  records, course registrations, and degree plans via SQL against
  `education_workshop_db`.

### R4: Streamlit chat interface
- The app SHALL provide a chat input and display conversation history.
- The app SHALL maintain per-session conversation context.
- The app SHALL provide a way to clear the conversation.
- The app SHALL offer copy-paste sample questions in the sidebar.
- The app SHALL NOT require a student-ID input; the agent looks up any student
  by querying the database directly.

### R5: Configuration
- Config values (`ATHENA_LAMBDA_NAME`, `AWS_REGION`, `BEDROCK_MODEL_ID`,
  `KNOWLEDGE_BASE_ID`) SHALL be loaded from `.env` via `python-dotenv`.
- `.env` SHALL be git-ignored; `.env.example` SHALL document every variable.
- `.env`/`.env.example` variables SHALL be listed in alphabetical order.
- Required config (`KNOWLEDGE_BASE_ID`) SHALL fail fast if missing.

## Non-Functional Requirements

### N1: Run from project root
- All three scripts SHALL run from the project root using the `src/` prefix:
  - `python src/simple_agent.py`
  - `python src/kb_advisor.py`
  - `streamlit run src/streamlit_advisor.py`

### N2: DRY (no duplicated code)
- Shared agent setup (config, tools, system prompt, agent factory) SHALL be
  defined exactly once and imported where needed. This is a hard requirement:
  the project is subject to a code-quality scan that fails on duplication.

### N3: No path hacks
- No `sys.path` manipulation. Imports SHALL resolve cleanly through normal
  package/module resolution when run from the project root.

### N4: Naming
- No shared module named `*_core` or anything that reads as "AgentCore", to
  avoid confusion with the later AgentCore phase.

### N5: Developer experience
- The README SHALL document, near the top, how to activate the virtual
  environment (PowerShell) and how to run each script.

### N6: Testability
- `data/students.json` SHALL be retained as a fixture for unit tests (e.g.
  asserting `query_student_db` response parsing against known records), even
  though it is no longer read at runtime.

### N7: Explicit configuration, no import-time side effects
- Importing any module SHALL NOT read the environment or load `.env`.
- A single `get_config()` function SHALL load `.env` (once) and return the
  resolved configuration; it is the one place configuration is loaded.
- Entry points SHALL call `get_config()` first, before building an agent.
- Shared modules SHALL obtain configuration via `get_config()` (cached) rather
  than receiving it as a passed-around parameter.
