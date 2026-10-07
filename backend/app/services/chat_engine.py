from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chat import ChatMessage, Conversation
from app.models.core import AgriculturalKnowledge, Crop, Farmer, Farmland
from app.models.profile import FarmerProfile
from app.models.season import GrowthStage, Season, SeasonPlan
from app.models.state import Problem, Task
from app.models.weather import WeatherAlert
from app.schemas.chat import (
    ChatIntent,
    ChatMessageRead,
    ChatResponse,
    FarmContextSummary,
)

logger = logging.getLogger(__name__)


@dataclass
class AggregatedFarmContext:
    farmland: Farmland
    farmer: Farmer
    profile: FarmerProfile | None
    active_season: Season | None
    active_crop: Crop | None
    growth_stage: GrowthStage | None
    pending_tasks: list[Task]
    open_problems: list[Problem]
    recent_weather_alerts: list[WeatherAlert]
    knowledge_snippets: list[str]
    missing_onboarding_fields: list[str]


def aggregate_farmland_context(
    db: Session, farmland_id: UUID, farmer_id: UUID
) -> AggregatedFarmContext:
    farmland = db.scalar(
        select(Farmland).where(
            Farmland.id == farmland_id, Farmland.farmer_id == farmer_id
        )
    )
    if farmland is None:
        raise ValueError("Farmland not found or access denied")

    farmer = db.scalar(select(Farmer).where(Farmer.id == farmer_id))
    profile = db.scalar(
        select(FarmerProfile).where(FarmerProfile.farmer_id == farmer_id)
    )

    # Active Season & Crop & Stage
    active_season = db.scalar(
        select(Season)
        .where(Season.farmland_id == farmland_id, Season.status == "active")
        .order_by(Season.updated_at.desc())
        .limit(1)
    )

    active_crop = None
    growth_stage = None
    if active_season:
        active_crop = db.scalar(
            select(Crop).where(Crop.id == active_season.crop_id)
        )
        if active_season.current_growth_stage_id:
            growth_stage = db.scalar(
                select(GrowthStage).where(
                    GrowthStage.id == active_season.current_growth_stage_id
                )
            )

    # Tasks
    tasks = []
    if active_season:
        tasks = list(
            db.scalars(
                select(Task)
                .where(
                    Task.season_id == active_season.id,
                    Task.status.in_(["pending", "in_progress"]),
                )
                .order_by(Task.due_at.asc().nulls_last())
                .limit(5)
            ).all()
        )

    # Open Problems
    open_problems = list(
        db.scalars(
            select(Problem)
            .where(
                Problem.farmland_id == farmland_id,
                Problem.status.in_(["open", "investigating"]),
            )
            .order_by(Problem.created_at.desc())
            .limit(5)
        ).all()
    )

    # Recent Weather Alerts
    weather_alerts = list(
        db.scalars(
            select(WeatherAlert)
            .where(
                WeatherAlert.farmland_id == farmland_id,
                WeatherAlert.status.in_(["new", "read"]),
            )
            .order_by(WeatherAlert.created_at.desc())
            .limit(3)
        ).all()
    )

    # Agricultural Knowledge
    knowledge_snippets: list[str] = []
    if active_crop:
        records = db.scalars(
            select(AgriculturalKnowledge)
            .where(
                AgriculturalKnowledge.crop_id == active_crop.id,
                AgriculturalKnowledge.review_status == "approved",
            )
            .limit(5)
        ).all()
        for r in records:
            content_dict = r.content if isinstance(r.content, dict) else {}
            factor = content_dict.get("factor") or r.category
            knowledge_snippets.append(
                f"[{r.category}/{factor}] {json.dumps(content_dict)}"
            )

    # Missing onboarding fields
    missing_fields = []
    if not farmland.soil_type:
        missing_fields.append("soil_type")
    if farmland.irrigation_available is None:
        missing_fields.append("irrigation_available")
    if not farmland.water_source:
        missing_fields.append("water_source")
    if not farmland.farming_method:
        missing_fields.append("farming_method")

    return AggregatedFarmContext(
        farmland=farmland,
        farmer=farmer,
        profile=profile,
        active_season=active_season,
        active_crop=active_crop,
        growth_stage=growth_stage,
        pending_tasks=tasks,
        open_problems=open_problems,
        recent_weather_alerts=weather_alerts,
        knowledge_snippets=knowledge_snippets,
        missing_onboarding_fields=missing_fields,
    )


def classify_intent(message_text: str) -> ChatIntent:
    text = message_text.lower()
    if any(
        w in text
        for w in [
            "disease",
            "leaf",
            "pest",
            "spots",
            "yellow",
            "blight",
            "fungus",
            "sick",
            "damage",
            "পোকা",
            "রোগ",
            "দাগ",
        ]
    ):
        return "disease_inquiry"
    if any(
        w in text
        for w in [
            "weather",
            "rain",
            "temp",
            "storm",
            "cold",
            "frost",
            "forecast",
            "বৃষ্টি",
            "আবহাওয়া",
            "ঝড়",
        ]
    ):
        return "weather_inquiry"
    if any(
        w in text
        for w in [
            "task",
            "todo",
            "schedule",
            "fertilizer",
            "irrigate",
            "water",
            "harvest",
            "weeding",
            "কাজ",
            "সার",
            "সেচ",
        ]
    ):
        return "task_inquiry"
    if any(
        w in text
        for w in [
            "recommend",
            "which crop",
            "variety",
            "suitable",
            "plant",
            "crop choice",
            "জাত",
            "ফসল",
        ]
    ):
        return "crop_advice"
    if any(
        w in text
        for w in [
            "profile",
            "setup",
            "onboard",
            "location",
            "land area",
            "তথ্য",
            "অনবোর্ডিং",
        ]
    ):
        return "onboarding_help"
    return "general_qa"


def build_system_prompt(ctx: AggregatedFarmContext) -> str:
    crop_name = ctx.active_crop.name if ctx.active_crop else "No active crop"
    stage_name = ctx.growth_stage.name if ctx.growth_stage else "Not established"
    location = (
        f"{ctx.farmland.upazila or ''}, {ctx.farmland.district or ''}, {ctx.farmland.division or 'Bangladesh'}"
    )

    tasks_str = (
        "; ".join(
            f"{t.title} (due {t.due_at.strftime('%Y-%m-%d') if t.due_at else 'unspecified'})"
            for t in ctx.pending_tasks
        )
        or "None pending"
    )

    problems_str = (
        "; ".join(f"{p.category}: {p.description}" for p in ctx.open_problems)
        or "None"
    )

    alerts_str = (
        "; ".join(f"{a.severity.upper()}: {a.title} - {a.message}" for a in ctx.recent_weather_alerts)
        or "None"
    )

    knowledge_str = (
        "\n".join(f"- {k}" for k in ctx.knowledge_snippets)
        or "Standard Bangladesh agricultural guidelines apply."
    )

    return f"""You are FieldShift AI, a season-long agricultural assistant and farm manager for Bangladesh farmers.
You speak clearly, respectfully, and practically in the farmer's language (Bengali or English depending on how they address you).

FARM PROFILE & OPERATIONAL CONTEXT:
- Farmer: {ctx.farmer.name if ctx.farmer else 'Farmer'}
- Farmland: {ctx.farmland.name} ({location})
- Land Area: {ctx.farmland.land_area_sqm} sqm ({ctx.farmland.land_area_display_unit})
- Soil Type: {ctx.farmland.soil_type or 'Not specified'}
- Irrigation: {'Available' if ctx.farmland.irrigation_available else 'Not available'} (Source: {ctx.farmland.water_source or 'Unspecified'})
- Farming Method: {ctx.farmland.farming_method or 'Conventional/Mixed'}
- Active Crop: {crop_name} (Variety: {ctx.active_season.variety_name if ctx.active_season else 'N/A'})
- Current Growth Stage: {stage_name}
- Pending Tasks: {tasks_str}
- Open Farm Problems: {problems_str}
- Active Weather Alerts: {alerts_str}

APPROVED AGRONOMIC EVIDENCE:
{knowledge_str}

RULES:
1. Always ground your advice in this specific farmland's crop, soil, stage, tasks, and weather.
2. If the farmer asks about disease or plant health, encourage them to upload a photo for visual disease diagnosis in the Crop Health tab.
3. If weather alerts are present, factor them into any irrigation or spraying advice.
4. Keep advice practical, actionable, and safe. Do not invent ungrounded chemical recipes.
"""


def generate_gemini_reply(
    prompt_system: str,
    history_messages: list[ChatMessage],
    new_message: str,
) -> str | None:
    secret = settings.GEMINI_API_KEY
    api_key = secret.get_secret_value().strip() if secret is not None else ""
    if not api_key:
        return None

    # Construct conversation turns
    turns = [{"role": "system", "parts": [{"text": prompt_system}]}]
    for msg in history_messages[-6:]:
        role = "user" if msg.sender_type == "farmer" else "model"
        turns.append({"role": role, "parts": [{"text": msg.message or ""}]})
    turns.append({"role": "user", "parts": [{"text": new_message}]})

    payload = {
        "model": settings.GEMINI_MODEL,
        "contents": turns[1:],
        "systemInstruction": {"parts": [{"text": prompt_system}]},
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 600,
        },
    }

    try:
        with httpx.Client(
            base_url="https://generativelanguage.googleapis.com",
            headers={"x-goog-api-key": api_key},
            timeout=settings.GEMINI_TIMEOUT_SECONDS,
        ) as client:
            resp = client.post(
                f"/v1beta/models/{settings.GEMINI_MODEL}:generateContent",
                json=payload,
            )
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
            else:
                logger.warning(
                    "Gemini API returned status %s for model %s",
                    resp.status_code,
                    settings.GEMINI_MODEL,
                )
    except httpx.HTTPError as exc:
        logger.warning("Gemini HTTP call failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error calling Gemini API")
    return None


def generate_fallback_reply(intent: ChatIntent, ctx: AggregatedFarmContext, message_text: str) -> str:
    crop_name = ctx.active_crop.name if ctx.active_crop else "your crop"
    stage_name = ctx.growth_stage.name if ctx.growth_stage else "current growth phase"

    if intent == "disease_inquiry":
        crop_context = ctx.active_crop.name if ctx.active_crop else "your field"
        return (
            f"For issues with {crop_context}, please upload a photo in the Crop Health & Disease tab. "
            "Our AI will analyze the visible symptoms and record the diagnosis directly in your farm problems list."
        )
    elif intent == "weather_inquiry":
        if ctx.recent_weather_alerts:
            alert = ctx.recent_weather_alerts[0]
            return f"Weather Alert for {ctx.farmland.name}: {alert.title} — {alert.message}. Recommended action: {alert.recommended_action or 'Monitor field conditions.'}"
        return f"Weather conditions for {ctx.farmland.name} are being tracked. Check the Weather & Alerts tab for upcoming rainfall and temperature trends."
    elif intent == "task_inquiry":
        if ctx.pending_tasks:
            tasks_list = ", ".join(t.title for t in ctx.pending_tasks[:3])
            if ctx.active_crop and ctx.growth_stage:
                task_context = f"For the {stage_name} stage of {crop_name}"
            elif ctx.active_crop:
                task_context = f"For {crop_name}"
            else:
                task_context = "Your upcoming farm tasks"
            return f"{task_context} include: {tasks_list}. You can mark them completed in the Tasks tab."
        if not ctx.active_season:
            return (
                "There is no active season for this farm, so no season tasks are scheduled yet. "
                "Start a season in Crop Advisor to create its task plan."
            )
        if not ctx.active_crop:
            return (
                "No crop is linked to this active season yet, so I cannot match tasks to a crop. "
                "Check the season details in Crop Advisor."
            )
        if not ctx.growth_stage:
            return (
                f"There are no urgent tasks pending for {crop_name}. "
                "Select the current growth stage in Crop Advisor to get stage-specific guidance."
            )
        return f"No urgent tasks pending for {crop_name} in the {stage_name} stage. Keep monitoring moisture and weed growth."
    elif intent == "crop_advice":
        return (
            f"Based on your soil ({ctx.farmland.soil_type or 'local conditions'}) and irrigation setup, "
            "explore the Crop Advisor tab to view suitable crops and full seasonal plans."
        )
    else:
        if ctx.active_crop and ctx.growth_stage:
            farm_context = f"Your active crop is {crop_name} in the {stage_name} stage."
        elif ctx.active_crop:
            farm_context = (
                f"Your active crop is {crop_name}, but its growth stage has not been set yet."
            )
        else:
            farm_context = (
                f"No crop or growth stage is set for {ctx.farmland.name} yet. "
                "Start a season in Crop Advisor, and I can tailor advice to that crop."
            )
        return (
            f"Hello! I am your assistant for {ctx.farmland.name}. {farm_context} "
            "Let me know if you need help with irrigation, fertilizer timing, pest management, or upcoming tasks."
        )


def handle_farmer_message(
    db: Session,
    farmland_id: UUID,
    farmer_id: UUID,
    conversation_id: UUID,
    message_text: str,
    attachment_key: str | None = None,
    client_request_id: UUID | None = None,
) -> ChatResponse:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.farmland_id == farmland_id,
            Conversation.farmer_id == farmer_id,
        )
    )
    if conversation is None:
        raise ValueError("Conversation not found or access denied")

    try:
        ctx = aggregate_farmland_context(db, farmland_id, farmer_id)
        intent = classify_intent(message_text)
        context_summary = FarmContextSummary(
            farmland_name=ctx.farmland.name,
            location=ctx.farmland.district,
            soil_type=ctx.farmland.soil_type,
            irrigation="Available" if ctx.farmland.irrigation_available else "Not available",
            active_crop=ctx.active_crop.name if ctx.active_crop else None,
            growth_stage=ctx.growth_stage.name if ctx.growth_stage else None,
            pending_tasks_count=len(ctx.pending_tasks),
            open_problems_count=len(ctx.open_problems),
            active_weather_alerts_count=len(ctx.recent_weather_alerts),
            onboarding_complete=len(ctx.missing_onboarding_fields) == 0,
            next_onboarding_question=f"Please provide your {ctx.missing_onboarding_fields[0]}"
            if ctx.missing_onboarding_fields
            else None,
        )

        # Reuse the saved pair when a browser retries after losing a response.
        if client_request_id is not None:
            request_key = str(client_request_id)
            request_filter = ChatMessage.metadata_json["client_request_id"].as_string() == request_key
            existing_farmer_message = db.scalar(
                select(ChatMessage)
                .where(
                    ChatMessage.conversation_id == conversation.id,
                    ChatMessage.sender_type == "farmer",
                    request_filter,
                )
                .limit(1)
            )
            existing_assistant_message = db.scalar(
                select(ChatMessage)
                .where(
                    ChatMessage.conversation_id == conversation.id,
                    ChatMessage.sender_type == "assistant",
                    request_filter,
                )
                .limit(1)
            )
            if existing_farmer_message is not None and existing_assistant_message is not None:
                saved_intent = (existing_farmer_message.metadata_json or {}).get("intent")
                if saved_intent in {
                    "task_inquiry",
                    "weather_inquiry",
                    "disease_inquiry",
                    "crop_advice",
                    "onboarding_help",
                    "general_qa",
                }:
                    intent = saved_intent
                return ChatResponse(
                    conversation_id=conversation.id,
                    farmer_message=ChatMessageRead.model_validate(existing_farmer_message),
                    assistant_message=ChatMessageRead.model_validate(existing_assistant_message),
                    intent=intent,
                    context_summary=context_summary,
                    suggested_actions=_suggested_actions(intent),
                )

        farmer_metadata = {"intent": intent}
        if client_request_id is not None:
            farmer_metadata["client_request_id"] = str(client_request_id)
        farmer_msg = ChatMessage(
            conversation_id=conversation.id,
            sender_type="farmer",
            message=message_text,
            message_type="image" if attachment_key else "text",
            attachment_key=attachment_key,
            metadata_json=farmer_metadata,
        )
        db.add(farmer_msg)
        db.flush()

        history = list(
            db.scalars(
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation.id)
                .order_by(ChatMessage.created_at.asc())
            ).all()
        )
        system_prompt = build_system_prompt(ctx)
        reply_text = generate_gemini_reply(system_prompt, history, message_text)
        if not reply_text:
            reply_text = generate_fallback_reply(intent, ctx, message_text)

        assistant_metadata = {"intent": intent, "model": settings.GEMINI_MODEL}
        if client_request_id is not None:
            assistant_metadata["client_request_id"] = str(client_request_id)
        assistant_msg = ChatMessage(
            conversation_id=conversation.id,
            sender_type="assistant",
            message=reply_text,
            message_type="text",
            metadata_json=assistant_metadata,
        )
        db.add(assistant_msg)

        default_titles = {"New conversation", "Chat", "New chat"}
        if not conversation.title or conversation.title in default_titles:
            short_title = message_text.strip().replace("\n", " ")
            conversation.title = (
                short_title[:40] + "..." if len(short_title) > 40 else short_title
            )

        db.commit()
        db.refresh(farmer_msg)
        db.refresh(assistant_msg)
    except Exception:
        db.rollback()
        raise

    return ChatResponse(
        conversation_id=conversation.id,
        farmer_message=ChatMessageRead.model_validate(farmer_msg),
        assistant_message=ChatMessageRead.model_validate(assistant_msg),
        intent=intent,
        context_summary=context_summary,
        suggested_actions=_suggested_actions(intent),
    )

def _suggested_actions(intent: ChatIntent) -> list[str]:
    if intent == "disease_inquiry":
        return ["Upload photo in Crop Health"]
    if intent == "task_inquiry":
        return ["View Season Tasks"]
    if intent == "weather_inquiry":
        return ["Check Weather Alerts"]
    return []
