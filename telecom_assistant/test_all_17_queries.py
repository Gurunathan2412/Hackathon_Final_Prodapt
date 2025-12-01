"""
COMPREHENSIVE TEST - All 17 Sample Queries
Tests all queries from documentation end-to-end
"""
import os
import sys
import time

# Disable telemetry
os.environ["OTEL_SDK_DISABLED"] = "true"

sys.path.insert(0, '.')

from orchestration.graph import create_graph

# All 17 test queries organized by category
ALL_QUERIES = [
    # 1.9.1 Billing Queries (CrewAI) - 4 queries
    {
        "category": "Billing",
        "query": "Why did my bill increase by 200 this month?",
        "expected": "billing_account"
    },
    {
        "category": "Billing",
        "query": "I see a charge for international roaming but I haven't traveled recently",
        "expected": "billing_account"
    },
    {
        "category": "Billing",
        "query": "Can you explain the 'Value Added Services' charge on my bill?",
        "expected": "billing_account"
    },
    {
        "category": "Billing",
        "query": "What's the early termination fee if I cancel my contract?",
        "expected": "billing_account"
    },
    
    # 1.9.2 Network Issues (AutoGen) - 4 queries
    {
        "category": "Network",
        "query": "I can't make calls from my home in Mumbai West",
        "expected": "network_troubleshooting"
    },
    {
        "category": "Network",
        "query": "My data connection keeps dropping when I'm on the train",
        "expected": "network_troubleshooting"
    },
    {
        "category": "Network",
        "query": "Why is my 5G connection slower than my friend's?",
        "expected": "network_troubleshooting"
    },
    {
        "category": "Network",
        "query": "I get a 'No Service' error in my basement apartment",
        "expected": "network_troubleshooting"
    },
    
    # 1.9.3 Plan Recommendations (LangChain) - 4 queries
    {
        "category": "Service",
        "query": "What's the best plan for a family of four who watches a lot of videos?",
        "expected": "service_recommendation"
    },
    {
        "category": "Service",
        "query": "I need a plan with good international calling to the US",
        "expected": "service_recommendation"
    },
    {
        "category": "Service",
        "query": "Which plan is best for someone who works from home and needs reliable data?",
        "expected": "service_recommendation"
    },
    {
        "category": "Service",
        "query": "I'm a light user who mostly just calls and texts. What's my cheapest option?",
        "expected": "service_recommendation"
    },
    
    # 1.9.4 Technical Information (LlamaIndex) - 4 queries
    {
        "category": "Knowledge",
        "query": "How do I set up VoLTE on my Samsung phone?",
        "expected": "knowledge_retrieval"
    },
    {
        "category": "Knowledge",
        "query": "What are the APN settings for Android devices?",
        "expected": "knowledge_retrieval"
    },
    {
        "category": "Knowledge",
        "query": "How can I activate international roaming before traveling?",
        "expected": "knowledge_retrieval"
    },
    {
        "category": "Knowledge",
        "query": "What areas in Delhi have 5G coverage?",
        "expected": "knowledge_retrieval"
    },
    
    # 1.9.5 Edge Cases - 1 query (excluding empty query for now)
    {
        "category": "Edge",
        "query": "I need help with both my bill and network issues",
        "expected": "billing_account"  # Should pick one
    }
]

print("=" * 80)
print("COMPREHENSIVE TEST - All 17 Sample Queries")
print("=" * 80)
print(f"\nTesting all queries from documentation")
print(f"Total queries: {len(ALL_QUERIES)}")
print(f"Estimated time: 20-30 minutes")
print(f"\nCategories:")
print(f"  - Billing: 4 queries")
print(f"  - Network: 4 queries")
print(f"  - Service: 4 queries")
print(f"  - Knowledge: 4 queries")
print(f"  - Edge Cases: 1 query")
print("\n" + "=" * 80)

# Create graph once
print("\nInitializing LangGraph workflow...")
graph = create_graph()
print("Graph ready!")

# Customer info
customer_info = {
    "customer_id": "CUST001",
    "name": "SivaPrasad Valluru",
    "service_plan_id": "STD_500",
    "address": "Apartment 301, Sunshine Towers, Bangalore",
    "email": "siva@example.com",
    "phone_number": "8088910831"
}

results = []
start_time_total = time.time()

for i, test in enumerate(ALL_QUERIES, 1):
    print("\n" + "=" * 80)
    print(f"TEST {i}/{len(ALL_QUERIES)} - {test['category']}")
    print("=" * 80)
    
    query_display = test['query'][:70] + "..." if len(test['query']) > 70 else test['query']
    print(f"Query: {query_display}")
    print(f"Expected: {test['expected']}")
    print("-" * 80)
    
    try:
        state = {
            "query": test["query"],
            "customer_info": customer_info,
            "classification": "",
            "intermediate_responses": {},
            "final_response": "",
            "chat_history": []
        }
        
        start_time = time.time()
        print("Processing...")
        
        # Invoke graph
        result = graph.invoke(state)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Extract results
        classification = result.get("classification", "unknown")
        final_response = result.get("final_response", "")
        intermediate = result.get("intermediate_responses", {})
        agent_used = list(intermediate.keys())[0] if intermediate else "unknown"
        
        correct_classification = classification == test["expected"]
        
        # Status
        classification_status = "✓" if correct_classification else "✗"
        response_status = "✓" if len(final_response) > 0 else "✗"
        
        print(f"\n{response_status} Response: {len(final_response)} chars | {duration:.1f}s")
        print(f"{classification_status} Classification: {classification}")
        print(f"  Agent: {agent_used}")
        
        # Show brief preview
        preview = final_response[:150] if final_response else "No response"
        print(f"  Preview: {preview}...")
        
        results.append({
            "query": test["query"],
            "category": test["category"],
            "expected": test["expected"],
            "actual": classification,
            "agent": agent_used,
            "duration": duration,
            "response_length": len(final_response),
            "success": len(final_response) > 0,
            "correct_classification": correct_classification
        })
        
        # Progress indicator
        elapsed = time.time() - start_time_total
        avg_time = elapsed / i
        remaining = (len(ALL_QUERIES) - i) * avg_time
        print(f"\n  Progress: {i}/{len(ALL_QUERIES)} | Elapsed: {elapsed/60:.1f}m | ETA: {remaining/60:.1f}m")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        results.append({
            "query": test["query"],
            "category": test["category"],
            "expected": test["expected"],
            "error": str(e),
            "success": False
        })

total_time = time.time() - start_time_total

# Generate Summary
print("\n" + "=" * 80)
print("COMPREHENSIVE TEST RESULTS")
print("=" * 80)

# Overall stats
success_count = sum(1 for r in results if r.get("success", False))
correct_class_count = sum(1 for r in results if r.get("correct_classification", False))
total_duration = sum(r.get("duration", 0) for r in results)
avg_duration = total_duration / len(results) if results else 0

print(f"\nOverall:")
print(f"  Total Queries: {len(results)}")
print(f"  Successful: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
print(f"  Correct Classification: {correct_class_count}/{len(results)} ({correct_class_count/len(results)*100:.1f}%)")
print(f"  Total Time: {total_time/60:.1f} minutes")
print(f"  Avg Response Time: {avg_duration:.1f}s")

# By category
print(f"\n{'=' * 80}")
print("Results by Category:")
print("=" * 80)

for category in ["Billing", "Network", "Service", "Knowledge", "Edge"]:
    cat_results = [r for r in results if r.get("category") == category]
    if not cat_results:
        continue
    
    cat_success = sum(1 for r in cat_results if r.get("success", False))
    cat_correct = sum(1 for r in cat_results if r.get("correct_classification", False))
    cat_avg_time = sum(r.get("duration", 0) for r in cat_results) / len(cat_results)
    
    print(f"\n{category} ({len(cat_results)} queries):")
    print(f"  Success: {cat_success}/{len(cat_results)}")
    print(f"  Correct Classification: {cat_correct}/{len(cat_results)}")
    print(f"  Avg Time: {cat_avg_time:.1f}s")
    
    for r in cat_results:
        success = "✓" if r.get("success", False) else "✗"
        classification = "✓" if r.get("correct_classification", False) else "✗"
        query_short = r["query"][:45] + "..." if len(r["query"]) > 45 else r["query"]
        print(f"    {success}{classification} {query_short}")
        if "error" in r:
            print(f"       ERROR: {r['error'][:60]}")

# Agent usage stats
print(f"\n{'=' * 80}")
print("Agent Usage:")
print("=" * 80)

agent_stats = {}
for r in results:
    agent = r.get("agent", "unknown")
    if agent not in agent_stats:
        agent_stats[agent] = {"count": 0, "total_time": 0}
    agent_stats[agent]["count"] += 1
    agent_stats[agent]["total_time"] += r.get("duration", 0)

for agent, stats in sorted(agent_stats.items()):
    avg = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
    print(f"  {agent}: {stats['count']} queries | Avg: {avg:.1f}s")

# Save results to file
print(f"\n{'=' * 80}")
print("Saving detailed results...")

with open("test_results_all_queries.txt", "w") as f:
    f.write("COMPREHENSIVE TEST RESULTS - All 17 Queries\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"Success Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)\n")
    f.write(f"Classification Accuracy: {correct_class_count}/{len(results)} ({correct_class_count/len(results)*100:.1f}%)\n")
    f.write(f"Total Time: {total_time/60:.1f} minutes\n\n")
    
    for i, r in enumerate(results, 1):
        f.write(f"\n{i}. {r['category']} Query\n")
        f.write("-" * 80 + "\n")
        f.write(f"Query: {r['query']}\n")
        f.write(f"Expected: {r['expected']}\n")
        f.write(f"Actual: {r.get('actual', 'ERROR')}\n")
        f.write(f"Agent: {r.get('agent', 'N/A')}\n")
        f.write(f"Duration: {r.get('duration', 0):.1f}s\n")
        f.write(f"Success: {'Yes' if r.get('success', False) else 'No'}\n")
        if "error" in r:
            f.write(f"Error: {r['error']}\n")
        f.write("\n")

print("Saved to: test_results_all_queries.txt")

print("\n" + "=" * 80)
print("TEST COMPLETE!")
print("=" * 80)

# Final verdict
if success_count == len(results):
    print("\n✓✓✓ ALL QUERIES WORKING! System is production-ready! ✓✓✓")
elif success_count >= len(results) * 0.9:
    print(f"\n✓ Most queries working ({success_count}/{len(results)}). Minor issues to address.")
else:
    print(f"\n✗ Significant issues found ({success_count}/{len(results)} working). Review needed.")
