# AutoGen implementation
from typing import Tuple, Dict, Any, List
from config.config import OPENAI_API_KEY
from utils.database import (
    list_active_incidents,
    search_common_network_issues,
    get_troubleshooting_steps,
    get_device_compatibility
)

try:
    import autogen  # type: ignore
    from autogen import UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager  # type: ignore
except Exception:  # pragma: no cover
    UserProxyAgent = AssistantAgent = GroupChat = GroupChatManager = object  # type: ignore

try:
    from loguru import logger  # type: ignore
except Exception:
    logger = None

# Constants for system messages
USER_PROXY_SYSMSG = """
You represent a customer with a network issue. Your job is to:
1. Present the customer's problem clearly
2. If asked for device information and it's not provided, respond: "I don't know my device model, please provide general troubleshooting steps"
3. Acknowledge when a solution is provided and thank the agents

Keep responses brief and natural. If agents ask for information not in the original query, politely indicate you don't have that information.
""".strip()

NETWORK_DIAG_SYSMSG = """
You are a network diagnostics expert who analyzes connectivity issues.
Your responsibilities:
1. Use the check_network_incidents function to check for known outages or incidents in the customer's area
2. Analyze network performance metrics based on incident data
3. Identify patterns that indicate specific network problems
4. Determine if the issue is widespread or localized to the customer

IMPORTANT: Always call the check_network_incidents function to get real incident data from the database.

HOW TO EXTRACT LOCATION:
- If the query starts with "Customer location: [city]", extract that city name
- Example: "Customer location: Bangalore. Issue: slow internet" → use region="Bangalore"
- If no location is provided in the query, call check_network_incidents with empty region (shows all active incidents)
- When calling the function, pass ONLY the city name (e.g., "Bangalore", "Delhi", "Mumbai")
- Do NOT pass full addresses or unnecessary details

Example function call:
- Query has "Customer location: Bangalore" → check_network_incidents(region="Bangalore")
- Query has "Customer location: Delhi West" → check_network_incidents(region="Delhi")
""".strip()

DEVICE_EXPERT_SYSMSG = """
You are a device troubleshooting expert who knows how to resolve connectivity issues on different phones and devices.
Your responsibilities:
1. Suggest device-specific settings to check (if device info available)
2. Provide step-by-step instructions for configuration
3. Explain how to diagnose hardware vs. software issues
4. Recommend specific actions based on the device type

IMPORTANT: 
- If the customer's device make/model is unknown, provide GENERAL troubleshooting steps that work across all devices
- Use get_device_info function to search for device-specific information if a device is mentioned
- DO NOT repeatedly ask for device information - provide universal solutions instead
- Focus on actions like: restart device, check airplane mode, verify SIM card, check signal strength, reset network settings
""".strip()

SOLN_INTEGRATOR_SYSMSG = """
You are a solution integrator who combines technical analysis into actionable plans for customers.
Your responsibilities:
1. Synthesize information from the network and device experts
2. Create a prioritized list of troubleshooting steps
3. Present solutions in order from simplest to most complex
4. Estimate which solution is most likely to resolve the issue

Your final answer should always be a numbered list of actions the customer can take, starting with the simplest and most likely to succeed.

IMPORTANT: End your response with "TERMINATE" after providing the complete troubleshooting plan to signal conversation completion.
""".strip()

_NETWORK_AGENT_CACHE = None


def _build_llm_config() -> Dict[str, Any]:
    """Return AutoGen LLM config with OpenAI model."""
    import os
    api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
    
    if not api_key:
        if logger:
            logger.warning("No OpenAI API key found for AutoGen")
        return None
    
    return {
        "model": "gpt-4o-mini",
        "api_key": api_key,
        "temperature": 0.2
    }


def create_network_agents(db_uri: str = "sqlite:///telecom_assistant/data/telecom.db") -> Tuple[Any, Any]:
    global _NETWORK_AGENT_CACHE
    if _NETWORK_AGENT_CACHE is not None:
        return _NETWORK_AGENT_CACHE

    llm_config = _build_llm_config()
    
    # If no API key, return None to trigger fallback
    if not llm_config:
        if logger:
            logger.warning("AutoGen agents not created: No API key")
        _NETWORK_AGENT_CACHE = (None, None)
        return None, None

    # Create network incident checking function for AutoGen
    def check_network_incidents(region: str = "") -> str:
        """Check for active network incidents in a region. Returns incident details or confirms no issues."""
        incidents = list_active_incidents(region if region else None)
        if not incidents:
            return f"No active incidents{' in ' + region if region else ''}. All networks operating normally."
        
        result = f"Found {len(incidents)} active incident(s):\n"
        for inc in incidents:
            result += (
                f"- [{inc['incident_id']}] {inc['incident_type']} in {inc['location']}\n"
                f"  Affected: {inc['affected_services']}, Severity: {inc['severity']}, Status: {inc['status']}\n"
            )
        return result
    
    def search_network_issue_kb(keyword: str) -> str:
        """Search knowledge base for common network issues and troubleshooting steps"""
        issues = search_common_network_issues(keyword)
        if not issues:
            return f"No knowledge base entries found for: {keyword}"
        
        result = f"Found {len(issues)} common issue(s) matching '{keyword}':\n"
        for issue in issues[:3]:  # Limit to top 3
            result += (
                f"\n{issue['issue_category']}:\n"
                f"  Symptoms: {issue['typical_symptoms'][:100]}...\n"
                f"  Steps: {issue['troubleshooting_steps'][:150]}...\n"
            )
        return result
    
    def get_device_info(device_make: str) -> str:
        """Get device-specific troubleshooting information"""
        devices = get_device_compatibility(device_make)
        if not devices:
            return f"No device information found for: {device_make}"
        
        result = f"Device compatibility info for {device_make}:\n"
        for device in devices[:2]:
            result += (
                f"\n{device['device_model']} - {device['network_technology']}:\n"
                f"  Known Issues: {device['known_issues']}\n"
                f"  Settings: {device['recommended_settings']}\n"
            )
        return result
    
    # Register functions for AutoGen function calling
    functions_for_agents = [
        {
            "name": "check_network_incidents",
            "description": "Check for active network incidents/outages in a specific region or all regions",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "The region to check (e.g., 'Mumbai', 'Delhi'). Leave empty for all regions."
                    }
                },
                "required": []
            }
        },
        {
            "name": "search_network_issue_kb",
            "description": "Search knowledge base for common network issues with structured troubleshooting steps",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Keyword to search (e.g., 'call', 'data', 'signal')"
                    }
                },
                "required": ["keyword"]
            }
        },
        {
            "name": "get_device_info",
            "description": "Get device-specific troubleshooting information and known issues",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_make": {
                        "type": "string",
                        "description": "Device manufacturer (e.g., 'Samsung', 'Apple', 'OnePlus')"
                    }
                },
                "required": ["device_make"]
            }
        }
    ]
    
    # Add function map for execution
    function_map = {
        "check_network_incidents": check_network_incidents,
        "search_network_issue_kb": search_network_issue_kb,
        "get_device_info": get_device_info
    }
    
    # Update llm_config with functions
    llm_config_with_functions = {
        **llm_config,
        "functions": functions_for_agents
    }

    # User proxy agent
    user_proxy = None
    network_diag_agent = None
    device_expert_agent = None
    soln_integrator_agent = None

    if UserProxyAgent is not object:
        try:  # pragma: no cover
            # Define termination condition - stop when solution is provided
            def is_termination_msg(msg):
                """Check if message contains TERMINATE or is from solution_integrator"""
                if msg.get("content"):
                    content = str(msg.get("content", "")).strip()
                    # Terminate if TERMINATE keyword found
                    if "TERMINATE" in content:
                        return True
                    # Terminate if solution integrator has provided a complete solution
                    # (numbered list with at least 5 steps)
                    if msg.get("name") == "solution_integrator" and content:
                        # Check for numbered steps (1., 2., etc.)
                        import re
                        steps = re.findall(r'^\d+\.', content, re.MULTILINE)
                        if len(steps) >= 5:  # Complete solution has 5+ steps
                            return True
                return False
            
            # User proxy - can respond to clarifying questions
            user_proxy = UserProxyAgent(
                name="user_proxy",
                system_message=USER_PROXY_SYSMSG,
                human_input_mode="NEVER",  # Changed back to NEVER to allow auto-responses
                max_consecutive_auto_reply=3,  # Allow up to 3 automatic responses
                code_execution_config={"use_docker": False},
                function_map=function_map,  # Register function execution
                is_termination_msg=is_termination_msg,  # Add termination condition
            )

            # Network diagnostics agent with function calling
            network_diag_agent = AssistantAgent(
                name="network_diagnostics",
                system_message=NETWORK_DIAG_SYSMSG,
                llm_config=llm_config_with_functions,  # Use config with functions
                function_map=function_map,  # Register function execution
            )

            # Device expert agent with function calling
            device_expert_agent = AssistantAgent(
                name="device_expert",
                system_message=DEVICE_EXPERT_SYSMSG,
                llm_config=llm_config_with_functions,  # Enable function calling
                function_map=function_map,  # Register function execution
            )

            # Solution integrator agent
            soln_integrator_agent = AssistantAgent(
                name="solution_integrator",
                system_message=SOLN_INTEGRATOR_SYSMSG,
                llm_config=llm_config,
            )
        except Exception:
            user_proxy = network_diag_agent = device_expert_agent = soln_integrator_agent = None

    manager = None
    if GroupChat is not object and all([user_proxy, network_diag_agent, device_expert_agent, soln_integrator_agent]):
        try:  # pragma: no cover
            group_chat = GroupChat(
                agents=[user_proxy, network_diag_agent, device_expert_agent, soln_integrator_agent],
                messages=[],
                max_round=6,  # Reduced from 8 to 6 for more focused conversations
                speaker_selection_method="auto",  # Let AutoGen decide speaker order
            )
            manager = GroupChatManager(groupchat=group_chat, llm_config=llm_config)
        except Exception:
            manager = None

    _NETWORK_AGENT_CACHE = (user_proxy, manager)
    return user_proxy, manager


def process_network_query(query: str) -> Dict[str, Any]:
    user_proxy, manager = create_network_agents()
    if not user_proxy or not manager:
        return {"query": query, "error": "AutoGen not initialized", "detail": "Missing autogen dependency or agent setup."}
    chat_transcript = []
    try:  # pragma: no cover
        user_proxy.initiate_chat(manager, message=query)
        if hasattr(manager.groupchat, 'messages'):
            chat_transcript = [m.get('content','') if isinstance(m, dict) else str(m) for m in manager.groupchat.messages]
    except Exception as e:
        if logger:
            logger.error(f"AutoGen network chat error: {e}")
        return {
            "query": query,
            "error": "AutoGen chat failed",
            "detail": str(e)[:500],
            "fallback_plan": [
                "Check for regional outages",
                "Toggle airplane mode",
                "Reset network/APN settings",
                "Verify SIM provisioning",
                "Escalate to Tier-2 with logs"
            ],
            "status": "error"
        }
    troubleshooting_plan = [
        "Check outages in region",
        "Toggle airplane mode",
        "Reset network settings/APN",
        "Re-seat SIM or eSIM refresh",
        "Escalate if unresolved",
    ]
    return {
        "query": query,
        "plan": troubleshooting_plan,
        "transcript": chat_transcript[:50],
        "summary": "Sequential troubleshooting generated",
        "status": "ok"
    }
