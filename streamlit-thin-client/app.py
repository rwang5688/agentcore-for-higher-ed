"""Streamlit chat interface for the Peculiar University advisor (THIN client).

Thin client: this app runs NO agent logic locally. It forwards each prompt to
the deployed AgentCore runtime (via the ``bedrock-agentcore`` SDK's
``invoke_agent_runtime``) and renders the streamed response. All the
intelligence — model inference, KB retrieval, Athena queries, multi-agent
orchestration, memory — runs on the AgentCore backend, not here.

This is Phase 2 of the demo roadmap (managed backend). The invoke logic here is
the same business logic that gets merged into ``deploy-streamlit-app`` for the
hosted (Cognito + ECS Fargate) Phase 3.

Requires ``AGENTCORE_RUNTIME_ARN`` in the repo-root ``.env`` (from
``agentcore status``).

Run from this directory with:

    streamlit run app.py
"""

import json
import uuid

import boto3
import streamlit as st

from config import get_config

config = get_config()

if not config.agentcore_runtime_arn:
    st.error(
        "AGENTCORE_RUNTIME_ARN is not set in .env. Deploy the agent with "
        "`agentcore deploy`, then copy the runtime ARN from `agentcore status` "
        "into .env as AGENTCORE_RUNTIME_ARN."
    )
    st.stop()


@st.cache_resource
def _client():
    """One bedrock-agentcore data-plane client per process."""
    return boto3.client("bedrock-agentcore", region_name=config.aws_region)


def _extract_text(chunk: dict) -> str:
    """Pull assistant text out of one streamed Strands event.

    The deployed agent streams Strands events. Text arrives as
    contentBlockDelta.delta.text. We ignore tool-use / metadata events.
    """
    event = chunk.get("event", chunk)
    delta = (
        event.get("contentBlockDelta", {}).get("delta", {})
        if isinstance(event, dict)
        else {}
    )
    text = delta.get("text")
    return text if isinstance(text, str) else ""


def invoke_agent(prompt: str, session_id: str) -> str:
    """Invoke the deployed AgentCore runtime and return the full response text.

    Reads the streaming response body, accumulating assistant text. Falls back
    to rendering the raw body if it isn't the expected event stream.
    """
    print(
        f"[thin-client] invoke_agent_runtime -> {config.agentcore_runtime_arn} "
        f"(session={session_id})\n  prompt: {prompt!r}",
        flush=True,
    )
    resp = _client().invoke_agent_runtime(
        agentRuntimeArn=config.agentcore_runtime_arn,
        runtimeSessionId=session_id,
        contentType="application/json",
        accept="application/json",
        payload=json.dumps({"prompt": prompt}).encode("utf-8"),
    )

    raw = resp["response"].read()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")

    parts: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        # SSE frames are prefixed with "data: "
        if line.startswith("data:"):
            line = line[len("data:"):].strip()
        try:
            parts.append(_extract_text(json.loads(line)))
        except (json.JSONDecodeError, AttributeError):
            continue

    text = "".join(parts).strip()
    return text or raw.strip()


st.set_page_config(page_title="Peculiar University Advisor (thin)", page_icon="🎓")

st.title("🎓 Peculiar University Advisor")
st.caption(
    "An assistant for academic advisors, powered by the deployed AgentCore "
    "agent. Look up a student's live records, registrations, and degree plans, "
    "and cross-reference the course handbook for programs and prerequisites. "
    "Name the student ID in your question (e.g. \"student 100033\")."
)

# --- Session state -------------------------------------------------------
# One AgentCore runtime session per browser session keeps conversation context
# on the server. `messages` is the local display transcript.
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session-{uuid.uuid4().hex}"  # >= 33 chars (AgentCore min)
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar: mode + sample questions + controls ------------------------
with st.sidebar:
    if st.button("Clear conversation"):
        st.session_state.session_id = f"session-{uuid.uuid4().hex}"
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("Thin client → AgentCore")
    st.caption("This UI runs no agent locally. Each prompt is sent to the "
               "deployed AgentCore runtime.")
    st.code(config.agentcore_runtime_arn, language=None)
    st.caption(f"Session: {st.session_state.session_id}")

    st.divider()
    st.header("Sample questions")
    st.caption("Copy one into the chat box to try it out.")
    st.code(
        "What computer science courses are available, and what are their prerequisites?",
        language=None,
    )
    st.code(
        "Which courses in the COMP department have the most registrations?",
        language=None,
    )
    st.code(
        "Pull up student 100033's profile: their program, enrollment status, "
        "and cumulative GPA.",
        language=None,
    )
    st.code(
        "Look up student 100033's completed courses, then recommend which "
        "Computer Science courses they're eligible to take next and list the "
        "prerequisites.",
        language=None,
    )
    st.code(
        "I'm student 100033. I'd like to request to have a conversation with an "
        "advisor for a course override for Data Science: Machine Learning — I "
        "completed equivalent prerequisites at another university and have a 3.8 "
        "GPA.",
        language=None,
    )

# --- Render prior conversation ------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle new input ----------------------------------------------------
if prompt := st.chat_input("Ask the advisor a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = invoke_agent(prompt, st.session_state.session_id)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
