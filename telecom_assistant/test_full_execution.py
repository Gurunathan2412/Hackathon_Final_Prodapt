"""
Full Execution Test - 5 Sample Queries
Tests actual agent responses (not just classification)
"""
import os
import sys
import time

# Disable telemetry before any imports
os.environ["OTEL_SDK_DISABLED"] = "true"

sys.path.insert(0, '.')

from orchestration.graph import create_graph

# Test queries: 3 misclassified + 2 correct
TEST_QUERIES = [
    {
        "query": "What's the early termination fee if I cancel my contract?",
        "expected_classification": "billing_account",
        "reason": "Misclassified as knowledge - should be billing"
    },
    {
        "query": "What's the best plan for a family of four who watches a lot of videos?",
        "expected_classification": "service_recommendation",
        "reason": "Misclassified as knowledge - should be service"
    },
    {
        "query": "Tell me a joke about telecom",
        "expected_classification": "fallback",
        "reason": "Misclassified as knowledge - should be fallback"
    },
    {
        "query": "I can't make calls from my home in Mumbai West",
        "expected_classification": "network_troubleshooting",
        "reason": "Correctly classified"
    },
    {
        "query": "How do I set up VoLTE on my Samsung phone?",
        "expected_classification": "knowledge_retrieval",
        "reason": "Correctly classified"
    }
]

print("=" * 80)
print("FULL EXECUTION TEST - Testing Agent Responses")
print("=" * 80)
print(f"\nTesting {len(TEST_QUERIES)} queries end-to-end")
print("This will take 5-10 minutes...\n")

# Create graph once
print("Initializing LangGraph workflow...")
graph = create_graph()
print("Graph ready!\n")

# Customer info for all queries
customer_info = {
    "customer_id": "CUST001",
    "name": "SivaPrasad Valluru",
    "service_plan_id": "STD_500",
    "address": "Apartment 301, Sunshine Towers, Bangalore",
    "email": "siva@example.com",
    "phone_number": "8088910831"
}

results = []

for i, test in enumerate(TEST_QUERIES, 1):
    print("=" * 80)
    print(f"TEST {i}/{len(TEST_QUERIES)}")
    print("=" * 80)
    print(f"Query: {test['query']}")
    print(f"Expected: {test['expected_classification']}")
    print(f"Note: {test['reason']}")
    print("-" * 80)
    
    try:
        # Create state
        state = {
            "query": test["query"],
            "customer_info": customer_info,
            "classification": "",
            "intermediate_responses": {},
            "final_response": "",
            "chat_history": []
        }
        
        # Time the execution
        start_time = time.time()
        
        # Invoke graph
        print("Processing... (this may take 1-2 minutes)")
        result = graph.invoke(state)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Extract results
        classification = result.get("classification", "unknown")
        final_response = result.get("final_response", "")
        
        # Determine which agent handled it
        intermediate = result.get("intermediate_responses", {})
        agent_used = list(intermediate.keys())[0] if intermediate else "unknown"
        
        # Check if classification was correct
        correct_classification = classification == test["expected_classification"]
        
        print(f"\nRESULTS:")
        print(f"  Classification: {classification} {'✓' if correct_classification else '✗ (wrong)'}")
        print(f"  Agent Used: {agent_used}")
        print(f"  Duration: {duration:.1f} seconds")
        print(f"  Response Length: {len(final_response)} chars")
        print(f"\n  Response Preview:")
        print(f"  {'-' * 76}")
        
        # Show first 300 chars of response
        preview = final_response[:300] if len(final_response) > 300 else final_response
        for line in preview.split('\n')[:5]:  # First 5 lines
            print(f"  {line}")
        if len(final_response) > 300:
            print(f"  ... (truncated)")
        print(f"  {'-' * 76}")
        
        # Check response quality
        has_response = len(final_response) > 0
        response_quality = "✓ GOOD" if has_response else "✗ FAILED"
        
        print(f"\n  Overall: {response_quality}")
        
        results.append({
            "query": test["query"],
            "expected": test["expected_classification"],
            "actual": classification,
            "agent": agent_used,
            "duration": duration,
            "success": has_response,
            "correct_classification": correct_classification
        })
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        results.append({
            "query": test["query"],
            "expected": test["expected_classification"],
            "error": str(e),
            "success": False
        })
    
    print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)

success_count = sum(1 for r in results if r.get("success", False))
correct_classification_count = sum(1 for r in results if r.get("correct_classification", False))

print(f"\nTotal Queries: {len(results)}")
print(f"Successful Responses: {success_count}/{len(results)}")
print(f"Correct Classifications: {correct_classification_count}/{len(results)}")
print(f"\nDetailed Results:")
print("-" * 80)

for i, r in enumerate(results, 1):
    success = "✓" if r.get("success", False) else "✗"
    classification = "✓" if r.get("correct_classification", False) else "✗"
    query_short = r["query"][:50] + "..." if len(r["query"]) > 50 else r["query"]
    
    print(f"{i}. {success} {classification} {query_short}")
    print(f"   Expected: {r['expected']} | Got: {r.get('actual', 'ERROR')}")
    if "agent" in r:
        print(f"   Agent: {r['agent']} | Duration: {r.get('duration', 0):.1f}s")
    if "error" in r:
        print(f"   Error: {r['error'][:100]}")
    print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
