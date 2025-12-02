# CrewAI implementation
import os
from typing import Dict, Any  # Removed Optional (unused)

# MUST disable telemetry BEFORE importing CrewAI
os.environ["OTEL_SDK_DISABLED"] = "true"

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
1. Use tools to fetch the customer's actual billing data from the database
2. Examine the customer's current and previous bills to identify any changes
3. Explain each charge in simple language
4. Identify any unusual or one-time charges
5. Verify that all charges are consistent with the customer's plan

CRITICAL RULES:
- ONLY report data that exists in the database (from get_customer_usage tool)
- If only ONE billing period exists, say "No previous billing data available for comparison"
- DO NOT invent or fabricate billing periods, dates, or usage numbers
- If a comparison is not possible, explain charges for the single period only

Available tools: customer data, usage history, service plans, past tickets, and more.
Always start by retrieving the customer's usage data with get_customer_usage.
""".strip()

ADVISOR_PROMPT = """
You are a telecom service advisor who helps customers optimize their plans.
Your job is to:
1. Use tools to fetch actual customer usage data from the database
2. Analyze the customer's usage patterns (data, calls, texts)
3. Compare their usage with their current plan limits
4. Identify if they are paying for services they don't use
5. Suggest better plans if available based on real usage data

CRITICAL RULES:
- ONLY use actual data from get_customer_usage and get_service_plan tools
- DO NOT make assumptions about usage patterns without data
- Base recommendations only on verified usage history from the database

Available tools: usage data, service plans, coverage quality, service areas, and more.
Be specific about potential savings or benefits of your recommendations.
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
                backstory=(
                    "Senior billing analyst with 10 years of telecom experience. "
                    "Known for accuracy and never making assumptions without data. "
                    "Always verifies information using database tools before reporting."
                ),
                goal="Explain bill components accurately using only verified database data",
                tools=database_tools,
                llm=llm,
                allow_delegation=False,
                max_iter=5,  # Limit iterations to prevent infinite loops
            )
            service_agent = Agent(
                role="Service Advisor",
                backstory=(
                    "Customer-focused telecom advisor who helps optimize plans. "
                    "Uses actual usage data to make recommendations. "
                    "Never suggests changes without verifying customer usage patterns first."
                ),
                goal="Provide data-driven plan recommendations based on verified usage",
                tools=database_tools,
                llm=llm,
                allow_delegation=False,
                max_iter=5,  # Limit iterations to prevent infinite loops
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
                description=(
                    "Analyze the customer's most recent bill using get_customer_usage tool. "
                    "Customer ID: {customer_id}\n"
                    "Query: {query}\n\n"
                    "IMPORTANT STEPS:\n"
                    "1. Use get_customer_usage tool with customer_id '{customer_id}' to fetch usage data\n"
                    "2. Check how many billing periods are returned\n"
                    "3. If user asks 'why is bill HIGHER' or asks for COMPARISON:\n"
                    "   - If only 1 period exists: START response with 'I can only see one billing period in your history. "
                    "Without previous billing data, I cannot determine if your bill increased or compare to prior months.'\n"
                    "   - If 2+ periods exist: Compare the two most recent periods\n"
                    "4. Only report data that actually exists in the database\n"
                    "5. Do not fabricate billing periods or usage data"
                ),
                expected_output=(
                    "A detailed bill analysis. "
                    "If user asks for comparison but only one period exists, start with limitation statement. "
                    "Then provide line-item explanations for the available period(s). "
                    "If multiple periods exist, include period-to-period comparison."
                ),
                agent=billing_agent,
            )
            advisor_task = Task(
                description=(
                    "Review the customer's actual usage data and plan suitability. "
                    "Customer ID: {customer_id}\n\n"
                    "Use get_customer_usage tool with customer_id '{customer_id}' to fetch usage data. "
                    "Then use get_service_plan tool to get their current plan details. "
                    "CRITICAL RULES:\n"
                    "1. Get actual usage numbers from get_customer_usage\n"
                    "2. Get plan limits from get_service_plan\n"
                    "3. NEVER recommend a plan with LOWER limits than customer's actual usage\n"
                    "   Example: If customer uses 4.5 GB, DO NOT suggest 3 GB plan (causes overages!)\n"
                    "4. Only suggest downgrade if usage is significantly below current plan limits\n"
                    "5. Consider buffer room - don't recommend plans at exact usage level"
                ),
                expected_output=(
                    "Plan optimization analysis with safe, practical recommendations. "
                    "If customer's usage is close to plan limits, say 'You are using your plan efficiently.' "
                    "Only suggest alternatives if there's significant underutilization. "
                    "Never recommend plans that would cause overage charges."
                ),
                agent=service_agent,
            )
            synthesis_task = Task(
                description=(
                    "Combine the billing analysis and plan review into a final customer report. "
                    "IMPORTANT RULES:\n"
                    "1. If billing analysis mentions 'only one billing period' or 'cannot compare', "
                    "KEEP that statement at the START of your response\n"
                    "2. If plan review says customer is using plan efficiently, don't override with downgrade suggestions\n"
                    "3. Provide clear explanations and actionable recommendations\n"
                    "4. Do not add information not present in previous task outputs\n"
                    "5. Do not contradict findings from billing or advisor tasks"
                ),
                expected_output=(
                    "Customer-friendly report that:\n"
                    "- Starts with any data limitation statements from billing analysis\n"
                    "- Explains charges clearly\n"
                    "- Includes safe, practical plan recommendations from advisor\n"
                    "- Does not suggest plans that would cause overages"
                ),
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
                verbose=True,  # Enable output so user can see progress
                max_rpm=10,  # Limit API calls
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
        
        # Return the actual CrewAI response directly
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
