"""Explicit configuration loading for the advisor app.

Importing this module has no side effects: it does NOT read the environment or
load `.env`. Callers invoke ``get_config()`` when they are ready, which loads
the repo-root `.env` (once) and returns an immutable ``Config``. This keeps
env loading explicit and predictable rather than an import-time side effect.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Repo root is one level above this src/ file.
REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_ATHENA_LAMBDA_NAME = "education-athena-query"
DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-6"


@dataclass(frozen=True)
class Config:
    """Resolved application configuration."""

    # Ordered to match the env vars: AGENTCORE, ATHENA, AWS, BEDROCK, KNOWLEDGE.
    agentcore_runtime_arn: str | None
    athena_lambda_name: str
    aws_region: str | None
    model_id: str
    knowledge_base_id: str


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Load `.env` (once) and return the resolved configuration.

    Cached so repeated calls are cheap and consistent within a process. Raises
    ``KeyError`` if the required ``KNOWLEDGE_BASE_ID`` is missing (fail fast).
    """
    load_dotenv(REPO_ROOT / ".env")

    return Config(
        agentcore_runtime_arn=os.getenv("AGENTCORE_RUNTIME_ARN"),
        athena_lambda_name=os.getenv("ATHENA_LAMBDA_NAME", DEFAULT_ATHENA_LAMBDA_NAME),
        aws_region=os.getenv("AWS_REGION"),
        model_id=os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID),
        knowledge_base_id=os.environ["KNOWLEDGE_BASE_ID"],
    )
