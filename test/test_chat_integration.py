"""Integration test: verify messages are correctly persisted after a chat turn."""

import uuid
from unittest.mock import patch

import pytest

from test.conftest import mock_agent_stream


@pytest.mark.asyncio
async def test_messages_persisted_after_chat(client):
    """
    After a successful POST /api/v1/chat/stream:
    - The user message should be persisted.
    - The assistant message should be persisted.
    - GET /sessions/{id}/history should return both in order.
    """
    session_id = str(uuid.uuid4())
    user_id = "integration-user"
    user_message = "What is 2 + 2?"
    assistant_chunks = ["The answer", " is ", "4."]

    with patch(
        "app.services.chat_service.run_agent_streamed",
        side_effect=mock_agent_stream(*assistant_chunks),
    ):
        stream_response = await client.post(
            "/api/v1/chat/stream",
            json={
                "session_id": session_id,
                "user_id": user_id,
                "message": user_message,
            },
        )

    assert stream_response.status_code == 200

    # Fetch history
    history_response = await client.get(
        f"/api/v1/sessions/{session_id}/history",
        params={"user_id": user_id},
    )
    assert history_response.status_code == 200

    data = history_response.json()
    assert data["session_id"] == session_id
    messages = data["messages"]
    assert len(messages) == 2

    # First message should be user, second should be assistant
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == user_message

    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "".join(assistant_chunks)


@pytest.mark.asyncio
async def test_session_delete(client):
    """
    After DELETE /sessions/{id}, the session and messages should be gone.
    """
    session_id = str(uuid.uuid4())
    user_id = "delete-user"

    with patch(
        "app.services.chat_service.run_agent_streamed",
        side_effect=mock_agent_stream("Hello!"),
    ):
        await client.post(
            "/api/v1/chat/stream",
            json={
                "session_id": session_id,
                "user_id": user_id,
                "message": "Hi",
            },
        )

    # Delete the session
    delete_response = await client.delete(
        f"/api/v1/sessions/{session_id}",
        params={"user_id": user_id},
    )
    assert delete_response.status_code == 204

    # History should now be empty
    history_response = await client.get(
        f"/api/v1/sessions/{session_id}/history",
        params={"user_id": user_id},
    )
    assert history_response.status_code == 200
    assert history_response.json()["messages"] == []


@pytest.mark.asyncio
async def test_user_cannot_access_other_users_session(client):
    """
    A user must only be able to access their own sessions.
    """
    session_id = str(uuid.uuid4())
    owner_id = "owner-user"
    intruder_id = "intruder-user"

    with patch(
        "app.services.chat_service.run_agent_streamed",
        side_effect=mock_agent_stream("secret data"),
    ):
        await client.post(
            "/api/v1/chat/stream",
            json={
                "session_id": session_id,
                "user_id": owner_id,
                "message": "My secret",
            },
        )

    # Intruder tries to read
    response = await client.get(
        f"/api/v1/sessions/{session_id}/history",
        params={"user_id": intruder_id},
    )
    assert response.status_code == 200
    assert response.json()["messages"] == []  # Empty — no access

    # Intruder tries to delete
    delete_response = await client.delete(
        f"/api/v1/sessions/{session_id}",
        params={"user_id": intruder_id},
    )
    assert delete_response.status_code == 404
