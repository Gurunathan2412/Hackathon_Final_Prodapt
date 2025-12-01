# Database Architecture - SQLite Schema & Data Model

## Overview

The Telecom Service Assistant uses **SQLite 3.x** as its relational database, storing customer data, billing records, usage history, service plans, and operational data. The database contains **13 tables** with approximately **300 records** total.

---

## Database Location

**File**: `data/telecom.db`

**Connection String**: `sqlite:///data/telecom.db`

**Size**: ~500 KB

**Format**: SQLite 3.x

---

## Schema Overview

### Entity-Relationship Diagram

```
┌────────────┐         ┌──────────────┐         ┌────────────┐
│ customers  │────────>│ service_plans│<────────│ promotions │
└─────┬──────┘         └──────────────┘         └────────────┘
      │                                          
      │                                          
      ├──────>┌──────────────┐
      │       │    bills     │
      │       └──────────────┘
      │       
      ├──────>┌──────────────┐
      │       │ usage_history│
      │       └──────────────┘
      │       
      ├──────>┌──────────────┐
      │       │   payments   │
      │       └──────────────┘
      │       
      ├──────>┌──────────────┐
      │       │    devices   │
      │       └──────────────┘
      │       
      └──────>┌──────────────────┐
              │ support_tickets  │
              └──────────────────┘

┌────────────────────┐    ┌───────────────┐
│ network_incidents  │    │ coverage_areas│
└────────────────────┘    └───────────────┘

┌─────────────┐  ┌─────────────┐  ┌───────────┐
│ data_usage  │  │ voice_usage │  │ sms_usage │
└─────────────┘  └─────────────┘  └───────────┘
```

---

## Table Schemas

### 1. customers

**Purpose**: Store customer profile information

**Schema**:
```sql
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    registration_date TEXT,
    service_plan_id TEXT,
    account_status TEXT CHECK(account_status IN ('active', 'suspended', 'inactive')),
    FOREIGN KEY (service_plan_id) REFERENCES service_plans(plan_id)
);
```

**Sample Data**:
```
customer_id: CUST001
name: John Doe
email: john.doe@email.com
phone: 555-0101
address: 123 Main St
city: Boston
state: MA
zip_code: 02101
registration_date: 2023-01-15
service_plan_id: PLAN002
account_status: active
```

**Record Count**: ~20 customers

**Indexes**:
- Primary key: `customer_id`
- Unique: `email`
- Foreign key: `service_plan_id`

### 2. service_plans

**Purpose**: Define available service plans and pricing

**Schema**:
```sql
CREATE TABLE service_plans (
    plan_id TEXT PRIMARY KEY,
    plan_name TEXT NOT NULL,
    monthly_cost REAL NOT NULL,
    data_limit_gb INTEGER,
    voice_minutes INTEGER,
    sms_limit INTEGER,
    overage_rate_per_gb REAL,
    description TEXT,
    is_5g_enabled BOOLEAN DEFAULT 0
);
```

**Sample Data**:
```
plan_id: PLAN002
plan_name: Premium 50GB
monthly_cost: 79.99
data_limit_gb: 50
voice_minutes: 1000
sms_limit: 500
overage_rate_per_gb: 5.00
description: Premium plan with 50GB data, 1000 minutes, 500 SMS
is_5g_enabled: 1
```

**Available Plans**:
1. **PLAN001**: Basic 10GB - $29.99/month
2. **PLAN002**: Premium 50GB - $79.99/month
3. **PLAN003**: Premium 100GB - $99.99/month
4. **PLAN004**: Unlimited - $119.99/month
5. **PLAN005**: Family Plan - $149.99/month

**Record Count**: 5 plans

### 3. bills

**Purpose**: Store monthly billing records

**Schema**:
```sql
CREATE TABLE bills (
    bill_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    billing_period_start TEXT NOT NULL,
    billing_period_end TEXT NOT NULL,
    base_charge REAL NOT NULL,
    data_overage_charge REAL DEFAULT 0,
    voice_overage_charge REAL DEFAULT 0,
    sms_overage_charge REAL DEFAULT 0,
    taxes REAL DEFAULT 0,
    total_amount REAL NOT NULL,
    payment_status TEXT CHECK(payment_status IN ('paid', 'pending', 'overdue')),
    due_date TEXT NOT NULL,
    payment_date TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

**Sample Data**:
```
bill_id: BILL035
customer_id: CUST001
billing_period_start: 2024-12-01
billing_period_end: 2024-12-31
base_charge: 79.99
data_overage_charge: 10.00
voice_overage_charge: 0.00
sms_overage_charge: 0.00
taxes: 0.00
total_amount: 89.99
payment_status: paid
due_date: 2024-12-15
payment_date: 2024-12-10
```

**Record Count**: ~60 bills (3 months × ~20 customers)

**Payment Status Distribution**:
- Paid: ~52 bills
- Pending: ~5 bills
- Overdue: ~3 bills

### 4. usage_history

**Purpose**: Track customer usage by month

**Schema**:
```sql
CREATE TABLE usage_history (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    month TEXT NOT NULL,
    data_used_gb REAL DEFAULT 0,
    voice_minutes_used INTEGER DEFAULT 0,
    sms_count INTEGER DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

**Sample Data**:
```
usage_id: 45
customer_id: CUST001
month: 2024-12
data_used_gb: 52.3
voice_minutes_used: 450
sms_count: 200
```

**Record Count**: ~60 usage records (3 months × ~20 customers)

**Usage Patterns**:
- Average data: 35-55 GB/month
- Average voice: 300-600 minutes/month
- Average SMS: 100-300/month

### 5. payments

**Purpose**: Track payment transactions

**Schema**:
```sql
CREATE TABLE payments (
    payment_id TEXT PRIMARY KEY,
    bill_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    payment_date TEXT NOT NULL,
    amount REAL NOT NULL,
    payment_method TEXT CHECK(payment_method IN ('credit_card', 'debit_card', 'bank_transfer', 'cash')),
    transaction_id TEXT,
    status TEXT CHECK(status IN ('completed', 'pending', 'failed')),
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

**Sample Data**:
```
payment_id: PAY001
bill_id: BILL035
customer_id: CUST001
payment_date: 2024-12-10
amount: 89.99
payment_method: credit_card
transaction_id: TXN20241210001
status: completed
```

**Record Count**: ~55 payments

**Payment Methods**:
- Credit Card: 70%
- Bank Transfer: 20%
- Debit Card: 10%

### 6. devices

**Purpose**: Store customer device information

**Schema**:
```sql
CREATE TABLE devices (
    device_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    device_type TEXT CHECK(device_type IN ('phone', 'router', 'modem', 'tablet')),
    brand TEXT,
    model TEXT,
    imei TEXT,
    activation_date TEXT,
    status TEXT CHECK(status IN ('active', 'inactive', 'replaced')),
    firmware_version TEXT,
    signal_strength INTEGER,
    location TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

**Sample Data**:
```
device_id: DEV001
customer_id: CUST001
device_type: router
brand: Netgear
model: XR500
imei: 123456789012345
activation_date: 2023-01-20
status: active
firmware_version: v1.2.3
signal_strength: -65
location: Home - Main Floor
```

**Record Count**: ~25 devices

**Device Types**:
- Routers: 15
- Phones: 7
- Modems: 2
- Tablets: 1

### 7. support_tickets

**Purpose**: Track customer support requests

**Schema**:
```sql
CREATE TABLE support_tickets (
    ticket_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    issue_category TEXT CHECK(issue_category IN ('billing', 'technical', 'account', 'network')),
    description TEXT NOT NULL,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    status TEXT CHECK(status IN ('open', 'in_progress', 'resolved', 'closed')),
    created_date TEXT NOT NULL,
    resolved_date TEXT,
    assigned_to TEXT,
    resolution_notes TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

**Sample Data**:
```
ticket_id: TICK001
customer_id: CUST001
issue_category: network
description: Slow internet speed in the evening
priority: medium
status: resolved
created_date: 2024-11-20
resolved_date: 2024-11-22
assigned_to: Tech Support Team
resolution_notes: Upgraded router firmware, issue resolved
```

**Record Count**: ~15 tickets

**Status Distribution**:
- Resolved: 10
- In Progress: 3
- Open: 2

### 8. network_incidents

**Purpose**: Track network outages and incidents

**Schema**:
```sql
CREATE TABLE network_incidents (
    incident_id TEXT PRIMARY KEY,
    issue_type TEXT NOT NULL,
    affected_area TEXT NOT NULL,
    severity TEXT CHECK(severity IN ('minor', 'major', 'critical')),
    status TEXT CHECK(status IN ('active', 'investigating', 'resolved')),
    reported_time TEXT NOT NULL,
    resolved_time TEXT,
    estimated_resolution TEXT,
    description TEXT
);
```

**Sample Data**:
```
incident_id: INC001
issue_type: slow_data
affected_area: Downtown
severity: major
status: resolved
reported_time: 2024-12-01 10:30:00
resolved_time: 2024-12-01 14:45:00
estimated_resolution: 2 hours
description: Fiber cut affecting downtown area
```

**Record Count**: ~8 incidents (mostly resolved)

**Issue Types**:
- Outages: 3
- Slow speeds: 4
- Intermittent: 1

### 9. coverage_areas

**Purpose**: Define network coverage by location

**Schema**:
```sql
CREATE TABLE coverage_areas (
    area_id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    coverage_type TEXT CHECK(coverage_type IN ('5G', '4G', '3G')),
    signal_quality TEXT CHECK(signal_quality IN ('excellent', 'good', 'fair', 'poor')),
    avg_speed_mbps REAL,
    population_coverage_percent REAL
);
```

**Sample Data**:
```
area_id: 1
location_name: Downtown
city: Boston
state: MA
coverage_type: 5G
signal_quality: excellent
avg_speed_mbps: 85.5
population_coverage_percent: 95.0
```

**Record Count**: ~12 coverage areas

**Coverage Quality**:
- Excellent: 6 areas
- Good: 4 areas
- Fair: 2 areas

### 10. promotions

**Purpose**: Store active promotional offers

**Schema**:
```sql
CREATE TABLE promotions (
    promo_id TEXT PRIMARY KEY,
    promo_name TEXT NOT NULL,
    description TEXT,
    discount_percent REAL,
    discount_amount REAL,
    applicable_plan_id TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (applicable_plan_id) REFERENCES service_plans(plan_id)
);
```

**Sample Data**:
```
promo_id: PROMO001
promo_name: Summer Special
description: 20% off Premium plans for 3 months
discount_percent: 20.0
discount_amount: NULL
applicable_plan_id: PLAN002
start_date: 2024-06-01
end_date: 2024-08-31
is_active: 0
```

**Record Count**: ~5 promotions (2 active)

### 11. data_usage

**Purpose**: Detailed data usage breakdown

**Schema**:
```sql
CREATE TABLE data_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    date TEXT NOT NULL,
    upload_mb REAL DEFAULT 0,
    download_mb REAL DEFAULT 0,
    total_mb REAL DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

**Sample Data**:
```
usage_id: 123
customer_id: CUST001
date: 2024-12-15
upload_mb: 150.5
download_mb: 1200.3
total_mb: 1350.8
```

**Record Count**: ~200 daily records

### 12. voice_usage

**Purpose**: Detailed voice call usage

**Schema**:
```sql
CREATE TABLE voice_usage (
    call_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    call_date TEXT NOT NULL,
    call_type TEXT CHECK(call_type IN ('incoming', 'outgoing')),
    duration_minutes REAL,
    destination_number TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

**Sample Data**:
```
call_id: 456
customer_id: CUST001
call_date: 2024-12-15 14:30:00
call_type: outgoing
duration_minutes: 15.5
destination_number: 555-0199
```

**Record Count**: ~150 call records

### 13. sms_usage

**Purpose**: Detailed SMS usage

**Schema**:
```sql
CREATE TABLE sms_usage (
    sms_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    sms_date TEXT NOT NULL,
    sms_type TEXT CHECK(sms_type IN ('sent', 'received')),
    destination_number TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

**Sample Data**:
```
sms_id: 789
customer_id: CUST001
sms_date: 2024-12-15 16:45:00
sms_type: sent
destination_number: 555-0188
```

**Record Count**: ~100 SMS records

---

## Database Utilities

### Connection Management

**File**: `utils/database.py`

```python
import sqlite3
from typing import Dict, List, Any, Optional

def get_db_connection():
    """Get SQLite database connection."""
    return sqlite3.connect("data/telecom.db")

def query_db(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute query and return results as list of dicts."""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row  # Enable column access by name
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results
```

### Customer Functions

```python
def get_customer_info(customer_id: str) -> Optional[Dict[str, Any]]:
    """Get customer information by ID."""
    query = """
        SELECT c.*, sp.plan_name, sp.monthly_cost
        FROM customers c
        LEFT JOIN service_plans sp ON c.service_plan_id = sp.plan_id
        WHERE c.customer_id = ?
    """
    results = query_db(query, (customer_id,))
    return results[0] if results else None

def get_all_customers() -> List[Dict[str, Any]]:
    """Get all customers."""
    query = "SELECT * FROM customers WHERE account_status = 'active'"
    return query_db(query)
```

### Billing Functions

```python
def get_recent_bills(customer_id: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Get recent bills for a customer."""
    query = """
        SELECT *
        FROM bills
        WHERE customer_id = ?
        ORDER BY billing_period_start DESC
        LIMIT ?
    """
    return query_db(query, (customer_id, limit))

def get_bill_details(bill_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed bill information."""
    query = "SELECT * FROM bills WHERE bill_id = ?"
    results = query_db(query, (bill_id,))
    return results[0] if results else None
```

### Usage Functions

```python
def get_customer_usage(customer_id: str) -> List[Dict[str, Any]]:
    """Get usage history for a customer."""
    query = """
        SELECT *
        FROM usage_history
        WHERE customer_id = ?
        ORDER BY month DESC
    """
    return query_db(query, (customer_id,))

def get_data_usage(customer_id: str, month: str = None) -> Dict[str, Any]:
    """Get data usage for a customer in a specific month."""
    if month:
        query = """
            SELECT SUM(total_mb) / 1024.0 as total_gb
            FROM data_usage
            WHERE customer_id = ? AND date LIKE ?
        """
        results = query_db(query, (customer_id, f"{month}%"))
    else:
        query = """
            SELECT SUM(total_mb) / 1024.0 as total_gb
            FROM data_usage
            WHERE customer_id = ?
        """
        results = query_db(query, (customer_id,))
    
    return results[0] if results else {"total_gb": 0}
```

---

## Performance Considerations

### Indexing Strategy

**Primary Keys**: All tables have primary keys
**Foreign Keys**: Enforce referential integrity
**Unique Constraints**: On `customers.email`

**Query Performance**:
- Simple queries: < 10ms
- Complex joins: 10-50ms
- Full table scans: 50-100ms

### Connection Pooling

Currently using simple connection per query.

**Future Enhancement**: Implement connection pooling for concurrent requests.

---

## Data Initialization

### Sample Data Script

**File**: `utils/init_db.py` (not in repo, but used during setup)

```python
def initialize_database():
    """Initialize database with sample data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript(SCHEMA_SQL)
    
    # Insert sample customers
    customers = [
        ("CUST001", "John Doe", "john.doe@email.com", ...),
        ("CUST002", "Jane Smith", "jane.smith@email.com", ...),
        # ...
    ]
    cursor.executemany(INSERT_CUSTOMER_SQL, customers)
    
    # Insert service plans
    # Insert bills
    # Insert usage history
    # ...
    
    conn.commit()
    conn.close()
```

---

## Database Statistics

**Total Tables**: 13
**Total Records**: ~300
**Database Size**: ~500 KB
**Relationships**: 10 foreign key constraints

**Table Size Distribution**:
- Large tables (50+ records): data_usage, voice_usage, bills
- Medium tables (20-50 records): customers, usage_history, payments
- Small tables (< 20 records): service_plans, promotions, support_tickets

---

## Future Enhancements

1. **Migrations**: Add Alembic for schema migrations
2. **Connection Pool**: SQLAlchemy connection pooling
3. **Indexes**: Add indexes on frequently queried columns
4. **Partitioning**: Partition large tables by date
5. **Replication**: Add read replicas for scalability

---

**Last Updated**: December 1, 2025
**Database File**: `data/telecom.db`
**Schema Version**: 1.0
**Total Tables**: 13
**Total Records**: ~300
