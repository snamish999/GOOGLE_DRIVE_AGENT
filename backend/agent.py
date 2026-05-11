

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Sequence, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from drive_service import search_drive_files

load_dotenv()

# ──────────────────────────────────────────────
# 1. Tool Definition
# ──────────────────────────────────────────────

@tool
def drive_search_tool(query: str) -> str:
    """
    Search for files in the designated Google Drive folder.

    Use this tool whenever the user wants to find, list, or filter files.
    
    The `query` argument must be a valid Google Drive API q-parameter string.
    
    Query syntax examples:
      - Exact name:         name = 'Budget 2024'
      - Partial name:       name contains 'budget'
      - File type (PDF):    mimeType = 'application/pdf'
      - Google Docs:        mimeType = 'application/vnd.google-apps.document'
      - Google Sheets:      mimeType = 'application/vnd.google-apps.spreadsheet'
      - Google Slides:      mimeType = 'application/vnd.google-apps.presentation'
      - Images:             mimeType contains 'image/'
      - Full-text search:   fullText contains 'quarterly revenue'
      - Modified after:     modifiedTime > '2024-01-01T00:00:00'
      - Modified before:    modifiedTime < '2024-06-01T00:00:00'
      - Combined:           name contains 'report' and mimeType = 'application/pdf'
      - OR logic:           name contains 'invoice' or fullText contains 'invoice'
    
    Always use AND / OR (uppercase) for combining conditions.
    Always wrap string values in single quotes.
    Return only the q-string, nothing else.
    """
    try:
        results = search_drive_files(query=query, max_results=15)
        if not results:
            return json.dumps({"found": 0, "files": []})
        return json.dumps({"found": len(results), "files": results}, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "files": []})


TOOLS = [drive_search_tool]

# ──────────────────────────────────────────────
# 2. LLM Setup
# ──────────────────────────────────────────────

def _build_llm():
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
    if groq_key:
        return ChatGroq(
            model=groq_model,
            groq_api_key=groq_key,
            temperature=0.2,
        ).bind_tools(TOOLS)

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key:
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=gemini_key,
            temperature=0.2,
        ).bind_tools(TOOLS)

    raise RuntimeError("Missing GROQ_API_KEY or GEMINI_API_KEY in environment.")


SYSTEM_PROMPT = """You are DriveBot 🤖, a smart and friendly Google Drive assistant.

Your job is to help users find and discover files in their Google Drive.

CAPABILITIES:
- Search files by name (exact or partial match)
- Filter by file type (PDF, Google Doc, Sheet, Slide, Image, etc.)
- Search by content inside documents (fullText)
- Filter by modification date
- Combine multiple filters

BEHAVIOUR RULES:
1. When the user asks to find/search/show/list files → ALWAYS call drive_search_tool.
2. Translate natural language into a valid Google Drive q-parameter string.
3. After getting results, present them in a clean, readable format with:
   - File name (as a clickable link if webViewLink is available)
   - File type
   - Last modified date
4. If no files are found, suggest alternative search terms.
5. Keep responses concise and helpful.
6. For follow-up filters ("only show PDFs", "from last month"), refine the query.
7. Never make up files — only report what the Drive API returns.

DATE CONTEXT: Today's date is available via the system clock. Use it for relative dates like
"last week", "this month", "yesterday".

FORMAT for file results:
📄 **File Name** — [Open in Drive](link)
   Type: Google Doc | Modified: Jan 15, 2024

Always be conversational and helpful!
"""


def _start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_week(dt: datetime) -> datetime:
    start = _start_of_day(dt)
    return start - timedelta(days=start.weekday())


def _start_of_month(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _normalize_relative_dates(text: str) -> str:
    """Append explicit ISO timestamps for common relative date phrases."""
    now = datetime.now(timezone.utc)
    replacements: dict[str, datetime] = {
        "last hour": now - timedelta(hours=1),
        "last day": now - timedelta(days=1),
        "last week": now - timedelta(days=7),
        "last month": now - timedelta(days=30),
        "yesterday": _start_of_day(now - timedelta(days=1)),
        "today": _start_of_day(now),
        "this week": _start_of_week(now),
        "this month": _start_of_month(now),
    }

    normalized = text
    for phrase, dt in replacements.items():
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        if pattern.search(normalized):
            iso = dt.isoformat().replace("+00:00", "Z")
            normalized = pattern.sub(f"{phrase} (since {iso})", normalized)

    return normalized

# ──────────────────────────────────────────────
# 3. LangGraph State & Nodes
# ──────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def call_llm(state: AgentState) -> dict:
    """Node: Send messages to LLM, get response (may include tool calls)."""
    llm = _build_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
    response = llm.invoke(messages)
    return {"messages": [response]}


def call_tools(state: AgentState) -> dict:
    """Node: Execute any tool calls the LLM requested."""
    last_message = state["messages"][-1]
    tool_messages = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name == "drive_search_tool":
            result = drive_search_tool.invoke(tool_args)
        else:
            result = json.dumps({"error": f"Unknown tool: {tool_name}"})

        tool_messages.append(
            ToolMessage(
                content=result,
                tool_call_id=tool_call["id"],
                name=tool_name,
            )
        )

    return {"messages": tool_messages}


def should_use_tools(state: AgentState) -> str:
    """Edge: Route to tools node or END based on last LLM message."""
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


# ──────────────────────────────────────────────
# 4. Build the Graph
# ──────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("llm", call_llm)
    graph.add_node("tools", call_tools)
    graph.set_entry_point("llm")
    graph.add_conditional_edges("llm", should_use_tools, {"tools": "tools", END: END})
    graph.add_edge("tools", "llm")  # After tools → back to LLM to format response
    return graph.compile()


GRAPH = build_graph()

# ──────────────────────────────────────────────
# 5. Public API used by FastAPI
# ──────────────────────────────────────────────

def run_agent(user_message: str, history: list[dict]) -> str:
    """
    Run the agent with full conversation history.

    Args:
        user_message: Latest user input string.
        history:      List of {"role": "user"|"assistant", "content": "..."} dicts.

    Returns:
        Agent's reply as a string.
    """
    # Convert history to LangChain message objects
    lc_messages: list[BaseMessage] = []
    for msg in history:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        else:
            lc_messages.append(AIMessage(content=msg["content"]))

    # Add current user message with normalized relative dates
    lc_messages.append(HumanMessage(content=_normalize_relative_dates(user_message)))

    # Invoke graph
    result = GRAPH.invoke({"messages": lc_messages})

    # Extract the final AI message (skip tool messages)
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content

    return "Sorry, I couldn't process that request. Please try again."
