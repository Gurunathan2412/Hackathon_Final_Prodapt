"""Debug classification for specific queries"""

# Test the classification logic
queries = [
    "Can you explain the 'Value Added Services' charge on my bill?",
    "How do i setup volte on my samsung phone?",
    "family plan",
    "What is the best plan for me?",
]

for query in queries:
    ql = query.lower()
    classification = "billing_account"
    
    # Heuristic classification
    if any(w in ql for w in ["bill","charge","payment","account"]):
        classification = "billing_account"
        print(f"✓ Initial: billing_account (found billing keywords)")
    elif any(w in ql for w in ["network","signal","connection","call","data","slow"]):
        classification = "network_troubleshooting"
        print("✓ Initial: network_troubleshooting")
    else:
        print(f"✗ No keywords matched, defaulting to: {classification}")
    
    # Keyword overrides with improved logic
    knowledge_keywords = {"how", "what", "configure", "setup", "apn", "volte"}
    if any(k in ql for k in knowledge_keywords):
        # Only override to knowledge if there are no billing keywords
        billing_keywords = {"bill", "charge", "payment", "account", "invoice", "balance"}
        if not any(k in ql for k in billing_keywords):
            classification = "knowledge_retrieval"
            print(f"  → Override to knowledge_retrieval (found: {[k for k in knowledge_keywords if k in ql]})")
        else:
            print(f"  → Kept {classification} (billing keywords present: {[k for k in billing_keywords if k in ql]})")
    else:
        service_keywords = {"plan", "recommend", "best", "upgrade", "family"}
        # Only override to service_recommendation if not billing or network troubleshooting
        if classification not in {"knowledge_retrieval", "billing_account", "network_troubleshooting"} and any(k in ql for k in service_keywords):
            classification = "service_recommendation"
            print(f"  → Override to service_recommendation (found: {[k for k in service_keywords if k in ql]})")
    
    print(f"Query: '{query}'")
    print(f"Final: {classification}\n")

