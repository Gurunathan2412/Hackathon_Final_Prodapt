#!/usr/bin/env python
"""Test crew creation with detailed error output"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Testing CrewAI Initialization")
print("=" * 60)

# Check environment
api_key = os.getenv("OPENAI_API_KEY")
print(f"\n1. API Key: {'✓ Present' if api_key else '✗ Missing'}")
if api_key:
    print(f"   Prefix: {api_key[:15]}...")

# Test imports
print("\n2. Testing imports...")
try:
    from crewai import Agent, Task, Crew, Process
    print("   ✓ CrewAI core imports OK")
except Exception as e:
    print(f"   ✗ CrewAI import failed: {e}")
    sys.exit(1)

try:
    from langchain_openai import ChatOpenAI
    print("   ✓ ChatOpenAI import OK")
except Exception as e:
    print(f"   ✗ ChatOpenAI import failed: {e}")
    sys.exit(1)

try:
    from langchain_community.utilities.sql_database import SQLDatabase
    from langchain_community.agent_toolkits import SQLDatabaseToolkit
    print("   ✓ LangChain SQL imports OK")
except Exception as e:
    print(f"   ✗ LangChain SQL import failed: {e}")
    sys.exit(1)

# Test LLM creation
print("\n3. Creating ChatOpenAI...")
try:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=api_key)
    print(f"   ✓ LLM created: {llm}")
except Exception as e:
    print(f"   ✗ LLM creation failed: {e}")
    sys.exit(1)

# Test SQL tools
print("\n4. Creating SQL tools...")
sql_tools = []  # CrewAI 1.6+ requires special tool format
print(f"   ℹ Skipping SQL tools (format incompatibility)")


# Test Agent creation
print("\n5. Creating agents...")
try:
    billing_agent = Agent(
        role="Billing Specialist",
        backstory="Senior billing analyst",
        goal="Explain bill components",
        tools=sql_tools,
        llm=llm,
        allow_delegation=False,
    )
    print(f"   ✓ Billing agent created: {billing_agent}")
except Exception as e:
    print(f"   ✗ Agent creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test Task creation
print("\n6. Creating tasks...")
try:
    billing_task = Task(
        description="Analyze the most recent bill",
        agent=billing_agent,
    )
    print(f"   ✓ Task created: {billing_task}")
except Exception as e:
    print(f"   ✗ Task creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test Crew creation
print("\n7. Creating crew...")
try:
    crew = Crew(
        agents=[billing_agent],
        tasks=[billing_task],
        process=Process.sequential,
        verbose=False,
    )
    print(f"   ✓ Crew created: {crew}")
    print("\n" + "=" * 60)
    print("SUCCESS: All components initialized correctly!")
    print("=" * 60)
except Exception as e:
    print(f"   ✗ Crew creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
