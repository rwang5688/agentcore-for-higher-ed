# AgentCore Build/Deploy Workflow (Checkpoint Discipline)

## Purpose

Building and deploying AgentCore agents involves Docker container image builds,
live AWS credentials, and a separate Amazon Linux 2023 Code Editor EC2 instance
for deployment. The human has to step in at specific points (apply credentials,
upload code, run `agentcore deploy`). This document defines a **checkpoint-based
workflow** so Kiro stops at clean handoff points and the human always knows when
it is their turn — instead of Kiro making an endless stream of changes with no
break to jump in.

**Core rule: Kiro works in short, bounded segments that end at a CHECKPOINT.
Kiro does NOT blow through checkpoints.**

## The Five Stages

Every AgentCore change moves through these stages. Ownership is explicit.

| # | Stage | Who | Needs credentials? | Where |
| --- | --- | --- | --- | --- |
| 1 | Shutdown + apply credentials | Human | — | laptop |
| 2 | Code/config edits + `agentcore validate` | Kiro | NO (no Docker/creds needed) | laptop |
| 3 | Upload changed code to EC2 | Human | — | laptop → EC2 (git) |
| 4 | Local tests on EC2 (`agentcore dev`) | Human | YES (instance profile) | EC2 |
| 5 | `agentcore deploy` | Human | YES (instance profile) | EC2 |

Kiro directly performs work only in **Stage 2** (code/config edits + `agentcore
validate`). Stages 1, 3, 4, 5 are **human-executed**; Kiro's job there is to
prepare and hand off cleanly with exact instructions.

**KEY CONSTRAINT: the laptop has NO Docker.** Container builds
(`agentcore dev`, `agentcore deploy`) require Docker, so ALL local testing and
deploy happen on the EC2 instance — NOT the laptop. The laptop cannot run
`agentcore dev`. This means Stage 2 on the laptop stops at `agentcore validate`;
credentials are only needed on EC2, not the laptop.

## Checkpoints (where Kiro STOPS and hands control back)

Kiro MUST pause and yield to the human at each of these. Do not proceed past a
checkpoint without an explicit go-ahead.

- **CP-A — Code/config ready, credentials needed.** All file edits for the current
  segment are done, but the next step (local test, or reading account ID) needs
  AWS credentials that the current shell lacks. Kiro stops so the human can
  shut down and apply credentials (Stage 1).
- **CP-C — Code valid, ready to upload.** Edits are done and `agentcore validate`
  passes. Kiro stops so the human can commit/push and upload to EC2 (Stage 3).
  Kiro does NOT commit or push (see git_safety). (There is no laptop local-test
  checkpoint: no Docker on the laptop.)
- **CP-D — EC2 handoff.** Everything the human runs by hand on EC2 (Stages 4-5) is
  written in the README deploy runbook. Kiro stops; the human runs EC2 local
  tests (`agentcore dev`) and `agentcore deploy`.

## Kiro's Responsibilities

1. **Announce the plan and the next checkpoint BEFORE starting a segment.** e.g.
   "I'll do tasks 1.6-1.7, then stop at CP-C for you to commit and upload." The
   human should always know how long until the next natural break.
2. **Batch edits, then pause.** Group the file/config edits for one segment, make
   them, then stop at the checkpoint. Do not chain into the next segment.
3. **Laptop work needs no credentials.** Code/config edits, `uv lock`, `uv sync`,
   `npm install`, and `agentcore validate` run without AWS creds or Docker.
   Anything that runs a container or hits AWS (`agentcore dev`, `agentcore deploy`,
   `agentcore invoke`) is EC2-only — do NOT attempt it on the laptop.
4. **Keep the paperwork current at every checkpoint:**
   - Update the spec `tasks.md` with per-task status (DONE / IN PROGRESS / BLOCKED).
   - Keep the EC2 deploy runbook current (the "Deploy the AgentCore agent" section
     in `README.md`) — the human has no Kiro on EC2 to automate anything.
   - Update the day's session notes with where we paused and what's next.
5. **Never run `agentcore deploy` or the EC2 steps.** Those are Stage 4-5, human
   only, on the EC2 instance. Kiro prepares and documents them.
6. **Do not commit or push** (per git_safety). Tell the human when a checkpoint
   is a good commit point.
7. **Respect "give me a break."** If the human signals they need to step in, STOP
   after the current file write — do not start new work.

## What Needs Credentials (so Kiro knows when CP-A applies)

- Reading the AWS account ID (`aws sts get-caller-identity`) — needed to fill
  `executionRoleArn` in `agentcore.json`.
- `agentcore dev -b` tool calls at runtime: Bedrock model invoke, Knowledge Base
  `retrieve`, and the Athena query Lambda (this repo: us-west-2).
- Any `agentcore invoke`, `agentcore deploy`, `agentcore status`, `agentcore logs`.

File edits, `uv lock`, `uv sync`, `npm install`, and `agentcore validate` do
**not** need credentials and can be done before CP-A.

## Local vs EC2 environments

- `uv.lock` and `package.json`/`package-lock.json` are committed and travel via
  git. `.venv/` and `node_modules/` are gitignored and regenerated per-machine
  (`uv sync` / `npm install`, or automatically by `agentcore dev`/`deploy`).
- `agentcore/.env.local` is gitignored and does NOT travel — it is recreated on
  EC2 from the repo `.env`.
- Region for this repo is **us-west-2** (KB + Lambdas), not the workshop's
  us-east-1 examples.

## Typical Segment (example)

1. Kiro: "Next segment = tasks X-Y (file edits + `agentcore validate`). I'll stop
   at CP-C."
2. Kiro makes the edits; runs `agentcore validate`; updates tasks.md; stops at CP-C.
3. Human: commits, pushes, uploads to EC2.
4. Human on EC2: runs the README deploy runbook — `agentcore dev` local test
   (Stage 4), then `agentcore deploy` (Stage 5).
