"""Configuration for the thin-client advisor app (self-contained).

Loads the repo-root ``.env`` once and returns an immutable ``Config``. Importing
this module has no side effects; callers invoke ``get_config()`` when ready.

The thin client only needs to know WHICH deployed AgentCore runtime to call and
in which region. All agent logic runs on the backend, so this is a strict subset
of the thick client's config. Self-contained: does not import from ``src/``.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Repo root is two levels above this file (repo/streamlit-thin-client/config.py).
REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    """Resolved configuration for invoking the deployed AgentCore runtime."""

    # Ordered by env-var name: AGENTCORE, AWS.
    agentcore_runtime_arn: str | None
    aws_region: str | None


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Load `.env` (once) and return the resolved configuration."""
    load_dotenv(REPO_ROOT / ".env")

    return Config(
        agentcore_runtime_arn=os.getenv("AGENTCORE_RUNTIME_ARN"),
        aws_region=os.getenv("AWS_REGION"),
    )
