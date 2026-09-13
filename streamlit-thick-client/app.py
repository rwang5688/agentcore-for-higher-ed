"""Streamlit chat interface for the Peculiar University advisor (THICK client).

Thick client: this app runs the full Strands advisor agent IN-PROCESS. Every AWS
service invocation happens locally with the developer's own credentials:

    - Bedrock model inference (Claude Sonnet)
    - Bedrock Knowledge Base retrieval (course handbook RAG)
    - the query_student_db tool -> Athena query Lambda

No AgentCore runtime is involved. This is the pre-AgentCore design: the same UX
as the thin client, but all the intelligence lives here rather than on a managed
backend. It is Phase 1 of the demo roadmap (local Strands agent).

Requires the repo-root ``.env`` with KNOWLEDGE_BASE_ID (and optionally
AWS_REGION, BEDROCK_MODEL_ID, ATHENA_LAMBDA_NAME).

Run from this directory with:

    streamlit run app.py
"""

import streamlit as st

from advisor_agent import create_agent
from config import get_config

get_config()  # fail fast if KNOWLEDGE_BASE_ID is missing


def _extract_text(result) -> str:
    """Pull the assistant's text out of a Strands AgentResult.

    Strands returns an AgentResult whose str() is the final assistant message.
    Fall back to str(result) for any shape we don't special-case.
    """
    try:
        message = getattr(result, "message", None)
        if isinstance(message, dict):
            parts = [
                block.get("text", "")
                for block in message.get("content", [])
                if isinstance(block, dict)
            ]
            text = "".join(parts).strip()
            if text:
                return text
    except Exception:  # be forgiving; the str() fallback below always works
        pass
    return str(result).strip()


st.set_page_config(page_title="Peculiar University Advisor (thick)", page_icon="🎓")

st.title("🎓 Peculiar University Advisor")
st.caption(
    "An assistant for academic advisors, running the Strands agent locally. "
    "Look up a student's live records, registrations, and degree plans, and "
    "cross-reference the course handbook for programs and prerequisites. Name "
    "the student ID in your question (e.g. \"student 100033\")."
)

# --- Session state -------------------------------------------------------
# One local agent per browser session preserves multi-turn conversation
# context. `messages` is the display transcript.
if "agent" not in st.session_state:
    st.session_state.agent = create_agent()
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar: mode + sample questions + controls ------------------------
with st.sidebar:
    if st.button("Clear conversation"):
        st.session_state.agent = create_agent()
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("Thick client → local Strands agent")
    st.caption(
        "This UI runs the agent in-process. Bedrock model, Knowledge Base "
        "retrieval, and the Athena tool all run locally with your credentials."
    )

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
            result = st.session_state.agent(prompt)
            response = _extract_text(result)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
