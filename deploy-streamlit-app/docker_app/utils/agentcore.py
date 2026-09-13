"""AgentCore runtime client for the hosted advisor (thin-client business logic).

This is the same invoke logic as ``streamlit-thin-client``, packaged as a small
utility for the containerized (Cognito + ECS Fargate) deployment. It forwards a
prompt to the deployed AgentCore runtime via ``bedrock-agentcore``'s
``invoke_agent_runtime`` and returns the assistant text from the streamed
response. All agent intelligence runs on the backend, not in this container.
"""

import json

import boto3


class AgentCoreClient:
    """Thin wrapper over ``invoke_agent_runtime`` for one deployed runtime."""

    def __init__(self, runtime_arn: str, region: str):
        self.runtime_arn = runtime_arn
        self._client = boto3.client("bedrock-agentcore", region_name=region)

    @staticmethod
    def _extract_text(chunk: dict) -> str:
        """Pull assistant text out of one streamed Strands event.

        Text arrives as contentBlockDelta.delta.text. Tool-use / metadata events
        are ignored.
        """
        event = chunk.get("event", chunk)
        delta = (
            event.get("contentBlockDelta", {}).get("delta", {})
            if isinstance(event, dict)
            else {}
        )
        text = delta.get("text")
        return text if isinstance(text, str) else ""

    def invoke(self, prompt: str, session_id: str, actor_id: str) -> str:
        """Invoke the deployed runtime and return the full response text.

        Args:
            prompt: The user's message.
            session_id: AgentCore runtime session id (>= 33 chars). One per
                browser session keeps conversation context on the server.
            actor_id: Identity used to scope long-term memory. In the hosted
                deployment this is the authenticated Cognito user, so memory is
                per-user.
        """
        resp = self._client.invoke_agent_runtime(
            agentRuntimeArn=self.runtime_arn,
            runtimeSessionId=session_id,
            contentType="application/json",
            accept="application/json",
            payload=json.dumps({"prompt": prompt, "actor_id": actor_id}).encode("utf-8"),
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
                parts.append(self._extract_text(json.loads(line)))
            except (json.JSONDecodeError, AttributeError):
                continue

        text = "".join(parts).strip()
        return text or raw.strip()
