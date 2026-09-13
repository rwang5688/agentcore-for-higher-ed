import json
import os

import boto3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("advisor-requests")

LAMBDA_NAME = os.environ.get("ADVISOR_REQUESTS_LAMBDA", "education-advisor-requests")
client = boto3.client(
    "lambda",
    region_name=os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION", "us-west-2"),
)


def _invoke_lambda(payload: dict) -> dict:
    response = client.invoke(
        FunctionName=LAMBDA_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )
    result = json.loads(response["Payload"].read())
    body = json.loads(result["body"]) if isinstance(result.get("body"), str) else result
    return body.get("result", body)


@mcp.tool()
def submit_advisor_request(student_id: str, request_type: str, description: str) -> str:
    """Submit an advisor request on behalf of a student.

    Args:
        student_id: The student's ID (e.g. '100016')
        request_type: one of course_override, advisor_meeting, program_change, special_consideration
        description: Detailed description of what the student is requesting
    """
    result = _invoke_lambda({
        "action": "submit_request",
        "student_id": student_id,
        "request_type": request_type,
        "description": description,
    })
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def list_advisor_requests(student_id: str) -> str:
    """List all advisor requests for a student.

    Args:
        student_id: The student's ID (e.g. '100016')
    """
    result = _invoke_lambda({
        "action": "list_requests",
        "student_id": student_id,
    })
    return json.dumps(result, indent=2, default=str)


if __name__ == "__main__":
    mcp.run(transport="stdio")
