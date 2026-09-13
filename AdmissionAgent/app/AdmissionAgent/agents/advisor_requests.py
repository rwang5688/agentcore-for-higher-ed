"""Advisor Requests Agent specialist (Module 9), exposed as an @tool.

Action specialist with judgement: evaluates whether a student's request is
reasonable and complex enough to warrant a formal advisor request, checks the
student's record for supporting evidence via ``query_student_db``, and only then
submits via MCP tools on an AgentCore Gateway. Trivial/unsupported requests get
guidance instead of a submission.

The MCP tools (submit_advisor_request, list_advisor_requests) are served by the
gateway at ``ADVISOR_MCP_URL``. That URL only exists after the gateway is
deployed, so this tool degrades gracefully when the env var is absent.
"""

import os

from strands import Agent, tool
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

from model.load import load_model
from tools.query_student_db import query_student_db

ADVISOR_PROMPT = """
You are a student services evaluator for Peculiar University. A student is asking
to submit a request (course_override, advisor_meeting, program_change, or
special_consideration).

Do NOT blindly submit. Instead:
1. Assess whether the request is reasonable and complex enough to need a formal
   advisor request.
2. Use `query_student_db` to check the student's record for supporting evidence
   (GPA, completed courses, standing).
3. If justified, submit it with `submit_advisor_request` (include a clear
   description that summarizes your evaluation). Use `list_advisor_requests` to
   show existing requests when asked.
4. If the request is trivial or unsupported (e.g. asking for a meeting to learn
   something you can answer directly), DECLINE to submit and give helpful
   guidance instead.

Be concise. Ground decisions in the student's actual record.
"""


@tool
def route_to_advisor_requests(query: str, student_id: str | None = None) -> str:
    """Evaluate and, if justified, submit an advisor request on a student's behalf
    (course override, advisor meeting, program change, special consideration), or
    list a student's existing requests.

    Use for ACTION requests where the student wants something submitted/tracked —
    not for information lookups.

    Args:
        query: The student's request.
        student_id: Optional student ID (e.g. '100033').
    """
    mcp_url = os.getenv("ADVISOR_MCP_URL")
    if not mcp_url:
        return (
            "The advisor-requests system isn't configured yet (ADVISOR_MCP_URL "
            "is not set). Deploy the AgentCore Gateway and set ADVISOR_MCP_URL, "
            "then try again."
        )

    mcp_client = MCPClient(lambda: streamablehttp_client(mcp_url))
    with mcp_client:
        mcp_tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=load_model(),
            system_prompt=ADVISOR_PROMPT,
            tools=[*mcp_tools, query_student_db],
        )
        text = query if not student_id else f"[student_id={student_id}] {query}"
        return str(agent(text))
