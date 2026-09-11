# Requirements: Harden Code Editor CloudFormation Template

## Overview

Harden the workshop `2-code-editor-full.yaml` template for self-hosted deployment in an Isengard development account. The workshop template deploys a VS Code Server (Code Editor) on EC2 with CloudFront, but uses a public-facing architecture with broad IAM permissions. The hardened version must apply defense-in-depth security controls while maintaining functional equivalence.

## Context

- Source: `cloudformation/workshop/2-code-editor-full.yaml` (v1.5.0)
- Target: `cloudformation/self-hosted/2-code-editor-full-hardened.yaml`
- Account: Isengard dev (331773567763, us-west-2)
- Purpose: POC development environment for AgentCore Higher Ed project

## Functional Requirements

### FR-1: Network Isolation
The EC2 instance must be deployed in a private subnet with no public IP address. Internet access for package installation and AWS API calls must be provided via NAT Gateway.

### FR-2: CloudFront VPC Origins
CloudFront must access the EC2 instance via VPC Origin (AWS::CloudFront::VpcOrigin) rather than a public HTTP origin. This eliminates the need for the instance to have a public IP or Elastic IP.

### FR-3: HTTPS Enforcement
All CloudFront viewer connections must be redirected from HTTP to HTTPS. ViewerProtocolPolicy must be set to `redirect-to-https` for both the default cache behavior and all path patterns (e.g., /proxy/*).

### FR-4: IMDSv2 Enforcement
The EC2 instance metadata service must require IMDSv2 (token-based). HttpTokens must be set to `required` to prevent SSRF-based credential theft via IMDSv1.

### FR-5: EBS Encryption
All EBS volumes attached to the EC2 instance must be encrypted at rest using the default AWS-managed key.

### FR-6: Security Group Egress Restriction
The security group must define explicit egress rules limited to:
- TCP 443 (HTTPS) - AWS APIs, package repositories
- TCP 80 (HTTP) - package mirrors
- UDP 53 (DNS) - name resolution

All other outbound traffic must be implicitly denied.

### FR-7: KMS IAM Scoping
KMS permissions in the instance role must be conditioned on `kms:ViaService: cloudformation.<region>.amazonaws.com` to prevent unauthorized key creation outside of IaC workflows.

### FR-8: Functional Equivalence
The hardened template must produce the same end-user outcome: a VS Code Server accessible via CloudFront HTTPS URL with authentication token, supporting Docker, AWS CLI, CDK, and AgentCore tooling.

## Non-Functional Requirements

### NFR-1: Deployment Time
Stack creation must complete within 20 minutes (VPC Origin propagation is the long pole).

### NFR-2: No Elastic IP
The hardened template must not allocate an Elastic IP. Cost savings and reduced attack surface.

### NFR-3: Self-Contained VPC
The template must create its own VPC, subnets, NAT Gateway, and routing - not depend on a pre-existing VPC. This ensures portability across accounts.

### NFR-4: Managed Policy Retention
All AWS-managed IAM policies from the workshop template must be retained (needed for workshop exercises: CDK, CloudFormation, SSM, etc.). Hardening is additive via conditions, not removal.

### NFR-5: CloudFront Logging
CloudFront access logging is intentionally omitted (requires ACL-enabled bucket, not justified for dev). The W10 cfn_nag suppression documents this decision.

## Out of Scope

- Custom domain / ACM certificate (no domain available for dev)
- WAF integration (overkill for single-user dev environment)
- CloudTrail / VPC Flow Logs (can be added later)
- Multi-AZ deployment (single-user, not HA)
