"""
Test the termination condition logic
"""
import re

def is_termination_msg(msg):
    """Check if message contains TERMINATE or is from solution_integrator"""
    if msg.get("content"):
        content = str(msg.get("content", "")).strip()
        
        # Terminate if TERMINATE keyword found
        if "TERMINATE" in content:
            return True
        
        # Terminate if solution integrator has provided a complete solution
        # (numbered list with at least 5 steps)
        if msg.get("name") == "solution_integrator" and content:
            # Check for numbered steps (1., 2., etc.)
            steps = re.findall(r'^\d+\.', content, re.MULTILINE)
            if len(steps) >= 5:  # Complete solution has 5+ steps
                return True
    return False

print("=" * 80)
print("TESTING TERMINATION CONDITION")
print("=" * 80)

# Test 1: TERMINATE keyword
msg1 = {
    "name": "solution_integrator",
    "content": "Here are the steps...\n\nTERMINATE"
}
result1 = is_termination_msg(msg1)
print(f"\n1. Message with TERMINATE keyword: {'✅ PASS' if result1 else '❌ FAIL'}")
print(f"   Result: {result1}")

# Test 2: Complete solution (7 steps)
msg2 = {
    "name": "solution_integrator",
    "content": """Here's a prioritized list:

1. Restart Your Device
2. Check Airplane Mode
3. Check Signal Strength
4. Verify SIM Card
5. Test with Another Device
6. Reset Network Settings
7. Contact Your Service Provider

Following these steps should help!"""
}
result2 = is_termination_msg(msg2)
print(f"\n2. Complete solution (7 steps): {'✅ PASS' if result2 else '❌ FAIL'}")
print(f"   Result: {result2}")

# Test 3: Incomplete solution (3 steps)
msg3 = {
    "name": "solution_integrator",
    "content": """Here are some steps:

1. Restart Device
2. Check Settings
3. Try again

Let me know if this helps."""
}
result3 = is_termination_msg(msg3)
print(f"\n3. Incomplete solution (3 steps): {'✅ PASS' if not result3 else '❌ FAIL'}")
print(f"   Result: {result3} (should be False)")

# Test 4: Message from other agent
msg4 = {
    "name": "device_expert",
    "content": """Let's try these steps:

1. Restart
2. Check mode
3. Verify SIM
4. Check signal
5. Reset settings"""
}
result4 = is_termination_msg(msg4)
print(f"\n4. Message from device_expert (not solution_integrator): {'✅ PASS' if not result4 else '❌ FAIL'}")
print(f"   Result: {result4} (should be False)")

# Test 5: Empty message
msg5 = {
    "name": "user_proxy",
    "content": ""
}
result5 = is_termination_msg(msg5)
print(f"\n5. Empty message: {'✅ PASS' if not result5 else '❌ FAIL'}")
print(f"   Result: {result5} (should be False)")

print("\n" + "=" * 80)
print("TERMINATION CONDITION TEST COMPLETE")
print("=" * 80)

# Summary
all_passed = result1 and result2 and not result3 and not result4 and not result5
if all_passed:
    print("\n✅ ALL TESTS PASSED - Termination condition working correctly!")
else:
    print("\n❌ SOME TESTS FAILED - Review logic")

print("\nExpected behavior:")
print("  ✅ Terminate when TERMINATE keyword present")
print("  ✅ Terminate when solution_integrator provides 5+ steps")
print("  ✅ Don't terminate on incomplete solutions (<5 steps)")
print("  ✅ Don't terminate on messages from other agents")
print("  ✅ Don't terminate on empty messages")
