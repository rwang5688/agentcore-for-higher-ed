"""CLI entry point for the Peculiar University admission advisor.

The agent itself is defined in ``advisor_agent``; this script loads config
first, then builds one agent and runs a sample query.
"""

from advisor_agent import create_agent
from config import get_config

if __name__ == "__main__":
    get_config()  # explicitly load configuration up front
    agent = create_agent()
    agent("Look up student 100016 and tell me what courses they've completed.")
