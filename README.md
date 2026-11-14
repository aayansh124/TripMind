# AI-Powered Multi-Agent Travel Planner

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-StateGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, autonomous **Multi-Agent Travel Planning & Concierge Platform** orchestrated with **LangGraph**, **Google Gemini**, **FastAPI**, and **Streamlit**. The system coordinates specialist AI agents operating in parallel to generate comprehensive, culturally informed travel plans, live flight timetables, accommodation discoveries, localized weather forecasts, itemized day-by-day itineraries, and deterministic budget audits.

---

## 1. Overview & Problem Statement

Modern travel planning is fragmented across dozens of disconnected websites: flight search engines, hotel aggregators, local activity guides, weather radars, and personal budgeting spreadsheets. Travelers waste hours copying details between tabs, reconciling flight arrival logistics with hotel check-in times, and calculating currency-adjusted budgets.

The **AI Multi-Agent Travel Planner** replaces this fragmented experience with an autonomous swarm of specialist agents. By distributing responsibilities across domain-specific agents operating concurrently in a directed graph, the platform produces structured, actionable travel plans with guaranteed arithmetic precision and real-time continuity.

---

## 2. Core Capabilities & Key Features

- **Concurrent Multi-Agent Architecture**: High-throughput parallel execution of Destination, Flight, Accommodation, and Weather agents via LangGraph fan-out and fan-in orchestration.
- **Deterministic Budget Reconciliation**: Financial calculations (lodging, dining, transit, activities, and budget overrun detection) are executed strictly via Python arithmetic rather than relying on LLM estimation.
- **Sourced Intelligence with Truthful Bounds**: Verified external flight status from AviationStack, meteorological observations from OpenWeather, and accommodation discovery from Tavily. No fabricated prices or booking confirmations.
- **Conversational Thread Continuity**: Stateful follow-up support using LangGraph checkpointing (`PostgresSaver` and `MemorySaver`) linked to unique trip IDs.
- **Resilient Layered Infrastructure**: Graceful degradation if PostgreSQL or Redis is offline, allowing complete local execution without crashing.
- **Enterprise SaaS User Interface**: Streamlit UI with tabbed itineraries, financial metrics, system health monitors, and conversational assistance.

---

## 3. High-Level Architecture

The system utilizes a modern tiered architecture separating agent orchestration from API routing, storage, caching, and frontend presentation.

```mermaid
flowchart TD
    subgraph UI ["Frontend (Streamlit)"]
        A["Streamlit Client (app.py)"]
        H["Chat Interface"]
        V["Itinerary & Budget View"]
    end

    subgraph API ["Backend API (FastAPI)"]
        B["FastAPI Routers (/api/v1/travel, /chat, /health)"]
        S["Travel Service Layer"]
    end

    subgraph LG ["LangGraph Multi-Agent Orchestrator"]
        START((START)) --> D_AGENT["Destination Agent (Gemini + Tavily)"]
        
        D_AGENT --> F_AGENT["Flight Agent (AviationStack)"]
        D_AGENT --> H_AGENT["Hotel Agent (Tavily Discovery)"]
        D_AGENT --> W_AGENT["Weather Agent (OpenWeather)"]
        
        F_AGENT --> I_AGENT["Itinerary Agent (Gemini Synthesis)"]
        H_AGENT --> I_AGENT
        W_AGENT --> I_AGENT
        
        I_AGENT --> R_AGENT["Response Agent (Budget Reconciliation)"]
        R_AGENT --> FINISH((END))
    end

    subgraph INFRA ["Persistence & Caching"]
        PG[("PostgreSQL (Trips & Checkpoints)")]
        RD[("Redis (External API Cache)")]
    end

    A -->|HTTP Requests| B
    H -->|Chat Stream| B
    B --> S
    S --> LG
    S <--> PG
    LG <--> RD
    LG <--> PG
    R_AGENT --> S
    S -->|Structured JSON| A
    V --- A
```

---

## 4. Multi-Agent System Roles

| Agent | Responsibility | Primary Tools & LLM |
| :--- | :--- | :--- |
| **Destination Agent** | Cultural analysis, top sights, activity curation matching travel style, local etiquette. | Gemini 2.5 Flash + Tavily Web Search |
| **Flight Agent** | Airline timetable retrieval, airport code validation, flight status tracking. | AviationStack API |
| **Hotel Agent** | Neighborhood accommodation discovery, price estimation, booking website URLs. | Tavily Discovery + Gemini Extraction |
| **Weather Agent** | Current meteorological readings, 5-day forecast horizon check, climate packing advice. | OpenWeather API |
| **Itinerary Agent** | Balanced day-wise schedule synthesis (Morning, Afternoon, Evening) grouped by district. | Gemini Structured Output |
| **Response Agent** | Budget calculation reconciliation, warning audit, travel tips compilation. | Python Budget Service |
| **Chat Assistant** | Context-aware conversational follow-up queries maintaining LangGraph thread continuity. | Gemini 2.5 Flash + Checkpointer |

---

## 5. Technology Stack

- **AI Orchestration**: LangGraph, LangChain Core, `langchain-google-genai`
- **LLM Provider**: Google Gemini (`gemini-2.5-flash`)
- **Backend Framework**: FastAPI, Uvicorn, Pydantic v2
- **Frontend Dashboard**: Streamlit, Python HTTPX
- **Database & Persistence**: PostgreSQL, SQLAlchemy 2.0, Psycopg 3, LangGraph Postgres Checkpointer
- **Cache Optimization**: Redis, `redis-py`
- **External APIs**: Tavily API, AviationStack API, OpenWeather API
- **Testing & Quality**: Pytest, Pytest-Asyncio, HTTPX TestClient

---

## 6. Directory Structure

```
travel_brain/
├── backend/
│   ├── main.py                     # FastAPI main application and lifespan
│   ├── api/
│   │   ├── dependencies.py         # Database and cache dependency injections
│   │   ├── routes/
│   │   │   ├── health.py           # Health probe endpoint (/health)
│   │   │   ├── travel.py           # Travel plan endpoints (/api/v1/travel)
│   │   │   └── chat.py             # Chat endpoint (/api/v1/chat)
│   │   └── schemas/
│   │       ├── travel.py           # Pydantic schemas for travel and agents
│   │       ├── chat.py             # Chat request/response schemas
│   │       └── response.py         # Standard API wrappers
│   ├── agents/
│   │   ├── destination_agent.py    # Destination Specialist Agent
│   │   ├── flight_agent.py         # Flight Intelligence Agent
│   │   ├── hotel_agent.py          # Accommodation Agent
│   │   ├── weather_agent.py        # Weather Specialist Agent
│   │   ├── itinerary_agent.py      # Day-by-day Itinerary Agent
│   │   └── response_agent.py       # Final Synthesizer Agent
│   ├── graph/
│   │   ├── state.py                # LangGraph TravelState and reducers
│   │   ├── nodes.py                # Graph node execution functions
│   │   ├── workflow.py             # StateGraph definition and compilation
│   │   └── runner.py               # Asynchronous workflow execution runner
│   ├── tools/
│   │   ├── search_tools.py         # Tavily web search integration
│   │   ├── flight_tools.py         # AviationStack flight tracking
│   │   ├── hotel_tools.py          # Hotel discovery search
│   │   └── weather_tools.py        # OpenWeather current and forecast
│   ├── services/
│   │   ├── travel_service.py       # Service coordinating graph and DB
│   │   └── budget_service.py       # Deterministic Python budget calculator
│   ├── clients/
│   │   ├── llm_client.py           # Google Gemini client manager
│   │   ├── database.py             # SQLAlchemy engine and session factory
│   │   └── redis_client.py         # Resilient Redis cache client
│   ├── database/
│   │   ├── models.py               # SQLAlchemy ORM models (trips, conversations)
│   │   ├── repositories.py         # Data access repositories
│   │   └── migrations/             # Alembic migration scripts
│   ├── prompts/
│   │   └── agent_prompts.py        # Specialist agent prompts
│   ├── config/
│   │   └── settings.py             # Pydantic BaseSettings configuration
│   └── utils/
│       ├── logger.py               # Sanitized logging setup
│       ├── exceptions.py           # Custom exception hierarchy
│       └── validators.py           # Date and input validators
│
├── frontend/
│   ├── app.py                      # Streamlit main dashboard application
│   ├── components/
│   │   ├── header.py               # SaaS brand header
│   │   ├── sidebar.py              # Navigation and health monitor
│   │   ├── trip_form.py            # Travel parameters submission form
│   │   ├── itinerary_view.py       # Day tabs and budget audit
│   │   ├── flight_view.py          # Flight timetables display
│   │   ├── hotel_view.py           # Accommodation cards
│   │   ├── weather_view.py         # Meteorological dashboard
│   │   └── chat_interface.py       # Conversational chat assistant
│   ├── services/
│   │   └── api_client.py           # Frontend HTTP client
│   └── utils/
│       └── session.py              # Streamlit session state manager
│
├── tests/
│   ├── conftest.py                 # Pytest fixtures and mock configurations
│   ├── test_api.py                 # FastAPI endpoint tests
│   ├── test_agents.py              # Specialist agent unit tests
│   ├── test_services.py            # Deterministic budget calculation tests
│   ├── test_workflow.py            # LangGraph parallel workflow tests
│   └── test_cache.py               # Redis caching and fallback tests
│
├── logs/                           # Runtime log files
├── .env.example                    # Sample environment variables
├── .gitignore                      # Git ignore patterns
├── requirements.txt                # Pinned dependency requirements
├── run_backend.ps1                 # Windows PowerShell script to start backend
├── run_frontend.ps1                # Windows PowerShell script to start frontend
└── README.md                       # Comprehensive project documentation
```

---

## 7. Installation & Environment Setup

### 7.1 Prerequisites
- **Python**: Version 3.10, 3.11, 3.12, 3.13, or 3.14
- **Operating System**: Windows, macOS, or Linux (Native Windows PowerShell supported)
- **PostgreSQL** *(Optional, in-memory fallback enabled)*
- **Redis** *(Optional, in-memory bypass enabled)*

### 7.2 Clone and Setup Environment

In Windows PowerShell:
```powershell
# Navigate to project workspace
cd c:\Users\aayan\OneDrive\Desktop\travel_brain

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install project dependencies
pip install -r requirements.txt
```

---

## 8. Configuration (.env)

Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

Edit `.env` with your API keys:

```ini
# Google Gemini API (Required for Agent Intelligence)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# External Search and Travel APIs (Optional)
TAVILY_API_KEY=your_tavily_api_key_here
AVIATIONSTACK_API_KEY=your_aviationstack_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here

# PostgreSQL Database (Optional - in-memory fallback if not connected)
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/travel_planner

# Redis Cache (Optional - memory bypass if offline)
REDIS_URL=redis://localhost:6379/0

# Network Settings
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_PORT=8501

# Cache Expiration (seconds)
CACHE_TTL_WEATHER=1800
CACHE_TTL_HOTEL=3600
CACHE_TTL_DESTINATION=86400

LOG_LEVEL=INFO
```

### Acquiring API Keys:
1. **Google Gemini API**: Free tier available via [Google AI Studio](https://aistudio.google.com/).
2. **Tavily API**: Free tier (1,000 requests/month) available at [Tavily AI](https://tavily.com/).
3. **AviationStack API**: Free flight status access at [AviationStack](https://aviationstack.com/).
4. **OpenWeather API**: Free current and 5-day forecast at [OpenWeatherMap](https://openweathermap.org/api).

*Note: If an external API key is left blank, the platform automatically logs the limitation and operates in safe fallback mode without crashing.*

---

## 9. Running the Application on Windows

### 9.1 Start FastAPI Backend
Execute the PowerShell startup script:
```powershell
.\run_backend.ps1
```
Or run directly:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend API**: `http://127.0.0.1:8000`
- **Swagger Interactive Documentation**: `http://127.0.0.1:8000/docs`
- **Health Check Probe**: `http://127.0.0.1:8000/health`

### 9.2 Start Streamlit Frontend
In a second PowerShell terminal:
```powershell
.\run_frontend.ps1
```
Or run directly:
```powershell
python -m streamlit run frontend/app.py --server.port 8501
```
- **Streamlit Web Application**: `http://localhost:8501`

---

## 10. API Specification & Documentation

### `POST /api/v1/travel`
Submit user travel requirements and initiate multi-agent LangGraph workflow.

**Request Payload:**
```json
{
  "origin": "New York",
  "destination": "Tokyo",
  "departure_date": "2026-10-01",
  "return_date": "2026-10-07",
  "travellers": 2,
  "budget": 5000.0,
  "currency": "USD",
  "travel_style": "Cultural",
  "travel_preferences": "Historic shrines, culinary ramen tour, quiet gardens",
  "accommodation_preference": "Traditional Ryokan or Central Boutique Hotel"
}
```

**Response Payload:**
```json
{
  "trip_id": "7f8b9e2a-4311-4b10-8b01-e23f98765432",
  "status": "success",
  "travel_plan": {
    "trip_id": "7f8b9e2a-4311-4b10-8b01-e23f98765432",
    "origin": "New York",
    "destination": "Tokyo",
    "departure_date": "2026-10-01",
    "return_date": "2026-10-07",
    "duration_days": 7,
    "travellers": 2,
    "budget": { "amount": 5000.0, "currency": "USD" },
    "travel_style": "Cultural",
    "destination_overview": {
      "overview": "Tokyo harmonizes futuristic innovation with rich ancient traditions...",
      "highlights": ["Sensō-ji Temple", "Meiji Jingu Shrine", "Shinjuku Gyoen National Garden"],
      "activities": ["Tea ceremony experience", "Tsukiji Outer Market walking tour"],
      "cultural_tips": ["Remove footwear when entering traditional tatami rooms."],
      "potential_constraints": ["Check seasonal booking schedules for popular museums."]
    },
    "flights": [],
    "hotels": [],
    "weather": {
      "temperature_celsius": 21.4,
      "condition": "Clear",
      "humidity": 52,
      "forecast_summary": "Autumn weather expected to remain mild and dry."
    },
    "itinerary": [
      {
        "day": 1,
        "morning": ["Arrival at Haneda/Narita airport", "Express transit to central hotel"],
        "afternoon": ["Check-in", "Walking orientation around Asakusa district"],
        "evening": ["Dinner at authentic izakaya in Yurakucho"],
        "places_to_visit": ["Sensō-ji Temple", "Kaminarimon Gate"],
        "estimated_transport_cost": 30.0,
        "estimated_food_cost": 80.0,
        "estimated_activity_cost": 20.0,
        "daily_total": 130.0
      }
    ],
    "budget_breakdown": {
      "user_budget": 5000.0,
      "currency": "USD",
      "hotel_estimate": 1320.0,
      "food_estimate": 770.0,
      "transport_estimate": 280.0,
      "activities_estimate": 490.0,
      "total_estimated_cost": 2860.0,
      "is_within_budget": true,
      "overrun_amount": 0.0
    },
    "travel_tips": [
      "Purchase a rechargeable digital transit card (Suica/Pasmo) on arrival."
    ],
    "sources": ["Gemini AI", "Tavily Search", "OpenWeather API"]
  },
  "agent_execution_status": {
    "destination_agent": "success",
    "flight_agent": "success",
    "hotel_agent": "success",
    "weather_agent": "success",
    "itinerary_agent": "success",
    "response_agent": "success"
  },
  "errors": []
}
```

### `POST /api/v1/chat`
Post a follow-up conversational question maintaining LangGraph thread memory.

**Request:**
```json
{
  "thread_id": "trip_7f8b9e2a-4311-4b10-8b01-e23f98765432",
  "message": "Can you recommend two quiet vegetarian ramen spots near Shinjuku for Day 3?",
  "trip_id": "7f8b9e2a-4311-4b10-8b01-e23f98765432"
}
```

---

## 11. Automated Test Suite

The test suite validates every layer: API endpoints, specialist agents, deterministic budget math, parallel workflow execution, and Redis cache fallbacks.

Run the complete test suite:
```powershell
python -m pytest tests/ -v
```

Expected output:
```
tests\test_agents.py::test_destination_agent_fallback_on_llm_error PASSED
tests\test_agents.py::test_flight_agent_with_mocked_results PASSED
tests\test_agents.py::test_weather_agent_with_mocked_observation PASSED
tests\test_agents.py::test_response_agent_consolidation PASSED
tests\test_api.py::test_root_endpoint PASSED
tests\test_api.py::test_health_endpoint PASSED
tests\test_api.py::test_invalid_travel_dates PASSED
tests\test_api.py::test_get_nonexistent_trip PASSED
tests\test_cache.py::test_cache_miss_returns_none PASSED
tests\test_cache.py::test_cache_hit_deserialization PASSED
tests\test_cache.py::test_cache_set_with_ttl PASSED
tests\test_cache.py::test_redis_unavailable_fallback PASSED
tests\test_services.py::test_budget_within_limit PASSED
tests\test_services.py::test_budget_overrun_detection PASSED
tests\test_services.py::test_budget_with_custom_hotel_and_itinerary PASSED
tests\test_workflow.py::test_full_graph_execution_success PASSED
tests\test_workflow.py::test_workflow_partial_recovery_on_agent_failure PASSED
tests\test_workflow.py::test_chat_turn_execution PASSED
============================== 18 passed in 12.10s ==============================
```

---

## 12. Security & Operational Limitations

### Security Architecture
- Secrets and credentials loaded exclusively via `.env` through Pydantic Settings.
- Custom `SanitizingFormatter` redacts API keys, credentials, and tokens from all application log output.
- All retrieved web content from Tavily is treated as untrusted external text.
- Pydantic v2 schemas strictly enforce data types, date formatting, and bounded ranges.

### API Limitations & Truthful Bounds
- **AviationStack**: Free tier tracks flight schedules and statuses by route/airline. It does not provide real-time fare pricing or seat booking. Ticket rates must be verified with airlines.
- **OpenWeather**: Live 3-hour forecasts are limited to a 5-day horizon. For travel dates starting >5 days in the future, the system provides seasonal climate trends.
- **Hotel Discovery**: Accommodation options are sourced from web search results. They do not constitute guaranteed room availability or confirmed reservations.

---

## 13. Future Roadmap

1. **Direct Booking Integrations**: Add Amadeus/Sabre enterprise flight and GDS hotel booking engine adapters.
2. **Interactive Map Visualization**: Embed Mapbox or Deck.gl geospatial pins for daily activity routing.
3. **Multi-Currency Real-Time Exchange**: Integrate Fixer.io or Frankfurter API for automated real-time foreign currency conversions.
4. **Calendar Sync**: Export itinerary events directly into `.ics` or Google Calendar format.

---

## 14. License

Distributed under the MIT License. See `LICENSE` for more information.

