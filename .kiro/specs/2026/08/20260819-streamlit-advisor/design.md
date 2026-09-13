# Design: Streamlit Admission Advisor

## Architecture Summary

One shared agent module is the single source of truth. Two thin entry points
(a CLI script and a Streamlit app) import from it. This satisfies DRY (N2), and
because everything lives under `src/` as normal modules, no `sys.path` hack is
needed (N3).

```
project root/
├── .env                     # config values (git-ignored)
├── .env.example             # documented config template
├── .kiro/steering/
│   └── database-schema.md   # always-included schema steering
├── data/
│   ├── payload.json         # sample Lambda payload for manual Athena testing
│   └── students.json        # retained only as a unit-test fixture
├── education-data/          # source CSVs the schema was derived from
├── README.md                # venv activation + run commands
├── requirements.txt
└── src/
    ├── __init__.py          # makes src/ a package
    ├── advisor_agent.py     # SHARED: SYSTEM_PROMPT, create_agent()
    ├── config.py            # SHARED: get_config() explicit env loading
    ├── kb_advisor.py        # CLI entry point -> get_config() + create_agent
    ├── query_student_db.py  # SHARED tool: live Athena query via Lambda
    ├── simple_agent.py      # standalone starter agent (no shared deps)
    └── streamlit_advisor.py # Streamlit UI -> get_config() + create_agent
```

All application code is concentrated under `src/` (flat package). The later
AgentCore phase gets its own CDK project/repo, so there is no need for a
separate top-level `tools/` package here; keeping the tool in `src/` alongside
`advisor_agent.py` keeps imports hack-free (N3).

## Module Responsibilities

### `src/config.py` (explicit configuration)
- Has NO import-time side effects: importing it neither reads the environment
  nor loads `.env`.
- Defines an immutable `Config` dataclass (`athena_lambda_name`, `aws_region`,
  `knowledge_base_id`, `model_id`).
- `get_config() -> Config` loads the repo-root `.env` (resolved via
  `Path(__file__)`), reads the values, and is cached with `lru_cache` so the
  load happens exactly once per process. `KNOWLEDGE_BASE_ID` uses
  `os.environ[...]` so a missing value fails fast (R5).

### `src/advisor_agent.py` (single source of truth)
- Defines `SYSTEM_PROMPT`, which instructs the agent to search the KB for
  course/program questions and to use SQL (via `query_student_db`) for live
  student records, registrations, and degree plans.
- Defines `create_agent() -> Agent`, which calls `get_config()`, builds a
  read-only `BedrockKnowledgeBaseStore`, wraps it in a `MemoryManager`, and
  returns an `Agent` with the KB memory plus the `query_student_db` tool.
- `create_agent()` returns a fresh agent each call so callers (e.g. Streamlit)
  can keep isolated per-session conversation history.
- No module-level env reads or `load_dotenv` (no import-time side effects).

### `src/query_student_db.py` (shared tool)
- Defines the `query_student_db` Strands `@tool`.
- Calls `get_config()` at call time (not import time) for `aws_region` and
  `athena_lambda_name`; constructs a boto3 Lambda client lazily.
- Invokes the Lambda (`InvocationType='RequestResponse'`, payload `{"sql": ...}`),
  parses `{"statusCode": 200, "body": "<json string>"}` -> `{"result": [...]}`,
  and returns the `result` list; returns the error when `statusCode != 200` or
  the invoke fails.
- Docstring embeds a condensed schema summary so the model writes correct SQL.

### `src/kb_advisor.py` (CLI)
- Under `__main__`, calls `get_config()` first (explicit up-front load), then
  `create_agent()`, then runs a sample live-data query.

### `src/streamlit_advisor.py` (UI)
- Calls `get_config()` at startup (before building any agent).
- Chat UI only: session state, history rendering, chat input, sidebar with
  sample questions and a clear-conversation button. No student-ID input, no
  agent/tool definitions.

### `src/simple_agent.py` (starter)
- Independent minimal example; intentionally not wired to the shared module.

## Key Design Decisions

### D1: Shared module instead of inlining
Inlining tool/agent setup into each script would duplicate code and fail the
quality scan (N2). A shared module keeps one definition.

### D2: No `sys.path` hack
Running `python src/kb_advisor.py` and `streamlit run src/streamlit_advisor.py`
from the root puts `src/` on the path automatically (Python adds the script's
directory; Streamlit does the same), so `from advisor_agent import ...` and
`from query_student_db import ...` resolve without manipulation (N3).

### D3: Naming (`advisor_agent`, not `advisor_core`)
Avoids collision with the later Amazon Bedrock AgentCore phase (N4).

### D4: KB via memory API, not deprecated `retrieve`
`strands_tools.retrieve` is deprecated. Using `MemoryManager` +
`BedrockKnowledgeBaseStore(writable=False)` is the supported path (R2). The
store takes the KB ID via config; the module reads it from the environment.

### D5: Path resolution relative to files, not CWD
`config.py` resolves `.env` from `Path(__file__)` so scripts work regardless of
the directory they are launched from (supports N1).

### D6: Agent generates SQL at runtime
Rather than a fixed-shape profile lookup, the agent writes Athena SQL from the
user's question. The schema is supplied twice: in the tool docstring (for the
runtime model) and as always-included Kiro steering (`database-schema.md`, for
the coding assistant). Generated SQL can vary run-to-run; the tool surfaces
Lambda/Athena errors back to the agent so it can correct and retry.

### D7: boto3 Lambda invoke inherits environment credentials
The tool invokes the Lambda directly with boto3, so it uses the environment's
IAM credentials automatically. No API keys or Function URLs are required, which
also eases the later move to AgentCore.

### D8: Explicit config loading via `get_config()`, no import-time side effects
Loading `.env` as a side effect of importing a module is fragile: it makes the
result depend on import order (an earlier bug had `query_student_db` snapshot
`AWS_REGION` at import, before `advisor_agent` had loaded `.env`, yielding
`None` and a Lambda "resource not found"). Instead, `config.get_config()` is the
single, explicit load point:

- Importing any module has no side effects; nothing reads env or loads `.env`.
- Entry points (`kb_advisor.py`, `streamlit_advisor.py`) call `get_config()`
  first, so config loading is an explicit, up-front action the app controls.
- Shared modules (`create_agent()`, `query_student_db`) also call `get_config()`
  where they need values; `lru_cache` makes every call after the first a cheap
  lookup, so the load happens exactly once regardless of call order.
- Config is not passed around as a parameter; callers read it from the cached
  `get_config()`, keeping tool signatures (e.g. the model-facing
  `query_student_db(sql)`) clean.

## Configuration Flow

Entry point calls `get_config()` -> `config.py` runs `load_dotenv()` on the
repo-root `.env` (once, via `lru_cache`) -> reads env into an immutable
`Config` -> `create_agent()` and `query_student_db` call the cached
`get_config()` for the values they need (`knowledge_base_id`, `aws_region`,
`model_id`, `athena_lambda_name`). `KNOWLEDGE_BASE_ID` uses `os.environ[...]`
so a missing value fails fast (R5). See D8.

## Out of Scope
- Amazon Bedrock AgentCore deployment (future phase, separate repo).
- Persisting conversations beyond a browser session.
- Auth / access control on the Streamlit app.
