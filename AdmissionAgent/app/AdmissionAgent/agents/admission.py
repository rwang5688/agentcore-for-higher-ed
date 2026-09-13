"""Admission Agent specialist (Module 9), exposed as an @tool.

Information-lookup specialist: answers course/handbook questions (via the
course-handbook Knowledge Base) and student-record questions (via the
`query_student_db` Athena tool). The orchestrator in main.py delegates to this
via ``route_to_admission``.
"""

import os

from strands import Agent, tool
from strands.memory import MemoryManager
from strands.vended_memory_stores import BedrockKnowledgeBaseStore

from model.load import load_model
from tools.query_student_db import query_student_db

# Course handbook KB, search-only. Same approach as the single-agent build and
# src/advisor_agent.py (no deprecated retrieve tool / no strands-agents-tools).
_kb_store = BedrockKnowledgeBaseStore(
    name="course_handbook",
    description=(
        "Peculiar University course handbook: courses, programs, "
        "prerequisites, and degree requirements."
    ),
    config={
        "knowledge_base_id": os.environ["KNOWLEDGE_BASE_ID"],
        "region_name": os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION"),
    },
)

ADMISSION_PROMPT = """
You are Alex, a university Admission Advisor for Peculiar University's College of
Engineering.

- Use the course handbook Knowledge Base (attached automatically) for questions
  about courses, prerequisites, programs, and electives; cite what you find.
- Use `query_student_db` (read-only SQL against `education_workshop_db`) for live
  student records: enrollments, completed courses, GPA, degree plans, schedules.

Ground every answer in what you retrieve/query. Do not invent course names,
prerequisites, grades, or student data. Be concise and accurate.
"""


@tool
def route_to_admission(query: str, student_id: str | None = None) -> str:
    """Answer a student information lookup: course handbook content and/or a
    student's academic records.

    Use for questions about courses, prerequisites, programs, electives, and a
    student's own record (completed courses, GPA, degree plan, eligibility).

    Args:
        query: The student's question.
        student_id: Optional student ID to scope record lookups (e.g. '100016').
    """
    agent = Agent(
        model=load_model(),
        system_prompt=ADMISSION_PROMPT,
        tools=[query_student_db],
        memory_manager=MemoryManager(stores=[_kb_store]),
    )
    text = query if not student_id else f"[student_id={student_id}] {query}"
    return str(agent(text))
