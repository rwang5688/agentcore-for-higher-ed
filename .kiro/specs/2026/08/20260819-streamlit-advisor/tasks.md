# Tasks: Streamlit Admission Advisor

Status legend: [x] done, [ ] not started. Tasks describe the final state of the
local Streamlit advisor app.

## Setup
- [x] 1. Add `requirements.txt` (python-dotenv, streamlit, strands-agents,
  strands-agents-bedrock, strands-agents-tools), alphabetically sorted. _(R5)_
- [x] 2. Create `.env` and `.env.example`; ensure `.env` is git-ignored. _(R5)_
- [x] 3. Add `ATHENA_LAMBDA_NAME` to `.env` and `.env.example`; keep all
  variables alphabetically sorted (`ATHENA_LAMBDA_NAME`, `AWS_REGION`,
  `BEDROCK_MODEL_ID`, `KNOWLEDGE_BASE_ID`). _(R5)_

## Knowledge Base + shared agent
- [x] 4. Create `src/advisor_agent.py` as the single source of truth: config
  constants, `SYSTEM_PROMPT`, `create_agent()`. _(N2)_
- [x] 5. Integrate the Knowledge Base via `MemoryManager` +
  `BedrockKnowledgeBaseStore` (read-only); do not use the deprecated `retrieve`
  tool. _(R2, D4)_
- [x] 6. Resolve `.env` path from `Path(__file__)`, not CWD. _(D5)_

## Live data (Athena)
- [x] 7. Derive `.kiro/steering/database-schema.md` from the `education-data/`
  CSVs; mark it `inclusion: always`. _(R3)_
- [x] 8. Create `src/query_student_db.py`: `query_student_db` `@tool` that reads
  `ATHENA_LAMBDA_NAME`, invokes the Lambda via boto3
  (`InvocationType='RequestResponse'`, `{"sql": ...}`), parses
  `{"statusCode": 200, "body": "{\"result\": [...]}"}`, returns `result` or the
  error. Embed a schema summary in the docstring. _(R3, D6, D7)_
- [x] 9. Wire `query_student_db` into `create_agent()` and update `SYSTEM_PROMPT`
  to describe SQL access to `education_workshop_db`. Remove any
  `student_profile`/`students.json` runtime code path. _(R3, N2)_

## Configuration (explicit, no import-time side effects)
- [x] 9a. Create `src/config.py`: immutable `Config` dataclass +
  `get_config()` (cached with `lru_cache`) that loads `.env` and reads env.
  Importing the module has no side effects. _(N7, D8)_
- [x] 9b. Remove module-level `load_dotenv`/`os.getenv` from `advisor_agent.py`
  and `query_student_db.py`; read values via `get_config()` instead. _(N7, D8)_
- [x] 9c. Call `get_config()` first in entry points (`kb_advisor.py` under
  `__main__`; `streamlit_advisor.py` at startup). _(N7, D8)_

## Entry points
- [x] 10. `src/simple_agent.py`: minimal starter agent. _(R1)_
- [x] 11. `src/kb_advisor.py`: import `create_agent`, run sample under
  `__main__`; sample prompt is a live-data query. _(R2, R3)_
- [x] 12. `src/streamlit_advisor.py`: chat UI with history, chat input,
  clear-conversation button, and sidebar sample questions; imports
  `create_agent`. Removed the student-ID sidebar input and the
  `[Student ID: ...]` prepend. _(R4)_
- [x] 13. Add `src/__init__.py` so `src/` is a package. _(N3)_

## Constraints (must hold in final state)
- [x] 14. No `sys.path` manipulation anywhere. _(N3)_
- [x] 15. No duplicated agent/tool setup across entry points. _(N2)_
- [x] 16. Shared module named `advisor_agent` (not `*_core`). _(N4)_
- [x] 17. Keep `data/students.json` as a unit-test fixture (not read at
  runtime). _(N6)_
- [x] 18. README documents venv activation (PowerShell) and the run command for
  each script. _(N5)_

## Verification
- [x] 19. `python src/simple_agent.py` from the project root responds. _(R1, N1)_
- [x] 20. `python src/kb_advisor.py` from the project root calls the KB
  (`search_memory`) and `query_student_db` for a live-data prompt. _(R2, R3, N1)_
  Verified live: returns real data for student 100016 (8 completed courses).
- [x] 21. Grep confirms no `sys.path` references and no duplicated agent setup.
  _(N2, N3)_
- [ ] 22. FINAL ACCEPTANCE TEST: `streamlit run src/streamlit_advisor.py` from
  the project root loads the chat UI, has no student-ID input, and answers
  live-data questions (including the combined KB + Athena flagship question)
  with history preserved across turns. _(R4, N1)_

## Future (separate spec / repo)
- [ ] 23. Migrate the agent to Amazon Bedrock AgentCore (own CDK project).
