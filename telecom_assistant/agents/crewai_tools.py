"""CrewAI-compatible database tools for telecom assistant agents"""

from typing import Type
from pydantic import BaseModel, Field
from utils.database import (
    get_customer,
    get_customer_usage,
    get_service_plan,
    list_active_incidents,
    # New imports
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

# Try to import CrewAI BaseTool, fallback if not available
try:
    from crewai.tools import BaseTool  # type: ignore
except ImportError:
    # Fallback for linting/when CrewAI not installed
    class BaseTool:  # type: ignore
        pass


class CustomerDataInput(BaseModel):
    """Input schema for customer data tool"""
    customer_id: str = Field(..., description="The customer ID to fetch data for (e.g., CUST001)")


class CustomerDataTool(BaseTool):
    name: str = "get_customer_data"
    description: str = (
        "Fetches complete customer information including name, email, phone, address, "
        "service plan ID, account status, and billing dates. "
        "Use this to get basic customer details."
    )
    args_schema: Type[BaseModel] = CustomerDataInput

    def _run(self, customer_id: str) -> str:
        """Fetch customer data from database"""
        customer = get_customer(customer_id)
        if not customer:
            return f"Customer {customer_id} not found in database."
        
        return (
            f"Customer: {customer['name']}\n"
            f"Email: {customer['email']}\n"
            f"Phone: {customer['phone_number']}\n"
            f"Address: {customer['address']}\n"
            f"Service Plan: {customer['service_plan_id']}\n"
            f"Account Status: {customer['account_status']}\n"
            f"Registration Date: {customer['registration_date']}\n"
            f"Last Billing Date: {customer['last_billing_date']}"
        )


class UsageDataInput(BaseModel):
    """Input schema for usage data tool"""
    customer_id: str = Field(..., description="The customer ID to fetch usage data for")


class UsageDataTool(BaseTool):
    name: str = "get_customer_usage"
    description: str = (
        "Fetches customer usage history including data used (GB), voice minutes, "
        "SMS count, billing periods, additional charges, and total bill amounts. "
        "Returns multiple billing periods sorted by most recent first. "
        "Use this to analyze usage patterns and billing history."
    )
    args_schema: Type[BaseModel] = UsageDataInput

    def _run(self, customer_id: str) -> str:
        """Fetch customer usage data from database"""
        usage_records = get_customer_usage(customer_id)
        if not usage_records:
            return f"No usage data found for customer {customer_id}."
        
        result = f"Usage data for {customer_id} ({len(usage_records)} records):\n\n"
        for i, record in enumerate(usage_records, 1):
            result += (
                f"Period {i}: {record['billing_period_start']} to {record['billing_period_end']}\n"
                f"  Data Used: {record['data_used_gb']} GB\n"
                f"  Voice Minutes: {record['voice_minutes_used']} mins\n"
                f"  SMS Count: {record['sms_count_used']}\n"
                f"  Additional Charges: ₹{record['additional_charges']}\n"
                f"  Total Bill: ₹{record['total_bill_amount']}\n\n"
            )
        return result.strip()


class ServicePlanInput(BaseModel):
    """Input schema for service plan tool"""
    plan_id: str = Field(..., description="The service plan ID to fetch details for (e.g., STD_500, BASIC_100)")


class ServicePlanTool(BaseTool):
    name: str = "get_service_plan"
    description: str = (
        "Fetches detailed service plan information including monthly cost, "
        "data limits, voice minutes, SMS counts, contract duration, fees, "
        "and plan description. Use this to understand plan features and costs."
    )
    args_schema: Type[BaseModel] = ServicePlanInput

    def _run(self, plan_id: str) -> str:
        """Fetch service plan details from database"""
        plan = get_service_plan(plan_id)
        if not plan:
            return f"Service plan {plan_id} not found in database."
        
        data_info = "Unlimited" if plan['unlimited_data'] else f"{plan['data_limit_gb']} GB"
        voice_info = "Unlimited" if plan['unlimited_voice'] else f"{plan['voice_minutes']} minutes"
        sms_info = "Unlimited" if plan['unlimited_sms'] else f"{plan['sms_count']} SMS"
        
        return (
            f"Plan: {plan['name']} ({plan['plan_id']})\n"
            f"Monthly Cost: ₹{plan['monthly_cost']}\n"
            f"Data: {data_info}\n"
            f"Voice: {voice_info}\n"
            f"SMS: {sms_info}\n"
            f"Contract Duration: {plan['contract_duration_months']} months\n"
            f"Early Termination Fee: ₹{plan['early_termination_fee']}\n"
            f"International Roaming: {'Yes' if plan['international_roaming'] else 'No'}\n"
            f"Description: {plan['description']}"
        )


class NetworkIncidentsInput(BaseModel):
    """Input schema for network incidents tool"""
    region: str = Field(
        default="",
        description="Optional region to filter incidents (e.g., 'Mumbai', 'Delhi'). Leave empty for all incidents."
    )


class NetworkIncidentsTool(BaseTool):
    name: str = "list_network_incidents"
    description: str = (
        "Lists active network incidents including outages, degradations, and maintenance. "
        "Shows incident type, location, affected services (4G/5G/Voice/SMS), "
        "start time, status, and severity. Optionally filter by region. "
        "Use this for network troubleshooting."
    )
    args_schema: Type[BaseModel] = NetworkIncidentsInput

    def _run(self, region: str = "") -> str:
        """Fetch network incidents from database"""
        incidents = list_active_incidents(region if region else None)
        if not incidents:
            location_text = f" in {region}" if region else ""
            return f"No active network incidents{location_text}. All services operating normally."
        
        result = f"Active network incidents ({len(incidents)} total):\n\n"
        for inc in incidents:
            result += (
                f"[{inc['incident_id']}] {inc['incident_type']} - {inc['severity']}\n"
                f"  Location: {inc['location']}\n"
                f"  Affected: {inc['affected_services']}\n"
                f"  Status: {inc['status']}\n"
                f"  Started: {inc['start_time']}\n\n"
            )
        return result.strip()


# ============================================================================
# NEW TOOLS - Support Tickets
# ============================================================================

class CustomerTicketsInput(BaseModel):
    """Input schema for customer tickets tool"""
    customer_id: str = Field(..., description="The customer ID to fetch ticket history for")


class CustomerTicketsTool(BaseTool):
    name: str = "get_customer_tickets"
    description: str = (
        "Fetches support ticket history for a customer including past issues, "
        "resolutions, and resolution notes. Use this to check if customer had "
        "similar issues before and how they were resolved."
    )
    args_schema: Type[BaseModel] = CustomerTicketsInput

    def _run(self, customer_id: str) -> str:
        """Fetch customer ticket history"""
        tickets = get_customer_tickets(customer_id)
        if not tickets:
            return f"No support tickets found for customer {customer_id}."
        
        result = f"Support ticket history for {customer_id} ({len(tickets)} tickets):\n\n"
        for ticket in tickets:
            result += (
                f"[{ticket['ticket_id']}] {ticket['issue_category']} - {ticket['status']}\n"
                f"  Issue: {ticket['issue_description']}\n"
                f"  Created: {ticket['creation_time']}\n"
                f"  Priority: {ticket['priority']}\n"
            )
            if ticket['resolution_notes']:
                result += f"  Resolution: {ticket['resolution_notes']}\n"
            result += "\n"
        return result.strip()


class SearchTicketsInput(BaseModel):
    """Input schema for searching tickets by category"""
    category: str = Field(..., description="The issue category to search (e.g., 'Billing', 'Connectivity', 'Service')")


class SearchTicketsTool(BaseTool):
    name: str = "search_past_tickets"
    description: str = (
        "Search resolved support tickets by issue category to find common solutions. "
        "Use this to reference past resolutions for similar problems."
    )
    args_schema: Type[BaseModel] = SearchTicketsInput

    def _run(self, category: str) -> str:
        """Search tickets by category"""
        tickets = search_tickets_by_category(category)
        if not tickets:
            return f"No resolved tickets found for category: {category}"
        
        result = f"Past resolutions for {category} issues ({len(tickets)} found):\n\n"
        for ticket in tickets[:5]:  # Limit to top 5
            result += (
                f"[{ticket['ticket_id']}] {ticket['issue_description'][:80]}...\n"
                f"  Resolution: {ticket['resolution_notes'][:100]}...\n"
                f"  Priority: {ticket['priority']}\n\n"
            )
        return result.strip()


# ============================================================================
# NEW TOOLS - Common Network Issues
# ============================================================================

class NetworkIssueSearchInput(BaseModel):
    """Input schema for network issue search"""
    keyword: str = Field(..., description="Keyword to search in issue descriptions (e.g., 'call', 'data', 'signal')")


class NetworkIssueSearchTool(BaseTool):
    name: str = "search_network_issues_kb"
    description: str = (
        "Search knowledge base of common network issues with structured troubleshooting steps. "
        "Returns issue descriptions, symptoms, and proven resolution approaches. "
        "Use this to get structured troubleshooting guidance."
    )
    args_schema: Type[BaseModel] = NetworkIssueSearchInput

    def _run(self, keyword: str) -> str:
        """Search common network issues"""
        issues = search_common_network_issues(keyword)
        if not issues:
            return f"No common network issues found matching: {keyword}"
        
        result = f"Common network issues matching '{keyword}' ({len(issues)} found):\n\n"
        for issue in issues:
            result += (
                f"[{issue['issue_category']}]\n"
                f"Description: {issue['issue_description']}\n"
                f"Affects: {issue['affected_technologies']} - {issue['affected_services']}\n"
                f"Symptoms: {issue['typical_symptoms'][:100]}...\n"
                f"Steps: {issue['troubleshooting_steps'][:150]}...\n\n"
            )
        return result.strip()


class TroubleshootingStepsInput(BaseModel):
    """Input schema for getting troubleshooting steps"""
    issue_category: str = Field(..., description="Issue category (e.g., 'Call Failure', 'Data Connectivity')")


class TroubleshootingStepsTool(BaseTool):
    name: str = "get_troubleshooting_guide"
    description: str = (
        "Get detailed step-by-step troubleshooting guide for a specific issue category. "
        "Returns structured steps and resolution approach from knowledge base."
    )
    args_schema: Type[BaseModel] = TroubleshootingStepsInput

    def _run(self, issue_category: str) -> str:
        """Get troubleshooting steps"""
        steps = get_troubleshooting_steps(issue_category)
        if not steps:
            return f"No troubleshooting guide found for: {issue_category}"
        
        return (
            f"Troubleshooting Guide: {steps['issue_category']}\n\n"
            f"Affected Technologies: {steps['affected_technologies']}\n\n"
            f"Steps:\n{steps['troubleshooting_steps']}\n\n"
            f"Resolution Approach:\n{steps['resolution_approach']}"
        )


# ============================================================================
# NEW TOOLS - Device Compatibility
# ============================================================================

class DeviceCompatibilityInput(BaseModel):
    """Input schema for device compatibility"""
    device_make: str = Field(..., description="Device manufacturer (e.g., 'Samsung', 'Apple', 'OnePlus')")
    device_model: str = Field(default="", description="Optional device model (e.g., 'Galaxy S21', 'iPhone 12')")


class DeviceCompatibilityTool(BaseTool):
    name: str = "check_device_compatibility"
    description: str = (
        "Check device compatibility, known issues, and recommended settings for specific devices. "
        "Use this for device-specific troubleshooting."
    )
    args_schema: Type[BaseModel] = DeviceCompatibilityInput

    def _run(self, device_make: str, device_model: str = "") -> str:
        """Get device compatibility info"""
        devices = get_device_compatibility(device_make, device_model if device_model else None)
        if not devices:
            return f"No compatibility information found for {device_make} {device_model}"
        
        result = f"Device compatibility info for {device_make}:\n\n"
        for device in devices:
            result += (
                f"{device['device_make']} {device['device_model']} (OS: {device['os_version']})\n"
                f"  Network: {device['network_technology']}\n"
                f"  Known Issues: {device['known_issues']}\n"
                f"  Recommended Settings: {device['recommended_settings']}\n\n"
            )
        return result.strip()


# ============================================================================
# NEW TOOLS - Service Areas & Coverage
# ============================================================================

class ServiceAreasInput(BaseModel):
    """Input schema for service areas"""
    city: str = Field(default="", description="City name (e.g., 'Mumbai', 'Delhi', 'Bangalore'). Leave empty for all.")


class ServiceAreasTool(BaseTool):
    name: str = "get_service_area_info"
    description: str = (
        "Get service area information including districts, terrain types, and population density. "
        "Use this to understand coverage characteristics of different areas."
    )
    args_schema: Type[BaseModel] = ServiceAreasInput

    def _run(self, city: str = "") -> str:
        """Get service area information"""
        areas = get_service_areas(city if city else None)
        if not areas:
            return f"No service area information found for: {city}"
        
        result = f"Service areas{' in ' + city if city else ''} ({len(areas)} found):\n\n"
        for area in areas:
            result += (
                f"{area['city']} - {area['district']}\n"
                f"  Region: {area['region']}, Postal: {area['postal_code']}\n"
                f"  Density: {area['population_density']}, Terrain: {area['terrain_type']}\n\n"
            )
        return result.strip()


class CoverageQualityInput(BaseModel):
    """Input schema for coverage quality"""
    technology: str = Field(default="", description="Technology type ('4G' or '5G'). Leave empty for all.")


class CoverageQualityTool(BaseTool):
    name: str = "check_coverage_quality"
    description: str = (
        "Check coverage quality metrics including signal strength, download/upload speeds, and latency. "
        "Use this to understand expected performance in different areas."
    )
    args_schema: Type[BaseModel] = CoverageQualityInput

    def _run(self, technology: str = "") -> str:
        """Get coverage quality metrics"""
        coverage = get_coverage_quality(technology=technology if technology else None)
        if not coverage:
            return "No coverage quality data available."
        
        result = f"Coverage quality{' for ' + technology if technology else ''} ({len(coverage)} records):\n\n"
        for cov in coverage[:10]:  # Limit to 10 records
            result += (
                f"{cov['area_id']} - {cov['technology']}: {cov['signal_strength_category']}\n"
                f"  Download: {cov['avg_download_speed_mbps']} Mbps, Upload: {cov['avg_upload_speed_mbps']} Mbps\n"
                f"  Latency: {cov['avg_latency_ms']} ms\n\n"
            )
        return result.strip()


# ============================================================================
# NEW TOOLS - Cell Towers & Technologies
# ============================================================================

class CellTowersInput(BaseModel):
    """Input schema for cell towers"""
    area_id: str = Field(default="", description="Area ID (e.g., 'AREA001'). Leave empty for all towers.")


class CellTowersTool(BaseTool):
    name: str = "get_tower_info"
    description: str = (
        "Get cell tower information including locations, types, and operational status. "
        "Use this for infrastructure-related queries."
    )
    args_schema: Type[BaseModel] = CellTowersInput

    def _run(self, area_id: str = "") -> str:
        """Get cell tower information"""
        towers = get_cell_towers(area_id if area_id else None)
        if not towers:
            return "No cell tower information available."
        
        result = f"Cell towers{' in ' + area_id if area_id else ''} ({len(towers)} found):\n\n"
        for tower in towers[:10]:
            result += (
                f"{tower['tower_id']} - {tower['tower_type']}\n"
                f"  Location: {tower['latitude']}, {tower['longitude']}\n"
                f"  Height: {tower['height_meters']}m, Status: {tower['operational_status']}\n\n"
            )
        return result.strip()


class TowerTechnologiesInput(BaseModel):
    """Input schema for tower technologies"""
    tower_id: str = Field(default="", description="Tower ID (e.g., 'TWR001'). Leave empty for all.")


class TowerTechnologiesTool(BaseTool):
    name: str = "check_tower_technologies"
    description: str = (
        "Check which technologies (4G/5G) are available on specific towers with frequency bands. "
        "Use this to verify technology availability in an area."
    )
    args_schema: Type[BaseModel] = TowerTechnologiesInput

    def _run(self, tower_id: str = "") -> str:
        """Get tower technology details"""
        tech = get_tower_technologies(tower_id if tower_id else None)
        if not tech:
            return "No tower technology information available."
        
        result = f"Tower technologies{' for ' + tower_id if tower_id else ''} ({len(tech)} found):\n\n"
        for t in tech[:15]:
            result += (
                f"{t['tower_id']}: {t['technology']} - {t['frequency_band']}\n"
                f"  Bandwidth: {t['bandwidth_mhz']} MHz, Max Speed: {t['max_capacity_mbps']} Mbps\n\n"
            )
        return result.strip()


# ============================================================================
# NEW TOOLS - Transportation & Buildings
# ============================================================================

class TransportationRoutesInput(BaseModel):
    """Input schema for transportation routes"""
    route_type: str = Field(default="", description="Route type ('Train', 'Metro', 'Bus'). Leave empty for all.")


class TransportationRoutesTool(BaseTool):
    name: str = "check_transit_coverage"
    description: str = (
        "Check mobile coverage quality on transportation routes (trains, metro, buses). "
        "Includes known connectivity issues on specific routes."
    )
    args_schema: Type[BaseModel] = TransportationRoutesInput

    def _run(self, route_type: str = "") -> str:
        """Get transportation route coverage"""
        routes = get_transportation_routes(route_type if route_type else None)
        if not routes:
            return "No transportation route information available."
        
        result = f"Transportation routes{' (' + route_type + ')' if route_type else ''} ({len(routes)} found):\n\n"
        for route in routes:
            result += (
                f"{route['route_name']} ({route['route_type']})\n"
                f"  {route['start_point']} to {route['end_point']}\n"
                f"  Coverage: {route['coverage_quality']}\n"
                f"  Known Issues: {route['known_issues']}\n\n"
            )
        return result.strip()


class BuildingTypesInput(BaseModel):
    """Input schema for building types"""
    building_category: str = Field(default="", description="Building category (e.g., 'Apartment', 'Office', 'Basement')")


class BuildingTypesTool(BaseTool):
    name: str = "check_building_coverage"
    description: str = (
        "Check signal characteristics for different building types including signal reduction "
        "and recommended solutions for indoor coverage issues."
    )
    args_schema: Type[BaseModel] = BuildingTypesInput

    def _run(self, building_category: str = "") -> str:
        """Get building type signal information"""
        buildings = get_building_types(building_category if building_category else None)
        if not buildings:
            return "No building type information available."
        
        result = f"Building types{' matching ' + building_category if building_category else ''} ({len(buildings)} found):\n\n"
        for bldg in buildings:
            result += (
                f"{bldg['building_category']} ({bldg['construction_material']})\n"
                f"  Signal Reduction: {bldg['avg_signal_reduction_percent']}%\n"
                f"  Solutions: {bldg['recommended_solutions']}\n\n"
            )
        return result.strip()


def get_all_crewai_tools():
    """Returns list of all CrewAI-compatible database tools"""
    try:
        return [
            # Original tools
            CustomerDataTool(),
            UsageDataTool(),
            ServicePlanTool(),
            NetworkIncidentsTool(),
            # New tools - Support Tickets
            CustomerTicketsTool(),
            SearchTicketsTool(),
            # New tools - Network Issues
            NetworkIssueSearchTool(),
            TroubleshootingStepsTool(),
            # New tools - Device
            DeviceCompatibilityTool(),
            # New tools - Coverage
            ServiceAreasTool(),
            CoverageQualityTool(),
            # New tools - Infrastructure
            CellTowersTool(),
            TowerTechnologiesTool(),
            # New tools - Transportation & Buildings
            TransportationRoutesTool(),
            BuildingTypesTool(),
        ]
    except Exception:
        # If CrewAI not properly installed, return empty list
        return []
