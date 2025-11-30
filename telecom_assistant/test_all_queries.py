"""
Comprehensive test script for all sample queries from project documentation
Tests all agent types: CrewAI (billing), AutoGen (network), LangChain (service), LlamaIndex (knowledge)
"""
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.graph import create_graph, classify_query
from utils.database import get_customer

print("=" * 100)
print("COMPREHENSIVE TELECOM ASSISTANT TEST - ALL SAMPLE QUERIES")
print("=" * 100)

# Get default customer for testing
customer = get_customer("CUST001")
print(f"\n🧪 Testing with customer: {customer['name']} (ID: {customer['customer_id']})")

# Test categories
test_categories = {
    "billing": [
        "Why did my bill increase by ₹200 this month?",
        "I see a charge for international roaming but I haven't traveled recently",
        "Can you explain the 'Value Added Services' charge on my bill?",
        "What's the early termination fee if I cancel my contract?"
    ],
    "network": [
        "I can't make calls from my home in Mumbai West",
        "My data connection keeps dropping when I'm on the train",
        "Why is my 5G connection slower than my friend's?",
        "I get a 'No Service' error in my basement apartment"
    ],
    "plan": [
        "What's the best plan for a family of four who watches a lot of videos?",
        "I need a plan with good international calling to the US",
        "Which plan is best for someone who works from home and needs reliable data?",
        "I'm a light user who mostly just calls and texts. What's my cheapest option?"
    ],
    "technical": [
        "How do I set up VoLTE on my Samsung phone?",
        "What are the APN settings for Android devices?",
        "How can I activate international roaming before traveling?",
        "What areas in Delhi have 5G coverage?"
    ],
    "edge_cases": [
        "Tell me a joke about telecom",
        "I need help with both my bill and network issues",
        ""  # Empty query
    ]
}

# Expected agent routing
expected_routing = {
    "billing": "crew_ai",
    "network": "autogen",
    "plan": "langchain",
    "technical": "llamaindex",
    "edge_cases": ["crew_ai", "crew_ai", "crew_ai"]  # fallback to crew_ai
}

# Test results tracking
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}

def test_query(query: str, category: str, expected_agent: str = None) -> dict:
    """Test a single query and return results"""
    results["total"] += 1
    
    print(f"\n{'=' * 100}")
    print(f"📝 Query: \"{query}\"")
    print(f"📂 Category: {category.upper()}")
    
    if not query.strip():
        print("⚠️  Empty query detected")
    
    try:
        # Test classification
        temp_state = {"query": query, "classification": None}
        classified_state = classify_query(temp_state)
        classification = classified_state.get("classification", "unknown")
        print(f"🎯 Classified as: {classification}")
        
        if expected_agent:
            routing_correct = classification == expected_agent
            print(f"✅ Routing: {'CORRECT' if routing_correct else 'INCORRECT (expected ' + expected_agent + ')'}")
        
        # Create graph and process
        graph = create_graph()
        initial_state = {
            "query": query,
            "customer_info": customer,
            "classification": classification,
            "intermediate_responses": {},
            "final_response": None,
            "chat_history": []
        }
        
        print(f"⚙️  Processing with workflow...")
        final_state = graph.invoke(initial_state)
        
        # Check results
        if final_state.get("final_response"):
            response = final_state["final_response"]
            
            # Check for errors
            if isinstance(response, dict) and response.get("error"):
                print(f"⚠️  Response contains error: {response.get('error')}")
                print(f"   Detail: {response.get('detail', 'N/A')[:200]}")
                results["failed"] += 1
                results["errors"].append({
                    "query": query,
                    "category": category,
                    "error": response.get("error"),
                    "detail": response.get("detail", "")[:200]
                })
            else:
                # Check response quality
                response_str = str(response)
                has_content = len(response_str) > 50
                
                if has_content:
                    print(f"✅ Response generated: {len(response_str)} characters")
                    print(f"📄 Preview: {response_str[:200]}...")
                    
                    # Check for agent-specific content
                    if category == "network":
                        # Check for troubleshooting steps
                        if "1." in response_str and "2." in response_str:
                            print(f"✅ Contains structured troubleshooting steps")
                        else:
                            print(f"⚠️  Missing structured steps")
                    
                    results["passed"] += 1
                else:
                    print(f"⚠️  Response too short: {len(response_str)} characters")
                    results["failed"] += 1
                    results["errors"].append({
                        "query": query,
                        "category": category,
                        "error": "Response too short",
                        "detail": response_str
                    })
        else:
            print(f"❌ No final response generated")
            results["failed"] += 1
            results["errors"].append({
                "query": query,
                "category": category,
                "error": "No response",
                "detail": "final_response is None"
            })
        
        # Check intermediate responses
        intermediate = final_state.get("intermediate_responses", {})
        if intermediate:
            agents_used = list(intermediate.keys())
            print(f"🤖 Agents used: {', '.join(agents_used)}")
            
            for agent_name, agent_response in intermediate.items():
                if isinstance(agent_response, dict):
                    status = agent_response.get("status", "unknown")
                    print(f"   - {agent_name}: {status}")
        
        return {
            "success": True,
            "classification": classification,
            "response_length": len(str(final_state.get("final_response", ""))),
            "agents_used": list(intermediate.keys()) if intermediate else []
        }
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)[:200]}")
        results["failed"] += 1
        results["errors"].append({
            "query": query,
            "category": category,
            "error": "Exception",
            "detail": str(e)[:200]
        })
        return {
            "success": False,
            "error": str(e)[:200]
        }

# Run all tests
print("\n" + "=" * 100)
print("STARTING COMPREHENSIVE TESTS")
print("=" * 100)

# Test each category
for category, queries in test_categories.items():
    print(f"\n\n{'#' * 100}")
    print(f"# CATEGORY: {category.upper()}")
    print(f"{'#' * 100}")
    
    for i, query in enumerate(queries, 1):
        # Determine expected agent
        if category in expected_routing:
            if isinstance(expected_routing[category], list):
                expected = expected_routing[category][i-1] if i-1 < len(expected_routing[category]) else None
            else:
                expected = expected_routing[category]
        else:
            expected = None
        
        test_query(query, category, expected)

# Print summary
print("\n\n" + "=" * 100)
print("TEST SUMMARY")
print("=" * 100)

print(f"\n📊 Overall Results:")
print(f"   Total queries tested: {results['total']}")
print(f"   ✅ Passed: {results['passed']}")
print(f"   ❌ Failed: {results['failed']}")
print(f"   Success rate: {(results['passed'] / results['total'] * 100):.1f}%")

if results["errors"]:
    print(f"\n❌ Errors encountered ({len(results['errors'])}):")
    for i, error in enumerate(results["errors"], 1):
        print(f"\n   {i}. Query: \"{error['query'][:60]}...\"")
        print(f"      Category: {error['category']}")
        print(f"      Error: {error['error']}")
        print(f"      Detail: {error['detail'][:150]}...")
else:
    print(f"\n🎉 NO ERRORS - ALL TESTS PASSED!")

print("\n" + "=" * 100)
if results["passed"] == results["total"]:
    print("✅ ALL SYSTEMS OPERATIONAL - PRODUCTION READY! 🚀")
else:
    print(f"⚠️  {results['failed']} tests need attention")
print("=" * 100)
