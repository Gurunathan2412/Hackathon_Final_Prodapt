#!/usr/bin/env python
"""Check if different customers have different data"""
import sys
sys.path.insert(0, '.')

from utils.database import get_customer, get_customer_usage, list_customers

print("=" * 60)
print("Checking Customer Data Variation")
print("=" * 60)

# Get list of customers
customers = list_customers(5)
print(f"\nFound {len(customers)} customers:")
for c in customers:
    print(f"  - {c['name']} ({c['customer_id']})")

print("\n" + "=" * 60)
print("Fetching detailed data for first 3 customers:")
print("=" * 60)

for i, cust in enumerate(customers[:3], 1):
    cust_id = cust['customer_id']
    print(f"\n{i}. Customer: {cust['name']} ({cust_id})")
    print("-" * 60)
    
    # Get customer details
    details = get_customer(cust_id)
    if details:
        print(f"   Email: {details['email']}")
        print(f"   Plan: {details['service_plan_id']}")
        print(f"   Status: {details['account_status']}")
        print(f"   Last Bill: {details['last_billing_date']}")
    
    # Get usage data
    usage = get_customer_usage(cust_id)
    print(f"   Usage records: {len(usage)}")
    if usage:
        latest = usage[0]
        print(f"   Latest period: {latest['billing_period_start']} to {latest['billing_period_end']}")
        print(f"   Data used: {latest['data_used_gb']} GB")
        print(f"   Voice minutes: {latest['voice_minutes_used']}")
        print(f"   Total bill: ₹{latest['total_bill_amount']}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("=" * 60)
# Check if data varies
test_ids = [c['customer_id'] for c in customers[:3]]
plans = [get_customer(cid)['service_plan_id'] for cid in test_ids]
emails = [get_customer(cid)['email'] for cid in test_ids]

if len(set(plans)) == 1 and len(set(emails)) == 1:
    print("⚠️  WARNING: All customers have IDENTICAL data!")
    print("    This suggests database has duplicate/template data.")
else:
    print("✓ Customers have DIFFERENT data (correctly personalized)")
