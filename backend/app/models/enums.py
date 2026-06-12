# app/models/enums.py
import enum


class ProjectStatus(str, enum.Enum):
    """
    Represents the current stage of a BuildFlow project in the workflow pipeline.

    State transition rules (enforced by ProjectService):
        IDEA              → DISCUSSION            (on project creation + chat session init)
        DISCUSSION        → REQUIREMENTS_READY    (on finalize_discussion)
        REQUIREMENTS_READY → ARCHITECTURE_READY   (on generate_architecture)
        ARCHITECTURE_READY → DIAGRAM_READY        (on generate_diagram)
        DIAGRAM_READY     → DIAGRAM_READY         (on diagram_review — stays, new version)
        DIAGRAM_READY     → CODE_READY            (on generate_code)
        any               → ARCHIVED              (soft archive, any time)

    Using str mixin so values serialize naturally in JSON and store
    as readable strings in PostgreSQL (not integers).
    """
    IDEA = "IDEA"
    DISCUSSION = "DISCUSSION"
    REQUIREMENTS_READY = "REQUIREMENTS_READY"
    ARCHITECTURE_READY = "ARCHITECTURE_READY"
    DIAGRAM_READY = "DIAGRAM_READY"
    CODE_READY = "CODE_READY"
    ARCHIVED = "ARCHIVED"


class MessageRole(str, enum.Enum):
    """
    Roles for messages stored in a ChatSession.

    - USER:      Message sent by the human user.
    - ASSISTANT: Message returned by the AI provider.
    - SYSTEM:    Injected context/instructions (not shown to user in UI,
                 but preserved for prompt reconstruction and context windows).
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"