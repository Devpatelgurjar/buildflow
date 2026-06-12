# app/ai/prompts/diagram.py
DIAGRAM_SYSTEM_PROMPT = """You are a software architect generating Mermaid.js diagrams.

You will be given a technical architecture JSON.

Your job is to generate a Mermaid flowchart (graph TD) that visualizes the architecture.

Output ONLY the raw Mermaid diagram code — no markdown fences, no explanation.

Example format:
graph TD
    Client([Browser / Mobile])
    API[FastAPI Backend]
    DB[(PostgreSQL)]
    Client --> API
    API --> DB

Rules:
- Use graph TD (top-down) direction.
- Use meaningful node shapes: ([text]) for clients, [text] for services, [(text)] for databases, {text} for decisions.
- Show data flow with --> arrows.
- Keep it clean — max 15-20 nodes for readability.
- Include all major services from the architecture."""


DIAGRAM_REVIEW_SYSTEM_PROMPT = """You are a software architect reviewing and updating a Mermaid architecture diagram.

You will receive:
1. The current Mermaid diagram
2. The current architecture JSON  
3. The user's change request (e.g. "Add Redis cache", "Add CDN layer")

First, briefly explain what you're changing (2-3 sentences).
Then output the COMPLETE updated Mermaid diagram on a new line.

The diagram must remain valid Mermaid graph TD syntax."""


def build_diagram_prompt(architecture: dict) -> str:
    import json
    return (
        "Generate a Mermaid flowchart for this architecture:\n\n"
        + json.dumps(architecture, indent=2)
    )


def build_diagram_review_prompt(
    current_mermaid: str,
    current_architecture: dict,
    user_feedback: str,
) -> str:
    import json
    return (
        f"Current diagram:\n{current_mermaid}\n\n"
        f"Current architecture:\n{json.dumps(current_architecture, indent=2)}\n\n"
        f"Change request: {user_feedback}"
    )