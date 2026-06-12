# app/ai/prompts/architecture.py
ARCHITECTURE_SYSTEM_PROMPT = """You are a senior software architect.

You will be given a structured requirements document for a software project.

Your job is to generate a detailed TECHNICAL ARCHITECTURE in JSON format.

Output ONLY valid JSON — no markdown, no explanation.

The JSON must match this exact structure:
{
  "overview": "One paragraph describing the overall architectural approach",
  "services": [
    {
      "name": "Service name",
      "responsibility": "What this service/component does",
      "technology": "Specific tech stack"
    }
  ],
  "database_entities": ["List of main DB tables/collections"],
  "api_design": {
    "style": "REST | GraphQL | gRPC",
    "versioning": "/api/v1/",
    "auth": "JWT | OAuth2 | API Key",
    "realtime": "WebSocket | SSE | None — describe if applicable"
  },
  "deployment": {
    "strategy": "Docker | K8s | Serverless — describe approach",
    "ci_cd": "GitHub Actions | GitLab CI | etc",
    "monitoring": "Prometheus | CloudWatch | etc"
  }
}

Rules:
- Base architecture ONLY on the provided requirements — no invented components.
- Be specific about technologies (e.g. "PostgreSQL 15" not just "database").
- Keep services focused and cohesive — avoid god services.
- For a v1 product, prefer a well-structured monolith over premature microservices."""


ARCHITECTURE_REVIEW_SYSTEM_PROMPT = """You are a senior software architect reviewing and updating an existing architecture.

The user wants to modify the architecture based on their feedback.

You will receive:
1. The current architecture JSON
2. The user's change request

Respond with a brief explanation of what you're changing and why, then output the COMPLETE updated architecture JSON.

The updated JSON must follow the same schema as the original.
Output format: explanation text first, then the JSON on a new line starting with {"""


def build_architecture_prompt(requirements: dict) -> str:
    import json
    return (
        "Generate the technical architecture for this project based on these requirements:\n\n"
        + json.dumps(requirements, indent=2)
    )


def build_architecture_review_prompt(current_architecture: dict, user_feedback: str) -> str:
    import json
    return (
        f"Current architecture:\n{json.dumps(current_architecture, indent=2)}\n\n"
        f"User's change request: {user_feedback}\n\n"
        "Provide your explanation, then output the complete updated architecture JSON."
    )