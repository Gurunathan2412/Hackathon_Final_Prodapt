# LangChain implementation
from typing import Dict, Any
from utils.database import get_customer_usage, get_service_plan, get_coverage_quality, get_service_areas

try:
    from langchain.agents import create_react_agent, AgentExecutor  # type: ignore
    from langchain.tools import Tool  # type: ignore
    from langchain.tools.python.tool import PythonREPLTool  # type: ignore
    from langchain.prompts import PromptTemplate  # type: ignore
    from langchain_openai import ChatOpenAI  # type: ignore
except Exception:  # pragma: no cover
    create_react_agent = AgentExecutor = Tool = PythonREPLTool = PromptTemplate = ChatOpenAI = object  # type: ignore

try:
    from loguru import logger  # type: ignore
except Exception:
    logger = None

from config.config import OPENAI_API_KEY

SERVICE_RECOMMENDATION_TEMPLATE = """You are a telecom service advisor who helps customers find the best plan for their needs.
When recommending plans, consider:
1. The customer's usage patterns (data, voice, SMS)
2. Number of people/devices that will use the plan
3. Special requirements (international calling, streaming, etc.)
4. Budget constraints
Always explain WHY a particular plan is a good fit for their needs.
User query: {query}
If you need more information, ask for it.
""".strip()


def _estimate_data_usage(activities: str) -> str:
    """Placeholder function to estimate data usage based on activity description.

    Replace with real parsing logic later.
    """
    # Very naive heuristic placeholder
    lower = activities.lower()
    gb = 0
    if "stream" in lower:
        gb += 3  # assume ~3GB/month for light streaming
    if "video" in lower:
        gb += 2
    if "brows" in lower:
        gb += 1
    if "gaming" in lower:
        gb += 4
    if gb == 0:
        gb = 1
    return f"Estimated monthly data need: ~{gb} GB (heuristic placeholder)"


_SERVICE_EXECUTOR_CACHE = None


def create_service_agent(db_uri: str = "sqlite:///telecom_assistant/data/telecom.db"):
    global _SERVICE_EXECUTOR_CACHE
    if _SERVICE_EXECUTOR_CACHE is not None:
        return _SERVICE_EXECUTOR_CACHE
    # TODO: Create an LLM instance
    llm = None
    if ChatOpenAI is not object:
        try:  # pragma: no cover
            llm = ChatOpenAI(model_name="gpt-4", temperature=0.2)
        except Exception:
            llm = None

    # TODO: Create tools for the agent
    # Create database query tools
    def get_usage_data(customer_id: str) -> str:
        """Get customer usage data from database"""
        usage = get_customer_usage(customer_id)
        if not usage:
            return f"No usage data found for {customer_id}"
        latest = usage[0]
        return (
            f"Latest usage: {latest['data_used_gb']} GB data, "
            f"{latest['voice_minutes_used']} voice mins, "
            f"{latest['sms_count_used']} SMS, "
            f"Bill: ₹{latest['total_bill_amount']}"
        )
    
    def get_plan_details(plan_id: str) -> str:
        """Get service plan details from database"""
        plan = get_service_plan(plan_id)
        if not plan:
            return f"Plan {plan_id} not found"
        data = "Unlimited" if plan['unlimited_data'] else f"{plan['data_limit_gb']} GB"
        voice = "Unlimited" if plan['unlimited_voice'] else f"{plan['voice_minutes']} mins"
        return (
            f"{plan['name']}: ₹{plan['monthly_cost']}/month, "
            f"Data: {data}, Voice: {voice}, "
            f"{plan['description']}"
        )
    
    def check_coverage_in_area(city: str) -> str:
        """Check coverage quality in a specific city"""
        areas = get_service_areas(city)
        if not areas:
            return f"No coverage information found for {city}"
        
        coverage = get_coverage_quality()
        result = f"Coverage in {city}:\n"
        for area in areas[:3]:
            area_coverage = [c for c in coverage if c['area_id'] == area['area_id']]
            if area_coverage:
                cov = area_coverage[0]
                result += f"  {area['district']}: {cov['signal_strength_category']}, {cov['avg_download_speed_mbps']} Mbps\n"
        return result.strip()
    
    usage_query_tool = None
    plan_query_tool = None
    coverage_tool = None
    if Tool is not object:
        try:  # pragma: no cover
            usage_query_tool = Tool(
                name="get_customer_usage",
                func=get_usage_data,
                description="Get customer usage history from database. Input: customer_id (e.g., CUST001)"
            )
            plan_query_tool = Tool(
                name="get_plan_details",
                func=get_plan_details,
                description="Get service plan details from database. Input: plan_id (e.g., STD_500, BASIC_100)"
            )
            coverage_tool = Tool(
                name="check_coverage_quality",
                func=check_coverage_in_area,
                description="Check coverage quality in a city. Input: city name (e.g., 'Mumbai', 'Delhi')"
            )
        except Exception:
            pass

    python_tool = None
    if PythonREPLTool is not object:
        try:  # pragma: no cover
            python_tool = PythonREPLTool()
        except Exception:
            python_tool = None

    usage_estimate_tool = None
    if Tool is not object:
        try:  # pragma: no cover
            usage_estimate_tool = Tool(
                name="estimate_data_usage",
                func=_estimate_data_usage,
                description="Estimate monthly data usage based on described activities",
            )
        except Exception:
            usage_estimate_tool = None

    tools = [t for t in [usage_query_tool, plan_query_tool, coverage_tool, python_tool, usage_estimate_tool] if t]

    # TODO: Create the agent prompt
    prompt = None
    if PromptTemplate is not object:
        try:  # pragma: no cover
            prompt = PromptTemplate(template=SERVICE_RECOMMENDATION_TEMPLATE, input_variables=["query"])
        except Exception:
            prompt = None

    # TODO: Create the ReAct agent
    agent = None
    if create_react_agent is not object and llm and tools and prompt:
        try:  # pragma: no cover
            agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
        except Exception:
            agent = None

    # TODO: Create the AgentExecutor
    executor = None
    if AgentExecutor is not object and agent:
        executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=6,
            handle_parsing_errors=True,
        )
    _SERVICE_EXECUTOR_CACHE = executor
    return executor


def process_recommendation_query(query: str) -> Dict[str, Any]:
    executor = create_service_agent()
    if not executor:
        return {"query": query, "error": "LangChain not initialized", "detail": "Dependencies or API key missing."}
    try:  # pragma: no cover
        result = executor.invoke({"query": query})
        return {
            "query": query,
            "plan": "Derived plan (see raw)",
            "benefits": ["Cost optimization", "Usage alignment", "Upgrade path"],
            "estimated_usage": _estimate_data_usage(query),
            "raw": str(result),
            "status": "ok",
        }
    except Exception as e:
        if logger:
            logger.error(f"LangChain service execution error: {e}")
        return {
            "query": query,
            "error": "Service agent execution failed",
            "detail": str(e)[:500],
            "fallback": "Compare data/call/SMS usage to current limits; suggest next tier if >80% usage consistently.",
            "status": "error",
        }
