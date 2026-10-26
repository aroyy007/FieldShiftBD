from datetime import datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

SenderType = Literal["farmer", "assistant", "system"]
MessageType = Literal["text", "image", "system"]
ChatIntent = Literal[
    "resource_inquiry",
    "task_inquiry",
    "weather_inquiry",
    "disease_inquiry",
    "crop_advice",
    "onboarding_help",
    "general_qa",
]


class ChatMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    message_type: MessageType = "text"
    attachment_key: str | None = None
    client_request_id: UUID | None = None


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender_type: SenderType
    message: str | None
    message_type: MessageType
    attachment_key: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farmland_id: UUID
    farmer_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: str | None = None


class ConversationDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farmland_id: UUID
    farmer_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageRead] = Field(default_factory=list)


class FarmContextSummary(BaseModel):
    farmland_name: str
    location: str | None = None
    soil_type: str | None = None
    irrigation: str | None = None
    active_crop: str | None = None
    growth_stage: str | None = None
    pending_tasks_count: int = 0
    open_problems_count: int = 0
    active_weather_alerts_count: int = 0
    onboarding_complete: bool = True
    next_onboarding_question: str | None = None


class ChatResponse(BaseModel):
    conversation_id: UUID
    farmer_message: ChatMessageRead
    assistant_message: ChatMessageRead
    intent: ChatIntent
    context_summary: FarmContextSummary
    suggested_actions: list[str] = Field(default_factory=list)
