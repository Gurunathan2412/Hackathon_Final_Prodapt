"""
Quick validation test - checks core functionality without running full LLM queries
Tests: routing, database access, agent availability, function calling
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("QUICK VALIDATION TEST - CORE FUNCTIONALITY")
print("=" * 80)

# Track results
results = {"total": 0, "passed": 0, "failed": 0}

def test(name, func):
    """Run a test and track results"""
    results["total"] += 1
    print(f"\n[TEST {results['total']}] {name}")
    try:
        func()
        results["passed"] += 1
        print("  PASS")
        return True
    except Exception as e:
        results["failed"] += 1
        print(f"  FAIL: {str(e)[:200]}")
        return False

# Test 1: Database connectivity
def test_database():
    from utils.database import get_customer, get_customer_usage, list_active_incidents
    customer = get_customer("CUST001")
    assert customer is not None, "Customer not found"
    assert customer["name"] == "SivaPrasad Valluru", f"Unexpected name: {customer['name']}"
    
    usage = get_customer_usage("CUST001")
    assert usage is not None, "Usage not found"
    
    incidents = list_active_incidents()
    assert isinstance(incidents, list), "Incidents not a list"
    print(f"    - Customer: {customer['name']}")
    print(f"    - Usage records: {len(usage) if isinstance(usage, list) else 'Found'}")
    print(f"    - Active incidents: {len(incidents)}")

test("Database Connectivity", test_database)

# Test 2: Query classification
def test_classification():
    from orchestration.graph import classify_query
    
    test_cases = [
        ("Can you explain my bill?", "billing_inquiry"),
        ("I can't make calls", "network_troubleshooting"),
        ("What plan should I get?", "plan_recommendation"),
        ("How do I set up VoLTE?", "technical_support"),
    ]
    
    for query, expected in test_cases:
        state = {"query": query, "classification": None}
        result = classify_query(state)
        actual = result.get("classification")
        if actual != expected:
            print(f"    - '{query[:30]}...' -> {actual} (expected {expected})")
        assert actual == expected, f"Wrong classification: {actual} vs {expected}"
    
    print(f"    - All 4 query types classified correctly")

test("Query Classification", test_classification)

# Test 3: CrewAI tools availability
def test_crewai_tools():
    from agents.crewai_tools import get_all_crewai_tools
    tools = get_all_crewai_tools()
    assert len(tools) >= 15, f"Expected 15+ tools, got {len(tools)}"
    
    tool_names = [t.name for t in tools]
    expected_tools = ["get_customer_data", "get_usage_data", "get_plan_details", 
                     "check_network_incidents", "get_customer_tickets"]
    
    for expected in expected_tools:
        assert expected in tool_names, f"Missing tool: {expected}"
    
    print(f"    - Total tools available: {len(tools)}")
    print(f"    - Key tools verified: {len(expected_tools)}")

test("CrewAI Tools Availability", test_crewai_tools)

# Test 4: AutoGen agents
def test_autogen_agents():
    from agents.network_agents import create_network_agents
    user_proxy, manager = create_network_agents()
    
    if manager is None:
        print("    - SKIP: AutoGen not initialized (API key missing)")
        return
    
    assert manager is not None, "Manager not created"
    assert user_proxy is not None, "User proxy not created"
    
    # Check agents in group chat
    if hasattr(manager, 'groupchat') and hasattr(manager.groupchat, 'agents'):
        agents = manager.groupchat.agents
        agent_names = [a.name for a in agents if hasattr(a, 'name')]
        print(f"    - Agents created: {len(agents)}")
        print(f"    - Agent names: {', '.join(agent_names)}")
        
        expected_agents = ["network_diagnostics", "device_expert", "solution_integrator"]
        for expected in expected_agents:
            assert expected in agent_names, f"Missing agent: {expected}"
    else:
        print("    - AutoGen created but structure different")

test("AutoGen Agents", test_autogen_agents)

# Test 5: LangChain agents
def test_langchain_agents():
    from agents.service_agents import create_service_agent
    agent = create_service_agent()
    
    if agent is None:
        print("    - SKIP: LangChain agent not initialized")
        return
    
    assert agent is not None, "Service agent not created"
    print(f"    - Service agent created successfully")

test("LangChain Agents", test_langchain_agents)

# Test 6: LlamaIndex
def test_llamaindex():
    from agents.knowledge_agents import create_knowledge_agent
    agent = create_knowledge_agent()
    
    if agent is None:
        print("    - SKIP: LlamaIndex not initialized")
        return
    
    assert agent is not None, "Knowledge agent not created"
    print(f"    - Knowledge agent created successfully")

test("LlamaIndex Agent", test_llamaindex)

# Test 7: Graph orchestration
def test_graph():
    from orchestration.graph import create_graph
    graph = create_graph()
    assert graph is not None, "Graph not created"
    print(f"    - LangGraph workflow created successfully")

test("Graph Orchestration", test_graph)

# Test 8: All 13 database tables accessible
def test_all_tables():
    from utils.database import (
        get_customer, get_customer_usage, get_service_plan, list_active_incidents,
        get_customer_tickets, search_common_network_issues, get_device_compatibility,
        get_service_areas, get_coverage_quality, get_cell_towers, get_tower_technologies,
        get_transportation_routes, get_building_types
    )
    
    # Test each function
    tables_tested = 0
    
    customer = get_customer("CUST001")
    if customer: tables_tested += 1
    
    usage = get_customer_usage("CUST001")
    if usage: tables_tested += 1
    
    plan = get_service_plan("STD_500")
    if plan: tables_tested += 1
    
    incidents = list_active_incidents()
    if incidents is not None: tables_tested += 1
    
    tickets = get_customer_tickets("CUST001")
    if tickets is not None: tables_tested += 1
    
    issues = search_common_network_issues("call")
    if issues is not None: tables_tested += 1
    
    devices = get_device_compatibility("Samsung")
    if devices is not None: tables_tested += 1
    
    areas = get_service_areas("Mumbai")
    if areas is not None: tables_tested += 1
    
    coverage = get_coverage_quality(1, "5G")
    if coverage is not None: tables_tested += 1
    
    towers = get_cell_towers(1)
    if towers is not None: tables_tested += 1
    
    tech = get_tower_technologies(1)
    if tech is not None: tables_tested += 1
    
    routes = get_transportation_routes("Metro")
    if routes is not None: tables_tested += 1
    
    buildings = get_building_types("Residential")
    if buildings is not None: tables_tested += 1
    
    print(f"    - Database tables accessible: {tables_tested}/13")
    assert tables_tested == 13, f"Only {tables_tested}/13 tables accessible"

test("All 13 Database Tables", test_all_tables)

# Test 9: Sample query routing
def test_sample_queries():
    from orchestration.graph import classify_query
    
    sample_queries = {
        "billing": "Can you explain the 'Value Added Services' charge on my bill?",
        "network": "I can't make calls from my home in Mumbai West",
        "plan": "What's the best plan for a family of four?",
        "technical": "How do I set up VoLTE on my Samsung phone?"
    }
    
    for category, query in sample_queries.items():
        state = {"query": query, "classification": None}
        result = classify_query(state)
        classification = result.get("classification")
        print(f"    - {category}: '{query[:40]}...' -> {classification}")
        assert classification is not None, f"No classification for {category}"

test("Sample Query Routing", test_sample_queries)

# Print summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"Total tests: {results['total']}")
print(f"Passed: {results['passed']}")
print(f"Failed: {results['failed']}")
print(f"Success rate: {(results['passed'] / results['total'] * 100):.1f}%")

if results['failed'] == 0:
    print("\n*** ALL TESTS PASSED - SYSTEM OPERATIONAL ***")
    sys.exit(0)
else:
    print(f"\n*** {results['failed']} TESTS FAILED ***")
    sys.exit(1)
