# Session Notes - 2026-08-09

## Key Decisions

- Created spec-driven documentation for both completed (hardened code editor) and upcoming (split athena) work
- Made access-logs bucket policy universal (`<acct>-<region>-*` pattern) - transparent, non-fragile
- All stacks use `Fn::ImportValue` - no parameters needed on any stack
- Split 4-athena.yaml into 4-athena-buckets.yaml + 4-athena-setup.yaml (required because setup Lambda reads CSV headers from S3)
- IAM Identity Center must be in us-east-1 (Kiro console only supports us-east-1/eu-central-1)
- Chose Managed KB (recommended) over Self-managed for Knowledge Base creation
- Education dataset confirmed aligned with KB docs (154 COMP courses in both)

## Actions Taken

### Specs Created
- `.kiro/specs/20260808-harden-code-editor/` (requirements, design, tasks - all marked complete)
- `.kiro/specs/20260809-split-athena-setup/` (requirements, design, tasks - all marked complete)

### Stacks Deployed (all in us-west-2 except noted)
- Stack 1 update: universal access-logs policy + AccessLogsBucketName export
- Stack 4a: `education-athena-buckets` (CREATE_COMPLETE)
- Stack 4b: `education-athena-setup` (CREATE_COMPLETE) - 12 Glue tables, Athena workgroup, query Lambda, DynamoDB, Cognito
- Stack 5: `identity-center-only` in **us-east-1** (CREATE_COMPLETE)

### Education Data
- Uploaded 12 CSV tables (2.6 MiB) to education-data bucket
- Verified: 987 students, 154 COMP courses matching KB docs

### Module 1: Environment Setup (complete)
- Disabled MFA, created SSO user (kiro-user-01@example.com)
- Signed up for Kiro Power, assigned user
- Authenticated Kiro CLI from VS Code Server (device flow, us-east-1)

### Module 3: Bedrock Knowledge Base (complete)
- Created Managed KB: `university-handbooks-kb` (ID: ONVQOQ7XJB)
- Auto-synced, tested query - results are excellent

### Documentation
- notes/1-environment-setup.md - full runbook with warnings
- notes/2-kiro-cli-overview.md - informational, quick commands
- notes/3-bedrock-foundations.md - two paths (Managed vs Self-managed KB)
- notes/README.md - consolidated module index
- iam/README.md - WSParticipantRole analysis
- README.md - additional notes, education dataset footnote
- cloudformation/self-hosted/README.md - full deployment guide with region callout

## Issues Encountered
- IDC must be in us-east-1 (discovered when Kiro console showed "Region Unsupported" for us-west-2)
- Kiro CLI login method is now "Use with Your Organization" (not "Use with Pro license")
- Bedrock KB console has new Managed KB option (workshop content doesn't cover it)
- Workshop Module 1 step ordering causes failures (MFA must be disabled before user creation)

## Next Steps
- Continue workshop Module 4: Building the Admission Agent
- Test more KB queries to validate Managed KB quality
- Start building Strands agent with KB ID and inference profile
