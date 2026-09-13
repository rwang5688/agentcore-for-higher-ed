# Tasks: Harden Code Editor CloudFormation Template

## Implementation Tasks

- [x] 1. Create self-hosted template file
  - Created `cloudformation/self-hosted/2-code-editor-full-hardened.yaml`
  - Copied workshop template as starting point
  - Updated Description to document hardening provenance

- [x] 2. Add VPC infrastructure
  - Added VPC (10.0.0.0/16) with DNS support and hostnames enabled
  - Added InternetGateway + VPCGatewayAttachment
  - Added PublicSubnet (10.0.1.0/24, AZ 0)
  - Added PrivateSubnet (10.0.2.0/24, AZ 0)
  - Added NatEIP + NatGateway in PublicSubnet
  - Added PublicRouteTable with 0.0.0.0/0 -> IGW route
  - Added PrivateRouteTable with 0.0.0.0/0 -> NAT route
  - Added subnet-to-route-table associations

- [x] 3. Move EC2 to private subnet
  - Set SubnetId to PrivateSubnet reference
  - Removed Elastic IP and EIP Association resources
  - Changed CloudFront origin to use PrivateDnsName instead of PublicDnsName

- [x] 4. Enforce IMDSv2
  - Added MetadataOptions with HttpTokens: required
  - Prevents SSRF-based credential theft via instance metadata

- [x] 5. Enable EBS encryption
  - Added BlockDeviceMappings with Encrypted: true on all volumes
  - Uses default AWS-managed encryption key

- [x] 6. Add CloudFront VPC Origin
  - Added AWS::CloudFront::VpcOrigin resource (CodeEditorVpcOrigin)
  - Configured VpcOriginEndpointConfig pointing to EC2 instance ARN
  - Updated distribution origin to use VpcOriginConfig instead of CustomOriginConfig
  - Added DependsOn: CodeEditorVpcOrigin to distribution

- [x] 7. Enforce HTTPS on CloudFront
  - Changed ViewerProtocolPolicy from allow-all to redirect-to-https
  - Applied to both DefaultCacheBehavior and /proxy/* CacheBehavior

- [x] 8. Restrict security group egress
  - Added explicit SecurityGroupEgress rules:
    - TCP 443 (HTTPS - AWS APIs, package repos)
    - TCP 80 (HTTP - package mirrors)
    - UDP 53 (DNS - name resolution)
  - Added VpcId reference to scope SG to new VPC
  - Removed cfn_nag F1000 suppression (no longer needed)

- [x] 9. Scope KMS IAM permissions
  - Added Condition to KMS actions in CDKBootstrapAndDeploy policy:
    - `kms:ViaService: cloudformation.REGION.amazonaws.com`
  - Prevents unauthorized key creation outside IaC workflows

- [x] 10. Remove CloudFront access logging suppression
  - Removed W10 suppression (access logging can be enabled later)
  - Kept W70 suppression (no custom domain for dev)

- [x] 11. Deploy and validate
  - Deployed stack `code-editor-full-hardened` to 331773567763 / us-west-2
  - CREATE_COMPLETE in ~14 minutes
  - Validated VS Code Server accessible via CloudFront HTTPS URL
  - Validated SSM bootstrap steps completed (Docker, AWS CLI, CDK, AgentCore)

- [x] 12. Document in session notes
  - Recorded all decisions, issues, and deployment status
  - Documented VPCOriginConfig casing issue (CloudFormation case-sensitive)
  - Noted CloudFront access logging ACL requirement (removed feature)

## Issues Resolved During Implementation

1. **VPCOriginConfig vs VpcOriginConfig** - CloudFormation property names are case-sensitive. The correct property is `VpcOriginConfig` (capital V, lowercase pc).
2. **CloudFront access logging** - Requires an ACL-enabled S3 bucket. Decided to remove feature entirely for dev (not worth the complexity).
3. **m8g.large instance type** - EC2 console greys out Graviton instances until ARM architecture is explicitly selected for AMI. Template works correctly via CloudFormation.
