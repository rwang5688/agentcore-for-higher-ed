# Session Notes - 2026-09-11

## Environment
- Machine: work laptop (Windows, PowerShell, local Kiro IDE)
- venv: `venv\` at repo root, Python 3.13.11
- Returned with fresh AWS credentials this session.

## What We're Working On
- Getting the local toolchain ready for the AgentCore build-out (per the
  2026-09-10 plan): activate the venv and confirm the `agentcore` CLI and
  AWS CDK are properly installed and up to date.
- Target versions: `agentcore` CLI `0.29.0` (latest stable).

## Work Completed / Findings This Session

### venv activation
- Activated with: `. .\venv\Scripts\Activate.ps1`
- Confirmed Python 3.13.11 inside the venv.

### Tooling inventory
| Tool | Found at start | Upgraded to | Notes |
| --- | --- | --- | --- |
| `agentcore` CLI | `0.15.0` | `0.29.0` (latest stable) | npm `@aws/agentcore`. Verified working. |
| `cdk` (AWS CDK) | `2.1134.0` | `2.1141.0` (latest) | npm `aws-cdk`. Verified working. |

Final verified state: `agentcore --version` -> `0.29.0`, `cdk --version` ->
`2.1141.0`, both bin shims present.

### Gotcha: agentcore install is VERY SLOW on Windows (looks frozen)
- Windows-specific: the install is much faster on Linux. On Windows,
  `npm install -g @aws/agentcore` sits on a no-output spinner and is SLOW —
  budget ~10-15 min per install (0.28.0 then 0.29.0 back-to-back this session
  felt like a solid 10-15 min combined, plus the earlier interrupted attempts).
  Slowness is from its large dep tree (`@aws-sdk/*`, `@opentelemetry/*`, native
  `@napi-rs/keyring`). It is progressing, not stuck.
- Interrupting it mid-write left the package present (`npm ls -g` showed it) but
  with the `agentcore` bin shim MISSING (`agentcore` -> "not recognized"). Fix
  was to let a fresh install run uninterrupted in the background to completion.
- Logged in ISSUES.md under the AgentCore section.

### KEY FINDING: `agentcore` CLI is an npm package, not pip
- The `agentcore` command does NOT come from the venv or from pip.
- It resolves to a **global npm install**:
  - `Get-Command agentcore` -> `D:\Users\wangrob\AppData\Roaming\npm\agentcore.ps1`
  - `where.exe agentcore` -> `...AppData\Roaming\npm\agentcore(.cmd)`
- Underlying package: **`@aws/agentcore`** (confirmed via `npm ls -g` ->
  `@aws/agentcore@0.15.0`, and the `.cmd` shim points at
  `node_modules\@aws\agentcore\dist\cli\index.mjs`).
- The pip package `bedrock-agentcore-starter-toolkit` is a DIFFERENT thing
  (its versions top out at 0.3.x), and is NOT what provides the `agentcore`
  command here. Do not confuse the two.
- `npm view @aws/agentcore version` -> `0.29.0` (latest stable). There are
  `1.0.0-preview.*` / `1.0.0-rc.1` prereleases published, but `0.29.0` is the
  latest STABLE and matches the target.

### AgentCore CLI: `agentcore create --defaults` is broken (confirmed on Linux)
- From a prior Linux workshop run (Node v24.19.0), reproduced on both CLI
  `0.26.0` and `0.29.0` — so NOT a version issue.
- FAILS: `agentcore create --name AdmissionAgent --defaults --build Container`
  -> `Use --no-agent for project-only, or provide all: --framework, --model-provider, --memory`
- WORKS: `agentcore create --name AdmissionAgent --framework Strands --model-provider Bedrock --memory none --build Container`
- `--defaults` does not merge with other flags; partial flags don't drop into
  the TUI; the failing command exits 0 (silent failure).
- Logged in ISSUES.md (AgentCore section + Workshop content Step 1 fix).

## Next Steps
- Toolchain is ready: `agentcore` 0.29.0 and `cdk` 2.1141.0 both verified.
- Proceed with the AgentCore build-out per the 2026-09-10 plan (resolve the
  open architecture questions, then scaffold/integrate under `agentcore/`).
- When we run `agentcore create` here, use the explicit-flags form above.

### Scaffolded AdmissionAgent/ (this session, Windows, agentcore 0.29.0)
- Ran from project root:
  `agentcore create --name AdmissionAgent --framework Strands --model-provider Bedrock --memory none --build Container`
  -> "Project created successfully!"
- Verified generated structure matches the workshop's target diagram:
  - `agentcore/`: `.cli/`, `.llm-context/`, `cdk/`, `.env.local`, `.gitignore`,
    `agentcore.json`, `aws-targets.json` (exact match)
  - `app/AdmissionAgent/`: `.venv/`, `mcp_client/`, `model/`, `.dockerignore`,
    `.gitignore`, `Dockerfile`, `main.py`, `pyproject.toml`, `README.md`,
    `uv.lock` — all present, PLUS a new `skills/` dir (0.29.0 addition not in
    the older target diagram).
  - top level: `AGENTS.md`, `README.md`.
- Confirms the workshop's claim that `--defaults` produces this structure is
  OUTDATED: `--defaults` won't even run alongside `--build`; the explicit-flags
  form is what actually generates it.
- TODO: decide `.gitignore` handling for `AdmissionAgent/` build artifacts
  (`.venv/`, `.cli/`, etc.) before committing.

### Transfer decision: scaffold on Code Editor, pull baseline via GitHub
- File counts for the local `AdmissionAgent/` scaffold (measured this session):
  - Everything on disk: **23,174** files.
  - Committed baseline (gitignore-respected): **33** files.
  - Ignored artifacts (`.venv/` ~6,085, `agentcore/cdk/node_modules/` ~17,054):
    **23,141** files.
- Conclusion: DO NOT upload the raw scaffold (~23K files). Scaffold on Code
  Editor (Linux, fast install), commit the ~33-file baseline, push to GitHub,
  then pull down here. Regenerate `node_modules/` + `.venv/` locally.
- Local `AdmissionAgent/` was DELETED this session (was fully untracked, 0
  tracked files — clean, reproducible). Repo is prepped for a clean pull.

## END-OF-SESSION STATE (2026-09-11 night) — resume here in the morning
- Toolchain ready: `agentcore` 0.29.0, `cdk` 2.1141.0, venv at `venv\`.
- Local `AdmissionAgent/` removed. `git status`: clean except two UNTRACKED,
  UNCOMMITTED files created this session (left for you to commit):
  - `ISSUES.md`
  - `.kiro/session-notes/2026/09/20260911-session-notes.md` (this file)
- `origin` = github.com/rwang5688/agentcore-for-higher-ed; local `main` in sync
  with `origin/main` at `753e3c5` (AdmissionAgent baseline NOT on remote yet).
- Kiro did NOT commit or push (per your instruction).

### Morning steps
1. On Code Editor (Linux):
   `agentcore create --name AdmissionAgent --framework Strands --model-provider Bedrock --memory none --build Container`
   - Confirm `git status` shows ~33 baseline files (artifacts ignored).
   - Commit the baseline, push to `origin/main`.
2. Back here (Windows): `git pull` to bring the baseline down.
3. Have Kiro repopulate envs locally:
   - `npm install` under `AdmissionAgent/agentcore/cdk/`
   - `uv sync` under `AdmissionAgent/app/AdmissionAgent/`
4. Then decide `.gitignore` handling + integrate.

## Open Questions
- Same architecture questions still open from 2026-09-10 (region, swarm
  topology, advisor appointments backend, MCP server split, CDK language).

## Related
- Created `ISSUES.md` at repo root to track out-of-date workshop content
  (known issue) plus the agentcore/aws-cdk update instructions.
