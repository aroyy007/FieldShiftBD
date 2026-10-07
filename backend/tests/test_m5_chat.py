"""Tests for Module 5 — Conversational Layer API."""

import pytest
from app.models.chat import ChatMessage, Conversation


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