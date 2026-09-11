# Module 1: Environment Setup

> **Warning:**
> - Kiro via IAM Identity Center is currently only available in us-east-1. All other resources can be deployed in any supported region (e.g., us-west-2).
> - The workshop content presents these steps in a significantly different order that will cause failures. Do NOT follow the workshop sequence as-is. The procedure below is the tested, working order.

## Workshop Content Summary

Sets up the cloud-based development environment: VS Code Server access, AWS credentials, IAM Identity Center user creation, Kiro CLI authentication, AgentCore CLI verification, and Python virtual environment.

## Correct Procedure (Order Matters)

The workshop content presents steps in a confusing order. Below is the correct sequence learned through trial and error - applies to both Workshop Studio and self-hosted environments.

### 1. IAM Identity Center - Disable MFA First

The workshop buries this in the middle. Do it first or you'll get stuck at user sign-in.

1. Navigate to IAM Identity Center console
2. Settings > Authentication tab
3. Multi-factor authentication > Configure
4. Set "Prompt users for MFA" to **Never (disabled)**
5. Save changes

### 2. Create SSO User

1. In IAM Identity Center console, select Users > Add user
2. Enter a fictitious email: `kiro-user-01@example.com` (email verification is not required)
3. Complete the user creation flow
4. **Use "Reset password" > "Generate one-time password"** to set the password
   - Do NOT rely on the invitation email
   - The one-time password option gives you immediate access
   - Remember the password you set after using the one-time password

### 3. Verify SSO User Can Sign In

1. Open the AWS access portal URL: `https://<identity-store-id>.awsapps.com/start`
2. Sign in with the SSO user credentials
3. Confirm you land on the portal - both **Accounts** and **Applications** lists should be empty at this point
4. Keep the AWS access portal tab open

### 4. Enable Kiro Power

1. **Switch console region to us-east-1** - the Kiro/Q Developer console only supports us-east-1 and eu-central-1 for "Enable small teams". IDC must also be deployed in us-east-1 (Stack 5 is the ONLY stack deployed in us-east-1 - everything else stays in us-west-2).
2. Navigate to the [Kiro console](https://console.aws.amazon.com/kiro)
3. Select **Enable small teams**
4. Select **IAM Identity Center** as the authentication method
5. Complete the setup flow
6. Select **Kiro Power** plan
7. Assign the SSO user you just created
8. Go back to the AWS access portal tab - **Kiro** should now appear under the **Applications** list

### 5. Open VS Code Server

Access via the CloudFront URL from Stack 2 output (`VSCodeURL`).

### 6. Verify Environment in VS Code Terminal

```bash
# AWS credentials (via EC2 Instance Profile)
aws sts get-caller-identity

# Kiro CLI
kiro-cli --version

# If not found:
export PATH="$HOME/.local/bin:$PATH"
kiro-cli --version

# AgentCore CLI
agentcore --help

# Python
python3 --version  # Must be 3.10+
```

### 7. Authenticate Kiro CLI

```bash
kiro-cli login --use-device-flow
```

- Select: **Use with Your Organization**
- Start URL: `https://<identity-store-id>.awsapps.com/start`
- Region: **us-east-1** (IDC must be in us-east-1 for Kiro console compatibility, even if other resources are in us-west-2)
- Open the displayed URL in your local browser, enter the code, complete sign-in

### 8. Create Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Issues & Workarounds

| Issue | Workaround |
|-------|------------|
| Workshop says to create user via Kiro console flow first, then go back to disable MFA | Disable MFA first, create user second - otherwise sign-in fails |
| Invitation email may not arrive or link expires | Use IAM Identity Center console > Users > Reset password > "Generate one-time password" |
| Kiro console "Region Unsupported" in us-west-2 | IDC must be deployed in us-east-1 (or eu-central-1). Only one IDC instance per account. Delete and recreate if in wrong region |
| Workshop defaults to us-east-1 for Kiro CLI region prompt | Use us-east-1 (where IDC lives) even if other resources are in us-west-2 |
| `kiro-cli` not found | Run `export PATH="$HOME/.local/bin:$PATH"` |
| Ctrl+` doesn't toggle terminal on Mac in web VS Code | Use menu: Terminal > New Terminal |
