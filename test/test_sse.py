"""Unit test: verify SSE events are emitted in the correct order."""

import json
import uuid
from unittest.mock import patch

import pytest

from test.conftest import mock_agent_stream


@pytest.mark.asyncio
async def test_sse_event_order(client):
    """
    POST /api/v1/chat/stream should emit:
    - one or more agent.message.delta events
    - exactly one agent.message.done event at the end
    All events should be valid JSON with the expected fields.
    """
    session_id = str(uuid.uuid4())
    user_id = "test-user"

    with patch(
        "app.services.chat_service.run_agent_streamed",
        side_effect=mock_agent_stream("Hello", ", ", "world!"),
    ):
        response = await client.post(
            "/api/v1/chat/stream",
            json={
                "session_id": session_id,
                "user_id": user_id,
                "message": "Hi there",
            },
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    # Parse SSE events
    raw = response.text
    events = _parse_sse(raw)

    # Filter out heartbeat events
    non_heartbeat = [e for e in events if e["event"] != "heartbeat"]

    # Must have at least one delta and exactly one done
    delta_events = [e for e in non_heartbeat if e["event"] == "agent.message.delta"]
    done_events = [e for e in non_heartbeat if e["event"] == "agent.message.done"]

    assert len(delta_events) >= 1, "Expected at least one delta event"
    assert len(done_events) == 1, "Expected exactly one done event"

    # Delta events should come before done
    last_delta_idx = max(non_heartbeat.index(e) for e in delta_events)
    done_idx = non_heartbeat.index(done_events[0])
    assert last_delta_idx < done_idx, "All deltas should come before done"

    # Verify delta payloads contain 'text' field
    for de in delta_events:
        data = json.loads(de["data"])
        assert "text" in data

    # Verify done payload contains 'session_id'
    done_data = json.loads(done_events[0]["data"])
    assert done_data["session_id"] == session_id


@pytest.mark.asyncio
async def test_sse_failed_event_on_error(client):
    """When the agent raises an error, an agent.workflow.failed event should be emitted."""
    session_id = str(uuid.uuid4())

    async def _failing_stream(user_message: str):
        raise RuntimeError("Test error")
        yield  # noqa: unreachable — makes this an async generator

    with patch(
        "app.services.chat_service.run_agent_streamed",
        side_effect=_failing_stream,
    ):
        response = await client.post(
            "/api/v1/chat/stream",
            json={
                "session_id": session_id,
                "user_id": "test-user",
                "message": "trigger error",
            },
        )

    assert response.status_code == 200
    events = _parse_sse(response.text)
    failed_events = [e for e in events if e["event"] == "agent.workflow.failed"]
    assert len(failed_events) >= 1, "Expected a failed event on error"

    data = json.loads(failed_events[0]["data"])
    assert "error" in data


def _parse_sse(raw: str) -> list[dict]:
    """Parse raw SSE text into a list of {'event': ..., 'data': ...} dicts."""
    events = []
    current = {}
    for line in raw.split("\n"):
        if line.startswith("event: "):
            current["event"] = line[7:].strip()
        elif line.startswith("data: "):
            current["data"] = line[6:].strip()
        elif line == "" and current:
            events.append(current)
            current = {}
    if current:
        events.append(current)
    return events
