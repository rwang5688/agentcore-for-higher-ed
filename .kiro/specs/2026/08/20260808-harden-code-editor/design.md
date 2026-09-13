# Design: Harden Code Editor CloudFormation Template

## Architecture Decision: Option B - CloudFront VPC Origins

Two hardening approaches were evaluated:

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| A | Public subnet + strict SG + IMDSv2 | Simpler, no NAT cost | Instance still has public IP |
| B | Private subnet + VPC Origin | No public IP, true isolation | NAT Gateway cost, longer deploy |

**Decision: Option B** - CloudFront VPC Origins provide the strongest isolation. The EC2 instance is unreachable from the internet except through CloudFront. NAT Gateway cost (~$0.045/hr) is acceptable for a dev environment.

## Network Architecture

```
Internet
    |
CloudFront Distribution (HTTPS only)
    |
VPC Origin (AWS::CloudFront::VpcOrigin)
    |
[Private Subnet 10.0.2.0/24]
    EC2 Instance (no public IP, port 80)
    |
NAT Gateway (in Public Subnet 10.0.1.0/24)
    |
Internet Gateway
    |
Internet (outbound only: 443, 80, 53)
```

### VPC Design (10.0.0.0/16)

| Subnet | CIDR | Purpose |
|--------|------|---------|
| PublicSubnet | 10.0.1.0/24 | NAT Gateway, Internet Gateway route |
| PrivateSubnet | 10.0.2.0/24 | EC2 instance, routes via NAT |

Single AZ (AZ 0) - no HA requirement for dev.

## Security Controls Layering

### Layer 1: Network
- EC2 in private subnet (no public IP, no direct internet ingress)
- Security group ingress: port 80 from CloudFront prefix list only
- Security group egress: TCP 443, TCP 80, UDP 53 only
- NAT Gateway for controlled outbound

### Layer 2: Compute
- IMDSv2 required (HttpTokens: required) - blocks SSRF credential theft
- EBS encryption at rest (default AWS key)
- No SSH key pair (SSM Session Manager for console access)

### Layer 3: Application
- CloudFront enforces HTTPS (redirect-to-https)
- VPC Origin - instance unreachable except via CloudFront
- Token-based authentication (random password in URL)

### Layer 4: IAM
- KMS actions conditioned on `kms:ViaService: cloudformation.REGION.amazonaws.com`
- Managed policies retained for workshop functionality
- Instance profile scoped to required services

## CloudFront VPC Origin Integration

```yaml
CodeEditorVpcOrigin:
  Type: AWS::CloudFront::VpcOrigin
  Properties:
    VpcOriginEndpointConfig:
      Arn: !Sub arn:aws:ec2:${AWS::Region}:${AWS::AccountId}:instance/${CodeEditorInstance}
      HTTPPort: 80
      HTTPSPort: 443
      Name: CodeEditor-VpcOrigin
      OriginProtocolPolicy: http-only
```

The distribution references VpcOriginConfig instead of CustomOriginConfig:

```yaml
Origins:
  - DomainName: !GetAtt CodeEditorInstance.PrivateDnsName
    Id: !Sub CloudFront-${AWS::StackName}
    VpcOriginConfig:
      VpcOriginId: !GetAtt CodeEditorVpcOrigin.Id
```

## Changes from Workshop Template

### Added Resources
| Resource | Type | Purpose |
|----------|------|---------|
| VPC | AWS::EC2::VPC | Isolated network |
| InternetGateway | AWS::EC2::InternetGateway | Public subnet egress |
| VPCGatewayAttachment | AWS::EC2::VPCGatewayAttachment | IGW attachment |
| PublicSubnet | AWS::EC2::Subnet | NAT Gateway placement |
| PrivateSubnet | AWS::EC2::Subnet | EC2 placement |
| NatEIP | AWS::EC2::EIP | Static IP for NAT |
| NatGateway | AWS::EC2::NatGateway | Private subnet egress |
| PublicRouteTable | AWS::EC2::RouteTable | Public routing |
| PublicRoute | AWS::EC2::Route | 0.0.0.0/0 to IGW |
| PublicSubnetRouteAssoc | AWS::EC2::SubnetRouteTableAssociation | Binds table |
| PrivateRouteTable | AWS::EC2::RouteTable | Private routing |
| PrivateRoute | AWS::EC2::Route | 0.0.0.0/0 to NAT |
| PrivateSubnetRouteAssoc | AWS::EC2::SubnetRouteTableAssociation | Binds table |
| CodeEditorVpcOrigin | AWS::CloudFront::VpcOrigin | Private origin access |

### Removed Resources
| Resource | Type | Reason |
|----------|------|--------|
| CodeEditorInstanceEIP | AWS::EC2::EIP | No public IP needed |
| ElasticIPAssociation | AWS::EC2::EIPAssociation | No public IP needed |

### Modified Resources
| Resource | Change |
|----------|--------|
| CodeEditorInstance | SubnetId set to PrivateSubnet; MetadataOptions added (IMDSv2); BlockDeviceMappings encrypted |
| SecurityGroup | VpcId explicit; egress rules added (443, 80, 53 only) |
| CloudFrontDistribution | VpcOriginConfig replaces CustomOriginConfig; ViewerProtocolPolicy: redirect-to-https; DependsOn VpcOrigin |
| CDKBootstrapAndDeploy policy | KMS actions conditioned on kms:ViaService |

## Deployment Notes

- Stack creation time: ~14 minutes (VPC Origin propagation is the bottleneck)
- Stack name: `code-editor-full-hardened`
- Region: us-west-2
- Outputs unchanged: VSCodeURL with CloudFront domain + token
