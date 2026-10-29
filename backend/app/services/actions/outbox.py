"""Transaction-aware outbox write boundary; it never commits or sends."""

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import DeliveryOutbox


class OutboxWriter(Protocol):
    def enqueue(
        self,
        session: Session,
        *,
        receipt_id: UUID,
        event_type: str,
        idempotency_key: str,
        payload: dict[str, Any],
        available_at: datetime,
    ) -> DeliveryOutbox: ...


class TransactionalOutboxWriter:
    """Persist an event in the caller's transaction without external I/O."""

    def enqueue(
        self,
        session: Session,
        *,
        receipt_id: UUID,
        event_type: str,
        idempotency_key: str,
        payload: dict[str, Any],
        available_at: datetime,
    ) -> DeliveryOutbox:
        if not event_type.strip() or not idempotency_key.strip():
            raise ValueError("outbox event type and idempotency key are required")
        row = DeliveryOutbox(
            receipt_id=receipt_id,
            event_type=event_type,
            idempotency_key=idempotency_key,
            payload=payload,
            status="pending",
            attempts=0,
            available_at=available_at,
            created_at=available_at,
        )
        session.add(row)
        session.flush()
        return row
