# Session Notes - August 8-9, 2026 (Late Night)

## Environment
- Machine: Amazon WorkSpaces (Windows)
- Started: ~10 PM Aug 8
- Ended: ~2:30 AM Aug 9

## Key Decisions

1. **Repo structure established:**
   - `cloudformation/workshop/` - Original templates as-is from Workshop Studio
   - `cloudformation/self-hosted/` - Hardened/adapted templates for Isengard dev account
   - `education-kb-docs/` - Knowledge Base source documents (294 files, Peculiar U course catalog)
   - `education-data/` - Athena data CSVs (12 tables)
   - `notes/` - Workshop issues and observations

2. **Naming conventions:**
   - Self-hosted templates keep workshop prefix, add descriptive suffix (e.g., `1-knowledge-base-buckets.yaml`, `2-code-editor-full-hardened.yaml`)
   - S3 buckets follow `<account-id>-<region>-<purpose>` pattern
   - Access logs bucket: `<account-id>-<region>-access-logs` (for all S3 buckets in account)

3. **Stack 2 hardening (Option B - CloudFront VPC Origins):**
   - EC2 in private subnet (no public IP, no EIP)
   - CloudFront VPC Origin (`AWS::CloudFront::VpcOrigin`) replaces public EC2 origin
   - IMDSv2 enforced (`HttpTokens: required`)
   - `ViewerProtocolPolicy: redirect-to-https`
   - Security group egress restricted to 443, 80, 53 UDP
   - IAM: kept all managed policies (needed for workshop), scoped KMS via condition
   - Removed CloudFront access logging (requires ACL-enabled bucket, not worth it for dev)

4. **Stack 5 (Identity Center) not needed for self-hosted** - workshop-only (depends on WSParticipantRole)

5. **Workshop vs self-hosted approach:** Deploy in parallel. Workshop Studio for reference, Isengard for actual POC. Use local Kiro IDE for development, Code Editor on EC2 for Docker builds (`agentcore build`/`agentcore deploy`).

## Detour: Agent Toolkit for AWS Setup

- Updated AWS CLI from v2.32.26 to v2.36.19
- Ran `aws configure agent-toolkit --yes --region us-east-1`
- Installed 18 AWS skills to `~/.kiro/skills`
- MCP server configured at `~/.kiro/settings/mcp.json`
- AWS steering rules saved to `~/.kiro/steering/aws-agent-rules.md`
- All at user level (applies across all workspaces)
- **TODO: Repeat this setup on work laptop**

## Actions Taken

1. Cleared default README, established repo structure
2. Synced KB docs from Workshop Studio S3 bucket (293 markdown files)
3. Synced education data CSVs (12 tables) from Workshop Studio
4. Created `cloudformation/self-hosted/1-knowledge-base-buckets.yaml` (3 buckets + access logging)
5. Captured all 5 workshop templates to `cloudformation/workshop/`
6. Created `cloudformation/self-hosted/2-code-editor-full-hardened.yaml` (VPC Origins hardening)
7. Copied `3-agentcore-role.yaml` as-is to self-hosted (no changes needed)
8. Documented workshop issues in `notes/workshop-issues.md`

## Deployments to Isengard Dev Account (331773567763, us-west-2)

| Stack | Template | Status |
|-------|----------|--------|
| education-kb-buckets | 1-knowledge-base-buckets.yaml | CREATE_COMPLETE |
| code-editor-full-hardened | 2-code-editor-full-hardened.yaml | CREATE_COMPLETE (14 min) |

## Issues Encountered

- `VPCOriginConfig` vs `VpcOriginConfig` casing issue - CloudFormation is case-sensitive
- CloudFront access logging requires ACL-enabled bucket - removed feature entirely
- m8g.large greyed out in EC2 console until ARM architecture selected for AMI

## Workshop Issues Documented

- IAM Identity Center MFA/SSO user order of operations
- Bedrock Knowledge Base console UI has changed significantly
- Stack 1 depends on Workshop Studio S3 assets bucket (knowledge.zip)
- Stack 2 AppSec concerns (public subnet, broad IAM, no IMDSv2, HTTP origin)
- Stack 4 depends on Workshop Studio S3 assets bucket (education-data.zip)
