"""Tests for Module 5 — Conversational Layer API."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.models.chat import ChatMessage, Conversation
from app.services.chat_engine import AggregatedFarmContext, generate_fallback_reply


def _context_without_active_season():
    return AggregatedFarmContext(
        farmland=SimpleNamespace(
            name="Test Field", soil_type="Clay loam", irrigation_available=True
        ),
        farmer=SimpleNamespace(),
        profile=None,
        active_season=None,
        active_crop=None,
        growth_stage=None,
        pending_tasks=[],
        open_problems=[],
        recent_weather_alerts=[],
        knowledge_snippets=[],
        missing_onboarding_fields=[],
    )


def test_general_fallback_does_not_claim_crop_or_stage_when_none_are_active():
    reply = generate_fallback_reply(
        "general_qa", _context_without_active_season(), "What should I check today?"
    )

    assert "no crop or growth stage is set" in reply.lower()
    assert "your crop" not in reply.lower()
    assert "current growth phase" not in reply.lower()


def test_task_fallback_explains_that_no_season_tasks_exist_when_no_season_is_active():
    reply = generate_fallback_reply(
        "task_inquiry", _context_without_active_season(), "What are my tasks?"
    )

    assert "no active season" in reply.lower()
    assert "your crop" not in reply.lower()


def test_create_and_list_conversations(client_and_farm):
    client, farmland_id, _, _ = client_and_farm

    # 1. Create conversation
    res = client.post(
        f"/farmlands/{farmland_id}/conversations",
        json={"title": "Season Advice"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Season Advice"
    assert data["farmland_id"] == str(farmland_id)
    conv_id = data["id"]

    # 2. List conversations
    res = client.get(f"/farmlands/{farmland_id}/conversations")
    assert res.status_code == 200
    list_data = res.json()
    assert len(list_data) == 1
    assert list_data[0]["id"] == conv_id


def test_send_message_and_receive_grounded_response(client_and_farm):
    client, farmland_id, _, _ = client_and_farm

    # Create thread
    res = client.post(
        f"/farmlands/{farmland_id}/conversations",
        json={"title": "General Help"},
    )
    conv_id = res.json()["id"]

    # Send a message
    res = client.post(
        f"/farmlands/{farmland_id}/conversations/{conv_id}/messages",
        json={"message": "What should I do for rice in vegetative stage?", "message_type": "text"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["conversation_id"] == conv_id
    assert data["farmer_message"]["message"] == "What should I do for rice in vegetative stage?"
    assert data["assistant_message"]["sender_type"] == "assistant"
    assert len(data["assistant_message"]["message"]) > 0
    assert data["intent"] in ["task_inquiry", "crop_advice", "general_qa"]


def test_cannot_access_other_farmer_conversation(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    other_farmland_id = client.app.state.other_farmland_id

    # Trying to start a conversation on someone else's farmland fails with 404
    res = client.post(
        f"/farmlands/{other_farmland_id}/conversations",
        json={"title": "Unauthorized"},
    )
    assert res.status_code == 404


def test_replaying_a_message_request_returns_the_saved_pair_without_duplicates(
    client_and_farm, monkeypatch
):
    client, farmland_id, _, _ = client_and_farm
    monkeypatch.setattr(
        "app.services.chat_engine.generate_gemini_reply", lambda *args: None
    )

    conversation_response = client.post(
        f"/farmlands/{farmland_id}/conversations", json={"title": "Retry test"}
    )
    conversation_id = conversation_response.json()["id"]
    body = {
        "message": "What should I check today?",
        "message_type": "text",
        "client_request_id": str(uuid4()),
    }
    endpoint = f"/farmlands/{farmland_id}/conversations/{conversation_id}/messages"

    first = client.post(endpoint, json=body)
    replay = client.post(endpoint, json=body)
    detail = client.get(
        f"/farmlands/{farmland_id}/conversations/{conversation_id}"
    )

    assert first.status_code == replay.status_code == 200
    assert first.json()["farmer_message"]["id"] == replay.json()["farmer_message"]["id"]
    assert first.json()["assistant_message"]["id"] == replay.json()["assistant_message"]["id"]
    assert len(detail.json()["messages"]) == 2
