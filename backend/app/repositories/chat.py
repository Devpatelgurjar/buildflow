# app/repositories/chat.py
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatSession, Message
from app.models.enums import MessageRole


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── ChatSession ───────────────────────────────────────────────

    async def create_session(self, project_id: uuid.UUID) -> ChatSession:
        session = ChatSession(project_id=project_id)
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_session_by_project(self, project_id: uuid.UUID) -> ChatSession | None:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.project_id == project_id)
        )
        return result.scalar_one_or_none()

    # ── Messages ──────────────────────────────────────────────────

    async def get_next_sequence(self, session_id: uuid.UUID) -> int:
        """
        Returns the next sequence number for a message in this session.
        Uses MAX(sequence_order) + 1 — safe for concurrent writes since
        session messages are user-scoped (one user per project).
        """
        result = await self.db.execute(
            select(func.max(Message.sequence_order)).where(
                Message.session_id == session_id
            )
        )
        current_max = result.scalar_one_or_none()
        return (current_max or 0) + 1

    async def create_message(
        self,
        session_id: uuid.UUID,
        role: MessageRole,
        content: str,
        token_count: int | None = None,
    ) -> Message:
        seq = await self.get_next_sequence(session_id)
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            sequence_order=seq,
            token_count=token_count,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def create_messages_bulk(
        self,
        session_id: uuid.UUID,
        messages: list[dict],  # [{"role": MessageRole, "content": str}]
    ) -> list[Message]:
        """
        Insert multiple messages atomically with correct sequence ordering.
        Used during project initialization (system prompt injection).
        """
        result = await self.db.execute(
            select(func.max(Message.sequence_order)).where(
                Message.session_id == session_id
            )
        )
        base_seq = (result.scalar_one_or_none() or 0)

        created = []
        for i, msg_data in enumerate(messages, start=1):
            message = Message(
                session_id=session_id,
                role=msg_data["role"],
                content=msg_data["content"],
                sequence_order=base_seq + i,
                token_count=msg_data.get("token_count"),
            )
            self.db.add(message)
            created.append(message)

        await self.db.flush()
        for m in created:
            await self.db.refresh(m)
        return created

    async def list_messages(
        self,
        session_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
        exclude_system: bool = False,
    ) -> tuple[list[Message], int]:
        """
        Returns (messages, total_count) ordered by sequence_order ASC.
        exclude_system=True hides injected system prompts from user-facing responses.
        """
        base_q = select(Message).where(Message.session_id == session_id)
        if exclude_system:
            base_q = base_q.where(Message.role != MessageRole.SYSTEM)

        count_result = await self.db.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            base_q
            .order_by(Message.sequence_order.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_full_history(self, session_id: uuid.UUID) -> list[Message]:
        """
        Returns ALL messages in order — used by AI context builder.
        No pagination here; the AI layer handles token budgeting.
        """
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.sequence_order.asc())
        )
        return list(result.scalars().all())

    async def get_last_n_messages(
        self, session_id: uuid.UUID, n: int
    ) -> list[Message]:
        """
        Returns the last N messages — used for sliding context windows.
        Returned in ascending order (oldest first) for correct prompt assembly.
        """
        subq = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.sequence_order.desc())
            .limit(n)
            .subquery()
        )
        result = await self.db.execute(
            select(Message)
            .join(subq, Message.id == subq.c.id)
            .order_by(Message.sequence_order.asc())
        )
        return list(result.scalars().all())