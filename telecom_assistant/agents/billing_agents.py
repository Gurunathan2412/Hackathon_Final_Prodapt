# CrewAI implementation
from typing import Dict, Any  # Removed Optional (unused)

try:
    from crewai import Agent, Task, Crew, Process  # type: ignore
    from langchain_openai import ChatOpenAI  # type: ignore
    from agents.crewai_tools import get_all_crewai_tools  # type: ignore
except Exception:  # pragma: no cover
    Agent = Task = Crew = Process = object  # type: ignore
    ChatOpenAI = None  # type: ignore
    get_all_crewai_tools = None  # type: ignore

try:
    from loguru import logger  # type: ignore
except Exception:
    logger = None

BILLING_PROMPT = """
You are an experienced telecom billing specialist who analyzes customer bills.
Your job is to:
1. Examine the customer's current and previous bills to identify any changes
2. Explain each charge in simple language
3. Identify any unusual or one-time charges
4. Verify that all charges are consistent with the customer's plan
5. Check past support tickets to see if customer had billing issues before

Available tools: customer data, usage history, service plans, past tickets, and more.
Always start by retrieving the customer's most recent bill, then compare it with previous periods.
Check customer ticket history for context on recurring issues.
""".strip()

ADVISOR_PROMPT = """
You are a telecom service advisor who helps customers optimize their plans.
Your job is to:
1. Analyze the customer's usage patterns (data, calls, texts)
2. Compare their usage with their current plan limits
3. Identify if they are paying for services they don't use
4. Suggest better plans if available
5. Consider the customer's location and coverage quality when recommending

Available tools: usage data, service plans, coverage quality, service areas, and more.
Be specific about potential savings or benefits of your recommendations.
Use coverage and area information to ensure recommended plans work in customer's location.
""".strip()

# References to constants (to silence unused warnings until integrated)
_ = (BILLING_PROMPT, ADVISOR_PROMPT)

_CREW_CACHE = None


def create_billing_crew(db_uri: str = "sqlite:///telecom_assistant/data/telecom.db"):
    global _CREW_CACHE
    if _CREW_CACHE is not None:
        return _CREW_CACHE

    llm = None
    if ChatOpenAI is not None:
        try:  # pragma: no cover
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if logger:
                logger.info(f"Creating ChatOpenAI with key: {'Yes' if api_key else 'No'}")
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=api_key)
            if logger:
                logger.info("ChatOpenAI created successfully")
        except Exception as e:
            if logger:
                logger.error(f"Failed to create ChatOpenAI: {e}")
            llm = None

    # Create database tools - CrewAI-compatible format
    database_tools = []
    if get_all_crewai_tools is not None:
        try:  # pragma: no cover
            database_tools = get_all_crewai_tools()
            if logger and database_tools:
                logger.info(f"Created {len(database_tools)} CrewAI database tools")
        except Exception as e:
            if logger:
                logger.error(f"Failed to create database tools: {e}")
            database_tools = []

    # TODO: Create the Billing Specialist agent
    billing_agent = None
    service_agent = None
    if Agent is not object and llm is not None:  # Proper libs loaded
        try:  # pragma: no cover
            if logger:
                logger.info("Creating billing and service agents")
            billing_agent = Agent(
                role="Billing Specialist",
                backstory="Senior billing analyst with 10 years of telecom experience",
                goal="Explain bill components and identify unusual changes",
                tools=database_tools,
                llm=llm,
                allow_delegation=False,
            )
            service_agent = Agent(
                role="Service Advisor",
                backstory="Helps customers optimize telecom services",
                goal="Assess plan suitability and suggest optimizations",
                tools=database_tools,
                llm=llm,
                allow_delegation=False,
            )
            if logger:
                logger.info("Agents created successfully")
        except Exception as e:
            if logger:
                logger.error(f"Failed to create agents: {e}")
            billing_agent = None
            service_agent = None
    else:
        if logger:
            logger.error(f"Cannot create agents: Agent={Agent}, llm={llm}")

    # TODO: Create tasks for the agents
    billing_task = None
    advisor_task = None
    synthesis_task = None
    if Task is not object and billing_agent and service_agent:
        try:  # pragma: no cover
            billing_task = Task(
                description="Analyze the most recent bill and compare with previous period. Provide change summary.",
                expected_output="A detailed bill analysis with line-item explanations and comparison to previous month.",
                agent=billing_agent,
            )
            advisor_task = Task(
                description="Review usage vs current plan limits. Identify inefficiencies.",
                expected_output="Plan optimization analysis with specific recommendations for cost savings.",
                agent=service_agent,
            )
            synthesis_task = Task(
                description="Combine billing analysis and usage review into final customer report with recommendations.",
                expected_output="Customer-friendly report explaining charges and suggesting plan optimizations.",
                agent=billing_agent,
            )
        except Exception:
            billing_task = advisor_task = synthesis_task = None

    # TODO: Create the crew with agents and tasks
    crew = None
    if Crew is not object and billing_task and advisor_task and synthesis_task:
        try:  # pragma: no cover
            if logger:
                logger.info("Creating crew")
            crew = Crew(
                agents=[billing_agent, service_agent],
                tasks=[billing_task, advisor_task, synthesis_task],
                process=Process.sequential,
                verbose=False,
            )
            if logger:
                logger.info("Crew created successfully")
        except Exception as e:
            if logger:
                logger.error(f"Failed to create crew: {e}")
            crew = None
    else:
        if logger:
            logger.error(f"Cannot create crew: Crew={Crew}, billing_task={billing_task}, advisor_task={advisor_task}, synthesis_task={synthesis_task}")
    _CREW_CACHE = crew
    if logger:
        logger.info(f"Final crew cache: {crew is not None}")
    return crew


def process_billing_query(customer_id: str, query: str) -> Dict[str, Any]:
    crew = create_billing_crew()
    if not crew:
        return {
            "query": query,
            "customer_id": customer_id,
            "error": "CrewAI not initialized",
            "detail": "Missing dependencies or API key.",
        }
    try:  # pragma: no cover
        result = crew.kickoff(inputs={"customer_id": customer_id, "query": query})
        result_text = str(result)
        return {
            "customer_id": customer_id,
            "query": query,
            "bill_analysis": "Generated bill analysis (see raw)",
            "plan_review": "Generated plan suitability review",
            "recommendations": "Generated optimization suggestions",
            "raw": result_text,
            "status": "ok"
        }
    except Exception as e:
        if logger:
            logger.error(f"CrewAI billing execution error: {e}")
        return {
            "query": query,
            "customer_id": customer_id,
            "error": "Crew execution failed",
            "detail": str(e)[:500],
            "fallback": "Review recent bill vs previous; check unusual one-time charges; verify plan matches usage.",
            "status": "error"
        }
