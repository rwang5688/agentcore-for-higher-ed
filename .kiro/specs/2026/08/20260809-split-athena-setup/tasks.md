# Tasks: Split Athena/Glue Setup for Self-Hosted Deployment

## Implementation Tasks

- [x] 1. Update 1-knowledge-base-buckets.yaml - make access-logs bucket universal
  - Make access-logs bucket policy universal: ArnLike `arn:aws:s3:::<acct>-<region>-*`
  - Remove enumerated bucket ARNs from Condition (no longer fragile)
  - Add export: AccessLogsBucketName (bucket name, not just URI)
  - Deploy update to dev account (stack: education-kb-buckets)
  - Verify UPDATE_COMPLETE (in-place policy update, no resource replacement)
  - Verify access logging still works: check for fresh log objects under education-kb-docs/ prefix after a few minutes

- [x] 2. Create 4-athena-buckets.yaml
  - Fn::ImportValue for AccessLogsBucketName (no parameters)
  - Two S3 buckets: education-data and education-results
  - Public access blocked on both
  - S3 access logging enabled on both (to imported access-logs bucket with appropriate prefixes)
  - 7-day lifecycle on results bucket
  - Export bucket names and ARNs as CloudFormation outputs
  - No Lambda custom resource for bucket cleanup on delete

- [x] 3. Deploy 4-athena-buckets.yaml to dev account
  - Stack name: `education-athena-buckets`
  - No parameters needed (all via ImportValue)
  - Region: us-west-2
  - Verify CREATE_COMPLETE
  - Verify exported outputs visible in CloudFormation console

- [x] 4. Upload education data to S3
  - Run: `aws s3 sync ./education-data/ s3://331773567763-us-west-2-education-data/`
  - Verify all 12 table folders present in bucket
  - Verify CSV files accessible (spot-check a few)

- [x] 5. Create 4-athena-setup.yaml - IAM roles
  - AthenaSetupRole: Glue, Athena, S3 (import bucket ARNs)
  - AthenaQueryLambdaRole: Athena, S3, Glue read
  - AdvisorRequestsLambdaRole: DynamoDB CRUD
  - CognitoClientSecretRole: cognito-idp:DescribeUserPoolClient
  - Remove Workshop Studio assets bucket references from IAM

- [x] 6. Create 4-athena-setup.yaml - AthenaSetupFunction (modified)
  - Remove zip download/extraction logic
  - Add S3 prefix listing to discover table folders
  - Read CSV headers from pre-uploaded files in data bucket
  - Keep Glue table creation logic identical to workshop
  - Keep Athena workgroup creation identical to workshop
  - Keep CloudFormation custom resource response handling
  - Keep delete handler (drop tables + database)

- [x] 7. Create 4-athena-setup.yaml - AthenaSetup custom resource
  - Pass DataBucket and ResultsBucket via Fn::ImportValue
  - Remove DataZipS3Path property (no longer needed)
  - Trigger AthenaSetupFunction

- [x] 8. Create 4-athena-setup.yaml - AthenaQueryLambda
  - Copy function code verbatim from workshop
  - Environment variables: DATABASE, WORKGROUP, RESULTS_BUCKET
  - DependsOn: AthenaSetup (ensure Glue schema exists first)

- [x] 9. Create 4-athena-setup.yaml - Advisor Requests (DynamoDB + Lambda)
  - Copy AdvisorRequestsTable verbatim from workshop
  - Copy AdvisorRequestsLambda verbatim from workshop
  - Copy AdvisorRequestsLambdaRole verbatim from workshop

- [x] 10. Create 4-athena-setup.yaml - Cognito OAuth
  - Copy EducationCognitoUserPool verbatim
  - Copy EducationCognitoUserPoolDomain verbatim
  - Copy EducationCognitoResourceServer verbatim
  - Copy EducationCognitoClient verbatim
  - Copy CognitoClientSecretRole, Function, and custom resource verbatim

- [x] 11. Create 4-athena-setup.yaml - Outputs
  - Export all outputs matching workshop template
  - AthenaQueryLambdaArn, AthenaQueryLambdaName
  - AthenaDataBucketName, AthenaDatabaseName
  - CognitoDiscoveryUrl, CognitoClientId, CognitoTokenUrl, CognitoClientSecret
  - AdvisorRequestsLambdaName, AdvisorRequestsTableName

- [x] 12. Deploy 4-athena-setup.yaml to dev account
  - Stack name: `education-athena-setup`
  - Capabilities: CAPABILITY_IAM
  - Verify CREATE_COMPLETE
  - Verify Glue database and 12 tables created
  - Verify Athena workgroup exists with correct results bucket

- [x] 13. Validate end-to-end
  - Run a test query in Athena console using education_workgroup
  - Verify AthenaQueryLambda executes successfully (invoke via console or CLI)
  - Verify Cognito token endpoint returns tokens
  - Verify AdvisorRequestsLambda responds to test event

- [x] 14. Update session notes
  - Record deployment status and any issues
  - Document stack names and outputs for reference
  - Note any deviations from design

## Verification

- COMP courses in Athena (`SELECT COUNT(*) ... WHERE course_code LIKE '%COMP%'`): **154**
- COMP course KB docs (`education-kb-docs/*COMP_courses*`): **154**
- Confirms education-data and education-kb-docs are aligned as designed.

## Dependencies

- Stack 1 (education-kb-buckets): DEPLOYED - must be updated first (universal access-logs policy + new export)
- Stack 2 (code-editor-full-hardened): DEPLOYED (not a dependency, but validates account access)
- Stack 3 (agentcore-role): DEPLOYED (not a dependency for Athena stacks)
- Education data in repo: COMMITTED (education-data/ directory, 12 folders)
