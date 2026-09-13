class Config:
    # Stack name
    # Change this value if you want to create a new instance of the stack
    STACK_NAME = "AdvisorStreamlit"

    # Put your own custom value here to prevent ALB to accept requests from
    # other clients that CloudFront. You can choose any random string.
    CUSTOM_HEADER_VALUE = "PeculiarU_advisor_9f3c1a7b2e"

    # ID of Secrets Manager containing cognito parameters
    # When you delete a secret, you cannot create another one immediately
    # with the same name. Change this value if you destroy your stack and need
    # to recreate it with the same STACK_NAME.
    SECRETS_MANAGER_ID = f"{STACK_NAME}ParamCognitoSecret12345"

    # AWS region in which to deploy the CDK stack. Must match the region of the
    # deployed AgentCore runtime (KB, Athena Lambda, and runtime all live in
    # us-west-2 for this project).
    DEPLOYMENT_REGION = "us-west-2"

    # ARN of the deployed AgentCore runtime this app invokes. Get it from
    # `agentcore status` (or AdmissionAgent/agentcore/.cli/deployed-state.json).
    # This app is a THIN CLIENT: all agent logic runs on this runtime.
    AGENTCORE_RUNTIME_ARN = (
        "arn:aws:bedrock-agentcore:us-west-2:331773567763:runtime/"
        "AdmissionAgent_AdmissionAgent-zc7w8t847K"
    )
