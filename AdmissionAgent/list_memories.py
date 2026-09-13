"""Inspect long-term memory records extracted by AgentCore Memory.

XXX / EDITORIAL NOTE: This script exists ONLY because the workshop (Module 8,
Exercise 2, Step 4) walks through it. It serves no purpose for the actual agent
— the deployed agent reads/writes memory on its own, and you can inspect the
exact same extracted facts/preferences in the Bedrock console under AgentCore >
Memory with zero code. It also drags in a pointless `.env` entry
(MEMORY_ADMISSION_AGENT_MEMORY_ID) that nothing else needs. Kept purely for
workshop parity; delete it and lose nothing. File under "much ado about nothing."


Lists the SEMANTIC facts and USER_PREFERENCE records for an actor. Run after a
few conversations so the strategies have had time to extract records
(extraction is asynchronous, ~10-30s after events are written).

Usage:
    python list_memories.py [ACTOR_ID]

Reads MEMORY_ADMISSION_AGENT_MEMORY_ID and AWS_DEFAULT_REGION from the
environment (or agentcore/.env.local). Get the memory id from `agentcore status`
(the value after `memory/` in the memory ARN).
"""

import os
import sys

import boto3

MEMORY_ID = os.environ["MEMORY_ADMISSION_AGENT_MEMORY_ID"]
ACTOR_ID = sys.argv[1] if len(sys.argv) > 1 else "default-actor"
REGION = os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION") or "us-west-2"

client = boto3.client("bedrock-agentcore", region_name=REGION)


def _print_records(title: str, namespace: str) -> None:
    print(f"=== {title} ===")
    resp = client.list_memory_records(memoryId=MEMORY_ID, namespace=namespace)
    for record in resp.get("memoryRecordSummaries", []):
        print(f"  - {record.get('content', {}).get('text', '')}")


_print_records("Semantic Facts", f"/users/{ACTOR_ID}/facts")
print()
_print_records("User Preferences", f"/users/{ACTOR_ID}/preferences/")
