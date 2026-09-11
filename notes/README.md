# Workshop Notes

Observations, issues, and feedback from working through the **Building Agents for Higher Education** workshop. Intended to share with customers and workshop authors.

## Module Issues Summary

### Module 1: Environment Setup

See [1-environment-setup.md](1-environment-setup.md#issues--workarounds) for full details.

| Issue | Summary |
|-------|---------|
| MFA / SSO user ordering | Disable MFA first, create user second - workshop presents this in wrong order |
| Invitation email unreliable | Use "Reset password > Generate one-time password" - email verification not required, use fictitious email like `kiro-user-01@example.com` |
| Kiro CLI region prompt | Must match where IDC instance is deployed, not workshop default |
| IDC must be in us-east-1 | Kiro console only supports us-east-1 / eu-central-1. Only one IDC instance per account |

### Module 3: Amazon Bedrock Foundations

See [3-bedrock-foundations.md](3-bedrock-foundations.md#step-2-create-a-knowledge-base) for full details.

| Issue | Summary |
|-------|---------|
| KB console UI has new options | New Managed KB (recommended) option available - simpler, no vector store config needed |
| Kiro CLI login method renamed | Now "Use with Your Organization" (not "Use with Pro license") |

### Pre-Module: CloudFormation Stack Issues

These are deployment-time observations, not tied to a specific workshop module.

| Issue | Summary |
|-------|---------|
| Amazon Bedrock KB console UI changed | The workshop's KB creation steps no longer match the current console experience |
| Stack 2 security posture | Workshop Code Editor template has multiple AppSec findings (see below) |

## Detailed Observations (Not Yet Tied to Modules)

### Amazon Bedrock - Knowledge Base Console UI Has Changed

The Amazon Bedrock console UI for creating a Knowledge Base has been significantly updated. The workshop content describing the Knowledge Base creation steps is now out of date and does not match the current console experience. Participants will need to figure out the new UI flow on their own.

### Stack 2 (Code Editor) - AppSec Concerns

The Code Editor stack (`2-code-editor-full.yaml`) has multiple security findings that internal AppSec scans will flag:

- EC2 in public subnet with public IP + Elastic IP
- Uses default VPC (no network segmentation)
- CloudFront to origin over plain HTTP
- CloudFront allows HTTP from viewers
- No CloudFront access logging
- Broad IAM role (ReadOnlyAccess + BedrockAgentCoreFullAccess + CDK bootstrap + `kms:CreateKey Resource: '*'`)
- All outbound traffic allowed from security group
- No IMDSv2 enforcement
- Password passed as plaintext SSM parameter

These are addressed in the self-hosted hardened template (`2-code-editor-full-hardened.yaml`). See [spec](../.kiro/specs/20260808-harden-code-editor/) for details.
