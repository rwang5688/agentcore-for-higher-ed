# Multi-Agent Systems Scope (as described by workshop labs)

This document captures the workshop lab content that defines the scope for this
spec. It covers Modules 7-9: deploying a single agent to AgentCore Runtime,
adding memory, and evolving into a multi-agent orchestrator.

---

## Module 7: Deploying to Production

Deploy the agent to AgentCore Runtime with IAM, CloudWatch monitoring, and
auto-scaling using the AgentCore CLI.

In this module you'll:

- Create an AgentCore project and add your agent code
- Test the agent locally with the dev server
- Deploy to AgentCore Runtime
- Verify the deployment through the AWS Console
- Test the production endpoint with sample student queries
- Connect the Streamlit app to the deployed agent
- Explore observability with logs and traces

### What is Amazon Bedrock AgentCore?

Amazon Bedrock AgentCore is a fully managed service for deploying and operating
AI agents at scale:

- **Managed Runtime:** Runs your agent with auto-scaling and session isolation
- **IAM Integration:** Fine-grained access control for Bedrock models, Knowledge
  Bases, and other AWS services
- **CloudWatch Monitoring:** Built-in logging, metrics, and distributed tracing
  for production observability
- **Cost Optimisation:** Serverless scaling, pay only for active invocations
- **Enterprise Security:** VPC support, encryption at rest and in transit

### Exercise 1: Create the AgentCore Project

The AgentCore CLI scaffolds a project structure, manages configuration, and
handles deployment. You'll create a project and add your existing agent code to
it.

#### Step 1: Create the Project

```bash
cd /workshop
agentcore create --name AdmissionAgent --defaults --build Container
cd AdmissionAgent
```

> **NOTE (see ISSUES.md):** The `--defaults --build Container` form is outdated
> and fails on current CLI (0.26.0+). Use the explicit-flags form instead:
> `agentcore create --name AdmissionAgent --framework Strands --model-provider Bedrock --memory none --build Container`

The `--defaults` flag creates a Python project using Strands Agents with Amazon
Bedrock. The `--build Container` flag packages the agent as a Docker container
image. This generates:

```text
AdmissionAgent/
├── agentcore/
│   ├── .cli/                   # CLI state (auto-managed)
│   ├── .llm-context/           # LLM context (auto-managed)
│   ├── cdk/                    # CDK infrastructure (auto-managed)
│   ├── .env.local              # Local dev environment variables
│   ├── .gitignore
│   ├── agentcore.json          # Project and resource configuration
│   └── aws-targets.json        # Deployment target (account and region)
├── app/
│   └── AdmissionAgent/         # Your agent code
│       ├── .venv/              # Python virtual environment
│       ├── mcp_client/         # MCP client (auto-generated)
│       ├── model/              # Model loading (load_model())
│       ├── .dockerignore
│       ├── .gitignore
│       ├── Dockerfile
│       ├── main.py             # Agent entrypoint
│       ├── pyproject.toml      # Python dependencies
│       ├── README.md
│       └── uv.lock
├── AGENTS.md
└── README.md
```

#### Step 2: Add Your Agent Code

The scaffold generates a working `app/AdmissionAgent/` directory with a
`main.py`, a `model/` directory (containing `load_model()` which reads model
configuration from `model_config.json`), and a `pyproject.toml`. You'll keep the
scaffold's model loading pattern and modify `main.py` to add your tools and
system prompt.

First, copy the `query_student_db` tool into the agent's code directory:

```bash
mkdir -p app/AdmissionAgent/tools
touch app/AdmissionAgent/tools/__init__.py
cp ../tools/query_student_db.py app/AdmissionAgent/tools/query_student_db.py
```

Now ask Kiro to update the generated `main.py`:

> "Update `app/AdmissionAgent/main.py` to add the Admission Agent tools and
> system prompt. Keep the existing `load_model()` import from the model directory
> and the `BedrockAgentCoreApp` scaffold pattern. Add
> `logging.basicConfig(level=logging.INFO)` for runtime visibility. Add imports
> for `retrieve` from `strands_tools` and `query_student_db` from
> `tools.query_student_db`. Add `os.environ['KNOWLEDGE_BASE_ID']` to set
> `os.environ['STRANDS_KNOWLEDGE_BASE_ID']` so the retrieve tool can find the
> Knowledge Base. Add both tools to the Agent's tools list. Set the system prompt
> to act as a university Admission Advisor named Alex that uses `retrieve` for
> course handbook queries and `query_student_db` for student record lookups via
> SQL against `education_workshop_db`."

> **TIP:** The scaffold generates a `model/` directory with `load_model()` that
> reads from `model_config.json`. This is the standard AgentCore pattern — don't
> replace it with a hardcoded model string.

#### Step 3: Update the Model

The scaffold defaults to a different model. Open
`app/AdmissionAgent/model/load.py` and change the model ID to
`us.anthropic.claude-sonnet-4-6`.

> **TIP:** If you see an `AccessDeniedException` mentioning
> `aws-marketplace:ViewSubscriptions` or `aws-marketplace:Subscribe` when testing
> the agent, the model ID in `model/load.py` hasn't been updated correctly. The
> scaffold's default model requires a Marketplace subscription that isn't
> available in the workshop account. Double-check that `load.py` uses
> `us.anthropic.claude-sonnet-4-6` (the cross-region inference profile, not a
> Marketplace model).

#### Step 4: Update Dependencies

Edit or ensure `app/AdmissionAgent/pyproject.toml` includes the required
dependencies:

```toml
[project]
name = "AdmissionAgent"
version = "0.1.0"
description = "AgentCore Runtime Application using Strands SDK"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "aws-opentelemetry-distro",
    "bedrock-agentcore >= 1.0.3",
    "botocore[crt] >= 1.35.0",
    "mcp >= 1.19.0",
    "strands-agents >= 1.13.0",
    "strands-agents-tools",
]
```

After updating `pyproject.toml`, regenerate the lock file so the container build
can use `--frozen`:

```bash
cd app/AdmissionAgent
uv lock
cd ../..
```

#### Step 5: Configure Environment Variables and Execution Role

The agent needs `KNOWLEDGE_BASE_ID` and `ATHENA_LAMBDA_NAME` at runtime, and a
custom execution role with permissions to invoke Bedrock models, query the
Knowledge Base, and call the Athena Lambda.

With a container build, the `.dockerignore` excludes `.env` files from the image,
so environment variables are configured differently for local dev and
production:

- **Production** (`agentcore deploy`): `envVars` in `agentcore.json` are injected
  into the container at runtime
- **Local dev** (`agentcore dev -b`): variables are read from
  `agentcore/.env.local`

Open `agentcore/agentcore.json` and update the agent entry in the `runtimes`
array to include `envVars` and `executionRoleArn`:

```json
{
  "runtimes": [
    {
      "name": "AdmissionAgent",
      "executionRoleArn": "arn:aws:iam::<your-account-id>:role/agentcore-agent-role",
      "envVars": [
        { "name": "KNOWLEDGE_BASE_ID", "value": "<your-knowledge-base-id>" },
        { "name": "ATHENA_LAMBDA_NAME", "value": "education-athena-query" },
        { "name": "AWS_DEFAULT_REGION", "value": "us-east-1" }
      ]
    }
  ]
}
```

Replace `<your-account-id>` with your AWS account ID
(`aws sts get-caller-identity --query Account --output text`) and
`<your-knowledge-base-id>` with the value from your `.env` file
(`grep KNOWLEDGE_BASE_ID ../.env`).

> **NOTE:** The `executionRoleArn` tells AgentCore to use the workshop's
> pre-provisioned role (`agentcore-agent-role`) instead of creating a new one.
> This role has permissions for Bedrock models, Knowledge Base retrieval, and the
> Athena query Lambda.

> **NOTE:** The `envVars` in `agentcore.json` are only injected during
> `agentcore deploy`. For local development with `agentcore dev`, you'll add the
> variables to `agentcore/.env.local` in the next step.

Copy your environment variables into `agentcore/.env.local` so
`agentcore dev -b` can inject them into the container:

```bash
grep -E 'KNOWLEDGE_BASE_ID|ATHENA_LAMBDA_NAME' ../.env >> agentcore/.env.local
```

Verify the file contains both variables:

```bash
cat agentcore/.env.local
```

_Reference: Production Agent Code (`main.py`)_

### Exercise 2: Test Locally

Before deploying, test the agent locally using the AgentCore dev server. The
environment variables you added to `agentcore/.env.local` in Step 5 are
automatically injected by `agentcore dev` into the container.

> **NOTE:** The `-b` (or `--no-browser`) flag runs the dev server in terminal
> mode. By default, `agentcore dev` launches a browser-based chat UI for testing
> — but since we're working in a web-hosted Code Editor, the browser can't open.
> The terminal TUI provides the same interactive testing experience.

Start the dev server:

```bash
agentcore dev -b
```

> **TIP:** If you see `ModuleNotFoundError` when the dev server starts, the lock
> file may be out of sync with `pyproject.toml`. Stop the dev server, regenerate
> the lock file, and restart: `cd app/AdmissionAgent && uv lock && cd ../..`

This creates a virtual environment, installs dependencies, and starts a local
server with an interactive chat session. Once the server is running and shows
`Status: running`, try these prompts directly in the chat:

```text
What are the prerequisites for Database Systems?
```

```text
Look up student 100016 and tell me what courses they have completed.
```

Verify the agent calls both the `retrieve` tool (for KB queries) and
`query_student_db` (for Athena queries) correctly before deploying.

> **NOTE:** Memory is not available during local development — it requires
> deployed AWS infrastructure. You'll add memory in Module 8 after deploying.

### Exercise 3: Deploy to AgentCore Runtime

#### Step 1: Deploy

```bash
agentcore deploy
```

The deploy command uses the AWS Cloud Development Kit (CDK) under the hood to
provision infrastructure. CDK is an infrastructure-as-code framework that
translates your agent configuration into CloudFormation stacks. On the first
deployment, CDK needs to bootstrap your account — this creates a staging bucket
and IAM roles that CDK uses to deploy resources.

When you run `agentcore deploy` for the first time, you'll be prompted to approve
the CDK bootstrap. Type `Y` and press Enter to proceed.

After bootstrap completes (this is a one-time step), the deployment continues
automatically:

- Packages your agent code
- Synthesizes a CloudFormation stack via CDK
- Creates an AgentCore Runtime endpoint for your agent
- Configures CloudWatch logging and observability

The first deployment takes a few minutes. Subsequent deployments are faster since
bootstrap is already done.

> **TIP:** You can preview what will be deployed without making changes by running
> `agentcore deploy --plan`.

#### Step 2: Monitor Deployment Progress

```bash
agentcore status
```

You can also view a live dashboard of all deployed resources by running
`agentcore` and selecting `status` from the TUI.

### Exercise 4: Test the Production Endpoint

Using the CLI:

```bash
agentcore invoke "What are the prerequisites for Database Systems?"
```

```bash
agentcore invoke "Look up student 100016 and tell me what courses they have completed."
```

You can also stream responses in real time:

```bash
agentcore invoke "What electives are available in the Computer Science department?" --stream
```

The agent should generate SQL, invoke the Athena Lambda, and return real data —
the same behaviour as your local agent, now running in AgentCore.

### Exercise 5: Connect Streamlit to AgentCore

Now that the agent is running in production, update your Streamlit app to call
the AgentCore endpoint instead of running the agent locally. This separates the
UI from the agent runtime — the Streamlit app becomes a thin client.

First, get the runtime ARN from the status output and add it to your `.env` file:

```bash
agentcore status
echo "AGENTCORE_RUNTIME_ARN=<YOUR_RUNTIME_ARN>" >> ../.env
```

Then ask Kiro to update the app:

> "Update my Streamlit app to call the deployed AgentCore agent instead of
> running the agent locally. The runtime ARN is stored in the
> `AGENTCORE_RUNTIME_ARN` environment variable in `.env` — use `load_dotenv()` to
> load it. Use the `bedrock-agentcore` SDK to send prompts to the deployed runtime
> via `invoke_agent_runtime`. Remove the local Agent creation, tool imports, and
> direct Bedrock calls — the app should only handle UI and forward requests to
> AgentCore. The AgentCore response is a dict with
> `{'role': 'assistant', 'content': [{'text': '...'}]}` — extract the text from
> `content[0]['text']` and pass it to `st.markdown()` so newlines and formatting
> render correctly."

Run the updated Streamlit app:

```bash
cd /workshop
streamlit run streamlit_advisor/app.py --server.port 8501
```

Verify it works the same as before — but now the agent logic runs in AgentCore,
not in the Streamlit process.

> **TIP:** The Streamlit app may throw an error related to how the AgentCore
> response text is parsed or rendered. If this happens, copy the full error
> message and paste it into your Kiro session — Kiro can diagnose the response
> format and suggest a fix to the parsing logic.

_Reference: Streamlit + AgentCore sample code_

### Exercise 6: Observe Agent Traces

AgentCore automatically instruments your agent with distributed tracing and
logging. You can access both from the CLI and the console.

#### Logs

Stream logs directly from the terminal:

```bash
# Stream recent logs
agentcore logs

# Filter by time range and severity
agentcore logs --since 30m --level error

# Search for specific patterns
agentcore logs --query "timeout"
```

#### Traces

View distributed traces that show the full execution flow of each invocation:

```bash
# List recent traces
agentcore traces list

# Get details for a specific trace
agentcore traces get <trace-id>
```

You can also explore traces in the console:

1. Navigate to the Amazon Bedrock console
2. In the left sidebar under AgentCore, select Observability
3. Select your agent runtime from the list

Each trace breaks down into spans showing:

- **Agent span:** The top-level invocation, including total latency and the final
  response
- **Model spans:** Each call to Claude — the prompt sent, tokens used, and
  response time
- **Tool spans:** Each tool invocation (`retrieve`, `query_student_db`) with input
  parameters and output
- **Memory spans:** Any memory read/write operations (once enabled in Module 8)

Try invoking the agent with different prompts and compare the traces:

- A simple KB question ("What programs are available?") should show a single
  `retrieve` tool span
- A student lookup ("Look up student 100016") should show a `query_student_db`
  span with SQL
- A complex question ("What courses should student 100016 take next?") should
  show multiple tool spans as the agent chains KB retrieval with database queries

Notice how the agent's reasoning changes based on the question — the traces make
the perception-thinking-action loop visible.

### Review

You created an AgentCore project, added your agent code, tested it locally with
`agentcore dev -b`, and deployed it to AgentCore Runtime with `agentcore deploy`.
The agent responds to prompts using live Athena data — the same behaviour as your
local agent, now running as a managed service. You then updated the Streamlit app
to call the AgentCore endpoint instead of running the agent locally, separating
the UI from the agent runtime. The result is a production architecture where
Streamlit is a thin client and AgentCore handles model invocation, tool
execution, scaling, and observability through CloudWatch.

---

## Module 8: Adding Memory

Enable short-term session memory and long-term preference memory so the agent
maintains context within conversations and personalises advice across sessions.

### Prerequisites

- Completed Module 7 (agent deployed to AgentCore Runtime via `agentcore deploy`)

### Why Memory Matters

In the introduction, you saw that agents interact with data through three
patterns: RAG for institutional knowledge, MCP for reading and writing external
systems, and memory for building persistent context about individual users. So
far, your Admission Agent uses RAG to retrieve course handbook content and tools
to look up student profiles, but every conversation starts from scratch. The
agent has no recollection of what was discussed a minute ago, let alone last
week.

This is a problem for real student-facing systems. Consider a prospective student
who:

- Asks about Computer Science prerequisites in one message
- Follows up with "Do I meet those requirements?" in the next
- Returns a week later and says "I've decided to focus on AI electives"

Without memory, the agent can't connect turn 2 to turn 1 (it's already forgotten
the prerequisites it just listed), and it certainly can't recall the student's
preference in a future session. The student has to repeat themselves every time,
which is the opposite of the personalised experience you're building toward.

Memory solves this at two levels:

- **Short-term (session) memory** keeps the conversation coherent across turns
  within a single session, so the agent can reference what was said earlier
  without the student repeating it.
- **Long-term (user) memory** persists facts and preferences across sessions, so
  the agent builds an evolving understanding of each student over time.

This is the third interaction pattern from the architecture diagram, and it's
what transforms a stateless Q&A tool into a personalised advisor.

### What You're Using: AgentCore Memory

Amazon Bedrock AgentCore provides memory as a managed resource alongside the
runtime you deployed in Module 7. An AgentCore Memory resource stores
conversation events (short-term memory) and can automatically extract insights
like facts and preferences into long-term memory records using configurable
strategies.

When you create a memory resource and wire it into your agent, the service:

- **Stores conversation events** from each session as short-term memory,
  retaining the full turn history for a configurable retention period.
- **Extracts insights automatically** using memory strategies — for example, a
  semantic strategy pulls out facts and preferences from conversations and stores
  them as searchable long-term memory records.
- **Scopes memory per actor**, so student 100033's preferences never leak into
  student 100016's sessions.

You don't need to build a database, write summarisation prompts, or manage
context windows yourself. AgentCore handles the storage, extraction, and scoping.

There are two ways to create and manage AgentCore Memory:

- **AgentCore CLI:** Use `agentcore add memory` to add a memory resource to your
  project and `agentcore deploy` to provision it in AWS. The CLI manages the
  lifecycle and makes the memory ID available to your agent as an environment
  variable. This is the approach we'll use in this module.
- **AWS SDK (boto3):** Use the `bedrock-agentcore-control` client to create memory
  resources programmatically, and the `bedrock-agentcore` SDK's
  `MemorySessionManager` to write events and retrieve records. This gives you full
  control and works for agents running outside AgentCore Runtime.

Both approaches create the same underlying resource — the CLI is simpler for
getting started, while the SDK is what your agent code uses at runtime to read and
write memory.

### Exercise 1: Create a Memory Resource with Short-Term Memory

Short-term memory gives the agent continuity within a single conversation.
Without it, each invocation is independent — the agent processes one message,
returns a response, and forgets everything. With it, the agent can reference
earlier turns in the same session.

#### Step 1: Add Memory to the Agent Project

From your `AdmissionAgent/` project directory, add a memory resource to the
project. The `agentcore add memory` command registers the memory within your
agent project so that `agentcore deploy` provisions it alongside the runtime and
makes the memory ID available as an environment variable.

```bash
cd AdmissionAgent
agentcore add memory --name admission_agent_memory
```

Then deploy to provision the memory resource in AWS:

```bash
agentcore deploy
```

This takes 2-3 minutes. The deploy creates the memory resource and injects the
`MEMORY_ADMISSION_AGENT_MEMORY_ID` environment variable into your agent's runtime
automatically.

> **WARNING:** You must use `agentcore add memory` (not `agentcore memory create`)
> to link the memory to your agent project. The `add` command registers the memory
> in the project configuration so that `deploy` provisions it and makes the memory
> ID available to the runtime. Using `memory create` alone creates a standalone
> resource that the runtime doesn't know about, which will cause invocation
> failures.

#### Step 2: Verify the Memory Resource

```bash
agentcore status
```

You should see the memory resource listed with status `ACTIVE`.

#### Step 3: Wire Memory into the Agent

Ask Kiro to integrate the memory session manager into your agent:

> "Update my AgentCore agent in `app/AdmissionAgent/main.py` to use the
> `AgentCoreMemorySessionManager` from
> `bedrock_agentcore.memory.integrations.strands` for short-term memory. The
> memory ID is available as the `MEMORY_ADMISSION_AGENT_MEMORY_ID` environment
> variable (AgentCore sets this automatically after deploy). Create an
> `app/AdmissionAgent/memory/session.py` module that builds the session manager
> from the memory ID, session ID, and actor ID. Update the invoke entrypoint in
> `main.py` to extract `session_id` and `actor_id` from the invocation payload and
> pass the session manager to the Strands Agent constructor via the
> `session_manager` parameter."

#### Step 4: Deploy and Test

```bash
agentcore deploy
```

Once deployed, test a multi-turn conversation using the interactive chat:

```bash
agentcore invoke
```

This opens an interactive chat session with your deployed agent. The CLI
automatically manages session IDs, so each conversation maintains context across
turns. Try this sequence:

```text
What are the prerequisites for Data Science: Machine Learning?
```

Then follow up in the same session:

```text
Do I meet those prerequisites if I have completed Statistics 201 and Programming 102?
```

The agent should reference the prerequisites from the first turn without you
repeating them. It knows what "those prerequisites" refers to because the session
manager retrieves the prior turns from short-term memory and injects them into the
agent's context.

Type `exit` or press Ctrl+C to end the session.

### Exercise 2: Add Long-Term Memory Strategies

Long-term memory is where the real personalisation happens. While short-term
memory retains raw conversation events for a limited period, long-term memory
strategies automatically extract structured insights — facts, preferences,
summaries — and store them as searchable records that persist indefinitely.

#### Step 1: Update the Memory Resource

Add semantic and user preference strategies to the existing memory resource.
Remove the current memory from the project and re-add it with strategies:

```bash
agentcore remove memory --name admission_agent_memory
agentcore add memory --name admission_agent_memory \
  --strategies SEMANTIC,USER_PREFERENCE
agentcore deploy
```

Wait for the deploy to complete and the memory to reach `ACTIVE` status:

```bash
agentcore status
```

> **NOTE:** Memory strategies define how conversation events are processed into
> long-term records. The semantic strategy extracts factual information (e.g.
> "student is enrolled in Computer Science"). The user preference strategy extracts
> stated preferences (e.g. "prefers AI electives"). Both are extracted
> automatically from conversation events — you don't write any extraction logic.

#### Step 2: Update the Session Manager

Ask Kiro to update the memory session manager to include retrieval configuration
for long-term memory:

> "Update `app/AdmissionAgent/memory/session.py` to add a `retrieval_config` to
> the `AgentCoreMemoryConfig` that searches both the semantic facts namespace and
> the user preferences namespace. Use `RetrievalConfig(top_k=5,
> relevance_score=0.5)` for both. The namespace templates should follow the pattern
> `/users/{actor_id}/facts` for semantic and `/users/{actor_id}/preferences/` for
> user preferences."

#### Step 3: Deploy and Test

```bash
agentcore deploy
```

First session — establish a preference. Start an interactive chat:

```bash
agentcore invoke
```

```text
I prefer electives related to artificial intelligence and data science.
```

> **NOTE:** Long-term memory extraction is asynchronous. After writing events, it
> may take 10-30 seconds for the strategies to process them into long-term records.
> Wait briefly before testing retrieval in a new session.

Exit the session (Ctrl+C), wait 30 seconds, then start a new session to verify the
agent remembers without being reminded:

```bash
agentcore invoke
```

```text
What electives would you recommend for me next semester? I am student 100033
```

The agent should prioritise AI and data science electives based on the stored
preference, even though this is a completely new session. The session manager
retrieved the student's long-term memory records and injected them into the
agent's context automatically.

```text
"text": "Great news, Diego! I've cross-referenced your completed courses, AI/Data Science electives available ...
Would you like me to help you formally plan out your full degree path toward Data Science: Machine Learning? 😊"
```

#### Step 4: Inspect Extracted Long-Term Memory

The strategies run asynchronously in the background — extracting facts and
preferences from your conversation events and storing them as long-term memory
records. You can inspect exactly what was extracted using the AgentCore SDK.

Create a script called `list_memories.py` in your project root. First, get the
memory ID — AgentCore sets `MEMORY_ADMISSION_AGENT_MEMORY_ID` inside the container
automatically, but locally you need to grab it from the status output:

```bash
cd /workshop/AdmissionAgent
agentcore status
```

Find the memory ARN in the output under Memories — it looks like:

```text
Memories
  admission_agent_memory: Deployed (SEMANTIC, USER_PREFERENCE) (arn:aws:bedrock-agentcore:us-east-1:123456789012:memory/AdmissionAgent_admission_agent_memory-XXXXXXXXXX)
```

The memory ID is the value after `memory/` in the ARN (e.g.
`AdmissionAgent_admission_agent_memory-XXXXXXXXXX`). Add it to your `.env`:

```bash
echo "MEMORY_ADMISSION_AGENT_MEMORY_ID=<memory-id>" >> /workshop/.env
```

Then create the script at `/workshop/list_memories.py`:

```python
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

MEMORY_ID = os.environ["MEMORY_ADMISSION_AGENT_MEMORY_ID"]
ACTOR_ID = "default-actor"

client = boto3.client("bedrock-agentcore")

# List semantic facts
print("=== Semantic Facts ===")
response = client.list_memory_records(
    memoryId=MEMORY_ID,
    namespace=f"/users/{ACTOR_ID}/facts",
)
for record in response.get("memoryRecordSummaries", []):
    print(f"  - {record.get('content', {}).get('text', '')}")

# List user preferences
print("\n=== User Preferences ===")
response = client.list_memory_records(
    memoryId=MEMORY_ID,
    namespace=f"/users/{ACTOR_ID}/preferences/",
)
for record in response.get("memoryRecordSummaries", []):
    print(f"  - {record.get('content', {}).get('text', '')}")
```

Run it:

```bash
python3 ../list_memories.py
```

You should see the extracted insights from your conversations — for example:

```text
=== Semantic Facts ===
  - The user asked about prerequisites for Data Science: Machine Learning.
  - The user inquired about electives in artificial intelligence.

=== User Preferences ===
  - The user prefers electives related to artificial intelligence and data science.
```

These are the long-term memory records that the strategies extracted
automatically from your conversation events. The semantic strategy pulls out
factual information, while the user preference strategy captures stated
preferences. Both are retrieved by the session manager at the start of each turn
and injected into the agent's context — which is how the agent "remembered" your
preference in the new session.

> **NOTE:** The namespaces (`/users/{actor_id}/facts` and
> `/users/{actor_id}/preferences/`) match the `retrieval_config` in `session.py`.
> This is how the session manager knows where to look for long-term records when
> building context for each turn.

_Reference: `memory/session.py`_
_Reference: `main.py` (with memory)_

### What This Enables

With both memory types active, the Admission Agent can now:

- **Maintain coherent multi-turn conversations** — students don't need to repeat
  context within a session.
- **Remember stated preferences** — "I'm interested in AI" persists across
  sessions without the student saying it again.
- **Personalise recommendations over time** — each interaction adds to what the
  agent knows about the student, making future advice more relevant.

In Module 9, you'll see this same `session_and_user` memory configuration power the
Learning Support Agent, where long-term memory builds a student learning profile
that tracks:

- **Learning strengths and gaps:** "This student consistently struggles with SQL
  joins but excels at data modelling"
- **Preferred explanation style:** "Responds well to worked examples rather than
  abstract definitions"
- **Accessibility needs:** "Uses screen reader; prefers text-based explanations
  over diagrams"
- **Study patterns:** "Typically asks questions the night before an assessment"

Each conversation enriches the profile. When the student returns days later, the
agent picks up where it left off — adapting its explanations, prioritising weak
areas, and avoiding unnecessary repetition. Memory is what makes this possible.

### Review

Before this module, the Admission Agent treated every message as an isolated
request. A student could ask about prerequisites, follow up with "Do I qualify?",
and the agent would have no idea what they were referring to. Across sessions, the
problem was worse — a student who mentioned their interest in AI last week would
get generic recommendations this week, as if they'd never spoken before. This is
the core problem: a stateless agent can't deliver the personalised, continuous
advising experience that students expect.

You addressed this by adding an AgentCore Memory resource to your project using
the CLI (`agentcore add memory`), wiring it into the agent via the
`AgentCoreMemorySessionManager`, and adding long-term memory strategies that
automatically extract facts and preferences from conversations. Short-term memory
gives the agent continuity within a conversation, so it can resolve references
like "those prerequisites" or "that program" without the student repeating
themselves. Long-term memory persists extracted insights across sessions, so the
agent accumulates an understanding of each student over time — their interests,
their program, their goals — and retrieves that context automatically in future
conversations.

The improvement is the shift from a transactional Q&A tool to a personalised
advisor. Students no longer repeat themselves within a session or across sessions.
Recommendations get more relevant with each interaction because the agent
remembers what it's learned. This is the foundation that the Learning Support
Agent in Module 9 builds on, where long-term memory tracks learning strengths,
weak areas, and preferred explanation styles to create a truly adaptive
experience.

---

## Module 9: Multi-Agent Systems

Build a multi-agent orchestrator that coordinates specialist agents within the
existing AgentCore project. The Admission Agent handles information lookups, while
a new Advisor Requests Agent evaluates student requests for validity and
complexity before submitting them via MCP — demonstrating the agents-as-tools
pattern.

### Why Multi-Agent?

A monolithic agent with every tool and instruction in a single system prompt
becomes brittle as scope grows. More importantly, some tasks require judgement —
not just tool calls. When a student asks to submit a course override, the agent
shouldn't blindly create a request. It should evaluate whether the request is
reasonable, check the student's record for supporting evidence, and only escalate
to a formal request if warranted.

Multi-agent architectures solve this by:

- **Separation of concerns:** Each agent has a focused role, toolset, and
  decision-making logic
- **Specialised reasoning:** The advisor requests agent can evaluate request
  validity without cluttering the admission agent's prompt
- **Independent prompts:** Each agent's system prompt is concise and
  domain-specific
- **Agents as tools:** The orchestrator delegates to specialists using the `@tool`
  pattern — the LLM decides which specialist to call based on tool descriptions

### Why MCP for Write Operations?

So far, the Admission Agent only reads data — retrieving from the Knowledge Base
and querying student records via Athena. But real student services need to write
too. When a student asks to submit a course override request, schedule an advisor
meeting, or request a program change, the agent needs to create records in
external systems.

Model Context Protocol (MCP) provides a standardised interface for these
operations. Instead of embedding direct API calls in your agent code, you expose
write operations through an MCP server that:

- Defines clear tool schemas with input validation
- Provides a consistent interface regardless of the backing service
- Can be shared across multiple agents via AgentCore Gateway
- Separates the data access layer from the agent logic

### Architecture

Module 9 multi-agent architecture: the Orchestrator routes student queries to
either the Admission Agent (RAG + Athena) or the Advisor Requests Agent (MCP via
AgentCore Gateway to a Lambda-backed DynamoDB store).

- **Orchestrator:** The `main.py` entrypoint. Routes student queries to the right
  specialist based on intent — information lookups go to the Admission Agent,
  action requests go to the Advisor Requests Agent.
- **Admission Agent (`@tool`):** The agent you built in Modules 4-8. Queries the
  course handbook Knowledge Base and looks up student records via Athena.
- **Advisor Requests Agent (`@tool`):** Evaluates whether a student's request is
  reasonable and sufficiently complex to warrant a formal advisor request. Checks
  the student's record for supporting evidence before submitting via MCP. Rejects
  trivial or unsupported requests with guidance instead.

### Exercise 1: Deploy the Advisor Requests MCP to AgentCore Gateway

The Advisor Requests system lets the agent write records on behalf of students.
When a student asks to submit a course override, request an advisor meeting, or
apply for a program change, the agent creates a tracked request in DynamoDB that
human advisors can review.

The workshop has pre-provisioned everything you need:

- A DynamoDB table (`education-advisor-requests`) for storing requests
- A Lambda function (`education-advisor-requests`) that handles create and list
  operations
- A pre-built MCP server at `/workshop/mcp/advisor_requests_server.py` that wraps
  the Lambda as MCP tools

You just need to deploy the MCP server to AgentCore Gateway so your agent can
connect to it.

#### Step 1: Review the Pre-Built MCP Server

Take a look at the MCP server to understand what it provides:

```bash
cat /workshop/mcp/advisor_requests_server.py
```

The server exposes two tools:

| Tool | Description | Read/Write |
| --- | --- | --- |
| `submit_advisor_request` | Create an advisor request (course override, meeting, program change, special consideration) | Write |
| `list_advisor_requests` | List all requests for a student | Read |

#### Step 2: Create the Gateway

AgentCore Gateway hosts MCP servers as managed endpoints that your agents can
connect to:

```bash
cd /workshop/AdmissionAgent
agentcore add gateway \
  --name education-advisor-gateway \
  --authorizer-type NONE \
  --runtimes AdmissionAgent
```

#### Step 3: Register the MCP Server

The workshop has pre-provisioned a tool schema at `/workshop/mcp/tools.json`
alongside the MCP server. Add the Lambda function as a gateway target:

```bash
agentcore add gateway-target \
  --name advisor-requests \
  --type lambda-function-arn \
  --lambda-arn $(aws lambda get-function --function-name education-advisor-requests --query 'Configuration.FunctionArn' --output text) \
  --tool-schema-file /workshop/mcp/tools.json \
  --gateway education-advisor-gateway
```

#### Step 4: Deploy

```bash
agentcore deploy
```

#### Step 5: Verify the Gateway

Once deployed, check the status to get the gateway ID:

```bash
agentcore status
```

The gateway ID is shown in the output (e.g.
`admissionagent-education-advisor-gateway-xxxxxxxxxx`). The MCP URL follows this
pattern:

```text
https://<gateway-id>.gateway.bedrock-agentcore.<region>.amazonaws.com/mcp
```

Construct the URL and save it to your environment:

```bash
GATEWAY_ID=<gateway-id-from-status>
REGION=us-east-1
ADVISOR_MCP_URL="https://${GATEWAY_ID}.gateway.bedrock-agentcore.${REGION}.amazonaws.com/mcp"

echo "ADVISOR_MCP_URL=${ADVISOR_MCP_URL}" >> /workshop/.env
echo "ADVISOR_MCP_URL=${ADVISOR_MCP_URL}" >> agentcore/.env.local
```

Also add `ADVISOR_MCP_URL` to the `envVars` array in `agentcore/agentcore.json`
so the deployed container can access it:

```json
{ "name": "ADVISOR_MCP_URL", "value": "<your-advisor-mcp-url>" }
```

> **NOTE:** The `.env.local` file is only used during local development with
> `agentcore dev`. For production deploys, environment variables must be in the
> `envVars` array in `agentcore.json`.

### Exercise 2: Create the Specialist Agent Tools

Now create the specialist agents as `@tool` functions inside the existing agent
code. The orchestrator will delegate to these based on the student's intent.

#### Step 1: Create the Agents Directory

```bash
cd /workshop/AdmissionAgent
mkdir -p app/AdmissionAgent/agents
touch app/AdmissionAgent/agents/__init__.py
```

#### Step 2: Create the Admission Agent Tool

Ask Kiro to create the admission agent tool:

> "Create `app/AdmissionAgent/agents/admission.py` with a `route_to_admission`
> function decorated with `@tool` from strands. It takes a query string and
> optional `student_id` string. Inside, it creates a Strands Agent with
> `load_model()` from `model.load`, tools `retrieve` (from `strands_tools`) and
> `query_student_db` (from `tools.query_student_db`), and a system prompt for a
> university Admission Advisor named Alex that uses `retrieve` for course handbook
> queries and `query_student_db` for student record lookups. It runs the agent
> with the query (prepending `student_id` if provided) and returns the result as a
> string. Set `os.environ['STRANDS_KNOWLEDGE_BASE_ID']` from
> `os.environ['KNOWLEDGE_BASE_ID']` at module level."

_Reference: `agents/admission.py`_

#### Step 3: Create the Advisor Requests Agent Tool

This agent doesn't just submit requests — it evaluates them first. It checks
whether the request is reasonable, looks up the student's record for supporting
evidence, and only submits if the request is warranted. Trivial requests (like
asking for a meeting to discuss something the agent can answer directly) are
handled with guidance instead.

Ask Kiro to create the advisor requests agent tool:

> "Create `app/AdmissionAgent/agents/advisor_requests.py` with a
> `route_to_advisor_requests` function decorated with `@tool` from strands. It
> takes a query string and optional `student_id` string. Inside the tool function,
> create an `MCPClient` from `strands.tools.mcp` using `streamablehttp_client` from
> `mcp.client.streamable_http` as the transport, with the URL from the
> `ADVISOR_MCP_URL` environment variable. Use the client as a context manager
> (`with mcp_client:`) and call `list_tools_sync()` to get the MCP tools. Create a
> Strands Agent with `load_model()` from `model.load`, the MCP tools AND
> `query_student_db` from `tools.query_student_db` so it can look up the student's
> record to validate requests. Set the system prompt to act as a student services
> evaluator that: (1) assesses whether the request is reasonable and complex enough
> to warrant a formal advisor request, (2) uses `query_student_db` to check the
> student's record for supporting evidence, (3) only submits via MCP if the request
> is justified, and (4) for trivial or unsupported requests, provides helpful
> guidance instead of submitting. Request types are: `course_override`,
> `advisor_meeting`, `program_change`, `special_consideration`."

_Reference: `agents/advisor_requests.py`_

> **NOTE:** The Advisor Requests Agent has access to `query_student_db` so it can
> verify the student's record before submitting. This is the key difference from a
> simple pass-through — the agent applies judgement, not just tool calls.

### Exercise 3: Build the Orchestrator

Now refactor `main.py` to be an orchestrator that routes student queries to the
specialist agent tools.

#### Step 1: Update main.py

Ask Kiro to update the entrypoint:

> "Update `app/AdmissionAgent/main.py` to be an orchestrator. Import
> `route_to_admission` from `agents.admission` and `route_to_advisor_requests` from
> `agents.advisor_requests`. Keep the existing `BedrockAgentCoreApp` scaffold,
> `load_model()`, logging, and memory session manager from Module 8. Change the
> Agent's tools to `[route_to_admission, route_to_advisor_requests]` and update the
> system prompt to be a student services orchestrator that analyses queries and
> routes to the right specialist — information lookups to admission, action requests
> to advisor requests. Pass the `student_id` if identified. Include the strands
> conversation manager."

_Reference: `main.py` (orchestrator)_

#### Step 2: Deploy and Test

```bash
agentcore deploy -y
```

Once deployed, test with the interactive chat:

```bash
agentcore invoke
```

Information lookup (routes to Admission Agent):

```text
What are the prerequisites for Data Science: Machine Learning?
```

Justified request (Advisor Requests Agent evaluates and submits):

```text
I'm student 100033. I'd like to request to have a conversation with an advisor for a course override for Data Science: Machine Learning — I completed equivalent prerequisites at another university and have a 3.8 GPA.
```

The agent should look up student 100033's record, verify the strong GPA, and
submit the override request.

Trivial request (Advisor Requests Agent declines with guidance):

```text
I'm student 100033. Can you submit a meeting request so I can ask my advisor what electives are available?
```

The agent should recognise this is something it can answer directly and provide
the elective information instead of creating an unnecessary meeting request.

Check existing requests:

```text
Can you show me all my pending requests? My student ID is 100033.
```

Cross-domain query (triggers both specialists):

```text
I'm student 100033. What's my current GPA, and can you submit a program change request to switch to Data Science?
```

The orchestrator should route the GPA lookup to the Admission Agent and the
program change to the Advisor Requests Agent, which will check the student's
standing before submitting.

#### Verify in DynamoDB

After a successful submission, verify the request was created by checking the
DynamoDB table:

1. Open the DynamoDB console.
2. Select the `education-advisor-requests` table.
3. Click Explore table items.
4. You should see the advisor request(s) created by the agent, including the
   student ID, request type, description with the agent's evaluation summary, and
   a `pending` status.

### Technology Patterns Summary

| Agent | Role | Tools | Key Behaviour |
| --- | --- | --- | --- |
| Orchestrator | Routes queries | `route_to_admission`, `route_to_advisor_requests` | Intent classification, multi-agent delegation |
| Admission Agent | Information lookup | `retrieve`, `query_student_db` | RAG + database queries |
| Advisor Requests Agent | Evaluate and submit requests | `query_student_db`, MCP tools | Validates requests against student record before submitting |

### Key Patterns

- **Agents as tools:** Each specialist is a `@tool` function. The orchestrator's
  LLM uses tool docstrings to decide which specialist to call — write clear
  descriptions that distinguish information lookups from action requests.
- **Evaluation before action:** The Advisor Requests Agent doesn't blindly submit
  — it checks the student's record, assesses whether the request is reasonable, and
  provides guidance for trivial or unsupported requests. This is judgement, not
  just routing.
- **Shared tools across agents:** `query_student_db` is used by both the Admission
  Agent (for lookups) and the Advisor Requests Agent (for validation). Tools are
  reusable building blocks.
- **MCP for write operations:** Write operations go through an MCP server on
  AgentCore Gateway, keeping the data access layer separate from agent logic.
- **AgentCore Gateway for managed MCP:** The MCP server is a managed, discoverable
  endpoint — not a local process.

### Review

Before this module, the Admission Agent was a single agent with a growing list of
responsibilities. Adding write capabilities to the same agent would mean one
system prompt trying to handle information lookups, request evaluation, and
submission logic — a recipe for prompt brittleness as scope grows.

You addressed this by introducing the agents-as-tools pattern. The orchestrator
(`main.py`) classifies student intent and delegates to focused specialists: the
Admission Agent for information lookups, and the Advisor Requests Agent for action
requests. Each specialist has its own system prompt, tools, and reasoning logic.
The Advisor Requests Agent doesn't just pass requests through — it evaluates
whether a request is reasonable by checking the student's record, assesses
complexity, and only submits to DynamoDB via MCP when the request is warranted.
Trivial requests get helpful guidance instead of unnecessary formal submissions.

This is the core value of multi-agent architectures: not just routing, but
specialised reasoning. The orchestrator decides who should handle a query, and
each specialist decides how to handle it within its domain. The Admission Agent
reasons about course prerequisites and student records. The Advisor Requests Agent
reasons about whether a request deserves human attention. Neither agent needs to
understand the other's domain — they're composed through tool interfaces, keeping
each one focused and maintainable.
