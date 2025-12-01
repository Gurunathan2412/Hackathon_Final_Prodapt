# Query Classification System - Complete Explanation

## Overview

Your system uses **LangGraph** to orchestrate query classification and routing to specialized AI agents. Here's how it works:

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER QUERY FLOW                                 │
└─────────────────────────────────────────────────────────────────────────┘

1. User Query: "My data connection keeps dropping"
   ↓
2. Entry Point: classify_query()
   ↓
3. Classification Decision (LLM or Keywords)
   ↓
4. Route to Appropriate Agent
   ↓
5. Agent Processes Query
   ↓
6. Format Response
   ↓
7. Return to User


┌──────────────────────────────────────────────────────────────────────────┐
│                    DETAILED CLASSIFICATION FLOW                          │
└──────────────────────────────────────────────────────────────────────────┘

                            User Query
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  classify_query()       │
                    │  (LangGraph Entry Node) │
                    └─────────────────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
                ▼                                 ▼
        ┌──────────────┐              ┌──────────────────┐
        │ LLM Enabled? │              │ Simple Queries?  │
        │ (GPT-4o-mini)│              │ (hi, hello, hey) │
        └──────────────┘              └──────────────────┘
                │                                 │
                ▼                                 ▼
     ┌────────────────────┐              ┌──────────────┐
     │ Call ChatOpenAI    │              │  "fallback"  │
     │ with prompt:       │              └──────────────┘
     │ "Classify into:    │
     │  - billing_account │
     │  - network_...     │
     │  - service_...     │
     │  - knowledge_..."  │
     └────────────────────┘
                │
                ▼
     ┌────────────────────┐
     │ Extract label from │
     │ LLM response       │
     └────────────────────┘
                │
                ▼
     ┌────────────────────────────────────┐
     │  KEYWORD OVERRIDE RULES            │
     │  (Applied AFTER LLM classification)│
     └────────────────────────────────────┘
                │
        ┌───────┴───────┬──────────────┬──────────────┐
        ▼               ▼              ▼              ▼
 ┌────────────┐  ┌────────────┐ ┌───────────┐ ┌──────────┐
 │ Knowledge? │  │ Service?   │ │ Billing?  │ │ Network? │
 │ (how,what, │  │ (plan,     │ │ (bill,    │ │ (signal, │
 │  setup)    │  │  upgrade)  │ │  payment) │ │  call)   │
 └────────────┘  └────────────┘ └───────────┘ └──────────┘
        │               │              │              │
        ▼               ▼              ▼              ▼
  knowledge_    service_       billing_      network_
  retrieval     recommendation account       troubleshooting
        │               │              │              │
        └───────────────┴──────────────┴──────────────┘
                            │
                            ▼
                ┌─────────────────────┐
                │   route_query()     │
                │   (Decision Router) │
                └─────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ crew_ai_node │    │ autogen_node │    │langchain_node│
│ (Billing)    │    │ (Network)    │    │ (Service)    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                ┌──────────────────────┐
                │ llamaindex_node      │
                │ (Knowledge)          │
                └──────────────────────┘
                            │
                            ▼
                ┌──────────────────────┐
                │ formulate_response() │
                │ (Format Output)      │
                └──────────────────────┘
                            │
                            ▼
                        END (Return)
```

---

## Step-by-Step Classification Process

### Step 1: Entry Point - `classify_query()`
**Location:** `orchestration/graph.py`, Lines 53-89

```python
def classify_query(state: TelecomAssistantState) -> TelecomAssistantState:
    query = state.get("query", "").strip()
    
    # Quick exit for simple greetings
    if len(query) < 3 or query.lower() in {"hi", "hello", "hey"}:
        return {**state, "classification": "fallback"}
```

**What happens:**
- Gets the user query from state
- Checks for simple greetings → Routes to fallback
- Otherwise, proceeds to classification

---

### Step 2: LLM Classification (If Enabled)
**Config:** `ENABLE_LLM_CLASSIFICATION = True` in `config/config.py`

```python
if _llm_classifier:  # ChatOpenAI(model="gpt-4o-mini")
    prompt = (
        "Classify the telecom user query into one of: "
        "billing_account, network_troubleshooting, "
        "service_recommendation, knowledge_retrieval.\n"
        f"Query: {query}\nLabel:"
    )
    resp = _llm_classifier.invoke(prompt)
    raw = resp.content.lower()
    
    # Extract classification from LLM response
    for label in ["billing_account", "network_troubleshooting", 
                  "service_recommendation", "knowledge_retrieval"]:
        if label in raw:
            classification = label
            break
```

**Example:**
```
Query: "My bill is too high"
LLM Response: "This query is about billing_account"
Classification: billing_account ✅
```

---

### Step 3: Fallback Heuristic (If LLM Disabled)
**Keyword-based classification:**

```python
else:  # No LLM, use keywords
    if any(w in ql for w in ["bill","charge","payment","account"]):
        classification = "billing_account"
    elif any(w in ql for w in ["network","signal","connection","call","data","slow"]):
        classification = "network_troubleshooting"
```

**Examples:**
- "My **bill** is high" → `billing_account`
- "**Signal** is weak" → `network_troubleshooting`

---

### Step 4: Keyword Override Rules
**Applied AFTER LLM classification to handle special cases:**

```python
# Knowledge keywords take precedence
knowledge_keywords = {"how", "what", "configure", "setup", "apn", "volte"}
if any(k in ql for k in knowledge_keywords):
    classification = "knowledge_retrieval"
else:
    # Service keywords override if not already knowledge
    service_keywords = {"plan", "recommend", "best", "upgrade", "family"}
    if any(k in ql for k in service_keywords):
        classification = "service_recommendation"
```

**Priority Order:**
1. **Knowledge** (highest) - "how", "what", "setup"
2. **Service** - "plan", "recommend", "upgrade"
3. **LLM/Heuristic** - Other classifications

**Examples:**
- "**What** is 5G?" → `knowledge_retrieval` (even if LLM says billing)
- "**Best plan** for me" → `service_recommendation`
- "**How** to setup APN?" → `knowledge_retrieval`

---

### Step 5: Routing Decision - `route_query()`
**Location:** Lines 120-136

```python
def route_query(state: TelecomAssistantState) -> str:
    classification = state.get("classification", "")
    
    if classification == "billing_account":
        return "crew_ai_node"
    if classification == "network_troubleshooting":
        return "autogen_node"
    if classification == "service_recommendation":
        return "langchain_node"
    if classification == "knowledge_retrieval":
        return "llamaindex_node"
    
    return "fallback_handler"  # Default
```

**Routing Map:**

| Classification | Node | AI Framework | Purpose |
|----------------|------|--------------|---------|
| `billing_account` | `crew_ai_node` | **CrewAI** | Multi-agent billing analysis |
| `network_troubleshooting` | `autogen_node` | **AutoGen** | Network diagnostics with location |
| `service_recommendation` | `langchain_node` | **LangChain** | Plan recommendations with GPT-4o |
| `knowledge_retrieval` | `llamaindex_node` | **LlamaIndex** | Document search & retrieval |
| (other) | `fallback_handler` | None | Generic response |

---

## Agent Processing Nodes

### 1. CrewAI Node (Billing)
**Location:** Lines 138-144

```python
def crew_ai_node(state: TelecomAssistantState) -> TelecomAssistantState:
    customer_info = state.get('customer_info', {})
    customer_id = customer_info.get('customer_id', 'UNKNOWN')
    
    # Add customer context
    if customer_info:
        context_query = f"Customer: {customer_id} ({name}), Plan: {plan}. Query: {query}"
    
    result = process_billing_query(customer_id=customer_id, query=context_query)
    return {**state, "intermediate_responses": {"crew_ai": result}}
```

**Enrichments:**
- Adds customer ID
- Adds customer name
- Adds current plan
- Passes to CrewAI agents

---

### 2. AutoGen Node (Network)
**Location:** Lines 146-172

```python
def autogen_node(state: TelecomAssistantState) -> TelecomAssistantState:
    query = state.get('query', '')
    customer_info = state.get('customer_info', {})
    
    # Extract city from customer address
    if customer_info:
        address = customer_info.get('address', '')
        city = extract_city_from_address(address)
        
        if city:
            # Add location context
            enriched_query = f"Customer location: {city}. Issue: {query}"
    
    result = process_network_query(query=enriched_query)
    return {**state, "intermediate_responses": {"autogen": result}}
```

**Enrichments:**
- Extracts city from address (e.g., "Bangalore" from "Apartment 301, Sunshine Towers, Bangalore")
- Adds location context: "Customer location: Bangalore. Issue: {query}"
- Helps AutoGen find location-specific incidents

---

### 3. LangChain Node (Service)
**Location:** Lines 175-185

```python
def langchain_node(state: TelecomAssistantState) -> TelecomAssistantState:
    customer_info = state.get('customer_info', {})
    query = state.get('query','')
    
    # Add customer context for personalized recommendations
    if customer_info:
        context_query = f"Customer {customer_id} on {plan_id} plan. {query}"
    
    result = process_recommendation_query(query=context_query)
    return {**state, "intermediate_responses": {"langchain": result}}
```

**Enrichments:**
- Adds customer ID
- Adds current plan (e.g., "STD_500")
- Enables personalized plan recommendations

---

### 4. LlamaIndex Node (Knowledge)
**Location:** Lines 188-190

```python
def llamaindex_node(state: TelecomAssistantState) -> TelecomAssistantState:
    result = process_knowledge_query(query=state.get('query',''))
    return {**state, "intermediate_responses": {"llamaindex": result}}
```

**Simple processing:**
- No enrichment needed
- Pure document search
- Returns relevant knowledge from PDFs/docs

---

### 5. Fallback Handler
**Location:** Lines 193-199

```python
def fallback_handler(state: TelecomAssistantState) -> TelecomAssistantState:
    response = (
        "I'm not sure how to help with that specific question. "
        "Could you try rephrasing or ask about our services, "
        "billing, network issues, or technical support?"
    )
    return {**state, "intermediate_responses": {"fallback": response}}
```

**When used:**
- Greetings ("hi", "hello")
- Unclear queries
- Classification failures

---

## Complete Query Examples

### Example 1: Billing Query
```
Input: "Why is my bill so high this month?"

Step 1: classify_query()
  - LLM Classification: "billing_account"
  - Keyword check: "bill" found ✅
  - Final: billing_account

Step 2: route_query()
  - Classification: billing_account
  - Returns: "crew_ai_node"

Step 3: crew_ai_node()
  - Enriches: "Customer: CUST001 (SivaPrasad), Plan: STD_500. Query: Why is my bill so high?"
  - Calls: process_billing_query() → CrewAI agents analyze usage

Step 4: formulate_response()
  - Formats CrewAI output
  - Returns final response

Output: "Your bill increased due to 15 GB data overage..."
```

---

### Example 2: Network Query with Location
```
Input: "My data connection keeps dropping"

Step 1: classify_query()
  - LLM Classification: "network_troubleshooting"
  - Keyword check: "data", "connection" found ✅
  - Final: network_troubleshooting

Step 2: route_query()
  - Classification: network_troubleshooting
  - Returns: "autogen_node"

Step 3: autogen_node()
  - Customer address: "Apartment 301, Sunshine Towers, Bangalore"
  - Extracts city: "Bangalore"
  - Enriches: "Customer location: Bangalore. Issue: My data connection keeps dropping"
  - Calls: process_network_query() → AutoGen agents find Bangalore incidents

Step 4: formulate_response()
  - Formats AutoGen output
  - Returns final response

Output: "Equipment failure detected in Bangalore West area..."
```

---

### Example 3: Service Recommendation
```
Input: "I need a plan with international roaming"

Step 1: classify_query()
  - LLM Classification: (may vary)
  - Keyword override: "plan" found ✅
  - Final: service_recommendation

Step 2: route_query()
  - Classification: service_recommendation
  - Returns: "langchain_node"

Step 3: langchain_node()
  - Enriches: "Customer CUST001 on STD_500 plan. I need a plan with international roaming"
  - Calls: process_recommendation_query() → LangChain GPT-4o agent

Step 4: Agent uses tools:
  - list_all_plans("international") → Finds PREM_UNL, BIZ_ESSEN
  - Recommends: PREM_UNL (₹1299)

Step 5: formulate_response()
  - Formats recommendation
  - Returns final response

Output: "I recommend Premium Unlimited (₹1299/month)..."
```

---

### Example 4: Knowledge Query
```
Input: "How do I configure APN settings?"

Step 1: classify_query()
  - LLM Classification: (may vary)
  - Keyword override: "How" found ✅
  - Final: knowledge_retrieval

Step 2: route_query()
  - Classification: knowledge_retrieval
  - Returns: "llamaindex_node"

Step 3: llamaindex_node()
  - Calls: process_knowledge_query()
  - LlamaIndex searches technical docs
  - Finds APN configuration instructions

Step 4: formulate_response()
  - Formats knowledge response
  - Returns final response

Output: "To configure APN: Go to Settings > Mobile Networks > APN..."
```

---

## Classification Priority Rules

### 1. Simple Queries → Fallback
```python
if len(query) < 3 or query.lower() in {"hi", "hello", "hey"}:
    return "fallback"
```

### 2. Knowledge Keywords → knowledge_retrieval
```python
if any(k in query for k in ["how", "what", "configure", "setup"]):
    return "knowledge_retrieval"
```

### 3. Service Keywords → service_recommendation
```python
if any(k in query for k in ["plan", "recommend", "upgrade", "family"]):
    return "service_recommendation"
```

### 4. LLM/Heuristic Classification
- billing_account: "bill", "charge", "payment"
- network_troubleshooting: "network", "signal", "connection"

---

## Configuration

### Enable/Disable LLM Classification
**File:** `config/config.py`

```python
# Use GPT-4o-mini for classification
ENABLE_LLM_CLASSIFICATION = True
OPENAI_MODEL_CLASSIFY = "gpt-4o-mini"

# Or disable for keyword-only classification
ENABLE_LLM_CLASSIFICATION = False
```

**Trade-offs:**

| Mode | Pros | Cons |
|------|------|------|
| **LLM Enabled** | More accurate, handles complex queries | Costs $0.15/1M tokens, slower |
| **Keywords Only** | Free, instant | Less accurate, rigid rules |

---

## LangGraph State Management

### State Structure
```python
class TelecomAssistantState(TypedDict):
    query: str                           # User's question
    customer_info: Dict[str, Any]        # Customer data from DB
    classification: str                  # Classification result
    intermediate_responses: Dict[str, Any]  # Agent outputs
    final_response: str                  # Formatted answer
    chat_history: List[Dict[str, str]]   # Conversation history
```

### State Flow
```
Initial State:
{
    "query": "My bill is high",
    "customer_info": {...},
    "classification": "",
    "intermediate_responses": {},
    "final_response": ""
}
    ↓
After classify_query():
{
    "classification": "billing_account",
    "status": "classified"
}
    ↓
After crew_ai_node():
{
    "intermediate_responses": {
        "crew_ai": {
            "analysis": "...",
            "status": "ok"
        }
    }
}
    ↓
After formulate_response():
{
    "final_response": "Your bill increased because...",
    "status": "completed"
}
```

---

## Graph Workflow Definition

### Node Addition
```python
workflow.add_node("classify_query", classify_query)
workflow.add_node("crew_ai_node", crew_ai_node)
workflow.add_node("autogen_node", autogen_node)
workflow.add_node("langchain_node", langchain_node)
workflow.add_node("llamaindex_node", llamaindex_node)
workflow.add_node("fallback_handler", fallback_handler)
workflow.add_node("formulate_response", formulate_response)
```

### Conditional Routing
```python
workflow.add_conditional_edges(
    "classify_query",   # Source node
    route_query,        # Decision function
    {                   # Routing map
        "crew_ai_node": "crew_ai_node",
        "autogen_node": "autogen_node",
        "langchain_node": "langchain_node",
        "llamaindex_node": "llamaindex_node",
        "fallback_handler": "fallback_handler",
    }
)
```

### Linear Edges (All paths lead to response)
```python
workflow.add_edge("crew_ai_node", "formulate_response")
workflow.add_edge("autogen_node", "formulate_response")
workflow.add_edge("langchain_node", "formulate_response")
workflow.add_edge("llamaindex_node", "formulate_response")
workflow.add_edge("fallback_handler", "formulate_response")
workflow.add_edge("formulate_response", END)
```

### Entry Point
```python
workflow.set_entry_point("classify_query")
```

---

## Summary

### Classification System:
1. ✅ **LangGraph** orchestrates the entire workflow
2. ✅ **ChatOpenAI (gpt-4o-mini)** performs LLM classification
3. ✅ **Keyword rules** provide fallback and overrides
4. ✅ **Context enrichment** adds customer data to queries
5. ✅ **4 specialized agents** handle different query types
6. ✅ **Fallback handler** catches edge cases

### Classification Flow:
```
Query → classify_query() → route_query() → Agent Node → formulate_response() → END
```

### Agent Routing:
- **Billing** → CrewAI (multi-agent collaboration)
- **Network** → AutoGen (location-aware troubleshooting)
- **Service** → LangChain (GPT-4o recommendations with tools)
- **Knowledge** → LlamaIndex (document search)

### Key Features:
- 🎯 **Hybrid classification** (LLM + keywords)
- 📍 **Location-aware** network troubleshooting
- 👤 **Customer context** enrichment
- 🚫 **Hallucination prevention** (list_all_plans tool)
- 🔄 **Flexible routing** with LangGraph

Your classification system is sophisticated and production-ready! 🎉
