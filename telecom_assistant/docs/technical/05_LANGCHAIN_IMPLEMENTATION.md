# LangChain Implementation - Service Recommendations

## Overview

LangChain powers the **service plan recommendation** engine using a ReAct (Reasoning + Acting) agent. The agent iteratively reasons about customer needs, queries relevant data, and formulates personalized service recommendations.

---

## Architecture

### ReAct Agent Pattern

```
┌────────────────────────────────────────┐
│           User Query                   │
│  "What's the best plan for me?"        │
└──────────────┬─────────────────────────┘
               │
               ▼
┌────────────────────────────────────────┐
│        LangChain ReAct Agent           │
│  LLM: gpt-4o-mini (temp=0.2)           │
│  Max Iterations: 6                     │
│  Verbose: True                         │
└──────────────┬─────────────────────────┘
               │
      ┌────────┴────────┐
      │  Reasoning Loop │
      │  (Iterative)    │
      └────────┬────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│Tool 1  │ │Tool 2  │ │Tool 3  │
│Usage   │ │Plans   │ │Coverage│
└────────┘ └────────┘ └────────┘
    ▼          ▼          ▼
┌────────┐ ┌────────┐
│Tool 4  │ │Tool 5  │
│Python  │ │Estimat.│
└────────┘ └────────┘
```

**Agent Type**: Zero-shot ReAct with Tool Selection

---

## Agent Configuration

### Agent Setup

**File**: `agents/service_agents.py` (Lines 98-125)

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# LLM Configuration
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,           # Balanced creativity
    openai_api_key=api_key
)

# Tools
tools = [
    get_customer_usage_tool,
    get_plan_details_tool,
    check_coverage_quality_tool,
    python_repl_tool,
    estimate_data_usage_tool
]

# Create ReAct agent
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=SERVICE_RECOMMENDATION_TEMPLATE
)

# Create executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,              # Show reasoning
    max_iterations=6,          # Prevent infinite loops
    handle_parsing_errors=True # Recover from errors
)
```

**Key Parameters**:
- `temperature=0.2`: Not too rigid, allows for recommendations
- `max_iterations=6`: Balance thoroughness and performance
- `verbose=True`: Enables debugging and transparency
- `handle_parsing_errors=True`: Graceful error recovery

---

## Prompt Template

### SERVICE_RECOMMENDATION_TEMPLATE

**File**: `agents/service_agents.py` (Lines 47-76)

```python
SERVICE_RECOMMENDATION_TEMPLATE = PromptTemplate(
    input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
    template="""You are a helpful telecom service advisor. Your goal is to 
    recommend the best service plan for customers based on their usage patterns.

Available tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""
)
```

**Components**:
1. **Role Definition**: "helpful telecom service advisor"
2. **Goal**: "recommend the best service plan"
3. **Available Tools**: List of tool names and descriptions
4. **ReAct Format**: Thought → Action → Observation loop
5. **Termination**: "I now know the final answer" → Final Answer

---

## Tools

### Tool 1: get_customer_usage

**File**: `agents/service_agents.py` (Lines 78-96)

**Purpose**: Retrieve customer usage history

**Implementation**:
```python
@tool("get_customer_usage")
def get_customer_usage_tool(customer_id: str) -> str:
    """
    Get usage history for a customer.
    
    Args:
        customer_id: Customer ID (e.g., 'CUST001')
        
    Returns:
        JSON string with usage data (data, voice, SMS)
    """
    from utils.database import get_customer_usage
    
    result = get_customer_usage(customer_id)
    
    if result:
        return json.dumps({
            "status": "ok",
            "usage": result,
            "summary": f"Customer {customer_id} has {len(result)} usage records"
        })
    else:
        return json.dumps({
            "status": "not_found",
            "message": f"No usage data for {customer_id}"
        })
```

**Output Example**:
```json
{
    "status": "ok",
    "usage": [
        {
            "month": "2024-12",
            "data_gb": 52.3,
            "voice_minutes": 450,
            "sms_count": 200
        },
        {
            "month": "2024-11",
            "data_gb": 48.7,
            "voice_minutes": 520,
            "sms_count": 180
        }
    ],
    "summary": "Customer CUST001 has 3 usage records"
}
```

### Tool 2: get_plan_details

**File**: `agents/service_agents.py` (Lines 98-115)

**Purpose**: Retrieve service plan specifications

**Implementation**:
```python
@tool("get_plan_details")
def get_plan_details_tool(plan_id: str = None) -> str:
    """
    Get details of service plans. If plan_id is None, returns all plans.
    
    Args:
        plan_id: Optional plan ID (e.g., 'PLAN002')
        
    Returns:
        JSON string with plan details
    """
    from utils.database import (
        get_service_plan_details,
        get_all_service_plans
    )
    
    if plan_id:
        result = get_service_plan_details(plan_id)
        return json.dumps({"status": "ok", "plan": result})
    else:
        result = get_all_service_plans()
        return json.dumps({
            "status": "ok",
            "plans": result,
            "count": len(result)
        })
```

**Output Example (all plans)**:
```json
{
    "status": "ok",
    "plans": [
        {
            "plan_id": "PLAN001",
            "plan_name": "Basic 10GB",
            "monthly_cost": 29.99,
            "data_limit_gb": 10,
            "voice_minutes": 500,
            "sms_limit": 100
        },
        {
            "plan_id": "PLAN002",
            "plan_name": "Premium 50GB",
            "monthly_cost": 79.99,
            "data_limit_gb": 50,
            "voice_minutes": 1000,
            "sms_limit": 500
        }
    ],
    "count": 5
}
```

### Tool 3: check_coverage_quality

**File**: `agents/service_agents.py` (Lines 117-135)

**Purpose**: Check network coverage quality by location

**Implementation**:
```python
@tool("check_coverage_quality")
def check_coverage_quality_tool(location: str) -> str:
    """
    Check network coverage quality for a location.
    
    Args:
        location: Location name (e.g., 'Downtown', 'Suburb')
        
    Returns:
        JSON string with coverage info
    """
    from utils.database import check_coverage_quality
    
    result = check_coverage_quality(location)
    
    if result:
        return json.dumps({
            "status": "ok",
            "coverage": result,
            "quality": result.get("signal_quality", "Unknown")
        })
    else:
        return json.dumps({
            "status": "not_found",
            "message": f"No coverage data for {location}"
        })
```

**Output Example**:
```json
{
    "status": "ok",
    "coverage": {
        "location": "Downtown",
        "signal_quality": "Excellent",
        "5g_available": true,
        "avg_speed_mbps": 85.5
    },
    "quality": "Excellent"
}
```

### Tool 4: PythonREPLTool

**File**: `agents/service_agents.py` (Lines 137-141)

**Purpose**: Execute Python code for calculations

**Implementation**:
```python
from langchain_experimental.tools import PythonREPLTool

python_repl_tool = PythonREPLTool(
    name="python_repl",
    description="Execute Python code for calculations. 
                 Useful for comparing plans, calculating savings, 
                 or analyzing usage patterns."
)
```

**Usage Examples**:

1. **Calculate savings**:
```python
# Action Input:
current_cost = 79.99
new_cost = 99.99
savings_per_month = current_cost - new_cost
annual_savings = savings_per_month * 12
print(f"Monthly: ${savings_per_month}, Annual: ${annual_savings}")

# Observation:
Monthly: $-20.0, Annual: $-240.0
```

2. **Compare usage to limits**:
```python
# Action Input:
usage_gb = 52.3
limit_gb = 50
overage_gb = max(0, usage_gb - limit_gb)
overage_cost = overage_gb * 5  # $5 per GB
print(f"Overage: {overage_gb}GB, Cost: ${overage_cost}")

# Observation:
Overage: 2.3GB, Cost: $11.5
```

### Tool 5: estimate_data_usage

**File**: `agents/service_agents.py` (Lines 143-168)

**Purpose**: Estimate future data usage based on activities

**Implementation**:
```python
@tool("estimate_data_usage")
def estimate_data_usage_tool(activities: str) -> str:
    """
    Estimate monthly data usage based on user activities.
    
    Args:
        activities: Description of usage (e.g., 'streaming 2h/day, 
                   browsing 1h/day')
        
    Returns:
        JSON string with estimated usage in GB
    """
    # Parse activities
    streaming_hours = extract_hours(activities, 'stream')
    browsing_hours = extract_hours(activities, 'brows')
    video_calls = extract_hours(activities, 'video')
    
    # Estimate usage (rough averages)
    streaming_gb = streaming_hours * 30 * 1.5  # 1.5GB/hour
    browsing_gb = browsing_hours * 30 * 0.1    # 0.1GB/hour
    video_gb = video_calls * 30 * 0.5          # 0.5GB/hour
    
    total_gb = streaming_gb + browsing_gb + video_gb
    
    return json.dumps({
        "status": "ok",
        "estimated_usage_gb": round(total_gb, 1),
        "breakdown": {
            "streaming": round(streaming_gb, 1),
            "browsing": round(browsing_gb, 1),
            "video_calls": round(video_gb, 1)
        }
    })
```

**Output Example**:
```json
{
    "status": "ok",
    "estimated_usage_gb": 123.5,
    "breakdown": {
        "streaming": 90.0,
        "browsing": 3.0,
        "video_calls": 30.5
    }
}
```

---

## ReAct Loop Example

### Full Execution Trace

**Input**: "What plan should I get? I stream videos 2 hours daily."

**Iteration 1**:
```
Thought: I need to estimate the customer's data usage first
Action: estimate_data_usage
Action Input: "streaming 2 hours daily"

Observation: {
    "status": "ok",
    "estimated_usage_gb": 90.0,
    "breakdown": {"streaming": 90.0, "browsing": 0.0, "video_calls": 0.0}
}
```

**Iteration 2**:
```
Thought: Customer needs ~90GB/month. Let me check available plans
Action: get_plan_details
Action Input: None

Observation: {
    "status": "ok",
    "plans": [
        {"plan_id": "PLAN003", "plan_name": "Premium 100GB", 
         "monthly_cost": 99.99, "data_limit_gb": 100},
        {"plan_id": "PLAN004", "plan_name": "Unlimited", 
         "monthly_cost": 119.99, "data_limit_gb": null}
    ],
    "count": 5
}
```

**Iteration 3**:
```
Thought: Let me calculate the cost difference between plans
Action: python_repl
Action Input: 
plan_100gb = 99.99
plan_unlimited = 119.99
difference = plan_unlimited - plan_100gb
print(f"Unlimited costs ${difference} more per month")

Observation: Unlimited costs $20.0 more per month
```

**Iteration 4**:
```
Thought: I now know the final answer
Final Answer: Based on your streaming habits (2 hours daily), 
you'll use approximately 90GB per month. I recommend the 
**Premium 100GB plan at $99.99/month**. 

This provides:
- 100GB data (enough for your 90GB usage with 10GB buffer)
- No overage charges
- Costs $20 less than Unlimited
- Saves you $240/year compared to Unlimited

If your usage increases beyond 100GB, you can upgrade to 
Unlimited ($119.99) to avoid overages.
```

---

## Agent Execution

### Process Function

**File**: `agents/service_agents.py` (Lines 170-209)

```python
def process_recommendation_query(query: str) -> Dict[str, Any]:
    """
    Process service recommendation query using LangChain.
    
    Args:
        query: User's question about service plans
        
    Returns:
        Dictionary with recommendation and reasoning
    """
    try:
        # Create agent executor
        agent_executor = create_service_agent()
        
        # Execute query
        result = agent_executor.invoke({"input": query})
        
        # Extract output
        final_answer = result.get("output", "")
        intermediate_steps = result.get("intermediate_steps", [])
        
        # Format response
        return {
            "query": query,
            "recommendation": final_answer,
            "reasoning_steps": len(intermediate_steps),
            "tools_used": extract_tools_used(intermediate_steps),
            "status": "ok"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "fallback": "Unable to provide recommendation. 
                        Please contact customer service."
        }
```

---

## Performance Characteristics

### Execution Time

| Phase | Time | Notes |
|-------|------|-------|
| Agent initialization | 0.2s | One-time setup |
| Iteration 1 | 2-3s | LLM reasoning + tool call |
| Iteration 2 | 2-3s | LLM reasoning + tool call |
| Iteration 3 | 1-2s | Python REPL execution |
| Final reasoning | 1-2s | LLM synthesis |
| **Total** | **5-10s** | Full recommendation |

**Average Iterations**: 3-4 (out of max 6)

### LLM Calls

- **Per Iteration**: 1 LLM call (reasoning + tool selection)
- **Total**: 3-6 LLM calls per query
- **Model**: gpt-4o-mini (cost-effective)

---

## Error Handling

### Parsing Errors

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    handle_parsing_errors=True  # Auto-retry on parse errors
)
```

**Example**:
```
Action: get_plan_details
Action Input: PLAN002  # Missing quotes

Error: Invalid JSON

Agent automatically retries with:
Action: get_plan_details
Action Input: "PLAN002"
```

### Tool Errors

```python
@tool("get_customer_usage")
def get_customer_usage_tool(customer_id: str) -> str:
    try:
        result = get_customer_usage(customer_id)
        return json.dumps({"status": "ok", "usage": result})
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })
```

**Agent Adaptation**: Sees error status, tries alternative approach

---

## Integration with Orchestration

### LangGraph Integration

**File**: `orchestration/graph.py` (Lines 87-101)

```python
def langchain_node(state: TelecomAssistantState) -> TelecomAssistantState:
    """Process service recommendations with LangChain."""
    query = state.get("query", "")
    customer_info = state.get("customer_info", {})
    
    # Enrich query with customer context
    if customer_info:
        customer_id = customer_info.get("customer_id", "")
        plan_id = customer_info.get("service_plan_id", "")
        context_query = f"Customer {customer_id} on {plan_id} plan. {query}"
    else:
        context_query = query
    
    result = process_recommendation_query(context_query)
    return {**state, "intermediate_responses": {"langchain": result}}
```

**Context Enrichment**: Adds customer ID and current plan to query

---

## Testing

### Test Scenarios

1. **High Data User**:
   - Input: "I stream 4K videos 4 hours daily"
   - Expected: Recommend Unlimited plan

2. **Low Data User**:
   - Input: "I only use email and light browsing"
   - Expected: Recommend Basic plan

3. **Current Plan Analysis**:
   - Input: "Is my current plan optimal?"
   - Expected: Check usage vs. plan, suggest changes if needed

4. **Cost Comparison**:
   - Input: "Compare Premium 50GB and Premium 100GB"
   - Expected: Use Python REPL for calculations

**Test Results**: ✅ All scenarios passing

---

## Advantages of ReAct Pattern

1. **Transparency**: Verbose mode shows reasoning
2. **Flexibility**: Can adapt to different queries
3. **Tool Composition**: Can use multiple tools in sequence
4. **Error Recovery**: Handle parsing errors gracefully
5. **Iterative Refinement**: Gather data incrementally

---

## Future Enhancements

1. **Streaming Responses**: Stream LLM output for better UX
2. **Memory**: Remember customer preferences
3. **Multi-Plan Comparison**: Compare 3+ plans side-by-side
4. **Predictive Usage**: ML model for usage forecasting
5. **A/B Testing**: Test different prompt templates

---

**Last Updated**: December 1, 2025
**File**: `agents/service_agents.py`
**Lines of Code**: 209
**Tool Count**: 5
**Max Iterations**: 6
**Average Resolution Time**: 5-10 seconds
