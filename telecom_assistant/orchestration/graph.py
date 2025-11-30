# LangGraph orchestration

from typing import TypedDict, Dict, Any, List
from config.config import ENABLE_LLM_CLASSIFICATION, OPENAI_MODEL_CLASSIFY
from agents.billing_agents import process_billing_query  # type: ignore
from agents.network_agents import process_network_query  # type: ignore
from agents.service_agents import process_recommendation_query  # type: ignore
from agents.knowledge_agents import process_knowledge_query  # type: ignore
import json

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
    if len(query) < 3 or query.lower() in {"hi", "hello", "hey"}:
        return {**state, "classification": "fallback"}
    classification = "billing_account"
    ql = query.lower()
    if _llm_classifier:
        try:  # pragma: no cover
            prompt = (
                "Classify the telecom user query into one of: billing_account, network_troubleshooting, service_recommendation, knowledge_retrieval.\n"
                f"Query: {query}\nLabel:" )
            resp = _llm_classifier.invoke(prompt)  # type: ignore
            raw = getattr(resp, 'content', '').lower()
            for label in ["billing_account","network_troubleshooting","service_recommendation","knowledge_retrieval"]:
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
    knowledge_keywords = {"how", "what", "configure", "setup", "apn", "volte"}
    if any(k in ql for k in knowledge_keywords):
        classification = "knowledge_retrieval"
    else:
        service_keywords = {"plan", "recommend", "best", "upgrade", "family"}
        if classification not in {"knowledge_retrieval"} and any(k in ql for k in service_keywords):
            classification = "service_recommendation"
    if logger and state.get("classification") != classification:
        logger.info(f"Classified query='{query}' -> {classification}")
    return {**state, "classification": classification, "status": "classified"}

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
    # Pass full customer info context in the query for better responses
    query = state.get('query','')
    if customer_info:
        context_query = f"Customer: {customer_id} ({customer_info.get('name','')}), Plan: {customer_info.get('service_plan_id','')}. Query: {query}"
    else:
        context_query = query
    result = process_billing_query(customer_id=customer_id, query=context_query)
    return {**state, "intermediate_responses": {"crew_ai": result}, "status": result.get("status", state.get("status"))}


def autogen_node(state: TelecomAssistantState) -> TelecomAssistantState:
    result = process_network_query(query=state.get('query',''))
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
    return {**state, "intermediate_responses": {"fallback": response}, "status": "ok"}


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
            formatted_lines = []
            for k,v in val.items():
                if k in {"raw"}:
                    continue
                formatted_lines.append(f"{k}: {v if not isinstance(v,(list,dict)) else json.dumps(v)[:400]}")
            formatted = "\n".join(formatted_lines)
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
