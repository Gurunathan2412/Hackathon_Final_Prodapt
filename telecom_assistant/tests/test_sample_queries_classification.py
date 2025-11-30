"""
Quick classification test for all sample queries
Tests routing without calling LLMs (fast test)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.graph import classify_query

print("=" * 80)
print("SAMPLE QUERIES CLASSIFICATION TEST")
print("=" * 80)

# All sample queries from documentation
test_queries = {
    "Billing Queries (CrewAI)": [
        "Why did my bill increase by ₹200 this month?",
        "I see a charge for international roaming but I haven't traveled recently",
        "Can you explain the 'Value Added Services' charge on my bill?",
        "What's the early termination fee if I cancel my contract?"
    ],
    "Network Issues (AutoGen)": [
        "I can't make calls from my home in Mumbai West",
        "My data connection keeps dropping when I'm on the train",
        "Why is my 5G connection slower than my friend's?",
        "I get a 'No Service' error in my basement apartment"
    ],
    "Plan Recommendations (LangChain)": [
        "What's the best plan for a family of four who watches a lot of videos?",
        "I need a plan with good international calling to the US",
        "Which plan is best for someone who works from home and needs reliable data?",
        "I'm a light user who mostly just calls and texts. What's my cheapest option?"
    ],
    "Technical Information (LlamaIndex)": [
        "How do I set up VoLTE on my Samsung phone?",
        "What are the APN settings for Android devices?",
        "How can I activate international roaming before traveling?",
        "What areas in Delhi have 5G coverage?"
    ],
    "Edge Cases": [
        "Tell me a joke about telecom",
        "I need help with both my bill and network issues",
        ""  # Empty query
    ]
}

# Expected agent routing
expected_agents = {
    "Billing Queries (CrewAI)": "crew_ai",
    "Network Issues (AutoGen)": "autogen",
    "Plan Recommendations (LangChain)": ["langchain", "crew_ai"],  # Could be either
    "Technical Information (LlamaIndex)": ["llamaindex", "crew_ai"],  # Could be either
    "Edge Cases": "crew_ai"  # Fallback
}

# Classification to agent mapping
classification_to_agent = {
    "billing_inquiry": "crew_ai",
    "billing_account": "crew_ai",
    "network_troubleshooting": "autogen",
    "plan_recommendation": "langchain",
    "technical_support": "llamaindex",
    "knowledge_retrieval": "llamaindex",
    "unknown": "crew_ai"
}

total = 0
correct_routing = 0
results = []

for category, queries in test_queries.items():
    print(f"\n{'=' * 80}")
    print(f"CATEGORY: {category}")
    print(f"{'=' * 80}")
    
    expected = expected_agents.get(category)
    
    for i, query in enumerate(queries, 1):
        total += 1
        
        # Handle empty query
        if not query.strip():
            print(f"\n{i}. [EMPTY QUERY]")
            state = {"query": query, "classification": None}
            try:
                result = classify_query(state)
                classification = result.get("classification", "unknown")
                agent = classification_to_agent.get(classification, "crew_ai")
                print(f"   Classification: {classification}")
                print(f"   Agent: {agent}")
                print(f"   Status: Handled (no crash)")
                correct_routing += 1
            except Exception as e:
                print(f"   ERROR: {str(e)[:100]}")
            continue
        
        print(f"\n{i}. Query: \"{query[:60]}...\"" if len(query) > 60 else f"\n{i}. Query: \"{query}\"")
        
        # Classify
        state = {"query": query, "classification": None}
        try:
            result = classify_query(state)
            classification = result.get("classification", "unknown")
            agent = classification_to_agent.get(classification, "crew_ai")
            
            print(f"   Classification: {classification}")
            print(f"   Routes to agent: {agent}")
            
            # Check if routing is correct
            if isinstance(expected, list):
                is_correct = agent in expected
                status = "✅ CORRECT" if is_correct else f"⚠️  (expected one of: {', '.join(expected)})"
            else:
                is_correct = agent == expected
                status = "✅ CORRECT" if is_correct else f"❌ WRONG (expected: {expected})"
            
            print(f"   Routing: {status}")
            
            if is_correct:
                correct_routing += 1
            
            results.append({
                "category": category,
                "query": query[:50],
                "classification": classification,
                "agent": agent,
                "expected": expected,
                "correct": is_correct
            })
            
        except Exception as e:
            print(f"   ERROR: {str(e)[:100]}")
            results.append({
                "category": category,
                "query": query[:50],
                "error": str(e)[:100]
            })

# Print summary
print(f"\n\n{'=' * 80}")
print("CLASSIFICATION SUMMARY")
print(f"{'=' * 80}")

print(f"\nTotal queries tested: {total}")
print(f"Correctly routed: {correct_routing}/{total}")
print(f"Success rate: {(correct_routing/total*100):.1f}%")

# Breakdown by category
print(f"\n{'=' * 80}")
print("BREAKDOWN BY CATEGORY")
print(f"{'=' * 80}")

for category in test_queries.keys():
    category_results = [r for r in results if r.get("category") == category]
    correct = sum(1 for r in category_results if r.get("correct"))
    total_cat = len(category_results)
    print(f"\n{category}: {correct}/{total_cat} correct")
    
    for r in category_results:
        if not r.get("correct") and "error" not in r:
            print(f"  - '{r['query'][:40]}...' -> {r['agent']} (expected: {r['expected']})")

# Print routing table
print(f"\n\n{'=' * 80}")
print("ROUTING TABLE")
print(f"{'=' * 80}")

print("\nClassification → Agent mapping:")
for classification, agent in classification_to_agent.items():
    count = sum(1 for r in results if r.get("classification") == classification)
    if count > 0:
        print(f"  {classification:25} → {agent:15} ({count} queries)")

# Final verdict
print(f"\n{'=' * 80}")
if correct_routing == total:
    print("✅ ALL QUERIES ROUTE CORRECTLY - PERFECT!")
elif correct_routing / total >= 0.8:
    print(f"✅ GOOD ROUTING - {correct_routing}/{total} correct ({(correct_routing/total*100):.1f}%)")
else:
    print(f"⚠️  ROUTING NEEDS ATTENTION - Only {correct_routing}/{total} correct")
print(f"{'=' * 80}")

print("\n✅ Test complete! See SAMPLE_QUERIES_TEST_GUIDE.md for manual UI testing.")
