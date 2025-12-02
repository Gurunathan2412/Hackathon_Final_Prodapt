"""Test region validation for network incidents"""

from utils.database import get_covered_regions, list_active_incidents

# Get regions we monitor
covered_regions = get_covered_regions()
print("=== Covered Regions ===")
print(f"We monitor: {', '.join(covered_regions)}\n")

# Test cases
test_cases = [
    ("Bangalore", True, "Valid region - should find incidents or say no incidents"),
    ("Philadelphia", False, "Invalid region - should say not in coverage"),
    ("Mumbai", True, "Valid region - should work"),
    ("New York", False, "Invalid region - should say not in coverage"),
    ("Delhi", True, "Valid region - should work"),
]

print("=== Testing Region Validation ===\n")

for region, should_be_valid, description in test_cases:
    # Check if region is covered (same logic as in agent)
    is_covered = any(region.lower() in loc.lower() or loc.lower() in region.lower() for loc in covered_regions)
    
    # Get incidents
    incidents = list_active_incidents(region)
    
    # Determine result
    if not is_covered:
        status = "❌ NOT COVERED"
        message = f"Should return: '{region}' is not in our coverage area"
    else:
        status = "✅ COVERED"
        if incidents:
            message = f"Found {len(incidents)} incidents"
        else:
            message = "No active incidents"
    
    print(f"{status} - {region}")
    print(f"  Description: {description}")
    print(f"  Result: {message}")
    print()
