# =============================================================================
# Eco-Travel Advisor - Streamlit Frontend (v2 - native chat components)
# Uses st.chat_message for proper rendering in Streamlit 1.31+
# =============================================================================

import streamlit as st
import requests
import time
import uuid
import random
from datetime import datetime

# ---- Page Config ----
st.set_page_config(
    page_title="Eco-Travel Advisor",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- Constants ----
RASA_API_URL = "http://localhost:5005/webhooks/rest/webhook"

# ---- Custom CSS ----
st.markdown("""
<style>
    /* ---- App background ---- */
    .stApp {
        background: linear-gradient(160deg, #0a1f0e 0%, #1a3a21 60%, #0d2b14 100%);
    }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background: rgba(10, 31, 14, 0.95) !important;
        border-right: 1px solid rgba(45, 158, 95, 0.3);
    }
    section[data-testid="stSidebar"] * {
        color: #d4edda !important;
    }

    /* ---- Header ---- */
    .eco-header {
        text-align: center;
        padding: 22px 10px 14px;
        background: linear-gradient(135deg, rgba(45,158,95,0.25), rgba(13,40,20,0.6));
        border-radius: 14px;
        border: 1px solid rgba(45,158,95,0.35);
        margin-bottom: 18px;
    }
    .eco-header h1 {
        color: #52b788 !important;
        font-size: 2.2rem !important;
        margin: 0 !important;
        letter-spacing: 1px;
    }
    .eco-header p {
        color: rgba(210,237,218,0.75) !important;
        margin: 6px 0 0 !important;
        font-size: 1rem;
    }

    /* ---- Chat container ---- */
    .chat-wrapper {
        background: rgba(5, 20, 9, 0.7);
        border: 1px solid rgba(45, 158, 95, 0.25);
        border-radius: 14px;
        padding: 16px 10px;
        min-height: 420px;
        max-height: 520px;
        overflow-y: auto;
        margin-bottom: 14px;
    }

    /* ---- User bubble ---- */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background: rgba(45, 158, 95, 0.15) !important;
        border-radius: 14px;
        padding: 8px 12px;
        margin: 6px 0;
    }

    /* ---- Assistant bubble ---- */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        background: rgba(255,255,255,0.06) !important;
        border-radius: 14px;
        padding: 8px 12px;
        margin: 6px 0;
    }

    /* ---- Chat message text ---- */
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span {
        color: #e8f5e9 !important;
    }

    /* ---- BLACK input box ---- */
    .stChatInput textarea,
    .stChatInput > div > div > textarea {
        background-color: #000000 !important;
        color: #00ff88 !important;
        border: 1px solid #2d9e5f !important;
        border-radius: 10px !important;
        font-size: 15px !important;
    }
    .stChatInput textarea::placeholder {
        color: #3a7d54 !important;
    }
    .stChatInput button {
        background: #1b7a3e !important;
        color: white !important;
        border-radius: 8px !important;
    }

    /* ---- Quick reply buttons ---- */
    .stButton > button {
        background: rgba(27, 122, 62, 0.75) !important;
        color: #d4edda !important;
        border: 1px solid rgba(82,183,136,0.4) !important;
        border-radius: 20px !important;
        font-size: 12px !important;
        padding: 5px 12px !important;
        width: 100%;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: rgba(45, 158, 95, 0.95) !important;
        border-color: #52b788 !important;
        transform: translateY(-1px);
    }

    /* ---- Metric / tip cards ---- */
    .tip-card {
        background: rgba(45, 158, 95, 0.12);
        border: 1px solid rgba(45, 158, 95, 0.25);
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        margin-bottom: 8px;
        color: #d4edda;
    }
    .tip-card .tip-icon { font-size: 22px; }
    .tip-card .tip-title { font-weight: 700; font-size: 13px; color: #52b788; }
    .tip-card .tip-desc  { font-size: 11px; color: rgba(210,237,218,0.7); }

    /* ---- Section labels ---- */
    .section-label {
        color: #52b788 !important;
        font-size: 13px;
        font-weight: 600;
        margin: 10px 0 4px;
        letter-spacing: 0.5px;
    }

    /* ---- Hide default streamlit elements ---- */
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }
</style>
""", unsafe_allow_html=True)


# ---- Session State ----
if "session_id"    not in st.session_state: st.session_state.session_id    = str(uuid.uuid4())[:8]
if "messages"      not in st.session_state: st.session_state.messages      = []
if "connected"     not in st.session_state: st.session_state.connected     = False
if "msg_count"     not in st.session_state: st.session_state.msg_count     = 0
if "trip"          not in st.session_state:
    st.session_state.trip = {"destination": "—", "dates": "—", "budget": "—",
                             "travelers": "—", "sustainability": "—"}


# ---- Helpers ----
def check_connection() -> bool:
    try:
        r = requests.get("http://localhost:5005/", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def send_to_rasa(message: str) -> list:
    try:
        r = requests.post(RASA_API_URL,
                          json={"sender": st.session_state.session_id, "message": message},
                          timeout=15)
        if r.status_code == 200:
            return r.json()
        return [{"text": f"⚠️ Server error {r.status_code}"}]
    except requests.exceptions.ConnectionError:
        return [{"text": "🔴 **Cannot connect to Rasa.**\n\nMake sure:\n- `rasa run --enable-api --cors \"*\"` is running\n- `rasa run actions` is running"}]
    except requests.exceptions.Timeout:
        return [{"text": "⏳ Server timeout. Please try again."}]
    except Exception as e:
        return [{"text": f"❌ Error: {e}"}]


def update_trip_slots(text: str):
    """Scan bot/user text and update sidebar trip details."""
    t = st.session_state.trip
    tl = text.lower()
    if "destination:" in tl:
        parts = text.split("Destination:")
        if len(parts) > 1:
            t["destination"] = parts[1].split("\n")[0].strip()
    if "travel dates:" in tl:
        parts = text.split("Travel Dates:")
        if len(parts) > 1:
            t["dates"] = parts[1].split("\n")[0].strip()
    if "budget:" in tl:
        parts = text.split("Budget:")
        if len(parts) > 1:
            t["budget"] = parts[1].split("\n")[0].strip()
    if "travelers:" in tl:
        parts = text.split("Travelers:")
        if len(parts) > 1:
            t["travelers"] = parts[1].split("\n")[0].strip()
    if "sustainability level:" in tl or "sustainability:" in tl:
        for key in ["Sustainability Level:", "Sustainability:"]:
            if key in text:
                parts = text.split(key)
                if len(parts) > 1:
                    t["sustainability"] = parts[1].split("\n")[0].strip()
                    break


def add_user_msg(text: str):
    st.session_state.messages.append({"role": "user", "content": text,
                                       "time": datetime.now().strftime("%H:%M")})
    st.session_state.msg_count += 1


def add_bot_msg(text: str):
    st.session_state.messages.append({"role": "assistant", "content": text,
                                       "time": datetime.now().strftime("%H:%M")})
    update_trip_slots(text)


def process_input(user_text: str):
    """Send to Rasa and store responses."""
    user_text = user_text.strip()
    if not user_text:
        return
    add_user_msg(user_text)
    with st.spinner("🌿 Thinking..."):
        responses = send_to_rasa(user_text)
    for resp in responses:
        if "text" in resp and resp["text"]:
            add_bot_msg(resp["text"])


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 🌿 Eco-Travel Advisor")
    st.markdown("---")

    # Connection
    if st.button("🔄 Check Connection", use_container_width=True):
        st.session_state.connected = check_connection()

    if st.session_state.connected:
        st.success("✅ Connected to Rasa")
    else:
        st.warning("⚠️ Not connected to Rasa")

    st.markdown("---")

    # Trip summary
    st.markdown('<p class="section-label">📋 YOUR TRIP DETAILS</p>', unsafe_allow_html=True)
    t = st.session_state.trip
    st.markdown(f"🗺️ **Destination:** {t['destination']}")
    st.markdown(f"📅 **Dates:** {t['dates']}")
    st.markdown(f"💰 **Budget:** {t['budget']}")
    st.markdown(f"👥 **Travelers:** {t['travelers']}")
    st.markdown(f"🌱 **Sustainability:** {t['sustainability']}")

    st.markdown("---")

    # Eco fact
    facts = [
        "🚆 Trains emit 90% less CO₂ than flights on the same route.",
        "🏨 Eco-certified hotels save up to 30% more water.",
        "🌱 Planting 1 tree absorbs ~21 kg CO₂ per year.",
        "☀️ Solar-powered lodges are the fastest growing accommodation type.",
        "♻️ You can offset 1 tonne of CO₂ for as little as $10.",
        "🚴 Cycling locally produces zero emissions and is free.",
    ]
    st.info(random.choice(facts))

    st.markdown("---")
    st.caption(f"Session: `{st.session_state.session_id}` | Messages: {st.session_state.msg_count}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset", use_container_width=True):
            for key in ["messages", "trip", "msg_count", "session_id"]:
                del st.session_state[key]
            st.rerun()
    with col2:
        if st.session_state.messages:
            log = "\n".join([f"[{m['time']}] {m['role'].upper()}: {m['content']}"
                             for m in st.session_state.messages])
            st.download_button("📥 Export", log,
                               file_name=f"eco_chat_{st.session_state.session_id}.txt",
                               mime="text/plain", use_container_width=True)


# ============================================================
# MAIN LAYOUT
# ============================================================
col_chat, col_tips = st.columns([3, 1])

with col_chat:
    # Header
    st.markdown("""
    <div class="eco-header">
        <h1>🌿 Eco-Travel Advisor</h1>
        <p>Your AI guide to sustainable &amp; eco-friendly travel</p>
    </div>
    """, unsafe_allow_html=True)

    # ---- Chat messages (native st.chat_message) ----
    chat_container = st.container(height=480)
    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                "<p style='text-align:center; color:rgba(210,237,218,0.45); margin-top:60px'>"
                "👋 Start by clicking a Quick Action below or type your message!</p>",
                unsafe_allow_html=True
            )
        for msg in st.session_state.messages:
            role = msg["role"]
            avatar = "🌿" if role == "assistant" else "🧑"
            with st.chat_message(role, avatar=avatar):
                st.markdown(msg["content"])
                st.caption(msg["time"])

    # ---- BLACK chat input ----
    user_input = st.chat_input(
        "Type your message here... (e.g., 'I want to plan an eco trip to Costa Rica')"
    )
    if user_input:
        process_input(user_input)
        st.rerun()

    # ---- Quick reply buttons ----
    st.markdown('<p class="section-label">⚡ QUICK ACTIONS</p>', unsafe_allow_html=True)
    quick = [
        ("🗺️ Plan a Trip",       "I want to plan an eco-friendly trip"),
        ("🏨 Eco Hotels",         "Show me eco-friendly hotels"),
        ("🚆 Green Transport",    "What are sustainable transport options?"),
        ("🌍 Carbon Footprint",   "Calculate my carbon footprint"),
        ("🎭 Activities",         "What eco-friendly activities are available?"),
        ("♻️ Carbon Offsets",     "Tell me about carbon offset programs"),
        ("👤 Human Agent",        "I want to speak with a human agent"),
        ("❓ Help",               "What can you help me with?"),
    ]
    rows = [quick[:4], quick[4:]]
    for row in rows:
        cols = st.columns(4)
        for i, (label, msg) in enumerate(row):
            with cols[i]:
                if st.button(label, key=f"qr_{label}", use_container_width=True):
                    process_input(msg)
                    st.rerun()


with col_tips:
    st.markdown('<p class="section-label">🌱 CARBON TIPS</p>', unsafe_allow_html=True)
    tips = [
        ("✈️", "Flight vs Train",  "Trains emit up to 90% less CO₂"),
        ("🏨", "Eco Hotels",       "Look for Green Key or Rainforest Alliance"),
        ("🥗", "Local Food",       "Eat local — cuts food-miles by 80%"),
        ("🚴", "Cycle Locally",    "Zero emissions, authentic experience"),
        ("♻️", "Offset Carbon",    "Offset from just $10 per tonne"),
    ]
    for icon, title, desc in tips:
        st.markdown(f"""
        <div class="tip-card">
            <div class="tip-icon">{icon}</div>
            <div class="tip-title">{title}</div>
            <div class="tip-desc">{desc}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p class="section-label">📊 ECO SCORE GUIDE</p>', unsafe_allow_html=True)
    st.markdown("🟢 **90–100** Excellent")
    st.markdown("🟡 **70–89** Good")
    st.markdown("🔴 **< 70** Needs Work")

    st.markdown("---")
    st.markdown('<p class="section-label">🔗 RESOURCES</p>', unsafe_allow_html=True)
    st.markdown("• [Gold Standard](https://goldstandard.org)")
    st.markdown("• [Green Key](https://www.greenkey.global)")
    st.markdown("• [Atmosfair](https://www.atmosfair.de)")
    st.markdown("• [Rainforest Alliance](https://www.rainforest-alliance.org)")
