---
inclusion: auto
name: build-warnings-workflow
description: How to handle AWS Holmes / Workshop Studio scan reports and build warnings. Use when the user uploads or references a raw scan-report JSON, an AWS Holmes scan, build warnings, code scan findings, or asks to summarize/remediate findings, or mentions .kiro/build-warnings.
---

# Build Warnings Workflow (AWS Holmes scan reports)

## Purpose

AWS Holmes (Workshop Studio content scanning) produces raw `scan-report*.json`
files. These are large, transient, and noisy. This workflow turns each raw scan
report into a small, human-readable findings summary that lives in git, then
deletes the raw JSON (it is always re-downloadable from the AWS Holmes portal).

## Home

All build-warning artifacts live under `.kiro/build-warnings/`, in a dated,
flattened folder per scan:

```
.kiro/build-warnings/
└── YYYYMMDD-build-warnings/
    ├── YYYYMMDD-aws-holmes-findings.md   # committed summary (source of truth in git)
    └── scan-report*.json                 # raw report — GITIGNORED; deleted after conversion
```

- `.kiro/build-warnings/` is under `.kiro/` (NOT `static/`), so nothing here is
  published to the Workshop Studio asset bucket or re-scanned.
- The raw JSON is gitignored via `.gitignore`:
  `.kiro/build-warnings/**/scan-report*.json`

## Trigger

When the user uploads / drops a raw `scan-report*.json` into
`.kiro/build-warnings/` (or references a new Holmes scan), do the conversion
below.

## What to do

1. **Locate the raw report.** It will be at
   `.kiro/build-warnings/YYYYMMDD-build-warnings/scan-report*.json`
   (create the dated folder if needed; use the scan/build date, not today's date,
   if they differ — confirm with the user if ambiguous).

2. **Generate the summary** at
   `.kiro/build-warnings/YYYYMMDD-build-warnings/YYYYMMDD-aws-holmes-findings.md`
   following the format of the existing summaries in that directory
   (see `20260616-aws-holmes-findings.md` and `20260617-aws-holmes-findings.md`
   for the canonical structure). Include, at minimum:
   - **Scan Overview** table: Scan ID, Baseline, Total Objects Scanned, Scan Date,
     Branch, Scanners.
   - **Build Warnings Summary** table: each warning with Severity, Error Code,
     Description.
   - **High Severity Findings**: a table per finding — Finding #, File, Resource,
     Lines, Check (e.g. `CKV_AWS_18`), and root cause / status
     (e.g. accepted/suppressed, legacy file, pending deletion).
   - **Comparison to previous scan** (if a prior summary exists): deltas in
     finding counts and which findings resolved / are new.
   - **Files scanned** (with findings, and clean) and a **Resolution Path**.
   - Note any **accepted / suppressed** findings explicitly (e.g. the permanent
     `CKV_AWS_18` on `LoggingBucket` — recursive logging is not recommended, so
     it is accepted and requires no action).

3. **Do NOT commit the raw JSON.** It is gitignored on purpose. Commit only the
   `*-aws-holmes-findings.md` summary.

4. **Delete the raw JSON after converting.** Once the summary is written and
   verified, delete the raw `scan-report*.json` — it is large and can be
   re-downloaded from the AWS Holmes portal at any time, so there is no need to
   keep it on local disk. Standard practice: convert, verify, then delete.
   (The `.gitignore` rule stays regardless, as a safety net.)

## Notes

- Do not rewrite git history to clear `LARGE_DELETED_FILE_WARNING` unless the user
  explicitly asks. It is non-blocking. Because raw scan JSON is now gitignored,
  new reports will not add to the warning; any residual warning is from historical
  blobs and is left alone by default.
- The accepted baseline finding for this workshop is `CKV_AWS_18` on
  `LoggingBucket` (1 High, suppressed). If a new scan shows exactly 1 High
  finding, confirm it is this one before treating the scan as clean.
