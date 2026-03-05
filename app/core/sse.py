import json


def format_sse_event(event_type: str, data: dict) -> str:
    """Format a server-sent event string."""
    payload = json.dumps(data)
    return f"event: {event_type}\ndata: {payload}\n\n"


def delta_event(text: str) -> str:
    return format_sse_event("agent.message.delta", {"text": text})


def done_event(session_id: str) -> str:
    return format_sse_event("agent.message.done", {"session_id": session_id})


def failed_event(error: str) -> str:
    return format_sse_event("agent.workflow.failed", {"error": error})


def heartbeat_event() -> str:
    return format_sse_event("heartbeat", {})
