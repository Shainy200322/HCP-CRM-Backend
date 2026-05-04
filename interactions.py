"""
LangGraph AI Agent for HCP CRM
Tools: log_interaction, edit_interaction, get_hcp_history, 
       suggest_follow_ups, analyze_sentiment, summarize_interaction
"""

import os
import json
from typing import TypedDict, Annotated, List, Optional
from datetime import datetime
import operator

from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# ─── LLM Setup ───────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your-groq-api-key-here")

llm_primary = ChatGroq(
    model="gemma2-9b-it",
    api_key=GROQ_API_KEY,
    temperature=0.3,
)

llm_large = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.2,
)

# ─── In-memory store (replace with DB calls in production) ───────────────────
_interaction_store: dict = {}
_hcp_store: dict = {
    "Dr. Smith": {"specialty": "Oncology", "territory": "North", "interactions": []},
    "Dr. Sharma": {"specialty": "Cardiology", "territory": "South", "interactions": []},
    "Dr. Patel": {"specialty": "Neurology", "territory": "East", "interactions": []},
}

# ─── Tool 1: Log Interaction ──────────────────────────────────────────────────
@tool
def log_interaction(
    hcp_name: str,
    interaction_type: str,
    topics_discussed: str,
    sentiment: str = "Neutral",
    outcomes: str = "",
    follow_up_actions: str = "",
    attendees: str = "",
    materials_shared: str = "",
    samples_distributed: str = "",
    date: str = "",
    time: str = "",
) -> str:
    """
    Log a new interaction with an HCP (Healthcare Professional).
    Use the LLM to extract entities, summarize topics, and generate 
    AI-suggested follow-ups. Stores structured data in the database.
    
    Args:
        hcp_name: Name of the healthcare professional
        interaction_type: Type (Meeting, Call, Email, Conference, etc.)
        topics_discussed: Key discussion points from the meeting
        sentiment: Observed sentiment (Positive/Neutral/Negative)
        outcomes: Key outcomes or agreements reached
        follow_up_actions: Next steps or tasks
        attendees: Comma-separated attendee names
        materials_shared: Brochures, PDFs, or other materials shared
        samples_distributed: Drug samples or product samples given
        date: Date of interaction (YYYY-MM-DD)
        time: Time of interaction (HH:MM)
    """
    interaction_id = f"INT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # AI Summarization via LLM
    summary_prompt = f"""
    Summarize this pharma rep interaction with {hcp_name} in 2-3 sentences:
    Type: {interaction_type}
    Topics: {topics_discussed}
    Outcomes: {outcomes}
    Focus on medical/business relevance.
    """
    try:
        summary_resp = llm_primary.invoke(summary_prompt)
        ai_summary = summary_resp.content
    except Exception:
        ai_summary = f"Met with {hcp_name} to discuss {topics_discussed[:100]}."

    # AI Follow-up suggestions
    followup_prompt = f"""
    Based on this pharma rep meeting with {hcp_name} ({interaction_type}):
    Topics: {topics_discussed}
    Sentiment: {sentiment}
    Outcomes: {outcomes}
    
    Suggest 3 specific follow-up actions as a JSON array of strings.
    Example: ["Schedule follow-up in 2 weeks", "Send product brochure", "Add to advisory board"]
    Return ONLY the JSON array, no other text.
    """
    try:
        followup_resp = llm_primary.invoke(followup_prompt)
        suggested_followups = json.loads(followup_resp.content.strip())
    except Exception:
        suggested_followups = [
            f"Schedule follow-up meeting with {hcp_name} in 2 weeks",
            f"Send relevant clinical data to {hcp_name}",
            "Update CRM with interaction notes"
        ]

    interaction = {
        "id": interaction_id,
        "hcp_name": hcp_name,
        "interaction_type": interaction_type,
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "time": time or datetime.now().strftime("%H:%M"),
        "attendees": attendees,
        "topics_discussed": topics_discussed,
        "materials_shared": materials_shared,
        "samples_distributed": samples_distributed,
        "sentiment": sentiment,
        "outcomes": outcomes,
        "follow_up_actions": follow_up_actions,
        "ai_summary": ai_summary,
        "ai_suggested_follow_ups": suggested_followups,
        "logged_at": datetime.now().isoformat(),
    }
    
    _interaction_store[interaction_id] = interaction
    
    return json.dumps({
        "success": True,
        "interaction_id": interaction_id,
        "message": f"Interaction with {hcp_name} logged successfully.",
        "ai_summary": ai_summary,
        "suggested_follow_ups": suggested_followups,
        "interaction": interaction,
    })


# ─── Tool 2: Edit Interaction ─────────────────────────────────────────────────
@tool
def edit_interaction(
    interaction_id: str,
    field: str,
    new_value: str,
) -> str:
    """
    Edit/modify a previously logged HCP interaction.
    Allows updating specific fields of an existing interaction record.
    Re-runs AI summarization if topics or outcomes are changed.
    
    Args:
        interaction_id: The ID of the interaction to edit (e.g., INT-20250419...)
        field: The field to update (topics_discussed, outcomes, sentiment, 
               follow_up_actions, attendees, materials_shared, samples_distributed)
        new_value: The new value for the field
    """
    if interaction_id not in _interaction_store:
        # Try to find by partial match
        matches = [k for k in _interaction_store.keys() if interaction_id.lower() in k.lower()]
        if not matches:
            return json.dumps({
                "success": False,
                "message": f"Interaction {interaction_id} not found. Available: {list(_interaction_store.keys())}"
            })
        interaction_id = matches[0]
    
    interaction = _interaction_store[interaction_id]
    old_value = interaction.get(field, "")
    
    allowed_fields = [
        "topics_discussed", "outcomes", "follow_up_actions", "sentiment",
        "attendees", "materials_shared", "samples_distributed", "interaction_type"
    ]
    
    if field not in allowed_fields:
        return json.dumps({
            "success": False,
            "message": f"Field '{field}' cannot be edited. Allowed: {allowed_fields}"
        })
    
    interaction[field] = new_value
    interaction["updated_at"] = datetime.now().isoformat()
    
    # Re-run AI summary if core content changed
    if field in ["topics_discussed", "outcomes"]:
        try:
            summary_prompt = f"""
            Summarize this updated pharma rep interaction with {interaction['hcp_name']}:
            Topics: {interaction['topics_discussed']}
            Outcomes: {interaction['outcomes']}
            Keep it to 2-3 sentences, medically focused.
            """
            summary_resp = llm_primary.invoke(summary_prompt)
            interaction["ai_summary"] = summary_resp.content
        except Exception:
            pass
    
    _interaction_store[interaction_id] = interaction
    
    return json.dumps({
        "success": True,
        "interaction_id": interaction_id,
        "message": f"Field '{field}' updated successfully.",
        "field": field,
        "old_value": old_value,
        "new_value": new_value,
        "updated_interaction": interaction,
    })


# ─── Tool 3: Get HCP History ──────────────────────────────────────────────────
@tool
def get_hcp_history(hcp_name: str, limit: int = 5) -> str:
    """
    Retrieve interaction history for a specific HCP.
    Returns past meetings, sentiment trends, and engagement patterns.
    Useful for pre-call planning and relationship analysis.
    
    Args:
        hcp_name: Name of the healthcare professional
        limit: Maximum number of recent interactions to return (default 5)
    """
    history = [
        v for v in _interaction_store.values()
        if hcp_name.lower() in v.get("hcp_name", "").lower()
    ]
    history.sort(key=lambda x: x.get("logged_at", ""), reverse=True)
    history = history[:limit]
    
    # Sentiment trend analysis
    sentiments = [h.get("sentiment", "Neutral") for h in history]
    sentiment_counts = {s: sentiments.count(s) for s in set(sentiments)}
    
    # AI analysis
    if history:
        analysis_prompt = f"""
        Analyze this HCP's engagement pattern based on {len(history)} interactions:
        Sentiments: {sentiments}
        Topics covered: {[h.get('topics_discussed', '')[:80] for h in history]}
        
        Provide a 2-sentence strategic insight for the next call.
        """
        try:
            analysis_resp = llm_primary.invoke(analysis_prompt)
            ai_insight = analysis_resp.content
        except Exception:
            ai_insight = f"{hcp_name} has had {len(history)} recorded interactions."
    else:
        ai_insight = f"No prior interactions found with {hcp_name}. This would be a first contact."
    
    return json.dumps({
        "success": True,
        "hcp_name": hcp_name,
        "total_interactions": len(history),
        "sentiment_trend": sentiment_counts,
        "ai_insight": ai_insight,
        "recent_interactions": history,
    })


# ─── Tool 4: Suggest Follow-Ups ───────────────────────────────────────────────
@tool
def suggest_follow_ups(
    hcp_name: str,
    topics_discussed: str,
    sentiment: str,
    interaction_type: str = "Meeting",
) -> str:
    """
    Generate AI-powered follow-up action suggestions for an HCP interaction.
    Uses LLM to create personalized, context-aware next steps based on 
    the HCP's specialty, sentiment, and discussion topics.
    
    Args:
        hcp_name: Name of the healthcare professional
        topics_discussed: What was discussed in the interaction
        sentiment: The HCP's observed sentiment (Positive/Neutral/Negative)
        interaction_type: Type of interaction that occurred
    """
    hcp_data = _hcp_store.get(hcp_name, {})
    specialty = hcp_data.get("specialty", "General Practice")
    
    prompt = f"""
    You are a pharma sales AI assistant. Generate 5 specific follow-up actions for:
    
    HCP: {hcp_name} ({specialty})
    Interaction: {interaction_type}
    Topics: {topics_discussed}
    Sentiment: {sentiment}
    
    Return ONLY a JSON object with this structure:
    {{
        "immediate": ["action1", "action2"],
        "within_week": ["action3"],
        "long_term": ["action4", "action5"],
        "risk_flags": ["any concerns if negative sentiment"]
    }}
    """
    
    try:
        resp = llm_large.invoke(prompt)
        content = resp.content.strip()
        # Clean JSON
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        follow_ups = json.loads(content)
    except Exception:
        follow_ups = {
            "immediate": [
                f"Send thank-you email to {hcp_name}",
                "Update CRM with meeting notes"
            ],
            "within_week": [
                f"Share relevant clinical study on discussed topics",
            ],
            "long_term": [
                f"Schedule quarterly review with {hcp_name}",
                f"Invite {hcp_name} to upcoming product symposium"
            ],
            "risk_flags": [f"Monitor sentiment trend for {hcp_name}"] if sentiment == "Negative" else []
        }
    
    return json.dumps({
        "success": True,
        "hcp_name": hcp_name,
        "follow_ups": follow_ups,
        "priority": "High" if sentiment == "Positive" else ("Medium" if sentiment == "Neutral" else "Critical"),
    })


# ─── Tool 5: Analyze Sentiment ────────────────────────────────────────────────
@tool
def analyze_sentiment(text: str, hcp_name: str = "") -> str:
    """
    Analyze the sentiment and key entities from interaction notes or chat text.
    Uses LLM to extract: overall sentiment, key concerns, product mentions,
    competitor mentions, and objection flags for the sales team.
    
    Args:
        text: The interaction notes, transcript, or chat text to analyze
        hcp_name: Optional HCP name for context
    """
    prompt = f"""
    Analyze this pharma sales interaction text and extract key insights:
    
    Text: "{text}"
    HCP: {hcp_name or "Unknown"}
    
    Return ONLY a JSON object:
    {{
        "overall_sentiment": "Positive|Neutral|Negative",
        "sentiment_score": 0.85,
        "key_topics": ["topic1", "topic2"],
        "product_mentions": ["product1"],
        "competitor_mentions": ["competitor1"],
        "objections": ["objection1"],
        "buying_signals": ["signal1"],
        "recommended_action": "Brief next step recommendation",
        "confidence": 0.9
    }}
    """
    
    try:
        resp = llm_primary.invoke(prompt)
        content = resp.content.strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        analysis = json.loads(content)
    except Exception:
        # Fallback simple analysis
        text_lower = text.lower()
        if any(w in text_lower for w in ["great", "interested", "yes", "positive", "excellent"]):
            sentiment = "Positive"
            score = 0.8
        elif any(w in text_lower for w in ["no", "not", "concern", "issue", "problem", "negative"]):
            sentiment = "Negative"
            score = 0.3
        else:
            sentiment = "Neutral"
            score = 0.5
        
        analysis = {
            "overall_sentiment": sentiment,
            "sentiment_score": score,
            "key_topics": [],
            "product_mentions": [],
            "competitor_mentions": [],
            "objections": [],
            "buying_signals": [],
            "recommended_action": "Review notes and schedule follow-up",
            "confidence": 0.6
        }
    
    return json.dumps({"success": True, "analysis": analysis})


# ─── Tool 6: Summarize Voice Note / Free Text ─────────────────────────────────
@tool
def summarize_interaction_notes(raw_notes: str, hcp_name: str = "") -> str:
    """
    Convert raw, unstructured voice-note transcriptions or free-text notes 
    into a structured interaction log. Extracts: HCP name, date, topics,
    materials shared, samples, sentiment, outcomes, and follow-up actions.
    
    Args:
        raw_notes: Unstructured text from voice note or free-form entry
        hcp_name: Optional HCP name to help with extraction
    """
    prompt = f"""
    Convert these raw pharma rep field notes into a structured CRM record:
    
    Raw Notes: "{raw_notes}"
    Known HCP: {hcp_name or "Extract from notes"}
    
    Return ONLY a JSON object:
    {{
        "hcp_name": "extracted or provided name",
        "interaction_type": "Meeting|Call|Email|Conference|Other",
        "date": "YYYY-MM-DD or today",
        "topics_discussed": "clean summary of discussion topics",
        "materials_shared": "list of materials",
        "samples_distributed": "list of samples",
        "sentiment": "Positive|Neutral|Negative",
        "outcomes": "key agreements or decisions",
        "follow_up_actions": "next steps",
        "summary": "2-sentence professional summary"
    }}
    """
    
    try:
        resp = llm_large.invoke(prompt)
        content = resp.content.strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        structured = json.loads(content)
    except Exception:
        structured = {
            "hcp_name": hcp_name or "Unknown HCP",
            "interaction_type": "Meeting",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "topics_discussed": raw_notes[:200],
            "materials_shared": "",
            "samples_distributed": "",
            "sentiment": "Neutral",
            "outcomes": "",
            "follow_up_actions": "",
            "summary": f"Interaction notes recorded for {hcp_name or 'HCP'}."
        }
    
    return json.dumps({"success": True, "structured_data": structured})


# ─── LangGraph Agent State ────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_interaction: Optional[dict]
    session_id: str


# ─── Agent Graph Builder ──────────────────────────────────────────────────────
tools = [
    log_interaction,
    edit_interaction,
    get_hcp_history,
    suggest_follow_ups,
    analyze_sentiment,
    summarize_interaction_notes,
]

tool_node = ToolNode(tools)
llm_with_tools = llm_primary.bind_tools(tools)


def agent_node(state: AgentState):
    """Main agent reasoning node."""
    system_msg = HumanMessage(content="""You are an AI assistant for a pharma CRM system helping field 
    representatives log and manage HCP (Healthcare Professional) interactions. 
    
    You have access to these tools:
    1. log_interaction - Log a new HCP meeting/call/interaction
    2. edit_interaction - Modify an existing interaction record  
    3. get_hcp_history - Retrieve past interactions with an HCP
    4. suggest_follow_ups - Generate AI follow-up recommendations
    5. analyze_sentiment - Analyze sentiment from interaction text
    6. summarize_interaction_notes - Convert raw notes to structured data
    
    Be concise, professional, and always confirm actions taken.""")
    
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState):
    """Route to tool node or end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def build_agent():
    """Build and compile the LangGraph agent."""
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


agent_graph = build_agent()


def run_agent(user_message: str, session_id: str = "default", history: list = None) -> dict:
    """Run the agent with a user message and return the response."""
    messages = []
    
    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
    
    messages.append(HumanMessage(content=user_message))
    
    state = {
        "messages": messages,
        "current_interaction": None,
        "session_id": session_id,
    }
    
    try:
        result = agent_graph.invoke(state)
        last_msg = result["messages"][-1]
        
        # Extract tool results if any
        tool_results = []
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage):
                try:
                    tool_results.append(json.loads(msg.content))
                except Exception:
                    tool_results.append({"raw": msg.content})
        
        return {
            "response": last_msg.content if hasattr(last_msg, "content") else str(last_msg),
            "tool_results": tool_results,
            "success": True,
        }
    except Exception as e:
        return {
            "response": f"I encountered an issue: {str(e)}. Please try rephrasing your request.",
            "tool_results": [],
            "success": False,
            "error": str(e),
        }