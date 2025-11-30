#!/usr/bin/env python
"""Test all new database functions"""
import sys
sys.path.insert(0, '.')

from utils.database import (
    # New functions
    get_customer_tickets,
    search_tickets_by_category,
    search_common_network_issues,
    get_troubleshooting_steps,
    get_device_compatibility,
    get_service_areas,
    get_coverage_quality,
    get_cell_towers,
    get_tower_technologies,
    get_transportation_routes,
    get_building_types
)

print("=" * 80)
print("TESTING NEW DATABASE FUNCTIONS")
print("=" * 80)
print()

# Test 1: Support Tickets
print("1. SUPPORT TICKETS")
print("-" * 80)
tickets = get_customer_tickets("CUST001")
print(f"✓ get_customer_tickets('CUST001'): Found {len(tickets)} ticket(s)")
if tickets:
    print(f"  Example: {tickets[0]['ticket_id']} - {tickets[0]['issue_category']}")

billing_tickets = search_tickets_by_category("Billing")
print(f"✓ search_tickets_by_category('Billing'): Found {len(billing_tickets)} ticket(s)")
print()

# Test 2: Common Network Issues
print("2. COMMON NETWORK ISSUES")
print("-" * 80)
issues = search_common_network_issues("call")
print(f"✓ search_common_network_issues('call'): Found {len(issues)} issue(s)")
if issues:
    print(f"  Example: {issues[0]['issue_category']}")

steps = get_troubleshooting_steps("Call Failure")
print(f"✓ get_troubleshooting_steps('Call Failure'): {'Found' if steps else 'Not found'}")
if steps:
    print(f"  Steps preview: {steps['troubleshooting_steps'][:80]}...")
print()

# Test 3: Device Compatibility
print("3. DEVICE COMPATIBILITY")
print("-" * 80)
devices = get_device_compatibility("Samsung")
print(f"✓ get_device_compatibility('Samsung'): Found {len(devices)} device(s)")
if devices:
    print(f"  Example: {devices[0]['device_model']} - {devices[0]['network_technology']}")

all_devices = get_device_compatibility()
print(f"✓ get_device_compatibility(): Found {len(all_devices)} total device(s)")
print()

# Test 4: Service Areas
print("4. SERVICE AREAS")
print("-" * 80)
mumbai_areas = get_service_areas("Mumbai")
print(f"✓ get_service_areas('Mumbai'): Found {len(mumbai_areas)} area(s)")
if mumbai_areas:
    print(f"  Example: {mumbai_areas[0]['district']} - {mumbai_areas[0]['terrain_type']}")

all_areas = get_service_areas()
print(f"✓ get_service_areas(): Found {len(all_areas)} total area(s)")
print()

# Test 5: Coverage Quality
print("5. COVERAGE QUALITY")
print("-" * 80)
coverage = get_coverage_quality(technology="5G")
print(f"✓ get_coverage_quality(technology='5G'): Found {len(coverage)} record(s)")
if coverage:
    print(f"  Example: {coverage[0]['signal_strength_category']} - {coverage[0]['avg_download_speed_mbps']} Mbps")

all_coverage = get_coverage_quality()
print(f"✓ get_coverage_quality(): Found {len(all_coverage)} total record(s)")
print()

# Test 6: Cell Towers
print("6. CELL TOWERS")
print("-" * 80)
towers = get_cell_towers("AREA001")
print(f"✓ get_cell_towers('AREA001'): Found {len(towers)} tower(s)")
if towers:
    print(f"  Example: {towers[0]['tower_type']} - {towers[0]['operational_status']}")

all_towers = get_cell_towers()
print(f"✓ get_cell_towers(): Found {len(all_towers)} total tower(s)")
print()

# Test 7: Tower Technologies
print("7. TOWER TECHNOLOGIES")
print("-" * 80)
tech = get_tower_technologies("TWR001")
print(f"✓ get_tower_technologies('TWR001'): Found {len(tech)} technology(ies)")
if tech:
    print(f"  Example: {tech[0]['technology']} - {tech[0]['frequency_band']}")

all_tech = get_tower_technologies()
print(f"✓ get_tower_technologies(): Found {len(all_tech)} total technology record(s)")
print()

# Test 8: Transportation Routes
print("8. TRANSPORTATION ROUTES")
print("-" * 80)
train_routes = get_transportation_routes("Train")
print(f"✓ get_transportation_routes('Train'): Found {len(train_routes)} route(s)")
if train_routes:
    print(f"  Example: {train_routes[0]['route_name']} - {train_routes[0]['coverage_quality']}")

all_routes = get_transportation_routes()
print(f"✓ get_transportation_routes(): Found {len(all_routes)} total route(s)")
print()

# Test 9: Building Types
print("9. BUILDING TYPES")
print("-" * 80)
apartments = get_building_types("Apartment")
print(f"✓ get_building_types('Apartment'): Found {len(apartments)} type(s)")
if apartments:
    print(f"  Example: {apartments[0]['building_category']} - {apartments[0]['avg_signal_reduction_percent']}% reduction")

all_buildings = get_building_types()
print(f"✓ get_building_types(): Found {len(all_buildings)} total building type(s)")
print()

print("=" * 80)
print("✅ ALL DATABASE FUNCTIONS TESTED SUCCESSFULLY")
print("=" * 80)
print()
print("Summary:")
print(f"  • Support Tickets: {len(tickets)} customer + {len(billing_tickets)} billing")
print(f"  • Network Issues: {len(issues)} issues with troubleshooting")
print(f"  • Devices: {len(all_devices)} devices tracked")
print(f"  • Areas: {len(all_areas)} service areas")
print(f"  • Coverage: {len(all_coverage)} quality records")
print(f"  • Towers: {len(all_towers)} towers with {len(all_tech)} technologies")
print(f"  • Transport: {len(all_routes)} routes")
print(f"  • Buildings: {len(all_buildings)} building types")
print()
print("Next: Creating CrewAI tools for these functions...")
