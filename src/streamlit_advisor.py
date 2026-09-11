"""Streamlit chat interface for the Peculiar University admission advisor.

The agent (Knowledge Base search + the ``query_student_db`` live-data tool) is
defined in ``advisor_agent``; this file is only the chat UI.

Run from the repo root with:

    streamlit run src/streamlit_advisor.py
"""

import streamlit as st

from advisor_agent import create_agent
from config import get_config

# Load configuration explicitly, up front, before building any agent.
get_config()

st.set_page_config(page_title="Peculiar University Advisor", page_icon="🎓")

st.title("🎓 Peculiar University Advisor")
st.caption(
    "An assistant for academic advisors. Look up a student's live records, "
    "registrations, and degree plans, and cross-reference the course handbook "
    "for programs and prerequisites. Name the student ID in your question "
    "(e.g. \"student 100033\")."
)

# --- Session state -------------------------------------------------------
# The agent holds its own conversation history, so we keep one agent per
# browser session. `messages` is the display transcript rendered on rerun.
if "agent" not in st.session_state:
    st.session_state.agent = create_agent()
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar: sample questions + controls -------------------------------
with st.sidebar:
    if st.button("Clear conversation"):
        st.session_state.agent = create_agent()
        st.session_state.messages = []
        st.rerun()

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
            response = str(result)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
