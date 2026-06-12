# app/ai/providers/mock_provider.py
"""
Mock AI Provider — for local development without API keys.

Returns realistic hardcoded responses for every workflow stage.
Swap to real provider by changing AI_PROVIDER in .env.

Set in .env:
    AI_PROVIDER=mock
"""
import json
from typing import Any

from pydantic import BaseModel

from app.ai.base import AIProvider
from app.core.exceptions import AIResponseValidationException
from app.schemas.chat import ContextMessage


# ─────────────────────────────────────────────────────────────────
# Canned responses per workflow stage
# Detected by scanning the system prompt content
# ─────────────────────────────────────────────────────────────────

DISCUSSION_RESPONSE = """Great idea! A food delivery platform like Swiggy involves several interesting technical challenges. Let me ask a few clarifying questions to understand your vision better:

1. **Target market** — Are you building for a specific city, country, or globally from day one?
2. **User types** — Will you have customers, restaurant partners, and delivery agents all in the same platform?
3. **Key differentiator** — What makes your platform different from existing ones? (e.g. faster delivery, niche cuisine, subscription model)

Once I understand these, we can think through the core feature set together."""

REQUIREMENTS_MOCK = {
    "project_summary": "A food delivery platform connecting customers, restaurants, and delivery agents with real-time order tracking.",
    "functional_requirements": [
        {
            "id": "FR-001",
            "category": "Authentication",
            "title": "Multi-role user authentication",
            "description": "Support registration and login for three roles: Customer, Restaurant Owner, Delivery Agent. JWT-based auth with role-based access control.",
            "priority": "HIGH"
        },
        {
            "id": "FR-002",
            "category": "Restaurant",
            "title": "Restaurant and menu management",
            "description": "Restaurant owners can create/update their profile, manage menu items with categories, prices, availability, and images.",
            "priority": "HIGH"
        },
        {
            "id": "FR-003",
            "category": "Ordering",
            "title": "Cart and order placement",
            "description": "Customers can browse restaurants, add items to cart, apply coupons, and place orders with delivery address selection.",
            "priority": "HIGH"
        },
        {
            "id": "FR-004",
            "category": "Payments",
            "title": "Payment processing",
            "description": "Integrate payment gateway supporting credit/debit cards, UPI, and wallets. Handle payment confirmation and refunds.",
            "priority": "HIGH"
        },
        {
            "id": "FR-005",
            "category": "Tracking",
            "title": "Real-time order tracking",
            "description": "WebSocket-based live tracking showing order status: Placed → Confirmed → Preparing → Picked Up → Delivered.",
            "priority": "HIGH"
        },
        {
            "id": "FR-006",
            "category": "Notifications",
            "title": "Push and in-app notifications",
            "description": "Notify customers on order status changes, restaurants on new orders, and agents on delivery assignments.",
            "priority": "MEDIUM"
        },
        {
            "id": "FR-007",
            "category": "Admin",
            "title": "Admin dashboard",
            "description": "Super admin panel for managing users, restaurants, viewing analytics, handling disputes, and configuring platform settings.",
            "priority": "MEDIUM"
        },
        {
            "id": "FR-008",
            "category": "Reviews",
            "title": "Ratings and reviews",
            "description": "Customers can rate and review restaurants and delivery agents after order completion.",
            "priority": "LOW"
        }
    ],
    "non_functional_requirements": [
        {
            "category": "Performance",
            "description": "API response time < 200ms for 95th percentile. Support 10,000 concurrent users at launch."
        },
        {
            "category": "Scalability",
            "description": "Horizontally scalable stateless services. Database read replicas for heavy read workloads."
        },
        {
            "category": "Security",
            "description": "JWT auth, HTTPS only, input validation, rate limiting on auth endpoints, PCI-DSS compliance for payments."
        },
        {
            "category": "Availability",
            "description": "99.9% uptime SLA. Graceful degradation when payment gateway is unavailable."
        }
    ],
    "out_of_scope": [
        "Grocery or non-food delivery in v1",
        "Multi-language support in v1",
        "Native mobile apps (web-first)"
    ],
    "assumptions": [
        "Single city launch for v1",
        "Third-party payment gateway integration (not building payments from scratch)",
        "Delivery agents use a mobile web app, not native app"
    ]
}

ARCHITECTURE_MOCK = {
    "overview": "Monolithic FastAPI backend with clear service boundaries, PostgreSQL primary database, Redis for caching and real-time, and S3-compatible storage for media.",
    "services": [
        {
            "name": "API Gateway / FastAPI App",
            "responsibility": "Single deployable FastAPI application handling all HTTP and WebSocket traffic. Internally organized into feature modules.",
            "technology": "FastAPI, Python 3.12, Uvicorn"
        },
        {
            "name": "PostgreSQL Database",
            "responsibility": "Primary persistent store for users, restaurants, menus, orders, payments.",
            "technology": "PostgreSQL 15, SQLAlchemy 2.0, Alembic"
        },
        {
            "name": "Redis",
            "responsibility": "Session cache, real-time order status pub/sub, rate limiting, background job queue.",
            "technology": "Redis 7, Celery"
        },
        {
            "name": "Background Workers",
            "responsibility": "Async tasks: notification dispatch, order timeout handling, analytics aggregation.",
            "technology": "Celery + Redis broker"
        },
        {
            "name": "File Storage",
            "responsibility": "Restaurant and menu item images.",
            "technology": "AWS S3 or MinIO (S3-compatible)"
        },
        {
            "name": "Payment Gateway",
            "responsibility": "External service for processing transactions.",
            "technology": "Razorpay / Stripe (abstracted behind PaymentProvider interface)"
        }
    ],
    "database_entities": [
        "User (with role: customer/restaurant/agent/admin)",
        "RestaurantProfile",
        "MenuItem",
        "MenuCategory",
        "Order",
        "OrderItem",
        "DeliveryAssignment",
        "Payment",
        "Review",
        "Notification"
    ],
    "api_design": {
        "style": "RESTful",
        "versioning": "/api/v1/",
        "auth": "JWT Bearer tokens",
        "realtime": "WebSocket for order tracking (/ws/orders/{order_id})"
    },
    "deployment": {
        "strategy": "Docker containers on a single VM for v1, migrate to Kubernetes for scale",
        "ci_cd": "GitHub Actions",
        "monitoring": "Prometheus + Grafana"
    }
}

DIAGRAM_MOCK = """graph TD
    Client([Customer / Restaurant / Agent])
    LB[Load Balancer / Nginx]
    API[FastAPI Application]
    WS[WebSocket Handler]
    DB[(PostgreSQL)]
    CACHE[(Redis)]
    WORKER[Celery Workers]
    STORAGE[S3 Storage]
    PAYMENT[Payment Gateway]

    Client -->|HTTPS REST| LB
    Client -->|WSS| LB
    LB --> API
    LB --> WS
    API --> DB
    API --> CACHE
    API --> STORAGE
    API --> PAYMENT
    API -->|Enqueue tasks| WORKER
    WORKER --> DB
    WORKER --> CACHE
    WS --> CACHE
    CACHE -->|Pub/Sub order updates| WS"""

DIAGRAM_REVIEW_RESPONSE = """Good suggestion! Adding Redis Cache to the architecture makes sense for:

1. **Restaurant menu caching** — menus change infrequently but are read constantly
2. **Session/token storage** — faster than DB lookups on every request  
3. **Rate limiting counters** — atomic Redis increments are perfect for this

I've updated the architecture to include Redis as a first-class component with explicit caching layers. The diagram has been regenerated with the new version showing Redis connections to both the API layer and the WebSocket handler."""

CODEGEN_MOCK = {
    "language": "python",
    "framework": "fastapi",
    "artifacts": [
        {
            "filename": "models/order.py",
            "language": "python",
            "description": "SQLAlchemy Order and OrderItem models",
            "content": '''import uuid
from enum import Enum
from sqlalchemy import String, ForeignKey, Numeric, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class OrderStatus(str, Enum):
    PLACED = "PLACED"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class Order(Base):
    __tablename__ = "orders"
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("restaurant_profiles.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus, name="orderstatus"), default=OrderStatus.PLACED)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    delivery_address: Mapped[str] = mapped_column(String(500), nullable=False)
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    menu_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("menu_items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    order: Mapped["Order"] = relationship("Order", back_populates="items")
'''
        },
        {
            "filename": "routers/orders.py",
            "language": "python",
            "description": "Order placement and tracking endpoints",
            "content": '''from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def place_order(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """Place a new food order."""
    pass  # Implementation goes here

@router.get("/{order_id}")
async def get_order(order_id: str, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get order details and current status."""
    pass

@router.patch("/{order_id}/status")
async def update_order_status(order_id: str, db: AsyncSession = Depends(get_db)):
    """Update order status (restaurant/agent only)."""
    pass
'''
        },
        {
            "filename": "websockets/order_tracking.py",
            "language": "python",
            "description": "WebSocket endpoint for real-time order tracking",
            "content": '''from fastapi import WebSocket, WebSocketDisconnect
import asyncio

class OrderTrackingManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, order_id: str, websocket: WebSocket):
        await websocket.accept()
        if order_id not in self.connections:
            self.connections[order_id] = []
        self.connections[order_id].append(websocket)

    def disconnect(self, order_id: str, websocket: WebSocket):
        if order_id in self.connections:
            self.connections[order_id].remove(websocket)

    async def broadcast_status(self, order_id: str, status: str):
        for ws in self.connections.get(order_id, []):
            await ws.send_json({"order_id": order_id, "status": status})

manager = OrderTrackingManager()
'''
        }
    ],
    "setup_instructions": "1. Run alembic upgrade head\n2. Configure REDIS_URL in .env\n3. Start Celery worker: celery -A app.worker worker --loglevel=info\n4. Start server: uvicorn app.main:app --reload"
}


class MockAIProvider(AIProvider):
    """
    Local development provider — no API key needed.

    Detects the workflow stage from the system prompt and returns
    a realistic mock response for that stage.

    Switch to real provider by setting AI_PROVIDER=openai in .env
    """

    provider_name = "mock"

    def _detect_stage(self, system_prompt: str | None) -> str:
        if not system_prompt:
            return "discussion"
        sp = system_prompt.lower()
        if "requirement" in sp:
            return "requirements"
        if "architecture" in sp:
            return "architecture"
        if "diagram" in sp and "review" in sp:
            return "diagram_review"
        if "diagram" in sp or "mermaid" in sp:
            return "diagram"
        if "code" in sp or "generate" in sp:
            return "codegen"
        return "discussion"

    async def complete(
        self,
        messages: list[ContextMessage],
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        stage = self._detect_stage(system_prompt)

        if stage == "requirements":
            return json.dumps(REQUIREMENTS_MOCK)
        if stage == "architecture":
            return json.dumps(ARCHITECTURE_MOCK)
        if stage == "diagram":
            return DIAGRAM_MOCK
        if stage == "diagram_review":
            return DIAGRAM_REVIEW_RESPONSE
        if stage == "codegen":
            return json.dumps(CODEGEN_MOCK)

        # Default: discussion
        return DISCUSSION_RESPONSE

    async def complete_structured(
        self,
        messages: list[ContextMessage],
        response_schema: type[BaseModel],
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> BaseModel:
        stage = self._detect_stage(system_prompt)

        if stage == "requirements":
            raw = json.dumps(REQUIREMENTS_MOCK)
        elif stage == "architecture":
            raw = json.dumps(ARCHITECTURE_MOCK)
        elif stage == "codegen":
            raw = json.dumps(CODEGEN_MOCK)
        else:
            raw = json.dumps(REQUIREMENTS_MOCK)  # safe fallback

        try:
            return response_schema.model_validate(json.loads(raw))
        except Exception as e:
            raise AIResponseValidationException(
                f"Mock provider failed schema validation for {response_schema.__name__}: {e}"
            )