# LangGraph orchestration

from typing import TypedDict, Dict, Any, List
from config.config import ENABLE_LLM_CLASSIFICATION, OPENAI_MODEL_CLASSIFY
from agents.billing_agents import process_billing_query  # type: ignore
from agents.network_agents import process_network_query  # type: ignore
from agents.service_agents import process_recommendation_query  # type: ignore
from agents.knowledge_agents import process_knowledge_query  # type: ignore
import json
import re

# Attempt to import LangGraph; provide minimal fallbacks if unavailable for linting
try:
    from langgraph.graph import StateGraph, END  # type: ignore
except Exception:  # pragma: no cover
    class _DummyStateGraph:
        def __init__(self, *_args, **_kwargs):
            pass
        def add_node(self, *_args, **_kwargs):
            pass
        def add_conditional_edges(self, *_args, **_kwargs):
            pass
        def add_edge(self, *_args, **_kwargs):
            pass
        def set_entry_point(self, *_args, **_kwargs):
            pass
        def compile(self):
            return self
    StateGraph = _DummyStateGraph  # type: ignore
    END = "END"  # type: ignore

# Define the state structure
class TelecomAssistantState(TypedDict):
    query: str  # The user's original query
    customer_info: Dict[str, Any]  # Customer information if available
    classification: str  # Query classification
    intermediate_responses: Dict[str, Any]  # Responses from different nodes
    final_response: str  # Final formatted response
    chat_history: List[Dict[str, str]]  # Conversation history

# Classification node - determines query type
_llm_classifier = None
if ENABLE_LLM_CLASSIFICATION:
    try:
        from langchain_openai import ChatOpenAI  # type: ignore
        _llm_classifier = ChatOpenAI(model=OPENAI_MODEL_CLASSIFY, temperature=0)
    except Exception:
        _llm_classifier = None

try:
    from loguru import logger  # type: ignore
except Exception:
    logger = None

def classify_query(state: TelecomAssistantState) -> TelecomAssistantState:
    query = state.get("query", "").strip()
    ql = query.lower()
    
    # Filter out non-support queries first
    if len(query) < 3 or ql in {"hi", "hello", "hey"}:
        return {**state, "classification": "fallback"}
    
    # Detect irrelevant/entertainment queries
    irrelevant_keywords = {"joke", "funny", "story", "poem", "song", "game", "play", "chat", "talk"}
    if any(k in ql for k in irrelevant_keywords):
        return {**state, "classification": "fallback"}
    
    classification = "billing_account"
    if _llm_classifier:
        try:  # pragma: no cover
            prompt = (
                "You are a telecom support query classifier. Classify ONLY legitimate telecom support queries.\n\n"
                "Valid Categories:\n"
                "- billing_account: Questions about bills, charges, payments, invoices, account balance, billing details\n"
                "- network_troubleshooting: Issues with network, signal, connectivity, call quality, data speed, internet problems\n"
                "- service_recommendation: Requests for plan recommendations, upgrades, best plans, comparing plans\n"
                "- knowledge_retrieval: How-to questions, setup instructions, configuration guides, technical procedures\n"
                "- fallback: Jokes, entertainment, chitchat, off-topic questions, anything not related to telecom support\n\n"
                f"Query: {query}\n\n"
                "If this is a legitimate telecom support question, respond with the category name.\n"
                "If this is a joke, entertainment, or off-topic request, respond with 'fallback'.\n"
                "Response:"
            )
            resp = _llm_classifier.invoke(prompt)  # type: ignore
            raw = getattr(resp, 'content', '').lower().strip()
            for label in ["billing_account","network_troubleshooting","service_recommendation","knowledge_retrieval","fallback"]:
                if label in raw:
                    classification = label
                    break
        except Exception:
            pass
    else:
        if any(w in ql for w in ["bill","charge","payment","account"]):
            classification = "billing_account"
        elif any(w in ql for w in ["network","signal","connection","call","data","slow"]):
            classification = "network_troubleshooting"
    # Apply keyword overrides AFTER LLM or heuristic classification
    # Check for billing keywords first to protect billing classification
    billing_keywords = {"bill", "charge", "payment", "account", "invoice", "balance"}
    has_billing_keywords = any(k in ql for k in billing_keywords)
    
    knowledge_keywords = {"configure", "setup", "apn", "volte", "install", "enable"}
    service_keywords = {"plan", "recommend", "best", "upgrade", "family"}
    
    # Priority 1: Knowledge retrieval (setup/configuration questions)
    if any(k in ql for k in knowledge_keywords):
        # Only override to knowledge if there are no billing keywords
        if not has_billing_keywords:
            classification = "knowledge_retrieval"
    # Priority 2: Service recommendations (plan questions without billing context)
    elif any(k in ql for k in service_keywords) and not has_billing_keywords:
        # Override to service_recommendation if not already billing or network troubleshooting
        if classification not in {"billing_account", "network_troubleshooting"}:
            classification = "service_recommendation"
    # Priority 3: Generic "what" or "how" questions about plans = service recommendation
    elif ("what" in ql or "how" in ql) and any(k in ql for k in service_keywords) and not has_billing_keywords:
        classification = "service_recommendation"
    if logger and state.get("classification") != classification:
        logger.info(f"Classified query='{query}' -> {classification}")
    return {**state, "classification": classification, "status": "classified"}


def extract_city_from_address(address: str) -> str:
    """
    Extract city name from customer address.
    
    Args:
        address: Full address string (e.g., "Apartment 301, Sunshine Towers, Bangalore")
        
    Returns:
        City name or empty string if not found
    """
    if not address:
        return ""
    
    # Common patterns: address usually ends with city name
    # Split by comma and get the last non-empty part
    parts = [p.strip() for p in address.split(',')]
    if parts:
        # Last part is usually the city
        city = parts[-1]
        # Remove any pin codes or state codes
        city = re.sub(r'\d{6}', '', city)  # Remove 6-digit pin codes
        city = re.sub(r'\b[A-Z]{2}\b', '', city)  # Remove state codes like "KA", "DL"
        city = city.strip()
        return city
    
    return ""

# Routing function - determines next node based on classification
def route_query(state: TelecomAssistantState) -> str:
    """Route the query to the appropriate node based on classification"""
    # TODO: Implement query routing logic
    classification = state.get("classification", "")

    if classification == "billing_account":
        return "crew_ai_node"
    if classification == "network_troubleshooting":
        return "autogen_node"
    if classification == "service_recommendation":
        return "langchain_node"
    if classification == "knowledge_retrieval":
        return "llamaindex_node"

    # For any other classification, return fallback handler
    return "fallback_handler"

# Node function templates for each framework

def crew_ai_node(state: TelecomAssistantState) -> TelecomAssistantState:
    customer_info = state.get('customer_info', {})
    customer_id = customer_info.get('customer_id', 'UNKNOWN')
    
    # Check if customer is selected
    if not customer_info or customer_id == 'UNKNOWN':
        # Return a helpful message asking user to select a customer
        return {
            **state, 
            "intermediate_responses": {
                "crew_ai": {
                    "query": state.get('query', ''),
                    "raw": "Please select a customer from the sidebar to view billing information. I need to know which account to analyze before I can help with billing questions.",
                    "status": "ok"
                }
            }, 
            "status": "ok"
        }
    
    # Pass full customer info context in the query for better responses
    query = state.get('query','')
    context_query = f"Customer: {customer_id} ({customer_info.get('name','')}), Plan: {customer_info.get('service_plan_id','')}. Query: {query}"
    result = process_billing_query(customer_id=customer_id, query=context_query)
    return {**state, "intermediate_responses": {"crew_ai": result}, "status": result.get("status", state.get("status"))}


def autogen_node(state: TelecomAssistantState) -> TelecomAssistantState:
    """Process network troubleshooting with AutoGen, enriched with customer location."""
    query = state.get('query', '')
    customer_info = state.get('customer_info', {})
    
    # Enrich query with customer location if available
    if customer_info:
        address = customer_info.get('address', '')
        city = extract_city_from_address(address)
        
        if city:
            # Add location context to help agents find relevant incidents
            enriched_query = f"Customer location: {city}. Issue: {query}"
            if logger:
                logger.info(f"Enriched network query with location: {city}")
        else:
            enriched_query = query
    else:
        enriched_query = query
    
    result = process_network_query(query=enriched_query)
    return {**state, "intermediate_responses": {"autogen": result}, "status": result.get("status", state.get("status"))}



def langchain_node(state: TelecomAssistantState) -> TelecomAssistantState:
    customer_info = state.get('customer_info', {})
    query = state.get('query','')
    # Add customer context for personalized recommendations
    if customer_info:
        context_query = f"Customer {customer_info.get('customer_id','')} on {customer_info.get('service_plan_id','')} plan. {query}"
    else:
        context_query = query
    result = process_recommendation_query(query=context_query)
    return {**state, "intermediate_responses": {"langchain": result}, "status": result.get("status", state.get("status"))}


def llamaindex_node(state: TelecomAssistantState) -> TelecomAssistantState:
    result = process_knowledge_query(query=state.get('query',''))
    return {**state, "intermediate_responses": {"llamaindex": result}, "status": result.get("status", state.get("status"))}


def fallback_handler(state: TelecomAssistantState) -> TelecomAssistantState:
    """Handle queries that don't fit other categories"""
    response = (
        "I'm not sure how to help with that specific question. Could you try rephrasing or ask "
        "about our services, billing, network issues, or technical support?"
    )
    return {
        **state, 
        "intermediate_responses": {
            "fallback": {
                "query": state.get("query", ""),
                "response": response,
                "status": "ok"
            }
        }, 
        "status": "ok"
    }


def formulate_response(state: TelecomAssistantState) -> TelecomAssistantState:
    intermediate_responses = state.get("intermediate_responses", {})
    if not intermediate_responses:
        return {**state, "final_response": "No response generated."}
    # Pick the only dict value and format
    key, val = next(iter(intermediate_responses.items()))
    if isinstance(val, dict):
        if val.get("status") == "error" and "error" in val:
            formatted = f"Error: {val['error']}\nDetail: {val.get('detail','')[:300]}"
            if 'fallback' in val:
                formatted += f"\nFallback: {val['fallback']}"
        else:
            # Extract human-readable response based on agent type
            if "answer" in val:
                # LlamaIndex knowledge response - direct answer
                formatted = val["answer"]
            elif "raw" in val and isinstance(val["raw"], str):
                # CrewAI billing or LangChain service response - contains actual LLM output
                raw_content = val["raw"]
                # Try to parse as dict/eval to extract 'output' field (LangChain format)
                try:
                    import ast
                    parsed = ast.literal_eval(raw_content)
                    if isinstance(parsed, dict) and "output" in parsed:
                        formatted = parsed["output"]
                    else:
                        formatted = raw_content
                except Exception:
                    # If parsing fails, use raw content as-is (CrewAI format)
                    formatted = raw_content
            elif "transcript" in val:
                # AutoGen network response - use last message from transcript
                transcript = val.get("transcript", [])
                if transcript:
                    # Get the last assistant message
                    formatted = transcript[-1] if isinstance(transcript[-1], str) else str(transcript[-1])
                else:
                    formatted = "Network troubleshooting steps generated. Check the detailed view for more information."
            elif "response" in val:
                # Generic response field
                formatted = val["response"]
            else:
                # Fallback to generic formatting
                formatted_lines = []
                for k,v in val.items():
                    if k in {"status", "summary", "query", "customer_id"}:
                        continue
                    formatted_lines.append(f"{k}: {v if not isinstance(v,(list,dict)) else json.dumps(v)[:400]}")
                formatted = "\n".join(formatted_lines) if formatted_lines else str(val)
    else:
        formatted = str(val)
    return {**state, "final_response": formatted, "status": state.get("status","completed")}


def create_graph():
    """Create and return the workflow graph"""
    # Build the graph
    workflow = StateGraph(TelecomAssistantState)

    # Add nodes
    workflow.add_node("classify_query", classify_query)
    workflow.add_node("crew_ai_node", crew_ai_node)
    workflow.add_node("autogen_node", autogen_node)
    workflow.add_node("langchain_node", langchain_node)
    workflow.add_node("llamaindex_node", llamaindex_node)
    workflow.add_node("fallback_handler", fallback_handler)
    workflow.add_node("formulate_response", formulate_response)

    # Add conditional edges from classification to appropriate node
    workflow.add_conditional_edges(
        "classify_query",
        route_query,
        {
            "crew_ai_node": "crew_ai_node",
            "autogen_node": "autogen_node",
            "langchain_node": "langchain_node",
            "llamaindex_node": "llamaindex_node",
            "fallback_handler": "fallback_handler",
        },
    )

    # Add edges from each processing node to response formulation
    workflow.add_edge("crew_ai_node", "formulate_response")
    workflow.add_edge("autogen_node", "formulate_response")
    workflow.add_edge("langchain_node", "formulate_response")
    workflow.add_edge("llamaindex_node", "formulate_response")
    workflow.add_edge("fallback_handler", "formulate_response")
    workflow.add_edge("formulate_response", END)

    # Set the entry point
    workflow.set_entry_point("classify_query")

    # Compile the graph
    return workflow.compile()
