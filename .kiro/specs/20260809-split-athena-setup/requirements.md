# Requirements: Split Athena/Glue Setup for Self-Hosted Deployment

## Overview

The workshop `4-athena.yaml` template bundles bucket creation, data extraction (from a Workshop Studio zip), Glue schema setup, Athena workgroup creation, a query Lambda, an advisor requests DynamoDB table + Lambda, and Cognito OAuth into a single stack. For the self-hosted deployment, this must be split into smaller, independently deployable templates that:

1. Remove the Workshop Studio zip dependency (data already in repo)
2. Allow incremental deployment and debugging
3. Minimize differences from workshop code (keep Lambda logic identical where possible)

## Context

- Source: `cloudformation/workshop/4-athena.yaml`
- Targets:
  - `cloudformation/self-hosted/4-athena-buckets.yaml` - S3 buckets for education data and query results
  - `cloudformation/self-hosted/4-athena-setup.yaml` - Glue database/tables, Athena workgroup, query Lambda, advisor requests, Cognito
- Account: Isengard dev (331773567763, us-west-2)
- Education data: already committed to `education-data/` directory (12 CSV folders)

## Functional Requirements

### FR-1: Education Data Bucket (4-athena-buckets.yaml)
Create an S3 bucket (`<account-id>-<region>-education-data`) with public access blocked and S3 access logging enabled. This bucket will hold the 12 education CSV datasets uploaded manually via `aws s3 sync`.

### FR-2: Education Results Bucket (4-athena-buckets.yaml)
Create an S3 bucket (`<account-id>-<region>-education-results`) with public access blocked, a 7-day lifecycle expiration rule, and S3 access logging enabled. This bucket stores Athena query results.

### FR-2a: Access Logging Parameter (4-athena-buckets.yaml)
The template must accept an input parameter for the S3 access logging destination bucket (the access-logs bucket created by Stack 1). Both education-data and education-results buckets log to this destination.

### FR-3: Glue Database and Tables (4-athena-setup.yaml)
A Lambda custom resource must create:
- Glue database: `education_workshop_db`
- Glue tables: one per CSV folder in education-data (12 tables total)
- Each table defined as EXTERNAL_TABLE with columns inferred from CSV headers
- S3 location pointing to the education-data bucket prefix for each table

### FR-4: Athena Workgroup (4-athena-setup.yaml)
The same Lambda custom resource must create an Athena workgroup (`education_workgroup`) with:
- Results location set to the education-results bucket
- EnforceWorkGroupConfiguration: true

### FR-5: Athena Query Lambda (4-athena-setup.yaml)
Deploy the `education-athena-query` Lambda function (identical to workshop code) that:
- Accepts SQL via event payload
- Executes against the education_workshop_db database using education_workgroup
- Polls for completion (up to 30 seconds)
- Returns results as JSON (max 50 rows)

### FR-6: Advisor Requests Table and Lambda (4-athena-setup.yaml)
Deploy the DynamoDB table (`education-advisor-requests`) and Lambda (`education-advisor-requests`) for managing advisor meeting requests. Identical to workshop code.

### FR-7: Cognito User Pool and OAuth (4-athena-setup.yaml)
Deploy the Cognito user pool, resource server, and client for gateway authentication (client_credentials flow). Identical to workshop code.

### FR-8: Remove Workshop Studio Zip Dependency
The self-hosted setup Lambda must NOT attempt to download or extract a zip from an assets bucket. Instead, it must read CSV headers directly from the education-data bucket (data pre-uploaded via `aws s3 sync`).

### FR-9: Cross-Stack References
The bucket template must export bucket names/ARNs so the setup template can import them. This enables independent deployment order: buckets first, data upload, then setup.

### FR-10: Code Parity with Workshop
Lambda function code for AthenaQueryLambda, AdvisorRequestsLambda, and CognitoClientSecretFunction must remain identical to workshop `4-athena.yaml`. Only AthenaSetupFunction changes (zip extraction removed, reads headers from pre-uploaded CSVs).

## Non-Functional Requirements

### NFR-1: Manual Data Upload Step
Between deploying 4-athena-bucket.yaml and 4-athena-setup.yaml, the operator must run:
```
aws s3 sync ./education-data/ s3://<account-id>-<region>-education-data/
```
This is a documented manual step, not automated by CloudFormation.

### NFR-2: Idempotent Setup Lambda
The AthenaSetupFunction must handle re-runs gracefully (AlreadyExistsException for database, tables, and workgroup).

### NFR-3: Clean Delete
On stack deletion, the setup Lambda must delete Glue tables and database (same as workshop). S3 buckets require manual emptying before bucket stack deletion - no Lambda custom resource for object cleanup.

### NFR-4: Stack Outputs
Both templates must export outputs compatible with downstream stacks (e.g., AthenaQueryLambdaArn, CognitoDiscoveryUrl, etc.).

## Out of Scope

- S3 access logging for data/results buckets (can use the access-logs bucket from Stack 1 later)
- Encryption (SSE-S3 is the default, sufficient for dev)
- VPC placement for Lambdas (not needed - they call AWS APIs only)
- Hardening Cognito beyond workshop config (workshop exercises depend on current setup)
