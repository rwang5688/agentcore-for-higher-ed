"""Local Strands advisor agent (self-contained thick-client copy).

Single source of truth for the agent's configuration, the system prompt, and
the ``create_agent`` factory used by the thick-client Streamlit app. The agent
runs entirely in-process: Bedrock model + Knowledge Base retrieval + the
``query_student_db`` Athena tool. No AgentCore runtime is involved.
"""

from strands import Agent
from strands.memory import MemoryManager
from strands.vended_memory_stores import BedrockKnowledgeBaseStore

from config import get_config
from query_student_db import query_student_db

SYSTEM_PROMPT = """You are an assistant for academic advisors at Peculiar University.

You help advisors support their students with questions about courses,
programs, prerequisites, and degree requirements. You are talking to the
advisor, not the student, so refer to the student in the third person (e.g.
"this student has completed...") rather than addressing them directly.

Search the course handbook Knowledge Base before answering questions about
course content, programs, or prerequisites, and base those responses on what
you find there. Cite the specific course or program details you retrieve. If the
Knowledge Base does not contain the answer, say so plainly rather than guessing.

Look up live student data using the query_student_db tool, which runs SQL
against the education_workshop_db database. Use it to answer questions about
specific students: their records, enrolled program (derived from their
department), course registrations, grades, and degree plans. Write correct
Athena (Presto/Trino) SQL based on the schema in the tool's documentation. If a
query returns an error, read it, correct the SQL, and try again. If it returns
no rows, say so rather than inventing data.

When advising on what a student should take next, combine both sources: pull the
student's completed courses from the database, then check the handbook for
eligible courses and their prerequisites.
"""


def create_agent() -> Agent:
    """Build a fresh advisor agent with its own conversation history.

    The Knowledge Base store is read-only (search-only). Callers that need
    isolated multi-turn context (e.g. one agent per Streamlit session) should
    call this once and reuse the returned agent.
    """
    config = get_config()

    kb_store = BedrockKnowledgeBaseStore(
        name="course_handbook",
        description=(
            "Peculiar University course handbook: courses, programs, "
            "prerequisites, and degree requirements."
        ),
        config={
            "knowledge_base_id": config.knowledge_base_id,
            "region_name": config.aws_region,
        },
    )

    return Agent(
        model=config.model_id,
        system_prompt=SYSTEM_PROMPT,
        memory_manager=MemoryManager(stores=[kb_store]),
        tools=[query_student_db],
    )
