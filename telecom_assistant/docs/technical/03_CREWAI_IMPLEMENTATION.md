# CrewAI Implementation - Billing & Account Management

## Overview

CrewAI powers the **billing and account management** capabilities of the Telecom Service Assistant. It uses a multi-agent approach where specialized agents collaborate to analyze bills, review service plans, and provide optimization recommendations.

---

## Architecture

### Agent Structure

```
┌────────────────────────────────────────┐
│         Billing Specialist             │
│  Role: Senior Billing Analyst          │
│  Goal: Accurate billing analysis       │
│  Tools: 15 database query tools        │
└──────────────┬─────────────────────────┘
               │
               │ Sequential Process
               │
               ▼
┌────────────────────────────────────────┐
│         Service Advisor                │
│  Role: Customer Service Expert         │
│  Goal: Optimization recommendations    │
│  Tools: 15 database query tools        │
└────────────────────────────────────────┘
```

**Process Type**: Sequential (Billing Specialist → Service Advisor)

---

## Agents

### 1. Billing Specialist Agent

**File**: `agents/billing_agents.py` (Lines 88-102)

**Configuration**:
```python
Agent(
    role="Senior Billing Analyst",
    goal="Provide accurate billing analysis and service plan reviews",
    backstory="Expert telecom billing analyst with deep knowledge 
               of pricing, charges, and service plans",
    tools=all_tools,              # 15 database tools
    verbose=True,                 # Show reasoning
    allow_delegation=False,       # Work independently
    llm=llm,                      # gpt-4o-mini, temp=0.1
)
```

**Capabilities**:
- Analyze billing statements
- Identify charge discrepancies
- Calculate total costs
- Review usage patterns
- Compare plan pricing

**Primary Tasks**:
- Billing analysis (Task 1)
- Data gathering from database
- Initial assessment

### 2. Service Advisor Agent

**File**: `agents/billing_agents.py` (Lines 104-119)

**Configuration**:
```python
Agent(
    role="Customer Service Expert",
    goal="Provide helpful recommendations for service optimization",
    backstory="Friendly customer service expert who helps customers 
               optimize their telecom services and reduce costs",
    tools=all_tools,              # 15 database tools
    verbose=True,
    allow_delegation=False,
    llm=llm,                      # gpt-4o-mini, temp=0.1
)
```

**Capabilities**:
- Review plan suitability
- Suggest optimizations
- Identify savings opportunities
- Provide personalized recommendations
- Format user-friendly responses

**Primary Tasks**:
- Service optimization (Task 2)
- Synthesis and formatting (Task 3)

---

## Tools

### Database Tools (15 total)

**File**: `agents/billing_agents.py` (Lines 54-68)

All tools are **framework-specific wrappers** around database functions:

```python
from utils.database import (
    get_customer_info,
    get_all_bills,
    get_recent_bills,
    get_bill_details,
    get_service_plan_info,
    get_service_plan_details,
    get_all_service_plans,
    get_usage_history,
    get_recent_usage,
    get_customer_usage,
    get_payments,
    get_data_usage,
    get_voice_usage,
    get_sms_usage,
    get_all_customers
)

all_tools = [
    get_customer_info_tool,
    get_all_bills_tool,
    get_recent_bills_tool,
    get_bill_details_tool,
    get_service_plan_info_tool,
    get_service_plan_details_tool,
    get_all_service_plans_tool,
    get_usage_history_tool,
    get_recent_usage_tool,
    get_customer_usage_tool,
    get_payments_tool,
    get_data_usage_tool,
    get_voice_usage_tool,
    get_sms_usage_tool,
    get_all_customers_tool,
]
```

### Tool Categories

#### 1. Customer Information (2 tools)
- `get_customer_info_tool`: Fetch customer profile
- `get_all_customers_tool`: List all customers

#### 2. Billing Tools (4 tools)
- `get_all_bills_tool`: All bills for a customer
- `get_recent_bills_tool`: Recent N bills
- `get_bill_details_tool`: Specific bill details
- `get_payments_tool`: Payment history

#### 3. Service Plan Tools (3 tools)
- `get_service_plan_info_tool`: Current plan info
- `get_service_plan_details_tool`: Plan specifications
- `get_all_service_plans_tool`: All available plans

#### 4. Usage Tools (6 tools)
- `get_usage_history_tool`: Historical usage
- `get_recent_usage_tool`: Recent usage records
- `get_customer_usage_tool`: Customer-specific usage
- `get_data_usage_tool`: Data usage breakdown
- `get_voice_usage_tool`: Voice call usage
- `get_sms_usage_tool`: SMS usage

### Tool Wrapping Pattern

Each tool follows this pattern:

```python
@tool("get_customer_info")
def get_customer_info_tool(customer_id: str) -> str:
    """
    Get customer information by customer_id.
    
    Args:
        customer_id: The customer ID (e.g., 'CUST001')
        
    Returns:
        JSON string with customer details or error message
    """
    try:
        result = get_customer_info(customer_id)  # Call database function
        if not result:
            return json.dumps({"status": "not_found"})
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
```

**Key Features**:
- JSON input/output for LLM compatibility
- Error handling with status codes
- Descriptive docstrings for LLM guidance
- Type hints for clarity

---

## Tasks

### Task 1: Billing Analysis

**File**: `agents/billing_agents.py` (Lines 121-128)

```python
Task(
    description=f"""
    Analyze the billing query: {customer_query}
    Use customer_id: {customer_id}
    Retrieve relevant billing, usage, and service plan data.
    """,
    agent=billing_specialist,
    expected_output="Detailed billing analysis with relevant data",
)
```

**Process**:
1. Parse query to understand request
2. Identify needed data (bills, usage, plans)
3. Use appropriate tools to gather data
4. Analyze data for patterns or issues
5. Format findings for next agent

**Output Example**:
```
Customer CUST001's recent billing analysis:
- Last bill: $89.99 (Dec 2024)
- Plan: Premium 50GB ($79.99/month)
- Overages: $10.00 (2GB extra data)
- Usage: 52GB data, 450 mins voice, 200 SMS
- Payment status: Paid on time
```

### Task 2: Service Optimization

**File**: `agents/billing_agents.py` (Lines 130-139)

```python
Task(
    description="""
    Review the billing analysis from the previous task.
    Determine if the customer's current service plan is optimal.
    Suggest improvements or confirm the current plan is appropriate.
    """,
    agent=service_advisor,
    expected_output="Plan review with recommendations or confirmation",
)
```

**Process**:
1. Review billing specialist's analysis
2. Compare usage vs. plan limits
3. Check for overages or underutilization
4. Query alternative plans if needed
5. Calculate potential savings
6. Formulate recommendations

**Output Example**:
```
Plan Review for CUST001:
- Current Plan: Premium 50GB ($79.99)
- Usage Pattern: Consistently 50-55GB/month
- Issue: Frequent $10-15 overage charges

Recommendation:
- Switch to Premium 100GB plan ($99.99)
- Savings: $10-15/month in overages
- Net change: +$5/month for stable billing
- Additional benefit: Future-proof for growth
```

### Task 3: Final Synthesis

**File**: `agents/billing_agents.py` (Lines 141-150)

```python
Task(
    description="""
    Synthesize the billing analysis and plan recommendations
    into a clear, customer-friendly response.
    Format the output as a JSON object.
    """,
    agent=service_advisor,
    expected_output="JSON with bill_analysis, plan_review, recommendations",
)
```

**Process**:
1. Combine insights from both agents
2. Format in customer-friendly language
3. Structure as JSON for system processing
4. Include actionable recommendations

**Output Structure**:
```json
{
    "bill_analysis": "Your last bill was $89.99...",
    "plan_review": "Your Premium 50GB plan is mostly suitable...",
    "recommendations": "Consider upgrading to Premium 100GB...",
    "status": "ok"
}
```

---

## Crew Configuration

### Crew Assembly

**File**: `agents/billing_agents.py` (Lines 152-160)

```python
crew = Crew(
    agents=[billing_specialist, service_advisor],
    tasks=[billing_task, advisor_task, synthesis_task],
    process=Process.sequential,    # Execute in order
    verbose=True,                   # Show reasoning steps
    cache=True,                     # Enable caching
    memory=False,                   # No long-term memory
)
```

**Process Flow**:
```
billing_task (Agent 1) → advisor_task (Agent 2) → synthesis_task (Agent 2) → Final Output
```

### Execution

**Function**: `process_billing_query(customer_id, query)`

```python
def process_billing_query(customer_id: str, query: str) -> Dict[str, Any]:
    """
    Process a billing/account query using CrewAI agents.
    
    Args:
        customer_id: Customer ID (e.g., 'CUST001')
        query: User's billing question
        
    Returns:
        Dictionary with analysis and recommendations
    """
    try:
        crew = create_billing_crew(customer_id, query)
        result = crew.kickoff()  # Execute all tasks
        
        # Parse result (can be string or TaskOutput)
        if hasattr(result, "raw"):
            raw_output = result.raw
        else:
            raw_output = str(result)
            
        # Try to parse JSON
        parsed = json.loads(raw_output)
        return {
            "customer_id": customer_id,
            "query": query,
            **parsed,
            "status": "ok"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "fallback": "Unable to process billing query"
        }
```

---

## Example Execution

### Input Query

```python
customer_id = "CUST001"
query = "Why is my bill higher than usual this month?"
```

### Execution Trace

**Task 1 - Billing Specialist**:
```
> Entering new Agent chain...
Thought: I need to gather the customer's billing data
Action: get_recent_bills
Action Input: {"customer_id": "CUST001", "limit": 3}

Observation: [
    {"bill_id": "BILL035", "amount": 89.99, "month": "2024-12"},
    {"bill_id": "BILL027", "amount": 79.99, "month": "2024-11"},
    {"bill_id": "BILL019", "amount": 79.99, "month": "2024-10"}
]

Thought: I see the December bill is $10 higher
Action: get_bill_details
Action Input: {"bill_id": "BILL035"}

Observation: {
    "base_charge": 79.99,
    "data_overage": 10.00,
    "taxes": 0.00,
    "total": 89.99
}

Thought: The increase is due to data overage
Action: get_data_usage
Action Input: {"customer_id": "CUST001", "month": "2024-12"}

Observation: {
    "allocated": 50,
    "used": 52,
    "overage": 2,
    "overage_rate": 5.00
}

Final Answer: Customer exceeded their 50GB data limit by 2GB,
resulting in a $10 overage charge ($5/GB).
```

**Task 2 - Service Advisor**:
```
> Entering new Agent chain...
Thought: Customer has regular overages, should review plan
Action: get_all_service_plans
Action Input: {}

Observation: [
    {"plan_id": "PLAN002", "name": "Premium 50GB", "price": 79.99},
    {"plan_id": "PLAN003", "name": "Premium 100GB", "price": 99.99},
    {"plan_id": "PLAN004", "name": "Unlimited", "price": 119.99}
]

Thought: Premium 100GB would eliminate overages
Final Answer: Recommend upgrading to Premium 100GB plan
```

**Task 3 - Synthesis**:
```json
{
    "bill_analysis": "Your December bill of $89.99 is $10 higher than usual 
                     due to a data overage charge. You used 52GB against your 
                     50GB limit, resulting in a $10 charge ($5 per GB over).",
    "plan_review": "Your current Premium 50GB plan costs $79.99/month. 
                   Based on recent usage, you frequently exceed this limit.",
    "recommendations": "Consider upgrading to the Premium 100GB plan ($99.99/month). 
                       This would eliminate overage charges and provide more headroom 
                       for future needs. The $20 increase is offset by avoiding 
                       $10-15/month in overages.",
    "status": "ok"
}
```

---

## Performance Characteristics

### Execution Time

| Phase | Time | Notes |
|-------|------|-------|
| Crew initialization | 0.5s | Create agents and tasks |
| Task 1 (Billing) | 8-12s | 3-5 tool calls, LLM reasoning |
| Task 2 (Advisor) | 5-8s | 1-3 tool calls, analysis |
| Task 3 (Synthesis) | 2-3s | Formatting only |
| **Total** | **15-23s** | Full query processing |

### LLM Configuration

```python
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,    # Low temperature for consistency
)
```

**Temperature Impact**:
- `0.1`: Deterministic, consistent outputs
- Good for billing (accuracy critical)
- Prevents creative but incorrect answers

### Caching Strategy

**Global Cache** (Lines 45-51):
```python
_cached_crew_components = {}

def create_billing_crew(customer_id: str, customer_query: str):
    cache_key = f"{customer_id}_{hash(customer_query)}"
    if cache_key in _cached_crew_components:
        return _cached_crew_components[cache_key]
    # ... create crew ...
    _cached_crew_components[cache_key] = crew
    return crew
```

**Benefits**:
- Avoid recreating agents for similar queries
- Faster response times
- Reduced API costs

---

## Error Handling

### Database Errors

```python
@tool("get_customer_info")
def get_customer_info_tool(customer_id: str) -> str:
    try:
        result = get_customer_info(customer_id)
        if not result:
            return json.dumps({"status": "not_found"})
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
```

**Agent Response**: LLM adapts to error messages and tries alternatives

### Process Errors

```python
def process_billing_query(customer_id: str, query: str):
    try:
        crew = create_billing_crew(customer_id, query)
        result = crew.kickoff()
        # ... process result ...
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "fallback": "Unable to process billing query. 
                        Please try again or contact support."
        }
```

**Graceful Degradation**: Returns structured error with fallback message

---

## Integration with Orchestration

### LangGraph Integration

**File**: `orchestration/graph.py` (Lines 58-74)

```python
def crew_ai_node(state: TelecomAssistantState) -> TelecomAssistantState:
    """Process billing/account queries with CrewAI."""
    query = state.get("query", "")
    customer_info = state.get("customer_info", {})
    customer_id = customer_info.get("customer_id", "CUST001")
    
    # Enrich query with context
    if customer_info:
        name = customer_info.get("name", "")
        plan_id = customer_info.get("service_plan_id", "")
        context_query = f"Customer: {customer_id} ({name}), 
                         Plan: {plan_id}. 
                         Query: {query}"
    else:
        context_query = query
    
    result = process_billing_query(customer_id, context_query)
    return {**state, "intermediate_responses": {"crew_ai": result}}
```

---

## Testing

### Test Coverage

**Sample Queries**:
1. "Why is my bill higher this month?"
2. "Show me my recent bills"
3. "Am I on the right plan?"
4. "What are my data usage patterns?"
5. "Can I save money by switching plans?"

**Test Results** (all passed):
- ✅ Bill retrieval and analysis
- ✅ Plan comparison
- ✅ Overage detection
- ✅ Recommendation generation
- ✅ JSON output formatting

---

## Future Enhancements

1. **Predictive Analysis**: Forecast future usage and bills
2. **Cost Optimization**: Automated plan switching recommendations
3. **Anomaly Detection**: Flag unusual charges automatically
4. **Memory**: Remember customer preferences across sessions
5. **Multi-Customer**: Handle family plans and shared accounts

---

**Last Updated**: December 1, 2025
**File**: `agents/billing_agents.py`
**Lines of Code**: 201
**Agent Count**: 2
**Tool Count**: 15
**Task Count**: 3
