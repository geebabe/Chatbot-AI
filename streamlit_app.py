import streamlit as st
import requests
import json
import uuid

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Assistant",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}
.stApp {
    background: #0e0e10 !important;
}
.block-container {
    max-width: 760px !important;
    padding: 0 1.5rem 2rem !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
[data-testid="stToolbar"] { display: none; }

/* ── Custom header ── */
.app-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 24px 4px 18px;
    border-bottom: 1px solid #1e1e22;
    margin-bottom: 28px;
}
.header-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #c8ff72;
    box-shadow: 0 0 10px #c8ff7299;
    flex-shrink: 0;
    animation: pulse 2.4s ease-in-out infinite;
}
@keyframes pulse {
    0%,100% { opacity:1; } 50% { opacity:.3; }
}
.header-title {
    font-family: 'Instrument Serif', serif !important;
    font-size: 1.2rem;
    color: #e8e6e1;
    letter-spacing: .01em;
}
.header-badge {
    margin-left: auto;
    font-size: .65rem;
    font-weight: 500;
    color: #555;
    letter-spacing: .1em;
    text-transform: uppercase;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 80px 0 60px;
    color: #2e2e34;
}
.empty-icon {
    font-family: 'Instrument Serif', serif;
    font-style: italic;
    font-size: 3.5rem;
    display: block;
    margin-bottom: 10px;
    color: #252528;
}
.empty-text {
    font-size: .82rem;
    font-weight: 300;
    letter-spacing: .05em;
    color: #333338;
}

/* ── Message rows ── */
.msg-row {
    display: flex;
    flex-direction: column;
    margin-bottom: 24px;
    animation: fadeUp .28s ease both;
}
@keyframes fadeUp {
    from { opacity:0; transform:translateY(6px); }
    to   { opacity:1; transform:translateY(0); }
}
.msg-row.user  { align-items: flex-end; }
.msg-row.assistant { align-items: flex-start; }

.msg-label {
    font-size: .62rem;
    font-weight: 500;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: #444;
    margin-bottom: 5px;
    padding: 0 3px;
}

.bubble {
    max-width: 82%;
    line-height: 1.7;
    font-size: .875rem;
    font-weight: 300;
    border-radius: 14px;
    padding: 12px 16px;
    white-space: pre-wrap;
    word-break: break-word;
}
.bubble.user {
    background: #1c1c20;
    border: 1px solid #2c2c32;
    color: #d4d2ce;
    border-bottom-right-radius: 4px;
}
.bubble.assistant {
    background: transparent;
    border: 1px solid #222226;
    color: #e2e0db;
    border-bottom-left-radius: 4px;
}

/* ── Typing indicator ── */
.typing-dots {
    display: inline-flex;
    gap: 4px;
    padding: 14px 18px;
    border: 1px solid #222226;
    border-radius: 14px;
    border-bottom-left-radius: 4px;
}
.typing-dots span {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #c8ff72;
    opacity: .3;
    animation: dot 1.2s ease-in-out infinite;
}
.typing-dots span:nth-child(2) { animation-delay: .2s; }
.typing-dots span:nth-child(3) { animation-delay: .4s; }
@keyframes dot {
    0%,80%,100% { opacity:.2; transform:scale(.85); }
    40%         { opacity:1;  transform:scale(1); }
}

/* ── Chat input override ── */
[data-testid="stChatInput"] > div {
    background: #141416 !important;
    border: 1px solid #272730 !important;
    border-radius: 16px !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #e8e6e1 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: .88rem !important;
    font-weight: 300 !important;
    caret-color: #c8ff72 !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #3a3a42 !important; }
[data-testid="stChatInput"] button {
    background: #c8ff72 !important;
    border-radius: 10px !important;
}
[data-testid="stChatInput"] button svg { color: #0e0e10 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2a2e; border-radius: 4px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0b0b0d !important;
    border-right: 1px solid #1a1a1e !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ── Sidebar config ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:20px 4px 12px;'>
        <span style='font-family:"Instrument Serif",serif;font-size:1.1rem;color:#e8e6e1;'>Settings</span>
    </div>
    """, unsafe_allow_html=True)

    api_url = st.text_input(
        "API Endpoint",
        value="http://localhost:8000/api/v1/chat/stream",
        help="Your backend streaming endpoint"
    )
    user_id = st.text_input("User ID", value="user-123")

    st.markdown("<div style='height:1px;background:#1e1e22;margin:16px 0'></div>", unsafe_allow_html=True)

    if st.button("🗑 Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.markdown(f"""
    <div style='margin-top:16px;padding:10px;background:#111114;border-radius:10px;border:1px solid #1e1e22;'>
        <div style='font-size:.65rem;color:#444;letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px;'>Session</div>
        <div style='font-size:.7rem;color:#333;font-family:monospace;word-break:break-all;'>{st.session_state.session_id[:16]}…</div>
    </div>
    """, unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="header-dot"></div>
    <span class="header-title">Assistant</span>
    <span class="header-badge">AI</span>
</div>
""", unsafe_allow_html=True)

# ── Message history ───────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <span class="empty-icon">✦</span>
        <p class="empty-text">Start a conversation</p>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        role = msg["role"]
        label = "You" if role == "user" else "AI"
        st.markdown(f"""
        <div class="msg-row {role}">
            <span class="msg-label">{label}</span>
            <div class="bubble {role}">{msg["content"]}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Streaming helper ──────────────────────────────────────────────────────────
def stream_response(prompt: str, api_endpoint: str, uid: str, sid: str):
    """Call backend SSE endpoint and yield text chunks."""
    payload = {
        "session_id": sid,
        "user_id": uid,
        "message": prompt,
    }
    try:
        with requests.post(
            api_endpoint,
            json=payload,
            stream=True,
            timeout=60,
            headers={"Accept": "text/event-stream"},
        ) as resp:
            resp.raise_for_status()
            buffer = ""
            for raw_bytes in resp.iter_content(chunk_size=None):
                if not raw_bytes:
                    continue
                buffer += raw_bytes.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        parsed = json.loads(data)
                        chunk = parsed.get("text", "")
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        continue
    except requests.exceptions.ConnectionError:
        yield "\n\n⚠️ Could not connect to the backend. Check your API endpoint in the sidebar."
    except requests.exceptions.Timeout:
        yield "\n\n⚠️ Request timed out."
    except requests.exceptions.HTTPError as e:
        yield f"\n\n⚠️ Backend error: {e.response.status_code}"

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Message…"):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Re-render user message immediately
    st.markdown(f"""
    <div class="msg-row user">
        <span class="msg-label">You</span>
        <div class="bubble user">{prompt}</div>
    </div>
    """, unsafe_allow_html=True)

    # Typing indicator placeholder
    typing_placeholder = st.empty()
    typing_placeholder.markdown("""
    <div class="msg-row assistant">
        <span class="msg-label">AI</span>
        <div class="typing-dots">
            <span></span><span></span><span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stream response
    full_response = ""
    response_placeholder = st.empty()

    for chunk in stream_response(
        prompt, api_url, user_id, st.session_state.session_id
    ):
        typing_placeholder.empty()
        full_response += chunk
        response_placeholder.markdown(f"""
        <div class="msg-row assistant">
            <span class="msg-label">AI</span>
            <div class="bubble assistant">{full_response}<span style="display:inline-block;width:2px;height:.85em;background:#c8ff72;margin-left:2px;vertical-align:text-bottom;animation:blink .9s step-end infinite;"></span></div>
        </div>
        <style>@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0}}}}</style>
        """, unsafe_allow_html=True)

    # Final render without cursor
    typing_placeholder.empty()
    response_placeholder.markdown(f"""
    <div class="msg-row assistant">
        <span class="msg-label">AI</span>
        <div class="bubble assistant">{full_response}</div>
    </div>
    """, unsafe_allow_html=True)

    # Save to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})