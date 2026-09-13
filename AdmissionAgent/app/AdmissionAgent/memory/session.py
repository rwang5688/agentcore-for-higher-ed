"""AgentCore Memory session manager wiring for the Admission Agent.

Builds an ``AgentCoreMemorySessionManager`` from the memory ID that AgentCore
injects as ``MEMORY_ADMISSION_AGENT_MEMORY_ID`` after ``agentcore deploy``.

- Short-term memory: conversation events per session (session_id).
- Long-term memory: the retrieval_config searches the SEMANTIC facts namespace
  and the USER_PREFERENCE namespace for the actor, injecting matches into the
  agent's context each turn.

Memory requires deployed AWS infrastructure, so ``build_session_manager`` returns
``None`` when the memory ID env var is absent (e.g. local ``agentcore dev``),
letting main.py run without it.
"""

import os

from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)

MEMORY_ID_ENV = "MEMORY_ADMISSION_AGENT_MEMORY_ID"


def build_session_manager(session_id: str, actor_id: str):
    """Return an AgentCoreMemorySessionManager, or None if memory isn't provisioned.

    Long-term retrieval searches two namespaces scoped to the actor:
      - /users/{actor_id}/facts        (SEMANTIC strategy)
      - /users/{actor_id}/preferences/ (USER_PREFERENCE strategy)
    """
    memory_id = os.getenv(MEMORY_ID_ENV)
    if not memory_id:
        return None

    retrieval_config = {
        f"/users/{actor_id}/facts": RetrievalConfig(top_k=5, relevance_score=0.5),
        f"/users/{actor_id}/preferences": RetrievalConfig(top_k=5, relevance_score=0.5),
    }

    config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=session_id,
        actor_id=actor_id,
        retrieval_config=retrieval_config,
        # Our entrypoint drives the agent with stream_async, so offload the
        # per-turn memory boto3 calls off the event loop.
        async_mode=True,
    )
    return AgentCoreMemorySessionManager(config)
