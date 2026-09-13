# Known Issues

Running list of known issues in this repo and the workshop content, with fixes
where available. Newest issues near the top of each section.

## AgentCore

Issues specific to Amazon Bedrock AgentCore and the `@aws/agentcore` CLI
(build / launch / deploy, runtime, MCP servers, identity, gateways, etc.).

<!-- Add AgentCore issues here as they are found. Suggested format:
### <short title>
- **Status:** Open | Worked around | Resolved
- **CLI / version:** e.g. @aws/agentcore 0.29.0
- **Symptom:** what you observed (error message, unexpected behavior).
- **Cause:** root cause if known.
- **Fix / workaround:** exact command or change.
-->

### `npm install -g @aws/agentcore` is VERY SLOW on Windows (looks frozen)
- **Status:** Resolved / known behavior.
- **CLI / version:** @aws/agentcore 0.29.0
- **Platform:** Windows-specific. The install is MUCH faster on Linux; on
  Windows a single install can take on the order of 10-15 minutes and appears
  frozen the whole time. (In this session, 0.28.0 then 0.29.0 back-to-back felt
  like a solid 10-15 min combined, on top of the earlier interrupted attempts.)
- **Symptom:** `npm install -g @aws/agentcore@<ver>` sits on a spinner with no
  visible output for several minutes and appears frozen.
- **Cause:** `@aws/agentcore` pulls a large dependency tree (many `@aws-sdk/*`,
  `@opentelemetry/*`, plus a native module `@napi-rs/keyring`). The final
  write/bin-link phase produces no line output, so it looks stuck while it is
  actually progressing. On Windows this phase is dramatically slower than on
  Linux (slow filesystem / antivirus scanning of the many small files and the
  native module are the usual culprits). Budget ~10-15 minutes per install on
  Windows, not just a few.
- **Fix / workaround:** Let it run to completion. Do NOT interrupt it — killing
  the process mid-write can leave the package installed (`npm ls -g` shows it)
  but with the `agentcore` bin shim missing (`agentcore` = "not recognized").
  If that happens, re-run the install and let it finish. Running with
  `--loglevel http` shows package fetches so you can confirm it is progressing.
  If you have a Linux environment available (e.g. the Code Editor EC2 box),
  installing there is noticeably faster.

### `agentcore create --defaults` cannot be combined with other flags
- **Status:** Confirmed (bug / design gap). Workaround known.
- **CLI / version:** Reproduced on both `0.26.0` and `0.29.0` (latest). Not a
  version issue — it is how the CLI currently behaves. Verified firsthand on
  Windows (0.29.0) and previously on Linux (0.26.0/0.29.0, Node v24.19.0).
- **Symptom:** The workshop Step 1 command fails immediately:
  ```bash
  agentcore create --name AdmissionAgent --defaults --build Container
  ```
  Error:
  ```
  Use --no-agent for project-only, or provide all: --framework, --model-provider, --memory
  ```
  Providing only some flags (e.g. `--name` + `--build`) fails the same way.
- **Platform difference on failure:**
  - Linux: prints the error and exits `0` (silent failure).
  - Windows: prints the error AND crashes libuv immediately after —
    `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING), file src\win\async.c`
    with exit code `-1073740791` (0xC0000409).
- **Cause (per `agentcore create --help`):** `--defaults` selects a *harness
  project with default settings* and is itself marked `[non-interactive]`.
  Every relevant flag (incl. `--build`) is also `[non-interactive]`, and "Flags
  marked [non-interactive] trigger CLI mode." In CLI mode the tool requires the
  full set `--framework` + `--model-provider` + `--memory`; it does NOT merge
  those from `--defaults`, and partial flags do NOT drop into the interactive
  TUI — they just error.
- **Fix / workaround:** Pass all three flags explicitly (this is confirmed to
  create the project successfully — `AdmissionAgent/`, `app/AdmissionAgent/`,
  `agentcore/`, etc.):
  ```bash
  agentcore create --name AdmissionAgent --framework Strands --model-provider Bedrock --memory none --build Container
  cd AdmissionAgent
  ```
  Verified with `--dry-run` on Windows (0.29.0): produces `AdmissionAgent/`,
  `AdmissionAgent/agentcore/` (agentcore.json, aws-targets.json, .env.local,
  cdk/), and `AdmissionAgent/app/AdmissionAgent/` (main.py, pyproject.toml).
  Valid flag values (from `agentcore create --help`, 0.29.0):
  - `--framework`: `Strands` | `LangChain_LangGraph` | `GoogleADK` | `OpenAIAgents` | `VercelAI`
  - `--model-provider`: `Bedrock` | `Anthropic` | `OpenAI` | `Gemini`
  - `--memory`: `none` | `shortTerm` | `longAndShortTerm`
  - `--build`: `CodeZip` (default) | `Container`
  - `--language`: `Python` (default) | `TypeScript`
- **Secondary issues seen with the same command:**
  - Error message is unhelpful: doesn't say `--defaults` is being ignored,
    doesn't list `--build` or the valid values, doesn't suggest the TUI.
  - Failure exit behavior is bad in different ways per platform: on Linux it
    exits `0` (silent failure — `&&` chains/scripts don't detect it, user only
    finds out when `cd AdmissionAgent` fails); on Windows it crashes with a
    libuv assertion and a 0xC0000409 exit code instead of a clean error.

### Scaffold defaults `runtimeVersion` to the newest Python (`PYTHON_3_14`)
- **Status:** Worked around (pinned to `PYTHON_3_13`).
- **CLI / version:** @aws/agentcore 0.29.0
- **Symptom:** A fresh `agentcore create` writes
  `"runtimeVersion": "PYTHON_3_14"` into `agentcore/agentcore.json`. Python 3.14
  is very new; many native wheels and the surrounding ecosystem lag a new Python
  release, so a brand-new project defaulting to it risks container-build/runtime
  failures.
- **Note:** This is NOT from the workshop content. The workshop only specifies
  `requires-python = ">=3.10"` (a lower bound) and never mentions 3.14 or any
  `runtimeVersion`. The value is purely the CLI's default.
- **Fix / workaround:** Set `runtimeVersion` to `PYTHON_3_13` in `agentcore.json`
  (valid enum per AGENTS.md: `PYTHON_3_10..3_14`). Re-run `agentcore validate`
  after editing.


### `agentcore dev -b` TUI output can't be copied — use `agentcore invoke`
- **Status:** Worked around.
- **CLI / version:** @aws/agentcore 0.29.0
- **Symptom:** The interactive `agentcore dev -b` chat TUI renders in a way that
  makes it impossible to select/copy the agent's output (esp. in the web Code
  Editor terminal). Wastes time.
- **Fix / workaround:** Don't use the TUI, and don't try to background
  `agentcore dev -b` (it errors: "This command requires an interactive
  terminal"). Use the TWO-TERMINAL pattern with copyable output:
  ```bash
  # Terminal 1: start the dev server, leave running (note the port, e.g. 8081)
  agentcore dev --logs
  # Terminal 2: send prompts (match --port to Terminal 1)
  agentcore dev "your prompt here" --port 8081
  ```
- **Also note:** `agentcore invoke` targets the DEPLOYED runtime, not the local
  dev server. For local testing use `agentcore dev "prompt"`, not
  `agentcore invoke`. And the OpenTelemetry `host.docker.internal:4318`
  connection errors in the dev server log are harmless noise on EC2.


## Workshop content

### Out-of-date CLI commands in workshop content
- **Status:** Open / tracking.
- **Summary:** Some workshop instructions reference older `agentcore` CLI
  behavior and commands that have changed. The CLI has moved fast
  (`0.15.0` -> `0.29.0`), so command syntax and flags in the walkthroughs may
  no longer match the installed CLI.
- **Action:** Audit workshop steps against `agentcore 0.29.0` and update the
  affected commands. Individual command corrections will be listed here as they
  are found.

### Step 1 `agentcore create` command is broken
- Old (fails, see AgentCore issue above):
  ```bash
  agentcore create --name AdmissionAgent --defaults --build Container
  ```
- New (works):
  ```bash
  agentcore create --name AdmissionAgent --framework Strands --model-provider Bedrock --memory none --build Container
  cd AdmissionAgent
  ```

<!-- Add more out-of-date commands below as they are identified:
### <command / page> is out of date
- Old: `...`
- New: `...`
-->

## Toolchain / setup

### Keep the `agentcore` CLI up to date (target: 0.29.0)
- **What it is:** The `agentcore` command is the npm package **`@aws/agentcore`**,
  installed **globally via npm** (NOT via pip, and NOT the same as the pip
  package `bedrock-agentcore-starter-toolkit`).
- **Check the installed version:**
  ```powershell
  agentcore --version
  npm ls -g @aws/agentcore
  ```
- **Check the latest published version:**
  ```powershell
  npm view @aws/agentcore version
  ```
- **Update to the target version:**
  ```powershell
  npm install -g @aws/agentcore@0.29.0
  ```
  Or install the latest stable:
  ```powershell
  npm install -g @aws/agentcore@latest
  ```
- **Verify:**
  ```powershell
  agentcore --version   # expect 0.29.0
  ```
- **Note:** `1.0.0-preview.*` / `1.0.0-rc.1` prereleases exist on npm. Do NOT
  use `@latest` if it starts resolving to a prerelease you don't want; pin the
  explicit stable version (`@0.29.0`) instead.

### Keep AWS CDK up to date
- **What it is:** The AWS CDK CLI (`cdk`), installed **globally via npm** as
  `aws-cdk`.
- **Check the installed version:**
  ```powershell
  cdk --version
  ```
- **Check the latest published version:**
  ```powershell
  npm view aws-cdk version
  ```
- **Update to the latest:**
  ```powershell
  npm install -g aws-cdk@latest
  ```
- **Verify:**
  ```powershell
  cdk --version
  ```
- **Note:** Last confirmed working version in this workspace was `2.1134.0`.
  Keep the CDK library (`aws-cdk-lib` in the project) reasonably aligned with
  the CLI version to avoid version-skew warnings.
