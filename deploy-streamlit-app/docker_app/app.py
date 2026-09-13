"""Hosted Peculiar University advisor (Cognito + ECS Fargate THIN client).

Phase 3 of the demo roadmap: the thin-client advisor UI, gated behind Cognito
authentication and deployed on ECS Fargate (ALB + CloudFront) via CDK.

After a user signs in through Cognito, each prompt is forwarded to the deployed
AgentCore runtime via ``invoke_agent_runtime`` (see ``utils/agentcore.py``). No
agent logic runs in this container. The authenticated Cognito username is passed
as ``actor_id`` so the backend scopes long-term memory per user.
"""

import uuid

import streamlit as st

from config_file import Config
from utils.agentcore import AgentCoreClient
from utils.auth import Auth

# --- Cognito authentication ---------------------------------------------
authenticator = Auth.get_authenticator(Config.SECRETS_MANAGER_ID, Config.DEPLOYMENT_REGION)

is_logged_in = authenticator.login()
if not is_logged_in:
    st.stop()


def logout():
    authenticator.logout()


# --- AgentCore client (one per process) ---------------------------------
@st.cache_resource
def _agentcore() -> AgentCoreClient:
    return AgentCoreClient(Config.AGENTCORE_RUNTIME_ARN, Config.DEPLOYMENT_REGION)


st.set_page_config(page_title="Peculiar University Advisor", page_icon="🎓")

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

username = authenticator.get_username()

# --- Sidebar: identity + controls + samples -----------------------------
with st.sidebar:
    st.text(f"Welcome,\n{username}")
    st.button("Logout", "logout_btn", on_click=logout)

    if st.button("Clear conversation"):
        st.session_state.session_id = f"session-{uuid.uuid4().hex}"
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("Hosted thin client → AgentCore")
    st.caption("Authenticated via Cognito. Each prompt is sent to the deployed "
               "AgentCore runtime; memory is scoped to your user.")
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
            response = _agentcore().invoke(
                prompt,
                session_id=st.session_state.session_id,
                actor_id=username,
            )
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
