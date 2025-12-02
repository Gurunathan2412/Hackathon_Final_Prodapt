"""Test classification for irrelevant queries"""

# Test queries that should be classified as fallback
irrelevant_queries = [
    "Tell me a joke about telecom",
    "Can you tell me a funny story?",
    "Sing me a song",
    "Let's play a game",
    "Write me a poem about 5G",
    "Tell me something funny",
    "Just want to chat",
]

# Test queries that should be valid
valid_queries = [
    ("Can you explain charges on my bill?", "billing_account"),
    ("My internet is slow", "network_troubleshooting"),
    ("What's the best family plan?", "service_recommendation"),
    ("How do I setup VoLTE?", "knowledge_retrieval"),
]

print("=== Testing Irrelevant Query Detection ===\n")

for query in irrelevant_queries:
    ql = query.lower()
    
    # Check keyword filter
    irrelevant_keywords = {"joke", "funny", "story", "poem", "song", "game", "play", "chat", "talk"}
    is_filtered = any(k in ql for k in irrelevant_keywords)
    
    status = "✅ FILTERED" if is_filtered else "❌ NOT FILTERED"
    print(f"{status}: '{query}'")
    if is_filtered:
        print(f"  → Found keyword: {[k for k in irrelevant_keywords if k in ql]}")
    print()

print("\n=== Testing Valid Query Classification ===\n")

for query, expected in valid_queries:
    ql = query.lower()
    
    # Check it's not filtered as irrelevant
    irrelevant_keywords = {"joke", "funny", "story", "poem", "song", "game", "play", "chat", "talk"}
    is_filtered = any(k in ql for k in irrelevant_keywords)
    
    # Check classification keywords
    if "bill" in ql or "charge" in ql or "payment" in ql:
        classification = "billing_account"
    elif "network" in ql or "signal" in ql or "slow" in ql or "internet" in ql:
        classification = "network_troubleshooting"
    elif "setup" in ql or "configure" in ql or "volte" in ql or "how do i" in ql:
        classification = "knowledge_retrieval"
    elif "plan" in ql or "recommend" in ql or "best" in ql or "family" in ql:
        classification = "service_recommendation"
    else:
        classification = "fallback"
    
    if is_filtered:
        classification = "fallback"
    
    status = "✅" if classification == expected else "❌"
    print(f"{status} '{query}'")
    print(f"  Expected: {expected}")
    print(f"  Got: {classification}")
    print()
