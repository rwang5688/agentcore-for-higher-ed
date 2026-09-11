# Module 6: Connecting to Live Data

> **Reminder (self-hosted):** Everything in this module runs in **us-west-2** (KB, Athena Lambda, and Bedrock model all live there). The workshop text shows `us-east-1`; ignore that for the self-hosted path.

This module replaces the mock `data/students.json` lookup with a live data layer: the agent writes SQL at runtime and queries the Student Information System (12 Athena tables in `education_workshop_db`) by invoking the `education-athena-query` Lambda.

By the end you have a local Streamlit "advisor's assistant" that answers questions grounded in real student records, cross-referenced against the course handbook Knowledge Base.

---

## What you're building

```
Advisor (chat) -> Streamlit app -> Strands Agent
                                     |-- KB search (course handbook)      -> Bedrock Knowledge Base
                                     |-- query_student_db(sql)  -> Lambda  -> Athena -> S3 (Glue catalog)
```

Two tools on one agent:
- **KB search** (via `MemoryManager` + `BedrockKnowledgeBaseStore`) for course/program/prerequisite questions.
- **`query_student_db`** for live student data. The model generates Athena SQL from the user's question.

---

## Lessons, gotchas, and booby traps

These are the traps we actually hit while building this. Watch for them.

### 1. Region must match everywhere
The KB, the Athena Lambda, and the Bedrock model all live in **us-west-2**. If your `.env` `AWS_REGION` (or a stray `AWS_REGION`/`AWS_DEFAULT_REGION` in your shell) points elsewhere, calls fail with `ResourceNotFoundException` (Lambda) or signing oddities. Confirm the region in `.env` matches where your stacks were deployed.

### 2. AWS credentials: check them FIRST, every session
Isengard credentials are short-lived. The most confusing failure is `InvalidSignatureException` / `SignatureDoesNotMatch` deep in a botocore stack trace when the agent initializes the KB. It looks like a code bug; it is not. It means your credentials are expired or mismatched (e.g. you refreshed only some of `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN`, or an already-open shell kept stale env vars).

**Always sanity-check before launching:**

```powershell
aws sts get-caller-identity
```

If that prints your ARN, you're good. If it errors, refresh your credentials and re-run it until it succeeds. (A SessionStart hook at `.kiro/hooks/aws-creds-check.json` runs this automatically when Kiro starts.)

### 3. Activate the venv, or `strands.memory` "disappears"
Running `streamlit run ...` from a shell where the venv is **not** activated uses a different Python and fails with `ModuleNotFoundError: No module named 'strands.memory'`. The package is installed in the venv, not globally. Activate first (one shot):

```powershell
.\venv\Scripts\Activate.ps1; streamlit run src\streamlit_advisor.py
```

### 4. Never `echo >>` into `.env` on PowerShell
PowerShell redirection writes UTF-16, which corrupts `.env` (characters appear spaced out, existing lines get clobbered) and `python-dotenv` then misreads it. Edit `.env` in your editor, or if scripting use `Add-Content -Encoding utf8`. Keep variables alphabetically sorted so it's easy to eyeball that everything is present.

### 5. Env loading order matters (don't read env at import time)
If a tool module reads `os.getenv("AWS_REGION")` into a module-level constant at **import** time, it can run **before** `.env` is loaded, capturing `None`. boto3 then falls back to a default region and the Lambda is "not found." Fix: read config at **call** time, not import time. This repo centralizes it in `src/config.py` via `get_config()` (loads `.env` once, cached), and entry points call `get_config()` first. Importing a module has no side effects.

### 6. The Lambda response is double-encoded JSON
The Lambda returns `{"statusCode": 200, "body": "<json string>"}`. The `body` is a **string** that must be parsed again to get `{"result": [ ...rows... ]}`. Parse `body`, then read `result`. On non-200, return the error so the agent can see it and retry.

### 7. Generated SQL varies run-to-run
The model writes SQL from natural language, so it won't be identical every time, and some attempts will be wrong (bad column, missing join, non-Athena syntax). This is expected. The tool surfaces the Athena error back to the agent, which usually corrects itself on the next try. To reduce misfires, keep the schema summary in the tool docstring accurate and rely on the `.kiro/steering/database-schema.md` steering file.

### 8. Athena is Presto/Trino, and IDs are typed inconsistently
Use single quotes for strings (`WHERE student_id = '100016'`). `student_id` is a **string**; most other `_id` columns are integers. There is **no `program` column** on `student` — a student's program is derived via `student.department_id -> department`.

### 9. Empty results usually mean the scope, not a bug
The dataset is scoped to the **College of Engineering** (AERO, COMP, Data Science, Engineering, Environment and Natural Resources). A query returning nothing often means the WHERE clause is outside that scope. Try a broader query to confirm data exists.

### 10. Pick a data-rich student for the "recommend next courses" demo
Aeronautics (AERO) has only **2 courses** in the handbook, so "what should this AERO student take next?" dead-ends immediately (there's nothing left to recommend). Use a **Computer Science** student (COMP has many courses) so the recommendation flow actually has something to work with. We use student **100033** (Diego Ramirez, CS).

### 11. Some data looks odd, on purpose / by artifact
Cumulative GPA may show `0` (treat as "not yet posted"), last names have suffixes like `Jackson_184`, and course levels have large numbers. This is sample data. A good advisor-assistant answer flags these as "verify with the department" rather than stating them as fact.

---

## Where things live (final structure)

```
src/
├── config.py            # get_config(): loads .env once, no import-time side effects
├── advisor_agent.py     # SHARED: SYSTEM_PROMPT + create_agent()
├── query_student_db.py  # SHARED tool: Athena query via Lambda
├── kb_advisor.py        # CLI entry point
├── streamlit_advisor.py # Streamlit chat UI
└── simple_agent.py      # standalone starter
.kiro/steering/database-schema.md   # full schema (always-included steering)
data/students.json                  # mock data, kept only as a test fixture
```

- The tool lives in `src/` (not a top-level `tools/`) so imports resolve with **no `sys.path` hacks**.
- Config is never passed around as a parameter; modules call the cached `get_config()`.

---

## Run it (RUNBOOK)

```powershell
# 1. Verify credentials (must print your ARN)
aws sts get-caller-identity

# 2. Activate venv + launch (one shot)
.\venv\Scripts\Activate.ps1; streamlit run src\streamlit_advisor.py
```

Opens at http://localhost:8501.

---

## Sample questions (in the sidebar, simple -> complex)

1. **KB only** — "What computer science courses are available, and what are their prerequisites?"
2. **Athena (aggregate)** — "Which courses in the COMP department have the most registrations?"
3. **Athena (single profile)** — "Pull up student 100033's profile: their program, enrollment status, and cumulative GPA."
4. **KB + Athena (flagship)** — "Look up student 100033's completed courses, then recommend which Computer Science courses they're eligible to take next and list the prerequisites."

---

## Sample Q&A (what "good" looks like)

**Q (flagship, hits both tools):**
> Look up student 100033's completed courses, then recommend which Computer Science courses they're eligible to take next and list the prerequisites.

**A (abridged):**

The agent first calls `query_student_db` to pull the student's profile and completed courses, then searches the handbook KB for candidate courses and prerequisites, and combines them:

- **Student profile:** Diego Ramirez (ID 100033), Department: Computer Science, Status: Enrolled, Cumulative GPA: 0 on record (flagged as "verify — likely a data entry issue").
- **Completed courses:** ~26 courses listed with grades and terms (mostly COMP, plus a couple of ENGI).
- **Recommended next COMP courses** — each with handbook prerequisites and an eligibility note, e.g.:
  - *COMP-8600 Introduction to Algorithms* — prereqs COMP-5210, COMP-5340, MATH-4120 + programming proficiency; note that Diego's completed work is strong equivalent prep, suggest a prerequisite equivalency check with the department.
  - *COMP-8400 Introduction to Artificial Intelligence* — prereqs listed; note Diego's ML/Python background aligns.
  - *COMP-9400 Programming Abstractions* — flags an unconfirmed prereq (COMP-7100) and the GPA-gated requirement (GPA shows 0, needs verification).
- **Advisor action items:** verify cumulative GPA (shows 0), confirm a missing prerequisite, consider a department equivalency review.

**Why this is a good answer:**
- It used **both** tools in one turn (live DB + handbook KB).
- It **cross-referenced** completed courses against prerequisites rather than listing them separately.
- It spoke to the **advisor** in third person about the student.
- It **flagged data quirks** (GPA = 0, unconfirmed prereqs) instead of stating them as fact.

> Contrast: asking the same question for an **Aeronautics** student (e.g. 100016) dead-ends because AERO has only 2 courses and they're already completed. That's expected given the sample data — see gotcha #10. Use a CS student for this demo.
