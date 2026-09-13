import logging
import os
from typing import Any
from collections import OrderedDict
from strands import Agent
from strands.agent.conversation_manager.null_conversation_manager import NullConversationManager
from strands.memory import MemoryManager
from strands.vended_memory_stores import BedrockKnowledgeBaseStore
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
from tools.query_student_db import query_student_db
from memory.session import build_session_manager

logging.basicConfig(level=logging.INFO)

# Course handbook Knowledge Base, search-only (no writable=True). Uses the core
# strands BedrockKnowledgeBaseStore — same approach as src/advisor_agent.py — so
# we DON'T need the deprecated `retrieve` tool or the strands-agents-tools
# package. KB ID comes from KNOWLEDGE_BASE_ID (no STRANDS_-prefixed var).
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

app = BedrockAgentCoreApp()
log = app.logger

DEFAULT_SYSTEM_PROMPT = """
You are Alex, a university Admission Advisor for Peculiar University's College of
Engineering. You help prospective and current students with course information and
their academic records.

You can:
- Search the course handbook Knowledge Base (attached automatically). Use it for
  questions about courses, prerequisites, programs, electives, and handbook/catalog
  content, and cite what you find.
- `query_student_db`: run read-only SQL against the `education_workshop_db` Athena
  database. Use this for live student records — enrollments, completed courses,
  GPA, degree plans, schedules, and related structured data.

Guidance:
- Some questions need both sources (e.g. "what should student 100016 take next?"
  needs the student's record AND handbook data).
- Ground every answer in what you retrieve/query. Do not invent course names,
  prerequisites, grades, or student data.
- Be concise, accurate, and helpful.
"""


# Only the Athena tool; KB search is provided via the memory_manager (KB store).
tools = [query_student_db]

_INLINE_FUNCTION_NAMES = set()


def _make_conversation_manager():
    return NullConversationManager()

# Reuses one Agent per session_id so each session keeps its own in-process
# conversation history (best-effort; resets on cold start). The cache is bounded
# to 128 sessions with LRU eviction (least-recently-used is dropped and its
# history reset) so a single process serving many sessions cannot leak history
# between them or grow without limit. For durable history, attach a session manager.
def agent_factory():
    cache = OrderedDict()
    def get_or_create_agent(session_id, actor_id):
        if session_id in cache:
            cache.move_to_end(session_id)
            return cache[session_id]
        if len(cache) >= 128:
            cache.popitem(last=False)
        # AgentCore Memory (short-term + long-term). None during local dev when
        # MEMORY_ADMISSION_AGENT_MEMORY_ID isn't set; the agent still runs, just
        # without cross-session memory.
        session_manager = build_session_manager(session_id, actor_id)
        agent_kwargs = dict(
            model=load_model(),
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            tools=tools,
            memory_manager=MemoryManager(stores=[_kb_store]),
            hooks=[],
        )
        if session_manager is not None:
            agent_kwargs["session_manager"] = session_manager
        else:
            agent_kwargs["conversation_manager"] = _make_conversation_manager()
        cache[session_id] = Agent(**agent_kwargs)
        return cache[session_id]
    return get_or_create_agent
get_or_create_agent = agent_factory()


def strip_trailing_tool_use(messages: Any) -> list[dict]:
    """Strip toolUse blocks from the tail until the last message has none."""
    if not isinstance(messages, list):
        raise ValueError("messages must be a list")

    messages = list(messages)
    while messages:
        last = messages[-1]
        if not isinstance(last, dict):
            raise ValueError("each message must be an object")
        original_content = last.get("content", [])
        if not isinstance(original_content, list) or not all(isinstance(block, dict) for block in original_content):
            raise ValueError("each message content value must be a list of content blocks")

        content = [block for block in original_content if "toolUse" not in block]
        if len(content) == len(original_content):
            break
        if content:
            messages[-1] = {**last, "content": content}
            break
        messages.pop()

    return messages


def _extract_prompt(payload: dict):
    """Accept validated harness messages, tool results, or a plain prompt string."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    if "messages" in payload:
        return strip_trailing_tool_use(payload["messages"])
    if "tool_results" in payload:
        tool_results = payload["tool_results"]
        if not isinstance(tool_results, list) or not all(
            isinstance(tool_result, dict) and isinstance(tool_result.get("toolUseId"), str)
            for tool_result in tool_results
        ):
            raise ValueError("tool_results must contain objects with a toolUseId string")
        return [{"role": "user", "content": [{"toolResult": {
            "toolUseId": tr["toolUseId"],
            "status": tr.get("status", "success"),
            "content": tr.get("content", []),
        }} for tr in tool_results]}]
    prompt = payload.get("prompt", "")
    if not isinstance(prompt, str):
        raise ValueError("prompt must be a string")
    return prompt


def _has_inline_function_call(messages) -> bool:
    """Return True if messages contains an assistant toolUse for an inline function tool."""
    if not _INLINE_FUNCTION_NAMES or not isinstance(messages, list):
        return False
    for msg in messages:
        if msg.get("role") == "assistant":
            for block in msg.get("content", []):
                if isinstance(block, dict) and block.get("toolUse", {}).get("name") in _INLINE_FUNCTION_NAMES:
                    return True
    return False


def _is_inline_function_call(event: dict) -> bool:
    """Check if a contentBlockStart event is for an inline function tool."""
    if not _INLINE_FUNCTION_NAMES:
        return False
    cbs = event.get("contentBlockStart", {})
    start = cbs.get("start", {})
    tool_use = start.get("toolUse") if isinstance(start, dict) else None
    return tool_use is not None and tool_use.get("name") in _INLINE_FUNCTION_NAMES



@app.entrypoint
async def invoke(payload, context):
    log.info("Invoking Agent.....")


    session_id = getattr(context, 'session_id', None) or 'default-session'
    # actor_id scopes long-term memory per user. Prefer an explicit payload
    # value (e.g. a student id); fall back to a default actor.
    actor_id = 'default-actor'
    if isinstance(payload, dict):
        actor_id = payload.get('actor_id') or actor_id
    agent = get_or_create_agent(session_id, actor_id)

    prompt = _extract_prompt(payload)


    async for event in agent.stream_async(
        prompt,
    ):
        if not isinstance(event, dict) or "event" not in event:
            continue
        cbs = event["event"].get("contentBlockStart")
        if cbs is not None and not cbs.get("start"):
            continue
        yield event


if __name__ == "__main__":
    app.run()
