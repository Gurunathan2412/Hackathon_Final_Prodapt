# Database utilities
import sqlite3
from typing import Any, Dict, List, Tuple, Optional
from config.config import SQLITE_DB_PATH

def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(SQLITE_DB_PATH)


def fetch_one(query: str, params: Tuple = ()) -> Optional[Tuple]:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(query, params)
        return cur.fetchone()
    finally:
        con.close()


def fetch_all(query: str, params: Tuple = ()) -> List[Tuple]:
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        con.close()


def get_customer_usage(customer_id: str) -> List[Dict[str, Any]]:
    rows = fetch_all(
        "SELECT billing_period_start, billing_period_end, data_used_gb, voice_minutes_used, sms_count_used, additional_charges, total_bill_amount FROM customer_usage WHERE customer_id = ? ORDER BY billing_period_start DESC",
        (customer_id,),
    )
    return [
        {
            'billing_period_start': r[0],
            'billing_period_end': r[1],
            'data_used_gb': r[2],
            'voice_minutes_used': r[3],
            'sms_count_used': r[4],
            'additional_charges': r[5],
            'total_bill_amount': r[6],
        } for r in rows
    ]


def get_service_plan(plan_id: str) -> Optional[Dict[str, Any]]:
    row = fetch_one("SELECT plan_id, name, monthly_cost, data_limit_gb, unlimited_data, voice_minutes, unlimited_voice, sms_count, unlimited_sms, contract_duration_months, early_termination_fee, international_roaming, description FROM service_plans WHERE plan_id = ?", (plan_id,))
    if not row:
        return None
    keys = ['plan_id','name','monthly_cost','data_limit_gb','unlimited_data','voice_minutes','unlimited_voice','sms_count','unlimited_sms','contract_duration_months','early_termination_fee','international_roaming','description']
    return dict(zip(keys, row))


def get_customer(customer_id: str) -> Optional[Dict[str, Any]]:
    row = fetch_one("SELECT customer_id, name, email, phone_number, address, service_plan_id, account_status, registration_date, last_billing_date FROM customers WHERE customer_id = ?", (customer_id,))
    if not row:
        return None
    keys = ['customer_id','name','email','phone_number','address','service_plan_id','account_status','registration_date','last_billing_date']
    return dict(zip(keys, row))


def get_covered_regions() -> List[str]:
    """Get list of regions we have network monitoring for"""
    rows = fetch_all("SELECT DISTINCT location FROM network_incidents")
    return [r[0] for r in rows]


def list_active_incidents(region: Optional[str] = None) -> List[Dict[str, Any]]:
    if region:
        rows = fetch_all("SELECT incident_id, incident_type, location, affected_services, start_time, status, severity FROM network_incidents WHERE status != 'Resolved' AND location LIKE ?", (f"%{region}%",))
    else:
        rows = fetch_all("SELECT incident_id, incident_type, location, affected_services, start_time, status, severity FROM network_incidents WHERE status != 'Resolved'")
    return [
        {
            'incident_id': r[0],
            'incident_type': r[1],
            'location': r[2],
            'affected_services': r[3],
            'start_time': r[4],
            'status': r[5],
            'severity': r[6],
        } for r in rows
    ]


def list_customers(limit: int = 50) -> List[Dict[str, Any]]:
    rows = fetch_all("SELECT customer_id, name FROM customers LIMIT ?", (limit,))
    return [{"customer_id": r[0], "name": r[1]} for r in rows]


# ============================================================================
# NEW FUNCTIONS - Support Tickets
# ============================================================================

def get_customer_tickets(customer_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get support ticket history for a customer, optionally filtered by status"""
    if status:
        rows = fetch_all(
            "SELECT ticket_id, issue_category, issue_description, creation_time, resolution_time, status, priority, resolution_notes FROM support_tickets WHERE customer_id = ? AND status = ? ORDER BY creation_time DESC",
            (customer_id, status)
        )
    else:
        rows = fetch_all(
            "SELECT ticket_id, issue_category, issue_description, creation_time, resolution_time, status, priority, resolution_notes FROM support_tickets WHERE customer_id = ? ORDER BY creation_time DESC",
            (customer_id,)
        )
    return [
        {
            'ticket_id': r[0],
            'issue_category': r[1],
            'issue_description': r[2],
            'creation_time': r[3],
            'resolution_time': r[4],
            'status': r[5],
            'priority': r[6],
            'resolution_notes': r[7],
        } for r in rows
    ]


def get_all_support_tickets(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all support tickets across all customers (for admin view), optionally filtered by status"""
    if status:
        rows = fetch_all(
            """SELECT t.ticket_id, t.customer_id, c.name as customer_name, t.issue_category, 
               t.issue_description, t.creation_time, t.resolution_time, t.status, t.priority, 
               t.resolution_notes 
               FROM support_tickets t 
               JOIN customers c ON t.customer_id = c.customer_id 
               WHERE t.status = ? 
               ORDER BY t.creation_time DESC""",
            (status,)
        )
    else:
        rows = fetch_all(
            """SELECT t.ticket_id, t.customer_id, c.name as customer_name, t.issue_category, 
               t.issue_description, t.creation_time, t.resolution_time, t.status, t.priority, 
               t.resolution_notes 
               FROM support_tickets t 
               JOIN customers c ON t.customer_id = c.customer_id 
               ORDER BY t.creation_time DESC"""
        )
    return [
        {
            'ticket_id': r[0],
            'customer_id': r[1],
            'customer_name': r[2],
            'issue_category': r[3],
            'issue_description': r[4],
            'creation_time': r[5],
            'resolution_time': r[6],
            'status': r[7],
            'priority': r[8],
            'resolution_notes': r[9],
        } for r in rows
    ]


def execute_query(query: str, params: Tuple = ()) -> int:
    """Execute INSERT/UPDATE/DELETE and return affected rows"""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(query, params)
        con.commit()
        return cur.rowcount
    finally:
        con.close()


def create_support_ticket(customer_id: str, category: str, description: str, priority: str) -> str:
    """Create a new support ticket"""
    import time
    ticket_id = f"TKT{str(int(time.time()))[-6:]}"
    
    execute_query(
        """INSERT INTO support_tickets 
           (ticket_id, customer_id, issue_category, issue_description, 
            priority, status, creation_time) 
           VALUES (?, ?, ?, ?, ?, 'Open', datetime('now'))""",
        (ticket_id, customer_id, category, description, priority)
    )
    
    return ticket_id


def update_ticket_status(ticket_id: str, status: str, resolution_notes: Optional[str] = None) -> None:
    """Update ticket status and optionally add resolution notes"""
    if status == "Resolved":
        execute_query(
            """UPDATE support_tickets 
               SET status = ?, resolution_notes = ?, resolution_time = datetime('now') 
               WHERE ticket_id = ?""",
            (status, resolution_notes or "", ticket_id)
        )
    else:
        execute_query(
            "UPDATE support_tickets SET status = ? WHERE ticket_id = ?",
            (status, ticket_id)
        )


def search_tickets_by_category(category: str) -> List[Dict[str, Any]]:
    """Search resolved tickets by issue category for common resolutions"""
    rows = fetch_all(
        "SELECT ticket_id, customer_id, issue_description, resolution_notes, priority FROM support_tickets WHERE issue_category LIKE ? AND status = 'Resolved' ORDER BY creation_time DESC LIMIT 10",
        (f"%{category}%",)
    )
    return [
        {
            'ticket_id': r[0],
            'customer_id': r[1],
            'issue_description': r[2],
            'resolution_notes': r[3],
            'priority': r[4],
        } for r in rows
    ]


# ============================================================================
# NEW FUNCTIONS - Common Network Issues
# ============================================================================

def search_common_network_issues(keyword: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search common network issues by keyword or get all"""
    if keyword:
        rows = fetch_all(
            "SELECT issue_id, issue_category, issue_description, affected_technologies, affected_services, typical_symptoms, troubleshooting_steps, resolution_approach FROM common_network_issues WHERE issue_category LIKE ? OR issue_description LIKE ? OR typical_symptoms LIKE ?",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")
        )
    else:
        rows = fetch_all(
            "SELECT issue_id, issue_category, issue_description, affected_technologies, affected_services, typical_symptoms, troubleshooting_steps, resolution_approach FROM common_network_issues"
        )
    return [
        {
            'issue_id': r[0],
            'issue_category': r[1],
            'issue_description': r[2],
            'affected_technologies': r[3],
            'affected_services': r[4],
            'typical_symptoms': r[5],
            'troubleshooting_steps': r[6],
            'resolution_approach': r[7],
        } for r in rows
    ]


def get_troubleshooting_steps(issue_category: str) -> Optional[Dict[str, Any]]:
    """Get detailed troubleshooting steps for a specific issue category"""
    row = fetch_one(
        "SELECT issue_id, issue_category, troubleshooting_steps, resolution_approach, affected_technologies FROM common_network_issues WHERE issue_category LIKE ? LIMIT 1",
        (f"%{issue_category}%",)
    )
    if not row:
        return None
    return {
        'issue_id': row[0],
        'issue_category': row[1],
        'troubleshooting_steps': row[2],
        'resolution_approach': row[3],
        'affected_technologies': row[4],
    }


# ============================================================================
# NEW FUNCTIONS - Device Compatibility
# ============================================================================

def get_device_compatibility(device_make: Optional[str] = None, device_model: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get device compatibility information and known issues"""
    if device_make and device_model:
        rows = fetch_all(
            "SELECT compatibility_id, device_make, device_model, os_version, network_technology, known_issues, recommended_settings FROM device_compatibility WHERE device_make LIKE ? AND device_model LIKE ?",
            (f"%{device_make}%", f"%{device_model}%")
        )
    elif device_make:
        rows = fetch_all(
            "SELECT compatibility_id, device_make, device_model, os_version, network_technology, known_issues, recommended_settings FROM device_compatibility WHERE device_make LIKE ?",
            (f"%{device_make}%",)
        )
    else:
        rows = fetch_all(
            "SELECT compatibility_id, device_make, device_model, os_version, network_technology, known_issues, recommended_settings FROM device_compatibility"
        )
    return [
        {
            'compatibility_id': r[0],
            'device_make': r[1],
            'device_model': r[2],
            'os_version': r[3],
            'network_technology': r[4],
            'known_issues': r[5],
            'recommended_settings': r[6],
        } for r in rows
    ]


# ============================================================================
# NEW FUNCTIONS - Service Areas & Coverage
# ============================================================================

def get_service_areas(city: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get service area information by city or all areas"""
    if city:
        rows = fetch_all(
            "SELECT area_id, city, district, postal_code, region, population_density, terrain_type FROM service_areas WHERE city LIKE ?",
            (f"%{city}%",)
        )
    else:
        rows = fetch_all(
            "SELECT area_id, city, district, postal_code, region, population_density, terrain_type FROM service_areas"
        )
    return [
        {
            'area_id': r[0],
            'city': r[1],
            'district': r[2],
            'postal_code': r[3],
            'region': r[4],
            'population_density': r[5],
            'terrain_type': r[6],
        } for r in rows
    ]


def get_coverage_quality(area_id: Optional[str] = None, technology: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get coverage quality metrics for an area and/or technology"""
    if area_id and technology:
        rows = fetch_all(
            "SELECT coverage_id, area_id, technology, signal_strength_category, avg_download_speed_mbps, avg_upload_speed_mbps, avg_latency_ms FROM coverage_quality WHERE area_id = ? AND technology = ?",
            (area_id, technology)
        )
    elif area_id:
        rows = fetch_all(
            "SELECT coverage_id, area_id, technology, signal_strength_category, avg_download_speed_mbps, avg_upload_speed_mbps, avg_latency_ms FROM coverage_quality WHERE area_id = ?",
            (area_id,)
        )
    elif technology:
        rows = fetch_all(
            "SELECT coverage_id, area_id, technology, signal_strength_category, avg_download_speed_mbps, avg_upload_speed_mbps, avg_latency_ms FROM coverage_quality WHERE technology = ?",
            (technology,)
        )
    else:
        rows = fetch_all(
            "SELECT coverage_id, area_id, technology, signal_strength_category, avg_download_speed_mbps, avg_upload_speed_mbps, avg_latency_ms FROM coverage_quality"
        )
    return [
        {
            'coverage_id': r[0],
            'area_id': r[1],
            'technology': r[2],
            'signal_strength_category': r[3],
            'avg_download_speed_mbps': r[4],
            'avg_upload_speed_mbps': r[5],
            'avg_latency_ms': r[6],
        } for r in rows
    ]


# ============================================================================
# NEW FUNCTIONS - Cell Towers
# ============================================================================

def get_cell_towers(area_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get cell tower information for an area"""
    if area_id:
        rows = fetch_all(
            "SELECT tower_id, area_id, latitude, longitude, tower_type, height_meters, operational_status FROM cell_towers WHERE area_id = ?",
            (area_id,)
        )
    else:
        rows = fetch_all(
            "SELECT tower_id, area_id, latitude, longitude, tower_type, height_meters, operational_status FROM cell_towers"
        )
    return [
        {
            'tower_id': r[0],
            'area_id': r[1],
            'latitude': r[2],
            'longitude': r[3],
            'tower_type': r[4],
            'height_meters': r[5],
            'operational_status': r[6],
        } for r in rows
    ]


def get_tower_technologies(tower_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get technology details for towers"""
    if tower_id:
        rows = fetch_all(
            "SELECT tower_tech_id, tower_id, technology, frequency_band, bandwidth_mhz, max_capacity_mbps, active FROM tower_technologies WHERE tower_id = ? AND active = 1",
            (tower_id,)
        )
    else:
        rows = fetch_all(
            "SELECT tower_tech_id, tower_id, technology, frequency_band, bandwidth_mhz, max_capacity_mbps, active FROM tower_technologies WHERE active = 1"
        )
    return [
        {
            'tower_tech_id': r[0],
            'tower_id': r[1],
            'technology': r[2],
            'frequency_band': r[3],
            'bandwidth_mhz': r[4],
            'max_capacity_mbps': r[5],
            'active': r[6],
        } for r in rows
    ]


# ============================================================================
# NEW FUNCTIONS - Transportation & Buildings
# ============================================================================

def get_transportation_routes(route_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get transportation route coverage information"""
    if route_type:
        rows = fetch_all(
            "SELECT route_id, route_name, route_type, start_point, end_point, coverage_quality, known_issues FROM transportation_routes WHERE route_type LIKE ?",
            (f"%{route_type}%",)
        )
    else:
        rows = fetch_all(
            "SELECT route_id, route_name, route_type, start_point, end_point, coverage_quality, known_issues FROM transportation_routes"
        )
    return [
        {
            'route_id': r[0],
            'route_name': r[1],
            'route_type': r[2],
            'start_point': r[3],
            'end_point': r[4],
            'coverage_quality': r[5],
            'known_issues': r[6],
        } for r in rows
    ]


def get_building_types(building_category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get building type signal characteristics and recommendations"""
    if building_category:
        rows = fetch_all(
            "SELECT building_type_id, building_category, construction_material, avg_signal_reduction_percent, recommended_solutions FROM building_types WHERE building_category LIKE ?",
            (f"%{building_category}%",)
        )
    else:
        rows = fetch_all(
            "SELECT building_type_id, building_category, construction_material, avg_signal_reduction_percent, recommended_solutions FROM building_types"
        )
    return [
        {
            'building_type_id': r[0],
            'building_category': r[1],
            'construction_material': r[2],
            'avg_signal_reduction_percent': r[3],
            'recommended_solutions': r[4],
        } for r in rows
    ]
