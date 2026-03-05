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
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;1,400&family=Syne:wght@300;400;500&display=swap');

/* ── Palette ──
   bg:        #0d1117  (deep blue-black)
   surface:   #131920  (card surface)
   border:    #1e2a35  (subtle borders)
   accent:    #f0a500  (warm amber)
   accent2:   #e06c3a  (burnt orange — gradient partner)
   text:      #c9d8e8  (cool blue-white)
   muted:     #4a6070
*/

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif !important;
}
.stApp {
    background: #0d1117 !important;
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
    gap: 12px;
    padding: 26px 4px 20px;
    border-bottom: 1px solid #1e2a35;
    margin-bottom: 32px;
}
.header-dot {
    width: 9px; height: 9px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f0a500, #e06c3a);
    box-shadow: 0 0 12px #f0a50077;
    flex-shrink: 0;
    animation: pulse 2.4s ease-in-out infinite;
}
@keyframes pulse {
    0%,100% { opacity:1; box-shadow: 0 0 12px #f0a50077; }
    50%      { opacity:.5; box-shadow: 0 0 4px #f0a50033; }
}
.header-title {
    font-family: 'Lora', serif !important;
    font-size: 1.2rem;
    font-style: italic;
    color: #c9d8e8;
    letter-spacing: .02em;
}
.header-badge {
    margin-left: auto;
    font-size: .62rem;
    font-weight: 500;
    color: #f0a500;
    letter-spacing: .18em;
    text-transform: uppercase;
    border: 1px solid #f0a50044;
    padding: 2px 8px;
    border-radius: 20px;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 80px 0 60px;
}
.empty-icon {
    font-family: 'Lora', serif;
    font-style: italic;
    font-size: 4rem;
    display: block;
    margin-bottom: 12px;
    background: linear-gradient(135deg, #f0a500, #e06c3a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    opacity: .25;
}
.empty-text {
    font-size: .8rem;
    font-weight: 300;
    letter-spacing: .1em;
    color: #2a3d4d;
    text-transform: uppercase;
}

/* ── Message rows ── */
.msg-row {
    display: flex;
    flex-direction: column;
    margin-bottom: 26px;
    animation: fadeUp .3s ease both;
}
@keyframes fadeUp {
    from { opacity:0; transform:translateY(8px); }
    to   { opacity:1; transform:translateY(0); }
}
.msg-row.user      { align-items: flex-end; }
.msg-row.assistant { align-items: flex-start; }

.msg-label {
    font-size: .6rem;
    font-weight: 500;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: #2e4455;
    margin-bottom: 6px;
    padding: 0 4px;
}
.msg-row.user .msg-label { color: #f0a50066; }

.bubble {
    max-width: 80%;
    line-height: 1.72;
    font-size: .875rem;
    font-weight: 300;
    border-radius: 16px;
    padding: 13px 18px;
    white-space: pre-wrap;
    word-break: break-word;
}
.bubble.user {
    background: linear-gradient(135deg, #1a2535, #1e2d3e);
    border: 1px solid #2a3f52;
    color: #b8cdd e;
    border-bottom-right-radius: 4px;
    color: #c2d4e4;
}
.bubble.assistant {
    background: #111820;
    border: 1px solid #1a2840;
    color: #c9d8e8;
    border-bottom-left-radius: 4px;
    position: relative;
}
.bubble.assistant::before {
    content: '';
    position: absolute;
    left: 0; top: 20%; bottom: 20%;
    width: 2px;
    background: linear-gradient(to bottom, transparent, #f0a500, transparent);
    border-radius: 2px;
    opacity: .4;
}

/* ── Typing indicator ── */
.typing-dots {
    display: inline-flex;
    gap: 5px;
    padding: 15px 20px;
    background: #111820;
    border: 1px solid #1a2840;
    border-radius: 16px;
    border-bottom-left-radius: 4px;
}
.typing-dots span {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f0a500, #e06c3a);
    opacity: .25;
    animation: dot 1.3s ease-in-out infinite;
}
.typing-dots span:nth-child(2) { animation-delay: .22s; }
.typing-dots span:nth-child(3) { animation-delay: .44s; }
@keyframes dot {
    0%,80%,100% { opacity:.2; transform:scale(.8); }
    40%         { opacity:1;  transform:scale(1.1); }
}

/* ── Chat input — nuclear override ── */
/* wrapper */
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div {
    background: #111820 !important;
    border-color: #1e2a35 !important;
    border-radius: 16px !important;
}
/* the actual textarea — every selector we can think of */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea:focus,
.stChatInput textarea,
section[data-testid="stChatInput"] textarea {
    background: #111820 !important;
    background-color: #111820 !important;
    color: #c9d8e8 !important;
    font-family: 'Syne', sans-serif !important;
    font-size: .88rem !important;
    font-weight: 300 !important;
    caret-color: #f0a500 !important;
    -webkit-text-fill-color: #c9d8e8 !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #2a3d4d !important;
    -webkit-text-fill-color: #2a3d4d !important;
}
/* send button */
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #f0a500, #e06c3a) !important;
    border-radius: 10px !important;
    border: none !important;
}
[data-testid="stChatInput"] button:hover {
    opacity: .88 !important;
}
[data-testid="stChatInput"] button svg path {
    stroke: #0d1117 !important;
    fill: #0d1117 !important;
}

/* ── Sidebar inputs ── */
[data-testid="stSidebar"] .stTextInput input {
    background: #0d1520 !important;
    color: #c9d8e8 !important;
    border-color: #1e2a35 !important;
    -webkit-text-fill-color: #c9d8e8 !important;
}
[data-testid="stSidebar"] label {
    color: #4a6070 !important;
}
[data-testid="stSidebar"] button {
    background: #131920 !important;
    color: #c9d8e8 !important;
    border: 1px solid #1e2a35 !important;
}
[data-testid="stSidebar"] button:hover {
    border-color: #f0a50055 !important;
    color: #f0a500 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1e2a35; border-radius: 4px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0b0f16 !important;
    border-right: 1px solid #1a2230 !important;
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
    <div style='margin-top:16px;padding:10px;background:#0d1520;border-radius:10px;border:1px solid #1e2a35;'>
        <div style='font-size:.62rem;color:#2e4455;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px;'>Session</div>
        <div style='font-size:.7rem;color:#2a3d4d;font-family:monospace;word-break:break-all;'>{st.session_state.session_id[:16]}…</div>
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
            <div class="bubble assistant">{full_response}<span style="display:inline-block;width:2px;height:.85em;background:linear-gradient(180deg,#f0a500,#e06c3a);margin-left:3px;vertical-align:text-bottom;animation:blink .9s step-end infinite;border-radius:1px;"></span></div>
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