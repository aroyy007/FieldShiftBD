"""Module 5 — Open-Ended Conversational Layer API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.models.chat import ChatMessage, Conversation
from app.models.core import Farmland
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatResponse,
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
)
from app.services.chat_engine import handle_farmer_message

router = APIRouter(prefix="/farmlands", tags=["Conversational Layer — Module 5"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentFarmerId = Annotated[UUID, Depends(get_current_farmer_id)]


def _require_farmland(db: Session, farmland_id: UUID, farmer_id: UUID) -> Farmland:
    farmland = db.scalar(
        select(Farmland).where(
            Farmland.id == farmland_id, Farmland.farmer_id == farmer_id
        )
    )
    if farmland is None:
        raise HTTPException(status_code=404, detail="Farmland not found")
    return farmland


@router.post(
    "/{farmland_id}/conversations",
    response_model=ConversationDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    farmland_id: UUID,
    payload: ConversationCreate,
    farmer_id: CurrentFarmerId,
    db: DbSession,
):
    """Create a new chat conversation thread for a farmland."""
    _require_farmland(db, farmland_id, farmer_id)

    conversation = Conversation(
        farmland_id=farmland_id,
        farmer_id=farmer_id,
        title=payload.title or "New conversation",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ConversationDetail(
        id=conversation.id,
        farmland_id=conversation.farmland_id,
        farmer_id=conversation.farmer_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[],
    )


@router.get(
    "/{farmland_id}/conversations",
    response_model=list[ConversationSummary],
)
def list_conversations(
    farmland_id: UUID,
    farmer_id: CurrentFarmerId,
    db: DbSession,
):
    """List all conversations for a farmland."""
    _require_farmland(db, farmland_id, farmer_id)

    conversations = db.scalars(
        select(Conversation)
        .where(
            Conversation.farmland_id == farmland_id,
            Conversation.farmer_id == farmer_id,
        )
        .order_by(Conversation.updated_at.desc())
    ).all()

    summaries = []
    for conv in conversations:
        msg_count = db.scalar(
            select(func.count(ChatMessage.id)).where(
                ChatMessage.conversation_id == conv.id
            )
        ) or 0
        last_msg = db.scalar(
            select(ChatMessage.message)
            .where(ChatMessage.conversation_id == conv.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        summaries.append(
            ConversationSummary(
                id=conv.id,
                farmland_id=conv.farmland_id,
                farmer_id=conv.farmer_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=msg_count,
                last_message=last_msg,
            )
        )
    return summaries


@router.get(
    "/{farmland_id}/conversations/{conversation_id}",
    response_model=ConversationDetail,
)
def get_conversation(
    farmland_id: UUID,
    conversation_id: UUID,
    farmer_id: CurrentFarmerId,
    db: DbSession,
):
    """Get conversation details and full message history."""
    _require_farmland(db, farmland_id, farmer_id)

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.farmland_id == farmland_id,
            Conversation.farmer_id == farmer_id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.created_at.asc())
    ).all()

    return ConversationDetail(
        id=conversation.id,
        farmland_id=conversation.farmland_id,
        farmer_id=conversation.farmer_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[ChatMessageRead.model_validate(m) for m in messages],
    )


@router.post(
    "/{farmland_id}/conversations/{conversation_id}/messages",
    response_model=ChatResponse,
)
def send_message(
    farmland_id: UUID,
    conversation_id: UUID,
    payload: ChatMessageCreate,
    farmer_id: CurrentFarmerId,
    db: DbSession,
):
    """Send a message, run intent analysis & context grounding, and return AI response."""
    _require_farmland(db, farmland_id, farmer_id)

    try:
        return handle_farmer_message(
            db=db,
            farmland_id=farmland_id,
            farmer_id=farmer_id,
            conversation_id=conversation_id,
            message_text=payload.message,
            attachment_key=payload.attachment_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{farmland_id}/chat",
    response_model=ChatResponse,
)
def quick_chat(
    farmland_id: UUID,
    payload: ChatMessageCreate,
    farmer_id: CurrentFarmerId,
    db: DbSession,
):
    """Convenience endpoint: sends message to the latest conversation or creates one."""
    _require_farmland(db, farmland_id, farmer_id)

    latest_conv = db.scalar(
        select(Conversation)
        .where(
            Conversation.farmland_id == farmland_id,
            Conversation.farmer_id == farmer_id,
        )
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )

    if not latest_conv:
        latest_conv = Conversation(
            farmland_id=farmland_id,
            farmer_id=farmer_id,
            title="Chat",
        )
        db.add(latest_conv)
        db.commit()
        db.refresh(latest_conv)

    return handle_farmer_message(
        db=db,
        farmland_id=farmland_id,
        farmer_id=farmer_id,
        conversation_id=latest_conv.id,
        message_text=payload.message,
        attachment_key=payload.attachment_key,
    )