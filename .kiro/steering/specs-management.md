# Specs Management

## Purpose

Organize feature specs, bugfix specs, and reference materials in a scalable, date-based directory structure that makes it easy to find work by time period.

## Directory Structure

### Specs

Specs are organized by **year/month/name** under `.kiro/specs/`:

```
.kiro/specs/
├── 2026/
│   ├── 03/
│   │   └── 20260325-resolve-build-warnings/
│   │       ├── .config.kiro
│   │       ├── requirements.md (or bugfix.md)
│   │       ├── design.md
│   │       └── tasks.md
│   └── 06/
│       └── 20260611-resolve-build-warnings/
│           ├── .config.kiro
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
└── legacy/
    └── (old specs that predate this convention)
```

### References

Reference materials (scan reports, external docs, research) follow the same pattern under `.kiro/references/`:

```
.kiro/references/
└── 2026/
    └── 06/
        └── 20260611-build-warnings/
            ├── 20260611-aws-holmes-findings.md
            └── scan-report.json
```

## Naming Conventions

### Spec Directories

- **Path**: `.kiro/specs/YYYY/MM/YYYYMMDD-descriptive-name/`
- **Date prefix**: The date the spec was created
- **Name**: Kebab-case description of the work
- **Example**: `.kiro/specs/2026/06/20260611-resolve-build-warnings/`

### Reference Directories

- **Path**: `.kiro/references/YYYY/MM/YYYYMMDD-descriptive-name/`
- **Date prefix**: The date the reference was captured
- **Example**: `.kiro/references/2026/06/20260611-build-warnings/`

### Reference Files

- **Format**: `YYYYMMDD-descriptive-name.ext`
- **Example**: `20260611-aws-holmes-findings.md`

## Branch Naming

When a spec requires a feature branch for implementation:

- **Branch name**: Same as the spec directory name
- **Example**: Spec at `specs/2026/06/20260611-resolve-build-warnings/` → branch `20260611-resolve-build-warnings`

Minor fixes that don't need a spec can go directly to main.

## Workflow

1. **Create reference materials** in `.kiro/references/YYYY/MM/` as needed
2. **Create spec directory** in `.kiro/specs/YYYY/MM/YYYYMMDD-name/`
3. **Generate spec files** (requirements → design → tasks) using Kiro's spec workflow
4. **Create feature branch** matching the spec name for implementation
5. **Execute tasks** via the spec task runner

## Legacy

Specs created before this convention live in `.kiro/specs/legacy/`. They are not moved or restructured — just preserved as-is.
