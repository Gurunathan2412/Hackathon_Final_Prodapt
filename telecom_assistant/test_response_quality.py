"""
Full Execution Test - 5 Key Queries
Tests actual response quality for misclassified and correct queries
"""
import sys
import os
import time

# Disable telemetry
os.environ["OTEL_SDK_DISABLED"] = "true"

sys.path.insert(0, '.')

from orchestration.graph import create_graph

# Test queries: 3 misclassified + 2 correct
TEST_QUERIES = [
    {
        "query": "What's the early termination fee if I cancel my contract?",
        "expected_classification": "billing_account",
        "issue": "MISCLASSIFIED - goes to knowledge instead of billing"
    },
    {
        "query": "What's the best plan for a family of four who watches a lot of videos?",
        "expected_classification": "service_recommendation",
        "issue": "MISCLASSIFIED - goes to knowledge instead of service"
    },
    {
        "query": "Tell me a joke about telecom",
        "expected_classification": "fallback",
        "issue": "MISCLASSIFIED - goes to knowledge instead of fallback"
    },
    {
        "query": "I can't make calls from my home in Mumbai West",
        "expected_classification": "network_troubleshooting",
        "issue": "CORRECT - properly classified"
    },
    {
        "query": "How do I set up VoLTE on my Samsung phone?",
        "expected_classification": "knowledge_retrieval",
        "issue": "CORRECT - properly classified"
    }
]

print("=" * 80)
print("FULL EXECUTION TEST - Response Quality Validation")
print("=" * 80)
print("\nTesting 5 queries to validate actual response quality...")
print("This will take 5-10 minutes due to agent processing.\n")

# Create graph once
print("Initializing graph...")
graph = create_graph()
print("Graph ready.\n")

results = []

for i, test_case in enumerate(TEST_QUERIES, 1):
    query = test_case["query"]
    expected = test_case["expected_classification"]
    issue = test_case["issue"]
    
    print("=" * 80)
    print(f"TEST {i}/5: {query}")
    print(f"Expected: {expected}")
    print(f"Issue: {issue}")
    print("=" * 80)
    
    # Create state
    state = {
        "query": query,
        "customer_info": {
            "customer_id": "CUST001",
            "name": "SivaPrasad Valluru",
            "service_plan_id": "STD_500",
            "address": "Apartment 301, Sunshine Towers, Bangalore",
            "email": "siva@example.com",
            "phone_number": "8088910831"
        },
        "classification": "",
        "intermediate_responses": {},
        "final_response": "",
        "chat_history": []
    }
    
    try:
        print("\nExecuting query...")
        start_time = time.time()
        
        result = graph.invoke(state)
        
        execution_time = time.time() - start_time
        
        classification = result.get("classification", "unknown")
        final_response = result.get("final_response", "")
        
        # Determine which agent handled it
        intermediate = result.get("intermediate_responses", {})
        agent_used = "unknown"
        if "crew_ai" in intermediate:
            agent_used = "CrewAI (Billing)"
        elif "autogen" in intermediate:
            agent_used = "AutoGen (Network)"
        elif "langchain" in intermediate:
            agent_used = "LangChain (Service)"
        elif "llamaindex" in intermediate:
            agent_used = "LlamaIndex (Knowledge)"
        elif "fallback" in intermediate:
            agent_used = "Fallback Handler"
        
        # Check if classification matches expectation
        classification_correct = classification == expected
        
        print(f"\n✓ Query completed in {execution_time:.1f} seconds")
        print(f"\nClassification: {classification}")
        print(f"Agent Used: {agent_used}")
        print(f"Classification Match: {'YES' if classification_correct else 'NO'}")
        print(f"Response Length: {len(final_response)} characters")
        print(f"\nResponse Preview (first 300 chars):")
        print("-" * 80)
        print(final_response[:300] + ("..." if len(final_response) > 300 else ""))
        print("-" * 80)
        
        results.append({
            "query": query,
            "expected_class": expected,
            "actual_class": classification,
            "agent_used": agent_used,
            "classification_correct": classification_correct,
            "has_response": len(final_response) > 0,
            "response_length": len(final_response),
            "execution_time": execution_time,
            "success": True
        })
        
    except Exception as e:
        print(f"\n✗ Query FAILED with error:")
        print(f"   {str(e)}")
        
        results.append({
            "query": query,
            "expected_class": expected,
            "success": False,
            "error": str(e)
        })
    
    print()

# Summary
print("\n" + "=" * 80)
print("SUMMARY - Response Quality Analysis")
print("=" * 80)

successful = [r for r in results if r.get("success", False)]
failed = [r for r in results if not r.get("success", False)]

print(f"\nExecution Results:")
print(f"  Successful: {len(successful)}/5")
print(f"  Failed: {len(failed)}/5")

if successful:
    print(f"\nClassification Accuracy:")
    correct_class = [r for r in successful if r.get("classification_correct", False)]
    print(f"  Correct: {len(correct_class)}/{len(successful)}")
    print(f"  Incorrect: {len(successful) - len(correct_class)}/{len(successful)}")
    
    print(f"\nResponse Quality:")
    avg_length = sum(r.get("response_length", 0) for r in successful) / len(successful)
    avg_time = sum(r.get("execution_time", 0) for r in successful) / len(successful)
    print(f"  Average response length: {avg_length:.0f} characters")
    print(f"  Average execution time: {avg_time:.1f} seconds")

print("\n" + "=" * 80)
print("DETAILED RESULTS")
print("=" * 80)

for i, r in enumerate(results, 1):
    status = "✓" if r.get("success", False) else "✗"
    query_short = r["query"][:50] + "..." if len(r["query"]) > 50 else r["query"]
    
    print(f"\n{i}. {status} {query_short}")
    
    if r.get("success", False):
        match = "✓" if r.get("classification_correct", False) else "✗"
        print(f"   Classification: {match} {r.get('actual_class')} (expected: {r.get('expected_class')})")
        print(f"   Agent: {r.get('agent_used')}")
        print(f"   Response: {r.get('response_length')} chars in {r.get('execution_time', 0):.1f}s")
        
        # Quality assessment
        if not r.get("classification_correct", False):
            if r.get("has_response", False) and r.get("response_length", 0) > 100:
                print(f"   Quality: ACCEPTABLE (wrong route but got response)")
            else:
                print(f"   Quality: POOR (wrong route, inadequate response)")
        else:
            print(f"   Quality: GOOD (correct route and response)")
    else:
        print(f"   Error: {r.get('error', 'Unknown')}")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

misclassified = [r for r in successful if not r.get("classification_correct", False)]

if misclassified:
    print(f"\n{len(misclassified)} queries were misclassified.")
    
    # Check if they still got good responses
    acceptable = [r for r in misclassified if r.get("response_length", 0) > 100]
    
    if len(acceptable) == len(misclassified):
        print("\n✓ All misclassified queries still produced adequate responses.")
        print("  → Classification fix is LOW PRIORITY")
        print("  → Current system is functional despite routing issues")
    else:
        print("\n✗ Some misclassified queries produced poor responses.")
        print("  → Classification fix is HIGH PRIORITY")
        print("  → User experience is impacted")
else:
    print("\n✓ All queries classified correctly!")
    print("  → No classification fixes needed")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
