"""Quick test of all sample queries - Classification only"""
import sys
sys.path.insert(0, '.')

from orchestration.graph import classify_query

queries = {
    "Billing": [
        "Why did my bill increase by 200 this month?",
        "I see a charge for international roaming but I haven't traveled recently",
        "What's the early termination fee if I cancel my contract?"
    ],
    "Network": [
        "I can't make calls from my home in Mumbai West",
        "My data connection keeps dropping",
        "I get a 'No Service' error in my basement"
    ],
    "Service": [
        "What's the best plan for a family of four?",
        "I need a plan with international calling to the US",
        "I'm a light user who mostly just calls and texts"
    ],
    "Knowledge": [
        "How do I set up VoLTE on my Samsung phone?",
        "What are the APN settings for Android?",
        "How can I activate international roaming?"
    ],
    "Edge": [
        "Tell me a joke about telecom",
        "I need help with both my bill and network issues"
    ]
}

expected = {
    "Billing": "billing_account",
    "Network": "network_troubleshooting",
    "Service": "service_recommendation",
    "Knowledge": "knowledge_retrieval",
    "Edge": "fallback"
}

print("=" * 70)
print("QUERY CLASSIFICATION TEST")
print("=" * 70)

total = 0
correct = 0

for category, query_list in queries.items():
    print(f"\n{category} Queries (expect: {expected.get(category, 'varies')}):")
    print("-" * 70)
    
    for query in query_list:
        state = {
            'query': query,
            'customer_info': {},
            'classification': '',
            'intermediate_responses': {},
            'final_response': '',
            'chat_history': []
        }
        
        result = classify_query(state)
        classification = result.get('classification', 'unknown')
        
        # Check if correct
        if category == "Edge":
            is_correct = classification in ["fallback", "billing_account"]  # Both valid for complex
        else:
            is_correct = classification == expected[category]
        
        total += 1
        if is_correct:
            correct += 1
            status = "[PASS]"
        else:
            status = "[FAIL]"
        
        # Truncate long queries
        q_display = query if len(query) <= 50 else query[:47] + "..."
        print(f"  {status} {q_display}")
        print(f"         -> {classification}")

print(f"\n{'=' * 70}")
print(f"RESULTS: {correct}/{total} correct ({correct/total*100:.1f}%)")
print("=" * 70)
