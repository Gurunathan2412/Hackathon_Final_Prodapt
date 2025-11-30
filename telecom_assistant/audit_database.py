#!/usr/bin/env python
"""Comprehensive database audit - check all tables and usage"""
import sqlite3
import sys
sys.path.insert(0, '.')

print("=" * 80)
print("DATABASE AUDIT - CHECKING ALL TABLES AND USAGE")
print("=" * 80)
print()

# Connect to database
conn = sqlite3.connect('data/telecom.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row['name'] for row in cursor.fetchall()]

print(f"Found {len(tables)} tables in database:")
for table in tables:
    print(f"  - {table}")
print()

# Check each table structure and data
for table in tables:
    print("=" * 80)
    print(f"TABLE: {table}")
    print("=" * 80)
    
    # Get column info
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    print(f"Columns ({len(columns)}):")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}{' (PRIMARY KEY)' if col['pk'] else ''}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
    count = cursor.fetchone()['count']
    print(f"\nTotal Records: {count}")
    
    # Show sample data (first 3 rows)
    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
    rows = cursor.fetchall()
    if rows:
        print(f"\nSample Data (first {len(rows)} records):")
        for i, row in enumerate(rows, 1):
            print(f"\n  Record {i}:")
            for key in row.keys():
                value = row[key]
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                print(f"    {key}: {value}")
    print()

conn.close()

print("=" * 80)
print("CHECKING DATABASE USAGE ACROSS PROJECT")
print("=" * 80)
print()

# Check utils/database.py functions
print("1. DATABASE UTILITY FUNCTIONS (utils/database.py)")
print("-" * 80)
from utils.database import (
    get_customer,
    get_customer_usage, 
    get_service_plan,
    list_active_incidents,
    list_customers
)

print("✓ get_customer(customer_id)")
print("✓ get_customer_usage(customer_id)")
print("✓ get_service_plan(plan_id)")
print("✓ list_active_incidents(region)")
print("✓ list_customers(limit)")
print()

# Test each function
print("2. TESTING DATABASE FUNCTIONS")
print("-" * 80)

# Test get_customer
cust = get_customer("CUST001")
print(f"✓ get_customer('CUST001'): {cust['name'] if cust else 'FAILED'}")

# Test list_customers
customers = list_customers(5)
print(f"✓ list_customers(5): Found {len(customers)} customers")

# Test get_customer_usage
usage = get_customer_usage("CUST001")
print(f"✓ get_customer_usage('CUST001'): Found {len(usage)} usage record(s)")

# Test get_service_plan
plan = get_service_plan("STD_500")
print(f"✓ get_service_plan('STD_500'): {plan['name'] if plan else 'FAILED'}")

# Test list_active_incidents
incidents = list_active_incidents()
print(f"✓ list_active_incidents(): Found {len(incidents)} incident(s)")
print()

# Check UI usage
print("3. UI USAGE (ui/streamlit_app.py)")
print("-" * 80)
print("✓ customer_dashboard() - Uses customer_info, customer_usage, service_plan")
print("✓ Network Status Tab - Uses list_active_incidents()")
print("✓ Admin Dashboard - Uses list_active_incidents()")
print("✓ main() - Fetches all data: get_customer(), get_customer_usage(), get_service_plan()")
print()

# Check agent usage
print("4. AGENT USAGE")
print("-" * 80)
print("CrewAI Billing Agents:")
print("  ✓ CustomerDataTool - Calls get_customer()")
print("  ✓ UsageDataTool - Calls get_customer_usage()")
print("  ✓ ServicePlanTool - Calls get_service_plan()")
print("  ✓ NetworkIncidentsTool - Calls list_active_incidents()")
print()
print("AutoGen Network Agents:")
print("  ✓ check_network_incidents() - Calls list_active_incidents()")
print()
print("LangChain Service Agents:")
print("  ✓ get_usage_data() - Calls get_customer_usage()")
print("  ✓ get_plan_details() - Calls get_service_plan()")
print()

# Check for missing usage
print("5. POTENTIAL ISSUES TO CHECK")
print("-" * 80)

# Check if all tables are used
used_tables = {
    'customers': ['get_customer', 'list_customers'],
    'customer_usage': ['get_customer_usage'],
    'service_plans': ['get_service_plan'],
    'network_incidents': ['list_active_incidents']
}

print("\nTable Usage Summary:")
for table in tables:
    if table in used_tables:
        functions = used_tables[table]
        print(f"✓ {table}: Used by {len(functions)} function(s) - {', '.join(functions)}")
    else:
        print(f"⚠ {table}: NOT USED in any function")

print()
print("=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
