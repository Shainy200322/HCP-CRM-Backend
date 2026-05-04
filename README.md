# 🏥 AI-First CRM — HCP Interaction Logger

> A production-grade, AI-powered Customer Relationship Management system for Life Science field representatives to log, analyze, and manage Healthcare Professional (HCP) interactions — powered by **LangGraph**, **Groq LLMs**, **FastAPI**, and **React + Redux**.

---

## 📋 Table of Contents

- [What This Project Does](#what-this-project-does)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [LangGraph Agent & Tools](#langgraph-agent--tools)
- [Prerequisites](#prerequisites)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Using the Application](#using-the-application)
- [Environment Variables](#environment-variables)

---

## 🎯 What This Project Does

This system helps **pharmaceutical field representatives** log their HCP interactions in two ways:

1. **Structured Form Interface** — Fill in fields manually: HCP name, interaction type, topics, sentiment, outcomes, follow-ups, materials shared, and samples distributed.
2. **Conversational AI Chat** — Simply describe your meeting in plain English (e.g., *"Met Dr. Sharma today, discussed OncoBoost Phase III data, she was very interested, shared the efficacy PDF"*) and the AI agent extracts everything automatically.

The **LangGraph AI agent** sits at the core, orchestrating 6 specialized tools using the **Groq gemma2-9b-it** model (primary) and **llama-3.3-70b-versatile** (for complex reasoning tasks).

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Redux Toolkit, Axios |
| **Backend** | Python 3.11+, FastAPI |
| **AI Framework** | LangGraph (StateGraph) |
| **LLMs** | Groq — `gemma2-9b-it` (primary), `llama-3.3-70b-versatile` (reasoning) |
| **Database** | SQLite (dev) / PostgreSQL or MySQL (production) |
| **Font** | Google Inter |
| **ORM** | SQLAlchemy |

---

## 📁 Project Structure

```
hcp-crm/
│
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Environment variables (create this)
│   │
│   ├── agents/
│   │   └── hcp_agent.py           # ⭐ LangGraph agent + all 6 tools
│   │
│   ├── database/
│   │   └── db.py                  # SQLAlchemy engine + session + Base
│   │
│   ├── models/
│   │   └── models.py              # HCP, Interaction, ChatMessage ORM models
│   │
│   └── routers/
│       ├── interactions.py        # CRUD endpoints for interactions
│       ├── hcp.py                 # HCP management endpoints
│       └── agent.py               # /api/agent/chat + /api/agent/tools
│
├── frontend/
│   ├── package.json
│   └── src/
│       ├── App.js                 # Root component
│       ├── styles/
│       │   └── global.css         # Inter font + CSS variables + animations
│       ├── store/
│       │   ├── store.js           # Redux store configuration
│       │   ├── interactionSlice.js# Interaction state + async thunks
│       │   ├── agentSlice.js      # Chat/agent state + async thunks
│       │   └── hcpSlice.js        # HCP list state
│       └── components/
│           └── LogInteractionScreen.js  # Main UI screen
│
└── README.md
```

---

## 🤖 LangGraph Agent & Tools

The LangGraph agent uses a **StateGraph** with two nodes:
- `agent` — The LLM reasoning node (gemma2-9b-it with tools bound)
- `tools` — The ToolNode that executes whichever tool the agent selects

A **conditional edge** checks after every agent response: if tool_calls exist → route to `tools` → route back to `agent`. If no tool calls → END.

### Agent State
```python
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_interaction: Optional[dict]
    session_id: str
```

### The 6 Tools

---

#### 🔧 Tool 1: `log_interaction` *(Core — Required)*
**Purpose:** Log a brand-new HCP interaction with full AI enrichment.

**What it does:**
1. Accepts all interaction fields (HCP name, type, topics, sentiment, outcomes, etc.)
2. Calls **gemma2-9b-it** to generate a professional 2–3 sentence AI summary
3. Calls **gemma2-9b-it** again to generate 3 personalized follow-up suggestions as structured JSON
4. Assigns a unique ID (`INT-YYYYMMDDHHMMSS`) and stores the record
5. Returns: `interaction_id`, `ai_summary`, `suggested_follow_ups`, full interaction object

**Example trigger:** *"Log a meeting with Dr. Sharma — we discussed OncoBoost Phase III efficacy data, she was very positive, I gave her two samples"*

---

#### 🔧 Tool 2: `edit_interaction` *(Core — Required)*
**Purpose:** Modify a specific field on a previously logged interaction.

**What it does:**
1. Looks up the interaction by ID (supports partial match)
2. Validates the field is editable (topics, outcomes, sentiment, attendees, etc.)
3. Updates the specific field and timestamps the change
4. If `topics_discussed` or `outcomes` changed → **re-runs AI summarization** automatically
5. Returns: old value, new value, updated full record

**Example trigger:** *"Edit the last interaction — change the sentiment to Positive"*

---

#### 🔧 Tool 3: `get_hcp_history`
**Purpose:** Pull full interaction history and engagement analytics for any HCP.

**What it does:**
1. Filters all logged interactions by HCP name (partial match supported)
2. Sorts by most recent first
3. Calculates sentiment trend counts (Positive/Neutral/Negative distribution)
4. Sends history to **gemma2-9b-it** for strategic pre-call insight generation
5. Returns: total count, sentiment breakdown, AI insight, recent interaction list

**Example trigger:** *"Show me Dr. Patel's history"* or *"What's my engagement with Dr. Sharma?"*

---

#### 🔧 Tool 4: `suggest_follow_ups`
**Purpose:** Generate structured, prioritized follow-up action plans post-interaction.

**What it does:**
1. Takes HCP name, topics, sentiment, and interaction type
2. Pulls HCP specialty from the store for context
3. Sends to **llama-3.3-70b-versatile** for high-quality follow-up generation
4. Returns JSON with three tiers: `immediate`, `within_week`, `long_term`, and `risk_flags`
5. Assigns overall priority: High (Positive) / Medium (Neutral) / Critical (Negative)

**Example trigger:** *"What should I do after my meeting with Dr. Kumar who had pricing concerns?"*

---

#### 🔧 Tool 5: `analyze_sentiment`
**Purpose:** Deep NLP analysis of any interaction text — extracts sentiment, objections, signals.

**What it does:**
1. Accepts raw text (notes, transcripts, chat descriptions)
2. Sends to **gemma2-9b-it** for structured extraction
3. Extracts: sentiment + score, key topics, product mentions, competitor mentions, objections, buying signals
4. Returns confidence score and a recommended action
5. Falls back to keyword matching if LLM is unavailable

**Example trigger:** *"Analyze: Dr. Smith was initially hesitant about pricing but got excited when I mentioned the Phase III data. She asked for competitor comparisons."*

---

#### 🔧 Tool 6: `summarize_interaction_notes`
**Purpose:** Convert messy, unstructured voice-note transcriptions into clean CRM records.

**What it does:**
1. Accepts raw free-form text (as if dictated while driving)
2. Sends to **llama-3.3-70b-versatile** for intelligent field extraction
3. Extracts all structured fields: HCP name, type, date, topics, materials, samples, sentiment, outcomes, follow-ups
4. Returns a complete, ready-to-save structured interaction object

**Example trigger:** *"Summarize my notes: Quick call with Dr. Patel around 3pm, she called about the cardiology trial results, seemed interested, asked me to send the Phase II PDF, will follow up Monday"*

---

## ✅ Prerequisites

- **Python** 3.11+
- **Node.js** 18+ and npm
- **Groq API Key** — Get free at [console.groq.com](https://console.groq.com)
- Git

---

## ⚙️ Setup & Installation

### Step 1 — Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/hcp-crm.git
cd hcp-crm
```

### Step 2 — Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3 — Create Environment File

Create a `.env` file inside the `backend/` folder:

```env
GROQ_API_KEY=your_actual_groq_api_key_here
DATABASE_URL=sqlite:///./hcp_crm.db
```

> 💡 To get your Groq API key: Visit [console.groq.com](https://console.groq.com) → Create account → API Keys → Create New Key

### Step 4 — Frontend Setup

```bash
cd ../frontend
npm install
```

---

## 🚀 Running the Application

### Start the Backend

```bash
cd backend
source venv/bin/activate   # or venv\Scripts\activate on Windows

uvicorn main:app --reload --port 8000
```

The API will be live at: `http://localhost:8000`
Swagger docs at: `http://localhost:8000/docs`

### Start the Frontend

Open a new terminal:

```bash
cd frontend
npm start
```

The app will open at: `http://localhost:3000`

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/interactions/` | List all interactions |
| `POST` | `/api/interactions/` | Create new interaction |
| `GET` | `/api/interactions/{id}` | Get single interaction |
| `PUT` | `/api/interactions/{id}` | Update interaction |
| `DELETE` | `/api/interactions/{id}` | Delete interaction |
| `GET` | `/api/hcp/` | List all HCPs |
| `POST` | `/api/hcp/` | Create HCP |
| `POST` | `/api/agent/chat` | Chat with AI agent |
| `GET` | `/api/agent/tools` | List all agent tools |

### Chat API Example

```bash
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Log a meeting with Dr. Sharma — discussed OncoBoost efficacy, positive sentiment, shared Phase III brochure",
    "session_id": "session-001",
    "history": []
  }'
```

---

## 💻 Using the Application

### Form Mode
1. Select or search for an HCP in the "HCP Name" field
2. Choose Interaction Type (Meeting, Call, Email, Conference)
3. Set Date and Time
4. Enter Topics Discussed
5. Add Materials Shared / Samples Distributed
6. Select Sentiment (Positive / Neutral / Negative)
7. Fill Outcomes and Follow-up Actions
8. Click **Log Interaction** — AI will auto-generate summary and follow-up suggestions

### Chat Mode (AI Assistant)
Type natural language commands in the right panel. Try:

```
"Met Dr. Patel today for 30 mins, discussed OncoBoost Phase III results,
 she was very positive, I left 2 samples and the efficacy brochure"

"Show me Dr. Sharma's interaction history"

"Suggest follow-ups for my meeting with Dr. Kumar — he had pricing objections"

"Analyze: The doctor seemed hesitant at first but became very interested
 when I mentioned the trial data. Competitor XYZ was mentioned."

"Summarize my voice note: Quick call with Dr. Reddy, she called about
 the new cardiology indication, send her the latest clinical study PDF"
```

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Your Groq API key from console.groq.com |
| `DATABASE_URL` | ❌ Optional | Defaults to SQLite. For production use: `postgresql://user:pass@host/dbname` |

---

## 📊 Database Schema

### `interactions` table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment primary key |
| hcp_name | VARCHAR | HCP full name |
| interaction_type | VARCHAR | Meeting/Call/Email/Conference |
| date | VARCHAR | Interaction date |
| time | VARCHAR | Interaction time |
| attendees | TEXT | Comma-separated names |
| topics_discussed | TEXT | Discussion content |
| materials_shared | JSON | List of shared materials |
| samples_distributed | JSON | List of samples given |
| sentiment | VARCHAR | Positive/Neutral/Negative |
| outcomes | TEXT | Agreements and decisions |
| follow_up_actions | TEXT | Next steps |
| ai_summary | TEXT | LLM-generated summary |
| ai_suggested_follow_ups | JSON | LLM-generated suggestions |
| created_at | DATETIME | Auto timestamp |
| updated_at | DATETIME | Auto update timestamp |

---

## 🧠 Architecture Diagram

```
User (Browser)
     │
     ▼
React + Redux (Port 3000)
     │  ┌─────────────────┐
     │  │  Form Interface │  ──► Redux Store ──► API calls
     │  └─────────────────┘
     │  ┌─────────────────┐
     │  │  AI Chat Panel  │  ──► Redux Store ──► /api/agent/chat
     │  └─────────────────┘
     │
     ▼
FastAPI Backend (Port 8000)
     │
     ├── /api/interactions  ──► SQLAlchemy ──► SQLite/PostgreSQL
     ├── /api/hcp           ──► SQLAlchemy ──► SQLite/PostgreSQL
     └── /api/agent/chat
              │
              ▼
        LangGraph Agent
        ┌─────────────────────────────────────┐
        │  StateGraph                         │
        │                                     │
        │  HumanMessage ──► [agent_node]      │
        │                        │            │
        │               has tool_calls?       │
        │                   YES │  NO → END   │
        │                       ▼             │
        │                 [tool_node]         │
        │                       │             │
        │         ┌─────────────┴──────────┐  │
        │    Tool 1: log_interaction        │  │
        │    Tool 2: edit_interaction       │  │
        │    Tool 3: get_hcp_history        │  │
        │    Tool 4: suggest_follow_ups     │  │
        │    Tool 5: analyze_sentiment      │  │
        │    Tool 6: summarize_notes        │  │
        │         └───────────── ───────────┘  │
        │                       │              │
        │               back to agent_node     │
        └─────────────────────────────────────-┘
                       │
                       ▼
                 Groq API
            ┌────────────────────────┐
            │ gemma2-9b-it (primary) │
            │ llama-3.3-70b (heavy)  │
            └────────────────────────┘
```

---

## 👨‍💻 Author

Built as part of an AI-First CRM technical assignment for Life Science HCP module design.

**Models Used:**
- `gemma2-9b-it` — Primary agent reasoning, summarization, sentiment analysis
- `llama-3.3-70b-versatile` — Complex reasoning: follow-up generation, voice note structuring
