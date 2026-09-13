"""Configuration for the thick-client advisor app (self-contained).

Loads the repo-root ``.env`` once and returns an immutable ``Config``. Importing
this module has no side effects; callers invoke ``get_config()`` when ready.

This is a self-contained copy for the thick client (runs the Strands agent
locally). It intentionally does not import from ``src/``.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Repo root is two levels above this file (repo/streamlit-thick-client/config.py).
REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_ATHENA_LAMBDA_NAME = "education-athena-query"
DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-6"


@dataclass(frozen=True)
class Config:
    """Resolved application configuration for the local agent."""

    # Ordered by env-var name: ATHENA, AWS, BEDROCK, KNOWLEDGE.
    athena_lambda_name: str
    aws_region: str | None
    model_id: str
    knowledge_base_id: str


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Load `.env` (once) and return the resolved configuration.

    Raises ``KeyError`` if the required ``KNOWLEDGE_BASE_ID`` is missing.
    """
    load_dotenv(REPO_ROOT / ".env")

    return Config(
        athena_lambda_name=os.getenv("ATHENA_LAMBDA_NAME", DEFAULT_ATHENA_LAMBDA_NAME),
        aws_region=os.getenv("AWS_REGION"),
        model_id=os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID),
        knowledge_base_id=os.environ["KNOWLEDGE_BASE_ID"],
    )
