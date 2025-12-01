# LangGraph Orchestration - Technical Deep Dive

## Overview

LangGraph serves as the **central nervous system** of the Telecom Service Assistant, coordinating the flow between different AI frameworks. It manages state, classifies queries, routes them to appropriate frameworks, and formats responses.

---

## Architecture

### State Management

**File**: `orchestration/graph.py`

```python
class TelecomAssistantState(TypedDict):
    query: str                      # Original user query
    customer_info: Dict[str, Any]   # Customer context from database
    classification: str             # Query category (4 types)
    intermediate_responses: Dict    # Responses from frameworks
    final_response: str             # Formatted final answer
    chat_history: List[Dict]        # Conversation history
```

### State Flow Diagram

```
┌──────────────┐
│ Initial      │
│ State        │
│ {query: "?"}│
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────┐
│  classify_query()                │
│  Adds: classification            │
│  Status: "classified"            │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  route_query()                   │
│  Returns: framework node name    │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  Framework Node                  │
│  (crew_ai/autogen/langchain/     │
│   llamaindex/fallback)           │
│  Adds: intermediate_responses    │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  formulate_response()            │
│  Adds: final_response            │
│  Status: "completed"             │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────┐
│  END         │
│  Return State│
└──────────────┘
```

---

## Query Classification

### Classification Node

**Function**: `classify_query(state: TelecomAssistantState)`

**Process**:

1. **Input Validation**
   ```python
   query = state.get("query", "").strip()
   if len(query) < 3 or query.lower() in {"hi", "hello", "hey"}:
       return {**state, "classification": "fallback"}
   ```

2. **LLM Classification** (Primary Method)
   ```python
   if _llm_classifier:  # ChatOpenAI(model="gpt-4o-mini", temperature=0)
       prompt = "Classify the telecom user query into one of: 
                 billing_account, network_troubleshooting, 
                 service_recommendation, knowledge_retrieval.
                 Query: {query}
                 Label:"
       resp = _llm_classifier.invoke(prompt)
       classification = extract_label(resp.content)
   ```

3. **Keyword-Based Fallback**
   ```python
   if any(w in ql for w in ["bill","charge","payment","account"]):
       classification = "billing_account"
   elif any(w in ql for w in ["network","signal","connection"]):
       classification = "network_troubleshooting"
   ```

4. **Keyword Overrides** (Highest Priority)
   ```python
   # Knowledge keywords take precedence
   if any(k in ql for k in {"how", "what", "configure", "setup"}):
       classification = "knowledge_retrieval"
   # Service keywords (if not knowledge)
   elif any(k in ql for k in {"plan", "recommend", "best"}):
       classification = "service_recommendation"
   ```

**Output**: Updated state with classification field

### Classification Accuracy

Based on testing with 19 sample queries:
- **Overall**: 79% (15/19 correct)
- **Network**: 100% (4/4 correct)
- **Technical**: 100% (4/4 correct)
- **Billing**: 75% (3/4 correct)
- **Service Plans**: 50% (2/4 correct)

---

## Query Routing

### Routing Function

**Function**: `route_query(state: TelecomAssistantState) -> str`

**Routing Logic**:

```python
classification = state.get("classification", "")

# Map classification to framework node
if classification == "billing_account":
    return "crew_ai_node"          # CrewAI billing agents
elif classification == "network_troubleshooting":
    return "autogen_node"          # AutoGen multi-agent chat
elif classification == "service_recommendation":
    return "langchain_node"        # LangChain ReAct agent
elif classification == "knowledge_retrieval":
    return "llamaindex_node"       # LlamaIndex hybrid engine
else:
    return "fallback_handler"      # Generic response
```

**Routing Table**:

| Classification | Node | Framework | Agent Type |
|---------------|------|-----------|------------|
| billing_account | crew_ai_node | CrewAI | Multi-agent crew |
| network_troubleshooting | autogen_node | AutoGen | GroupChat |
| service_recommendation | langchain_node | LangChain | ReAct agent |
| knowledge_retrieval | llamaindex_node | LlamaIndex | Router engine |
| (other) | fallback_handler | None | Static response |

---

## Framework Nodes

### 1. CrewAI Node

**Function**: `crew_ai_node(state: TelecomAssistantState)`

**Process**:
```python
1. Extract customer_info from state
2. Enrich query with customer context
3. Call process_billing_query(customer_id, enriched_query)
4. Return state with intermediate_responses["crew_ai"]
```

**Context Enrichment**:
```python
if customer_info:
    context_query = f"Customer: {customer_id} ({name}), 
                     Plan: {service_plan_id}. 
                     Query: {query}"
```

**Output Structure**:
```python
{
    "customer_id": "CUST001",
    "query": "...",
    "bill_analysis": "...",
    "plan_review": "...",
    "recommendations": "...",
    "status": "ok"
}
```

### 2. AutoGen Node

**Function**: `autogen_node(state: TelecomAssistantState)`

**Process**:
```python
1. Extract query from state
2. Call process_network_query(query)
3. Return state with intermediate_responses["autogen"]
```

**No Context Enrichment**: Network issues are query-specific

**Output Structure**:
```python
{
    "query": "...",
    "plan": ["Step 1", "Step 2", ...],
    "transcript": [...],
    "summary": "...",
    "status": "ok"
}
```

### 3. LangChain Node

**Function**: `langchain_node(state: TelecomAssistantState)`

**Process**:
```python
1. Extract customer_info and query
2. Enrich query with customer context
3. Call process_recommendation_query(enriched_query)
4. Return state with intermediate_responses["langchain"]
```

**Context Enrichment**:
```python
if customer_info:
    context_query = f"Customer {customer_id} on {plan_id} plan. {query}"
```

**Output Structure**:
```python
{
    "query": "...",
    "plan": "...",
    "benefits": [...],
    "estimated_usage": "...",
    "status": "ok"
}
```

### 4. LlamaIndex Node

**Function**: `llamaindex_node(state: TelecomAssistantState)`

**Process**:
```python
1. Extract query from state
2. Call process_knowledge_query(query)
3. Return state with intermediate_responses["llamaindex"]
```

**No Context Enrichment**: Knowledge retrieval is query-specific

**Output Structure**:
```python
{
    "query": "...",
    "answer": "...",
    "sources": [...],
    "summary": "...",
    "status": "ok"
}
```

### 5. Fallback Handler

**Function**: `fallback_handler(state: TelecomAssistantState)`

**Process**:
```python
response = "I'm not sure how to help with that specific question. 
            Could you try rephrasing or ask about our services, 
            billing, network issues, or technical support?"
return {**state, "intermediate_responses": {"fallback": response}}
```

---

## Response Formatting

### Formulation Node

**Function**: `formulate_response(state: TelecomAssistantState)`

**Process**:

1. **Extract Intermediate Responses**
   ```python
   intermediate_responses = state.get("intermediate_responses", {})
   if not intermediate_responses:
       return {**state, "final_response": "No response generated."}
   ```

2. **Format Based on Response Type**
   ```python
   key, val = next(iter(intermediate_responses.items()))
   
   if isinstance(val, dict):
       # Handle error responses
       if val.get("status") == "error":
           formatted = format_error(val)
       # Handle success responses
       else:
           formatted = format_dict(val)
   else:
       # Handle string responses (fallback)
       formatted = str(val)
   ```

3. **Structure Output**
   ```python
   # Format as key-value pairs
   formatted_lines = []
   for k, v in val.items():
       if k not in {"raw"}:  # Skip raw output
           formatted_lines.append(f"{k}: {v}")
   formatted = "\n".join(formatted_lines)
   ```

**Output**: State with `final_response` field populated

---

## Graph Construction

### Graph Builder

**Function**: `create_graph()`

**Steps**:

1. **Initialize StateGraph**
   ```python
   workflow = StateGraph(TelecomAssistantState)
   ```

2. **Add Nodes**
   ```python
   workflow.add_node("classify_query", classify_query)
   workflow.add_node("crew_ai_node", crew_ai_node)
   workflow.add_node("autogen_node", autogen_node)
   workflow.add_node("langchain_node", langchain_node)
   workflow.add_node("llamaindex_node", llamaindex_node)
   workflow.add_node("fallback_handler", fallback_handler)
   workflow.add_node("formulate_response", formulate_response)
   ```

3. **Add Conditional Edges** (Routing)
   ```python
   workflow.add_conditional_edges(
       "classify_query",          # Source node
       route_query,               # Routing function
       {                          # Mapping
           "crew_ai_node": "crew_ai_node",
           "autogen_node": "autogen_node",
           "langchain_node": "langchain_node",
           "llamaindex_node": "llamaindex_node",
           "fallback_handler": "fallback_handler",
       }
   )
   ```

4. **Add Sequential Edges** (To Response Formatting)
   ```python
   workflow.add_edge("crew_ai_node", "formulate_response")
   workflow.add_edge("autogen_node", "formulate_response")
   workflow.add_edge("langchain_node", "formulate_response")
   workflow.add_edge("llamaindex_node", "formulate_response")
   workflow.add_edge("fallback_handler", "formulate_response")
   workflow.add_edge("formulate_response", END)
   ```

5. **Set Entry Point**
   ```python
   workflow.set_entry_point("classify_query")
   ```

6. **Compile Graph**
   ```python
   return workflow.compile()
   ```

### Graph Visualization

```
                    START
                      ↓
            ┌─────────────────┐
            │ classify_query  │
            └────────┬────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   [billing]   [network]    [service]    [knowledge]   [other]
        │            │            │            │          │
        ▼            ▼            ▼            ▼          ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
   │crew_ai  │  │autogen  │  │langchain│  │llamaidx │  │fallback │
   │  node   │  │  node   │  │  node   │  │  node   │  │ handler │
   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
        │            │            │            │            │
        └────────────┴────────────┴────────────┴────────────┘
                              ↓
                    ┌───────────────────┐
                    │formulate_response │
                    └─────────┬─────────┘
                              ↓
                            END
```

---

## Performance Characteristics

### Execution Times (Approximate)

| Node | Average Time | Notes |
|------|-------------|-------|
| classify_query | 0.5-1.5s | LLM classification |
| route_query | < 0.01s | Simple conditional |
| crew_ai_node | 10-20s | Multi-agent collaboration |
| autogen_node | 8-15s | GroupChat with 6 rounds |
| langchain_node | 5-10s | ReAct with iterations |
| llamaindex_node | 2-5s | Vector or SQL query |
| fallback_handler | < 0.01s | Static response |
| formulate_response | < 0.1s | String formatting |

**Total Query Time**: 2-25 seconds (depending on complexity)

### Optimization Strategies

1. **LLM Caching**: Repeated classifications cached
2. **Agent Reuse**: Agents created once, reused
3. **Graph Caching**: Compiled graph stored in session
4. **Parallel Processing**: Could parallelize where possible (future)

---

## Error Handling

### Error Propagation

Each framework node returns status:
```python
{
    "status": "ok"  # or "error"
    "error": "...",   # if status == "error"
    "detail": "...",  # error details
    "fallback": "..." # fallback response
}
```

### Graceful Degradation

```python
# If LLM classification fails → Use keyword classification
# If framework fails → Return error with fallback response
# If routing fails → Use fallback_handler
# If formatting fails → Return raw response
```

---

## Integration with UI

### Invocation from Streamlit

```python
# In ui/streamlit_app.py
workflow = st.session_state.graph  # Cached graph
state = {
    "query": query,
    "customer_info": customer_info or {},
    "classification": "",
    "intermediate_responses": {},
    "final_response": "",
    "chat_history": st.session_state.chat_history,
}
result = workflow.invoke(state)
final_answer = result["final_response"]
```

### State Persistence

- **Graph**: Cached in `st.session_state.graph`
- **Chat History**: Maintained in `st.session_state.chat_history`
- **Customer Info**: Fetched per session

---

## Testing & Validation

### Test Coverage

**Classification Tests**:
- 19 sample queries tested
- 79% accuracy achieved
- Edge cases identified

**Routing Tests**:
- All 4 routes verified
- Fallback handler tested
- Error scenarios covered

**Integration Tests**:
- End-to-end flow validated
- Each framework tested independently
- Combined workflow verified

---

## Future Enhancements

1. **Parallel Processing**: Execute multiple frameworks simultaneously
2. **Confidence Scores**: Add classification confidence thresholds
3. **Multi-Label**: Support queries spanning multiple categories
4. **Streaming Responses**: Stream LLM responses for better UX
5. **A/B Testing**: Compare different classification strategies

---

**Last Updated**: December 1, 2025
**File**: `orchestration/graph.py`
**Lines of Code**: 217
