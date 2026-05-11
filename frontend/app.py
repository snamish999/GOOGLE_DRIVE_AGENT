"""
app.py  —  Streamlit Frontend for TailorTalk Drive Agent
─────────────────────────────────────────────────────────
Run with:  streamlit run app.py
"""

import time
import os
import requests
import streamlit as st

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Google Drive Agent",
    page_icon="🗂️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS — clean, professional look
# ──────────────────────────────────────────────

st.markdown(
    """
    <style>
        /* ── General ── */
        body { font-family: 'Inter', sans-serif; }

        /* ── Header ── */
        .tt-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem 2rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            color: white;
            text-align: center;
        }
        .tt-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
        .tt-header p  { margin: 0.3rem 0 0; opacity: 0.85; font-size: 0.95rem; }

        /* ── Chat bubbles ── */
        .chat-user {
            background: #667eea;
            color: white;
            padding: 0.75rem 1.1rem;
            border-radius: 18px 18px 4px 18px;
            margin: 0.4rem 0;
            max-width: 80%;
            margin-left: auto;
            word-wrap: break-word;
        }
        .chat-bot {
            background: #f4f6fb;
            color: #1a1a2e;
            padding: 0.75rem 1.1rem;
            border-radius: 18px 18px 18px 4px;
            margin: 0.4rem 0;
            max-width: 85%;
            border: 1px solid #e0e4f0;
            word-wrap: break-word;
        }
        .chat-label {
            font-size: 0.7rem;
            color: #888;
            margin-bottom: 2px;
        }

        /* ── Sidebar ── */
        .sidebar-tip {
            background: #f0f4ff;
            border-left: 3px solid #667eea;
            padding: 0.6rem 0.8rem;
            border-radius: 0 8px 8px 0;
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
            color: #333;
        }

        /* ── Input area ── */
        .stTextInput > div > div > input {
            border-radius: 24px !important;
            border: 2px solid #e0e4f0 !important;
            padding: 0.6rem 1.2rem !important;
        }
        .stButton > button {
            border-radius: 24px !important;
            background: linear-gradient(135deg, #667eea, #764ba2) !important;
            color: white !important;
            border: none !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.5rem !important;
        }
        .stButton > button:hover {
            opacity: 0.9;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Session State Init
# ──────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                "👋 Hi! I'm **DriveBot**, your Google Drive assistant.\n\n"
                "I can help you find files by **name**, **type**, **content**, or **date**.\n\n"
                "Try asking me:\n"
                "- *\"Show me all PDFs\"*\n"
                "- *\"Find files named budget\"*\n"
                "- *\"List all Google Sheets modified this month\"*\n"
                "- *\"Search for documents about marketing\"*"
            ),
        }
    )

# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🗂️ DriveBot")
    st.markdown("**Conversational Google Drive Search**")
    st.divider()

    st.markdown("### 💡 Example Queries")
    example_queries = [
        "Show me all PDF files",
        "Find files named 'report'",
        "List all Google Sheets",
        "Find images uploaded this week",
        "Search documents about sales",
        "Show files modified last month",
        "Find all presentations",
        "Look for files containing 'invoice'",
    ]
    for q in example_queries:
        st.markdown(f'<div class="sidebar-tip">💬 {q}</div>', unsafe_allow_html=True)

    st.divider()

    # Backend health check
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if r.status_code == 200:
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Error")
    except Exception:
        st.error("❌ Backend Offline\nMake sure FastAPI is running on port 8000")

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────

st.markdown(
    """
    <div class="tt-header">
        <h1>🗂️ Google Drive Agent</h1>
        <p>Search your Google Drive through natural conversation</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Chat Display
# ──────────────────────────────────────────────

chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-label" style="text-align:right">You</div>'
                f'<div class="chat-user">{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-label">🤖 DriveBot</div>',
                unsafe_allow_html=True,
            )
            # Use st.markdown for proper markdown rendering in bot messages
            with st.container():
                st.markdown(
                    f'<div class="chat-bot">', unsafe_allow_html=True
                )
                st.markdown(msg["content"])
                st.markdown("</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Input Area
# ──────────────────────────────────────────────

st.divider()

col1, col2 = st.columns([5, 1])

with col1:
    user_input = st.text_input(
        label="Message",
        placeholder="Ask me to find files... e.g. 'Show all PDFs'",
        label_visibility="collapsed",
        key="user_input_field",
    )

with col2:
    def _handle_send():
        st.session_state.pending_user_input = st.session_state.user_input_field
        st.session_state.user_input_field = ""
        st.session_state.send_clicked = True

    send_clicked = st.button(
        "Send 🚀",
        use_container_width=True,
        on_click=_handle_send,
    )

# ──────────────────────────────────────────────
# Handle Send
# ──────────────────────────────────────────────

def call_backend(message: str, history: list[dict]) -> str:
    """POST to FastAPI /chat and return the reply string."""
    payload = {
        "message": message,
        "history": [
            {"role": m["role"], "content": m["content"]}
            for m in history
            if m["role"] in ("user", "assistant")
        ],
    }
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["reply"]
    except requests.exceptions.ConnectionError:
        return (
            "❌ **Cannot reach the backend.**\n\n"
            "Make sure FastAPI is running:\n"
            "```\ncd backend && uvicorn main:app --reload\n```"
        )
    except requests.exceptions.Timeout:
        return "⏱️ The request timed out. Please try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"


pending_input = st.session_state.get("pending_user_input", "")
should_send = st.session_state.get("send_clicked", False)

if should_send and pending_input.strip():
    # Add user message
    st.session_state.messages.append(
        {"role": "user", "content": pending_input.strip()}
    )

    # Show thinking indicator
    with st.spinner("🔍 DriveBot is searching..."):
        reply = call_backend(
            message=pending_input.strip(),
            history=st.session_state.messages[:-1],  # history without current msg
        )

    # Add assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Reset send state
    st.session_state.send_clicked = False
    st.session_state.pending_user_input = ""

    # Rerun to refresh UI
    st.rerun()
