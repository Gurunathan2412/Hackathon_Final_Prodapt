# Query Classification Test Results
**Date:** December 1, 2025  
**Overall Accuracy:** 78.6% (11/14 correct)

## ✅ Working Correctly (11 queries)

### Billing Queries (2/3) ✅
- ✅ "Why did my bill increase by 200 this month?" → billing_account
- ✅ "I see a charge for international roaming..." → billing_account
- ❌ "What's the early termination fee..." → knowledge_retrieval (WRONG)

### Network Queries (3/3) ✅✅✅
- ✅ "I can't make calls from my home in Mumbai West" → network_troubleshooting
- ✅ "My data connection keeps dropping" → network_troubleshooting
- ✅ "I get a 'No Service' error in my basement" → network_troubleshooting

### Service Queries (2/3) ✅
- ❌ "What's the best plan for a family of four?" → knowledge_retrieval (WRONG)
- ✅ "I need a plan with international calling to the US" → service_recommendation
- ✅ "I'm a light user who mostly just calls and texts" → service_recommendation

### Knowledge Queries (3/3) ✅✅✅
- ✅ "How do I set up VoLTE on my Samsung phone?" → knowledge_retrieval
- ✅ "What are the APN settings for Android?" → knowledge_retrieval
- ✅ "How can I activate international roaming?" → knowledge_retrieval

### Edge Cases (1/2) ✅
- ❌ "Tell me a joke about telecom" → knowledge_retrieval (WRONG)
- ✅ "I need help with both my bill and network issues" → billing_account

---

## ❌ Issues Found (3 queries)

### 1. "What's the early termination fee if I cancel my contract?"
**Expected:** billing_account  
**Got:** knowledge_retrieval  
**Reason:** Keywords "what" triggers knowledge override  
**Impact:** MEDIUM - Will search docs instead of querying billing database

**Fix Needed:** Add "fee", "contract", "termination" as billing keywords

---

### 2. "What's the best plan for a family of four?"
**Expected:** service_recommendation  
**Got:** knowledge_retrieval  
**Reason:** "What" keyword triggers knowledge override  
**Impact:** HIGH - Won't use LangChain recommendation agent with tools

**Fix Needed:** "best plan" should override "what" keyword

---

### 3. "Tell me a joke about telecom"
**Expected:** fallback  
**Got:** knowledge_retrieval  
**Reason:** Not detected as greeting/casual query  
**Impact:** LOW - Will search docs for jokes (not ideal but not broken)

**Fix Needed:** Add joke/casual query detection

---

## Root Cause Analysis

### Problem: Keyword Override Too Aggressive

Current logic in `orchestration/graph.py`:

```python
# Knowledge keywords override everything (TOO AGGRESSIVE)
knowledge_keywords = {"how", "what", "configure", "setup", "apn", "volte"}
if any(k in ql for k in knowledge_keywords):
    classification = "knowledge_retrieval"
```

**Issue:** "What" keyword overrides even when query is clearly about billing/plans

### Solution Needed:

**Option 1:** More specific keyword matching
```python
# Only override if it's a "how-to" question
if query starts with "how do I" or "how can I" or "what is" or "what are":
    classification = "knowledge_retrieval"
```

**Option 2:** Check context after "what"
```python
# Don't override if "what" is followed by plan/billing keywords
if "what" in query and any(k in query for k in ["plan", "fee", "charge", "cost"]):
    # Don't override to knowledge
    pass
```

---

## Recommendation

**Current Status:** 78.6% accuracy is acceptable but can be improved

**Priority Fixes:**
1. **HIGH:** Fix "What's the best plan" → should be service_recommendation
2. **MEDIUM:** Fix "early termination fee" → should be billing_account  
3. **LOW:** Fix "tell me a joke" → should be fallback

**Effort:** Medium (30 minutes to adjust keyword logic)

**Risk:** Low (only affects classification, won't break existing queries)

---

## Testing Next Steps

### Already Tested:
✅ Classification (all 14 sample queries)

### Still Need to Test:
⏸️ **Full Execution** (actual agent responses) - Will take 5-10 minutes
   - Test 1 query from each category end-to-end
   - Verify agents produce correct responses
   - Check for errors/timeouts

Want to proceed with full execution test or fix classification issues first?

---

## Summary

**Working Well:**
- Network troubleshooting (100% accuracy)
- Knowledge retrieval (100% accuracy)
- Most billing queries (67%)
- Most service queries (67%)

**Needs Improvement:**
- Keyword override logic too aggressive
- "What" shouldn't always mean knowledge_retrieval
- Need context-aware classification

**Overall:** System works but classification could be smarter.
