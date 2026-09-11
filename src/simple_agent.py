import os

from dotenv import load_dotenv
from strands import Agent

# Load variables from the repo-root .env file.
load_dotenv()

MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")

agent = Agent(
    model=MODEL_ID,
    system_prompt="You are a helpful university admission assistant. You help prospective students learn about courses, programs, and the application process.",
)

agent("What kind of help can you provide to a prospective student?")
