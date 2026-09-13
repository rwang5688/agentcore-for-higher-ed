# Design: Split Athena/Glue Setup for Self-Hosted Deployment

## Split Strategy

The workshop `4-athena.yaml` is one monolithic stack. For self-hosted, we split into two stacks with a manual data-upload step in between:

```
[4-athena-buckets.yaml]  -->  aws s3 sync  -->  [4-athena-setup.yaml]
   (S3 buckets)            (manual upload)      (Glue, Athena, Lambda,
                                                 DynamoDB, Cognito)
```

### Rationale for Split

The `AthenaSetupFunction` Lambda reads CSV headers from S3 (`s3.get_object` on each file's first line) to discover column names for Glue table definitions. This means the education data must exist in the bucket before the custom resource executes. Since the workshop zip-download-and-upload step is removed, we need a manual upload step between bucket creation and schema setup. Hence the split.

### Data Foundation for Agents

Despite its name, `4-athena.yaml` actually contains the entire data foundation for the workshop's agents. It deploys:
- S3 buckets (data + results)
- Glue database and table definitions (via custom resource Lambda)
- Athena workgroup
- Athena query execution Lambda (MCP tool target)
- DynamoDB table + Lambda for advisor requests (another MCP tool target)
- Cognito user pool, resource server, and OAuth client (gateway auth)

We preserve this grouping in `4-athena-setup.yaml` to minimize diff from the workshop.

## Template 1: 4-athena-buckets.yaml

### Parameters

None. Uses `Fn::ImportValue` for the access-logs bucket name (exported by Stack 1).

### Resources

| Resource | Type | Properties |
|----------|------|------------|
| AthenaDataBucket | AWS::S3::Bucket | Name: `<acct>-<region>-education-data`, PublicAccessBlock: all true, LoggingConfiguration: AccessLogsBucket with prefix `education-data/` |
| AthenaResultsBucket | AWS::S3::Bucket | Name: `<acct>-<region>-education-results`, PublicAccessBlock: all true, Lifecycle: 7-day expiration, LoggingConfiguration: AccessLogsBucket with prefix `education-results/` |

Note: No Lambda custom resource for bucket object cleanup. Buckets must be emptied manually before stack deletion.

### Outputs (Exported)

| Output | Export Name | Value |
|--------|------------|-------|
| AthenaDataBucketName | AthenaDataBucketName | !Ref AthenaDataBucket |
| AthenaDataBucketArn | AthenaDataBucketArn | !GetAtt AthenaDataBucket.Arn |
| AthenaResultsBucketName | AthenaResultsBucketName | !Ref AthenaResultsBucket |
| AthenaResultsBucketArn | AthenaResultsBucketArn | !GetAtt AthenaResultsBucket.Arn |

## Template 2: 4-athena-setup.yaml

### Parameters

None. Uses `Fn::ImportValue` to reference bucket stack outputs.

### Parameters

None. Uses `Fn::ImportValue` to reference bucket stack outputs.

### Resources

| Resource | Type | Purpose |
|----------|------|---------|
| AthenaSetupRole | AWS::IAM::Role | Lambda execution role for Glue/Athena/S3 |
| AthenaSetupFunction | AWS::Lambda::Function | Custom resource: creates Glue DB, tables, Athena workgroup |
| AthenaSetup | AWS::CloudFormation::CustomResource | Triggers AthenaSetupFunction |
| AthenaQueryLambdaRole | AWS::IAM::Role | Lambda execution role for query function |
| AthenaQueryLambda | AWS::Lambda::Function | Executes Athena SQL queries |
| AdvisorRequestsTable | AWS::DynamoDB::Table | Advisor meeting requests |
| AdvisorRequestsLambdaRole | AWS::IAM::Role | Lambda execution role for advisor function |
| AdvisorRequestsLambda | AWS::Lambda::Function | CRUD for advisor requests |
| EducationCognitoUserPool | AWS::Cognito::UserPool | OAuth provider |
| EducationCognitoUserPoolDomain | AWS::Cognito::UserPoolDomain | Token endpoint domain |
| EducationCognitoResourceServer | AWS::Cognito::UserPoolResourceServer | Scopes definition |
| EducationCognitoClient | AWS::Cognito::UserPoolClient | Client credentials client |
| CognitoClientSecretRole | AWS::IAM::Role | Lambda role for secret retrieval |
| CognitoClientSecretFunction | AWS::Lambda::Function | Retrieves client secret |
| CognitoClientSecret | Custom::ClientSecret | Triggers secret retrieval |

### AthenaSetupFunction - Key Modification

The workshop version downloads a zip, extracts CSVs, uploads them to S3, then reads headers to create Glue tables. The self-hosted version skips zip download/extraction and reads CSV headers directly from the pre-uploaded bucket:

**Workshop flow:**
```
1. Download zip from assets bucket
2. Extract CSVs from zip
3. Upload CSVs to data bucket
4. Read first line of each CSV for headers
5. Create Glue table from headers
6. Create Athena workgroup
```

**Self-hosted flow:**
```
1. List prefixes in data bucket (each prefix = one table)
2. Read first line of CSV in each prefix for headers
3. Create Glue table from headers
4. Create Athena workgroup
```

#### Modified Lambda Logic (pseudocode)

```python
# Instead of zip extraction, list bucket prefixes
s3 = boto3.client('s3')
paginator = s3.get_paginator('list_objects_v2')

# Discover table folders by listing top-level prefixes
prefixes = set()
for page in paginator.paginate(Bucket=data_bucket, Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        prefixes.add(prefix['Prefix'].rstrip('/'))

# For each prefix (table), find a CSV and read headers
for table_name in sorted(prefixes):
    objects = s3.list_objects_v2(Bucket=data_bucket, Prefix=f'{table_name}/', MaxKeys=1)
    csv_key = objects['Contents'][0]['Key']
    response = s3.get_object(Bucket=data_bucket, Key=csv_key, Range='bytes=0-4096')
    first_line = response['Body'].read().decode('utf-8').split('\n')[0]
    headers = csv.reader(io.StringIO(first_line))
    # ... create Glue table (same as workshop)
```

### AthenaSetupRole - Modified IAM

The setup role no longer needs access to the Workshop Studio assets bucket. Policy simplified:

```yaml
- Effect: Allow
  Action: [s3:GetObject, s3:ListBucket]
  Resource:
    - !ImportValue AthenaDataBucketArn
    - !Sub "${AthenaDataBucketArn}/*"  # via Fn::ImportValue + Fn::Sub
```

### Cross-Stack References

```yaml
# In 4-athena-setup.yaml, import bucket values:
DataBucket: !ImportValue AthenaDataBucketName
DataBucketArn: !ImportValue AthenaDataBucketArn
ResultsBucket: !ImportValue AthenaResultsBucketName
ResultsBucketArn: !ImportValue AthenaResultsBucketArn
```

### Outputs (Exported)

Same as workshop `4-athena.yaml`:
- AthenaQueryLambdaArn / AthenaQueryLambdaName
- AthenaDataBucketName (re-export from import)
- AthenaDatabaseName
- CognitoDiscoveryUrl / CognitoClientId / CognitoTokenUrl / CognitoClientSecret
- AdvisorRequestsLambdaName / AdvisorRequestsTableName

## Deployment Sequence

```
Step 0:  aws cloudformation deploy ... --template-file 1-knowledge-base-buckets.yaml \
           --stack-name education-kb-buckets
         (updates access-logs policy + adds AccessLogsBucketName export)

Step 1:  aws cloudformation deploy ... --template-file 4-athena-buckets.yaml \
           --stack-name education-athena-buckets

Step 2:  aws s3 sync ./education-data/ \
           s3://331773567763-us-west-2-education-data/

Step 3:  aws cloudformation deploy ... --template-file 4-athena-setup.yaml \
           --stack-name education-athena-setup \
           --capabilities CAPABILITY_IAM
```

## Design Decisions

1. **Keep AthenaSetupFunction name** - Even though it primarily sets up Glue, the workshop calls it "Athena Setup" and it also creates the Athena workgroup. Keeping the name minimizes diff from workshop code.

2. **Keep all downstream resources in setup template** - DynamoDB, Cognito, and advisor Lambda are logically separate but they're small and the workshop deploys them together. Splitting further adds complexity without benefit.

3. **No Parameters in setup template** - Uses Fn::ImportValue for everything. Zero deployment-time decisions beyond stack name.

4. **Fn::ImportValue over Parameters** - Ensures bucket stack must exist before setup stack. Provides built-in dependency validation.
