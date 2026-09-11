# IAM Policies - Workshop vs Self-Hosted

## Workshop: WSParticipantRole

The Workshop Studio test account provisions a `WSParticipantRole` with the following attached policies:

### AWS Managed Policies

| Policy | Purpose |
|--------|---------|
| IAMFullAccess | Full IAM management (create roles, policies, etc.) |
| PowerUserAccess | Full access to all AWS services except IAM user/group management |

### Customer Managed Policies

#### bedrock_policy

Marketplace subscriptions (for Bedrock model access), OpenSearch/ECR/CodeBuild (for vector stores and Knowledge Bases), and S3 Vectors.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["aws-marketplace:Subscribe"],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": ["aws-marketplace:Unsubscribe", "aws-marketplace:ViewSubscriptions"],
      "Resource": ["*"]
    },
    {
      "Sid": "OpenSearchECRFull",
      "Effect": "Allow",
      "Action": ["ecr:*", "aoss:*", "codebuild:*", "es:*"],
      "Resource": ["*"]
    },
    {
      "Sid": "S3VectorsFull",
      "Effect": "Allow",
      "Action": ["s3vectors:*"],
      "Resource": ["*"]
    }
  ]
}
```

#### WorkshopIdentityCenterAccess

Created and attached by `5-identity-center.yaml`. Grants full SSO management and Q Developer access.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "FullSSOAccess",
      "Effect": "Allow",
      "Action": ["sso:*", "sso-directory:*", "identitystore:*", "sso-oauth:*"],
      "Resource": "*"
    },
    {
      "Sid": "QDeveloperSetup",
      "Effect": "Allow",
      "Action": ["q:*", "codewhisperer:*"],
      "Resource": "*"
    }
  ]
}
```

#### ws-default-policy

Created and attached by Workshop Studio during account provisioning. Provides IAM read-only, service-linked role creation, PassRole to itself, and a region-deny guardrail (restricts most actions to `us-east-1` only).

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowIamReadOnly",
      "Effect": "Allow",
      "Action": ["iam:List*", "iam:Get*", "iam:Generate*", "sts:GetCallerIdentity"],
      "Resource": ["*"]
    },
    {
      "Sid": "AllowCreateSLR",
      "Effect": "Allow",
      "Action": ["iam:CreateServiceLinkedRole"],
      "Resource": ["arn:aws:iam::*:role/aws-service-role/*"]
    },
    {
      "Sid": "AllowIamPassRole",
      "Effect": "Allow",
      "Action": ["iam:PassRole"],
      "Resource": ["arn:aws:iam::268097579020:role/WSParticipantRole"]
    },
    {
      "Sid": "DenyAllOutsideAllowedRegions",
      "Effect": "Deny",
      "NotAction": [
        "iam:*", "sts:*", "s3:*", "ds:*",
        "artifact:Get", "artifact:DownloadAgreement",
        "lightsail:*", "networkmanager:*", "braket:*",
        "quicksight:*", "cloudfront:*",
        "route53:*", "route53-recovery-cluster:*",
        "route53-recovery-control-config:*", "route53-recovery-readiness:*",
        "servicediscovery:*", "waf:*", "waf-regional:*", "wafv2:*",
        "cloudwatch:DescribeAlarms", "cloudwatch:PutMetricAlarm",
        "cloudwatch:DeleteAlarms", "cloudwatch:GetMetricStatistics",
        "elasticloadbalancing:DescribeLoadBalancers",
        "ec2:Describe*",
        "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability", "ecr:GetAuthorizationToken",
        "globalaccelerator:*",
        "acm:List*", "acm:Describe*",
        "cloudformation:List*", "cloudformation:Describe*",
        "kms:Describe*", "kms:ReEncrypt*", "kms:GenerateDataKey*",
        "kms:Get*", "kms:List*", "kms:CreateGrant", "kms:RevokeGrant",
        "ssm:List*", "directconnect:*",
        "sso:List*", "sso:Describe*", "sso:Get*",
        "bedrock:Invoke*"
      ],
      "Resource": ["*"],
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": ["us-east-1"]
        }
      }
    }
  ]
}
```

### Analysis

The effective permissions of `WSParticipantRole` are:
- **PowerUserAccess** + **IAMFullAccess** = essentially AdministratorAccess
- **bedrock_policy** adds Marketplace + OpenSearch Serverless + S3 Vectors (already included in PowerUserAccess, but explicit for clarity)
- **WorkshopIdentityCenterAccess** adds SSO + Q Developer (already in PowerUserAccess)
- **ws-default-policy** is primarily a region guardrail (deny outside us-east-1) with some IAM read/PassRole additions that are redundant given IAMFullAccess

The only meaningful constraint is the **region deny** (us-east-1 only). In a self-hosted account with AdministratorAccess, there is no region restriction.

---

## Self-Hosted: AdministratorAccess

For self-hosted deployment in an Isengard dev (or customer sandbox) account, `AdministratorAccess` via the Admin role is sufficient.

### Why WSParticipantRole is not needed

The workshop's `WSParticipantRole` is a broad role designed to let participants complete all workshop exercises without hitting permission errors. In a sandbox account with `AdministratorAccess`, you already have equal or greater permissions.

The only functional difference is that the Code Editor's EC2 Instance Profile role (from Stack 2) gates what `aws` and `agentcore` CLI commands can do from within the VS Code Server. That instance profile is the same in both cases.

### Recommendation

Proceed with AdministratorAccess in the Isengard dev account. Use the VS Code Server (with its EC2 Instance Profile) as the execution environment for workshop CLI commands. There is no meaningful benefit to using the workshop test account beyond this point.
