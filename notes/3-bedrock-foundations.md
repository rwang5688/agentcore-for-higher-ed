# Module 3: Amazon Bedrock Foundations

> **Reminder (self-hosted):** Switch console back to **us-west-2** before starting this module. The KB docs bucket is in us-west-2.

## Step 1: Your First Conversation with a Foundation Model

1. In AWS Console, navigate to Amazon Bedrock (make sure you're in **us-west-2**)
2. From left nav, select **Playground**
3. Click **Select model**
4. Provider: **Anthropic**
5. Select **Claude Sonnet 4.6** with the **US cross-region** inference profile
6. Click **Apply**
7. Record the inference profile ID: `us.anthropic.claude-sonnet-4-6`

### Playground Prompts (copy-paste)

General prompt (model answers from training data):

```
What are the typical prerequisites for a third-year computer science elective?
```

Institutional prompt (model fails or hallucinates):

```
What electives are available in Semester 2 for a Bachelor of Engineering student who has completed 120 credit points?
```

## Step 2: Create a Knowledge Base

> **Note:** The Bedrock console UI for Knowledge Base creation now has new options from what the workshop describes.

### Choose your path

| | Managed KB (recommended) | Self-managed (workshop path) |
|-|--------------------------|------------------------------|
| Embedding model | Managed (no choice needed, no cost) | You choose (Titan Text Embeddings V2) |
| Vector store | Fully managed (no config) | You choose (S3 Vectors, OpenSearch, etc.) |
| Chunking | Default (managed parser) | You choose (Hierarchical) |
| Sync | Auto-syncs on creation | Must click Sync manually |

### Path A: Managed KB (recommended)

1. In Bedrock console (us-west-2), left nav > **Knowledge Bases** > **Create**
2. Select **Managed KB** (recommended)
3. Fill in:
   - KB name: `university-handbooks-kb`
   - Embeddings model: **Managed embeddings model** (recommended, no additional cost)
   - IAM Permissions: **Create and use a new service role**
4. Data source:
   - Data source name: `university-handbooks-kb-data-source`
   - Data source type: **Amazon S3**
   - S3 URI: `s3://331773567763-us-west-2-education-kb-docs`
   - Parsing strategy: **Managed parser**
   - Text chunking strategy: **Default chunking**
5. Leave all other options as defaults (ACL disabled, CloudWatch logs auto-configured)
6. Click **Create Knowledge Base**
7. KB auto-syncs on creation. Wait for sync status: **Complete**

### Path B: Self-managed (follow workshop instructions exactly)

1. In Bedrock console (us-west-2), left nav > **Knowledge Bases** > **Create**
2. Select **Self-managed > Unstructured Vector Store KB**
3. Name: `university-handbooks-kb`, IAM role: "Create and use a new service role"
4. Data source: Amazon S3, S3 URI: `s3://331773567763-us-west-2-education-kb-docs`, hierarchical chunking
5. Embedding: Titan Text Embeddings V2, Vector store: Amazon S3 Vectors
6. Create, then click **Sync**

## Step 3: Query the Knowledge Base

Test in KB console with "Retrieval and response generation" mode.

Sample queries:

```
What are the prerequisites for Database Systems?
```

```
What are the prerequisites for Data Science: Machine Learning?
```

```
Can I take Data Science: Machine Learning without completing Statistics 201?
```

## Step 4: Record Knowledge Base ID

Add to `.env`:
```
KNOWLEDGE_BASE_ID=<from KB detail page>
INFERENCE_PROFILE_ID=us.anthropic.claude-sonnet-4-6
```

## Issues

| Issue | Details |
|-------|---------|
| KB console UI changed | Workshop screenshots and steps no longer match current Bedrock console |
| S3 Vectors not visible | New wizard likely uses S3 Vectors by default but doesn't show it in S3 Vectors console |
