# Telecom Service Assistant - Technical Overview

## Table of Contents
1. [Project Summary](#project-summary)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [System Components](#system-components)
5. [Data Flow](#data-flow)

---

## Project Summary

### What is This Project?

The **Telecom Service Assistant** is a sophisticated, multi-framework AI-powered customer support system designed for telecom service providers. It demonstrates the integration of **four major AI frameworks** (CrewAI, AutoGen, LangChain, LlamaIndex) orchestrated by **LangGraph** to handle different types of customer queries intelligently.

### Key Features

- **Intelligent Query Routing**: Automatically classifies and routes queries to specialized AI frameworks
- **Multi-Framework Integration**: Seamlessly combines CrewAI, AutoGen, LangChain, and LlamaIndex
- **Real Database Integration**: 13 tables with comprehensive telecom customer data
- **Knowledge Base**: Vector store with technical documentation for instant retrieval
- **Interactive UI**: Streamlit-based interface with chat functionality and admin dashboard
- **Production-Ready**: Error handling, logging, caching, and graceful fallbacks

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Customer   │  │    Admin     │  │     Chat     │     │
│  │  Dashboard   │  │  Dashboard   │  │  Interface   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Orchestration Layer                  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Classify   │→ │    Route     │→ │   Process    │     │
│  │    Query     │  │    Query     │  │   & Format   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 Specialized AI Frameworks                   │
│                                                             │
│  ┌──────────────┬──────────────┬──────────────┬─────────┐  │
│  │   CrewAI     │   AutoGen    │  LangChain   │LlamaIdx │  │
│  │   Billing    │   Network    │   Service    │Knowledge│  │
│  │   Agents     │   Agents     │   Agent      │ Engine  │  │
│  └──────────────┴──────────────┴──────────────┴─────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                             │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  SQLite DB   │  │  Vector DB   │  │  Documents   │     │
│  │  13 Tables   │  │  ChromaDB    │  │   (5 files)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Design Philosophy

1. **Separation of Concerns**: Each framework handles what it does best
2. **Centralized Orchestration**: LangGraph manages the entire workflow
3. **Intelligent Routing**: Queries go to the most appropriate framework
4. **Context Enrichment**: Customer data enhances all responses
5. **Graceful Degradation**: System continues working even if components fail

---

## Technology Stack

### Core Technologies

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.13.3 | Primary programming language |
| **OpenAI** | GPT-4o-mini | Large Language Model backend |
| **Streamlit** | Latest | Web interface framework |
| **SQLite** | 3.x | Database engine |

### AI Frameworks

| Framework | Version | Use Case |
|-----------|---------|----------|
| **CrewAI** | 1.6.1 | Billing & account queries (multi-agent collaboration) |
| **AutoGen** | Latest | Network troubleshooting (conversational agents) |
| **LangChain** | Latest | Service recommendations (ReAct agents) |
| **LlamaIndex** | Latest | Knowledge retrieval (vector + SQL hybrid) |
| **LangGraph** | Latest | Workflow orchestration (state management) |

### Supporting Libraries

- **pandas**: Data manipulation
- **loguru**: Advanced logging
- **chromadb**: Vector database
- **sqlalchemy**: Database ORM
- **python-dotenv**: Environment configuration

---

## System Components

### 1. Orchestration Layer (LangGraph)

**File**: `orchestration/graph.py`

**Responsibilities**:
- Query classification (4 categories)
- Intelligent routing
- State management
- Response formatting

**State Structure**:
```python
class TelecomAssistantState(TypedDict):
    query: str                           # User's question
    customer_info: Dict[str, Any]        # Customer context
    classification: str                  # Query category
    intermediate_responses: Dict         # Framework responses
    final_response: str                  # Formatted answer
    chat_history: List[Dict]             # Conversation history
```

### 2. Billing & Account (CrewAI)

**File**: `agents/billing_agents.py`

**Agents**:
1. **Billing Specialist**: Analyzes bills, explains charges
2. **Service Advisor**: Reviews usage, suggests optimizations

**Tools**: 15 specialized database tools

**Process**: Sequential collaboration

### 3. Network Troubleshooting (AutoGen)

**File**: `agents/network_agents.py`

**Agents**:
1. **User Proxy**: Represents customer
2. **Network Diagnostics**: Checks incidents, analyzes patterns
3. **Device Expert**: Device-specific troubleshooting
4. **Solution Integrator**: Creates action plan

**Functions**: 3 registered functions with JSON schemas

**Process**: GroupChat with max 6 rounds

### 4. Service Recommendations (LangChain)

**File**: `agents/service_agents.py`

**Agent Type**: ReAct (Reasoning + Acting)

**Tools**:
- get_customer_usage
- get_plan_details
- check_coverage_quality
- PythonREPLTool (calculations)
- estimate_data_usage

**Process**: Iterative reasoning loop (max 6 iterations)

### 5. Knowledge Retrieval (LlamaIndex)

**File**: `agents/knowledge_agents.py`

**Engines**:
1. **Vector Search**: Conceptual questions (documentation)
2. **SQL Database**: Factual queries (database)

**Router**: LLMSingleSelector chooses appropriate engine

**Process**: Hybrid query execution with intelligent routing

### 6. User Interface (Streamlit)

**File**: `ui/streamlit_app.py`

**Features**:
- Login/authentication system
- Customer dashboard (4 tabs)
- Admin dashboard (3 tabs)
- Chat interface with history
- Real-time network monitoring

---

## Data Flow

### Query Processing Flow

```
1. User Input
   ↓
2. UI Layer (streamlit_app.py)
   - Capture query
   - Add customer context
   ↓
3. LangGraph Orchestration
   - classify_query() → Determines category
   - route_query() → Selects framework
   ↓
4. Framework Processing
   - CrewAI: Billing analysis (Sequential crew)
   - AutoGen: Network troubleshooting (GroupChat)
   - LangChain: Plan recommendation (ReAct agent)
   - LlamaIndex: Knowledge retrieval (Router)
   ↓
5. Response Formatting
   - formulate_response() → Structures output
   ↓
6. UI Display
   - Chat bubble or detailed view
   - Include sources/intermediate results
```

### Query Classification Logic

**Categories**:
1. **billing_account**: bill, charge, payment, account
2. **network_troubleshooting**: network, signal, connection, call, data, slow
3. **service_recommendation**: plan, recommend, best, upgrade, family
4. **knowledge_retrieval**: how, what, configure, setup, apn, volte

**Classification Method**:
1. LLM-based (OpenAI GPT-4o-mini) - Primary
2. Keyword-based - Fallback
3. Keyword overrides - Final adjustments

---

## Database Schema

### 13 Tables Overview

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| customers | Customer profiles | customer_id, name, email, plan_id |
| service_plans | Available plans | plan_id, name, cost, limits |
| billing_history | Bill records | bill_id, customer_id, amount, date |
| usage_summary | Usage tracking | usage_id, data_used, voice_used |
| support_tickets | Customer issues | ticket_id, issue, status |
| payment_history | Payment records | payment_id, amount, method |
| add_on_packs | Additional services | pack_id, name, price |
| service_areas | Coverage regions | area_id, city, district |
| coverage_quality | Network quality | area_id, signal, speed |
| network_incidents | Active issues | incident_id, type, severity |
| common_network_issues | Knowledge base | issue_id, symptoms, steps |
| device_compatibility | Device info | device_id, make, model |
| promotional_offers | Active promos | offer_id, discount, validity |

**Total Records**: ~300+ across all tables

---

## Vector Store

### Document Collection

**Location**: `data/documents/`

**Files**:
1. `5G Network Deployment.txt` - 5G rollout information
2. `Billing FAQs.txt` - Common billing questions
3. `Network_Troubleshooting_Guide.txt` - Technical troubleshooting
4. `Technical Support Guide.txt` - General support procedures
5. `Telecom Service Plans Guide.txt` - Plan details and features

**Vector Database**: ChromaDB at `data/chromadb/`

**Indexing**: Automatic embeddings via LlamaIndex

---

## Performance Optimizations

### Caching Strategies

1. **Agent Caching**: Global caches for CrewAI, AutoGen, LangChain agents
2. **Graph Caching**: Session state stores LangGraph workflow
3. **Engine Caching**: LlamaIndex query engine cached globally

### Resource Management

- **Connection Pooling**: SQLite connections reused
- **Lazy Loading**: Frameworks loaded on first use
- **Error Handling**: Graceful degradation to fallbacks

---

## Security & Configuration

### Environment Variables

**File**: `.env`

```
OPENAI_API_KEY=sk-...
ENABLE_LLM_CLASSIFICATION=true
OPENAI_MODEL_CLASSIFY=gpt-4o-mini
DOCUMENTS_DIR=data/documents
```

### Configuration

**File**: `config/config.py`

- API keys
- Model selection
- Feature flags
- Paths and directories

---

## Project Statistics

- **Total Python Files**: 56
- **Total Lines of Code**: ~3,000+
- **Frameworks Integrated**: 5 (CrewAI, AutoGen, LangChain, LlamaIndex, LangGraph)
- **Database Tables**: 13
- **Document Files**: 5
- **Test Files**: 3
- **Documentation Files**: 10+

---

## Next Steps

See detailed documentation:
- [02_LANGGRAPH_ORCHESTRATION.md](02_LANGGRAPH_ORCHESTRATION.md) - LangGraph workflow
- [03_CREWAI_IMPLEMENTATION.md](03_CREWAI_IMPLEMENTATION.md) - Billing agents
- [04_AUTOGEN_IMPLEMENTATION.md](04_AUTOGEN_IMPLEMENTATION.md) - Network agents
- [05_LANGCHAIN_IMPLEMENTATION.md](05_LANGCHAIN_IMPLEMENTATION.md) - Service agent
- [06_LLAMAINDEX_IMPLEMENTATION.md](06_LLAMAINDEX_IMPLEMENTATION.md) - Knowledge engine
- [07_DATABASE_ARCHITECTURE.md](07_DATABASE_ARCHITECTURE.md) - Database design
- [08_UI_IMPLEMENTATION.md](08_UI_IMPLEMENTATION.md) - Streamlit interface
- [09_DEPLOYMENT_GUIDE.md](09_DEPLOYMENT_GUIDE.md) - Production deployment

---

**Last Updated**: December 1, 2025
**Version**: 1.0
**Status**: Production Ready ✅
