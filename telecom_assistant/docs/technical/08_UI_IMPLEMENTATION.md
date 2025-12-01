# Streamlit UI Implementation - Web Interface

## Overview

The Telecom Service Assistant uses **Streamlit** as its web framework, providing an interactive interface for customers and administrators. The UI features **authentication**, **chat interface**, **customer dashboard**, and **admin tools**.

---

## Architecture

### Application Structure

```
┌──────────────────────────────────────────┐
│         Streamlit Application            │
│         (ui/streamlit_app.py)            │
└──────────────┬───────────────────────────┘
               │
      ┌────────┴────────┐
      │  Session State  │
      │  Management     │
      └────────┬────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│  Auth   │ │Customer │ │  Admin  │
│Sidebar  │ │Dashboard│ │Dashboard│
└─────────┘ └─────────┘ └─────────┘
```

**Entry Point**: `app.py` → `ui/streamlit_app.py`

---

## Session State Management

### State Initialization

**File**: `ui/streamlit_app.py` (Lines 19-45)

```python
def init_session_state():
    """Initialize Streamlit session state variables."""
    
    # Authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # User information
    if "user_type" not in st.session_state:
        st.session_state.user_type = None  # 'customer' or 'admin'
    
    if "email" not in st.session_state:
        st.session_state.email = None
    
    # Chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # LangGraph workflow (cached)
    if "graph" not in st.session_state:
        st.session_state.graph = create_graph()
    
    # Customer context
    if "selected_customer_id" not in st.session_state:
        st.session_state.selected_customer_id = None
```

**State Variables**:

| Variable | Type | Purpose |
|----------|------|---------|
| `authenticated` | bool | Login status |
| `user_type` | str | "customer" or "admin" |
| `email` | str | User email address |
| `chat_history` | list | Conversation history |
| `graph` | CompiledGraph | LangGraph workflow (cached) |
| `selected_customer_id` | str | Current customer ID |

---

## Authentication System

### Login Interface

**File**: `ui/streamlit_app.py` (Lines 47-92)

**Location**: Sidebar

```python
with st.sidebar:
    st.header("🔐 Authentication")
    
    if not st.session_state.authenticated:
        # Login form
        email = st.text_input("Email", key="login_email")
        user_type = st.selectbox(
            "User Type",
            ["customer", "admin"],
            key="login_user_type"
        )
        
        if st.button("Login", type="primary"):
            if email and "@" in email:
                st.session_state.authenticated = True
                st.session_state.email = email
                st.session_state.user_type = user_type
                
                # Fetch customer info if customer login
                if user_type == "customer":
                    customer_info = get_customer_by_email(email)
                    if customer_info:
                        st.session_state.selected_customer_id = customer_info["customer_id"]
                
                st.rerun()
            else:
                st.error("Please enter a valid email")
    else:
        # Logout interface
        st.success(f"✓ Logged in as {st.session_state.email}")
        st.info(f"Role: {st.session_state.user_type.title()}")
        
        if st.button("Logout", type="secondary"):
            st.session_state.authenticated = False
            st.session_state.email = None
            st.session_state.user_type = None
            st.session_state.selected_customer_id = None
            st.session_state.chat_history = []
            st.rerun()
```

**Features**:
- Email validation (must contain @)
- User type selection (customer/admin)
- Auto-fetch customer ID for customer logins
- Clear session on logout

**No Password**: Demo application (would add in production)

### Authorization Logic

```python
if not st.session_state.authenticated:
    # Show welcome screen
    show_welcome_screen()
elif st.session_state.user_type == "customer":
    # Show customer dashboard
    customer_dashboard()
elif st.session_state.user_type == "admin":
    # Show admin dashboard
    admin_dashboard()
```

---

## Customer Dashboard

### Dashboard Structure

**File**: `ui/streamlit_app.py` (Lines 150-280)

**Tabs**:
1. Chat Assistant
2. Account Overview
3. Usage Analytics
4. Quick Query

```python
def customer_dashboard():
    """Customer-facing dashboard with chat interface."""
    
    st.title("📱 Telecom Service Assistant")
    st.write(f"Welcome, {st.session_state.email}!")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "💬 Chat Assistant",
        "📊 Account Overview",
        "📈 Usage Analytics",
        "⚡ Quick Query"
    ])
    
    with tab1:
        chat_assistant_tab()
    
    with tab2:
        account_overview_tab()
    
    with tab3:
        usage_analytics_tab()
    
    with tab4:
        quick_query_tab()
```

### Tab 1: Chat Assistant

**Purpose**: Interactive chat interface with AI assistant

**Implementation**:
```python
def chat_assistant_tab():
    """Chat interface with message history."""
    
    st.header("💬 Chat with AI Assistant")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your telecom services..."):
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = process_query(prompt)
                st.write(response)
        
        # Add assistant response to history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })
        
        st.rerun()
```

**Features**:
- `st.chat_message()`: Styled message bubbles
- `st.chat_input()`: Bottom-anchored input
- Message history persistence
- Spinner during processing
- Auto-rerun to display new messages

### Tab 2: Account Overview

**Purpose**: Display customer account information

**Implementation**:
```python
def account_overview_tab():
    """Show customer account details."""
    
    st.header("📊 Account Overview")
    
    customer_id = st.session_state.selected_customer_id
    if not customer_id:
        st.warning("Customer ID not found. Please re-login.")
        return
    
    # Fetch customer data
    customer_info = get_customer_info(customer_id)
    
    if not customer_info:
        st.error("Unable to load customer information")
        return
    
    # Display in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Information")
        st.write(f"**Name:** {customer_info.get('name', 'N/A')}")
        st.write(f"**Email:** {customer_info.get('email', 'N/A')}")
        st.write(f"**Phone:** {customer_info.get('phone', 'N/A')}")
        st.write(f"**Customer ID:** {customer_id}")
    
    with col2:
        st.subheader("Service Plan")
        st.write(f"**Plan:** {customer_info.get('plan_name', 'N/A')}")
        st.write(f"**Monthly Cost:** ${customer_info.get('monthly_cost', 0):.2f}")
        st.write(f"**Status:** {customer_info.get('account_status', 'N/A')}")
    
    # Recent bills
    st.subheader("Recent Bills")
    bills = get_recent_bills(customer_id, limit=3)
    
    if bills:
        bills_df = pd.DataFrame(bills)
        st.dataframe(bills_df[[
            'bill_id', 'billing_period_start', 'total_amount', 'payment_status'
        ]])
    else:
        st.info("No billing data available")
```

**Features**:
- Two-column layout
- Personal info + Service plan info
- Recent bills table with `st.dataframe()`
- Error handling

### Tab 3: Usage Analytics

**Purpose**: Visualize usage patterns

**Implementation**:
```python
def usage_analytics_tab():
    """Show usage analytics with charts."""
    
    st.header("📈 Usage Analytics")
    
    customer_id = st.session_state.selected_customer_id
    usage_data = get_customer_usage(customer_id)
    
    if not usage_data:
        st.info("No usage data available")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(usage_data)
    
    # Data usage chart
    st.subheader("Data Usage Over Time")
    fig = px.line(
        df,
        x="month",
        y="data_used_gb",
        title="Monthly Data Usage (GB)",
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Voice usage chart
    st.subheader("Voice Minutes Over Time")
    fig2 = px.bar(
        df,
        x="month",
        y="voice_minutes_used",
        title="Monthly Voice Usage (Minutes)"
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Avg Data", f"{df['data_used_gb'].mean():.1f} GB")
    with col2:
        st.metric("Avg Voice", f"{df['voice_minutes_used'].mean():.0f} min")
    with col3:
        st.metric("Avg SMS", f"{df['sms_count'].mean():.0f}")
```

**Features**:
- Plotly charts for interactive visualization
- Line chart for data usage trends
- Bar chart for voice usage
- Summary metrics with `st.metric()`

### Tab 4: Quick Query

**Purpose**: Single-query interface (original functionality)

**Implementation**:
```python
def quick_query_tab():
    """Quick query interface without chat history."""
    
    st.header("⚡ Quick Query")
    
    customer_id = st.session_state.selected_customer_id
    
    # Query input
    query = st.text_area(
        "Enter your question:",
        height=100,
        placeholder="e.g., Why is my bill higher this month?"
    )
    
    if st.button("Submit Query", type="primary"):
        if query:
            with st.spinner("Processing..."):
                response = process_query(query)
                st.success("Response:")
                st.write(response)
        else:
            st.warning("Please enter a query")
```

**Features**:
- Single query/response (no chat history)
- Faster for one-off questions
- Preserves original functionality

---

## Admin Dashboard

### Dashboard Structure

**File**: `ui/streamlit_app.py` (Lines 282-400)

**Tabs**:
1. Customer Management
2. System Analytics
3. Database Query

```python
def admin_dashboard():
    """Admin dashboard with management tools."""
    
    st.title("🔧 Admin Dashboard")
    st.write(f"Admin: {st.session_state.email}")
    
    tab1, tab2, tab3 = st.tabs([
        "👥 Customer Management",
        "📊 System Analytics",
        "🗄️ Database Query"
    ])
    
    with tab1:
        customer_management_tab()
    
    with tab2:
        system_analytics_tab()
    
    with tab3:
        database_query_tab()
```

### Tab 1: Customer Management

**Purpose**: View and manage customers

**Implementation**:
```python
def customer_management_tab():
    """Manage customers."""
    
    st.header("👥 Customer Management")
    
    # Get all customers
    customers = get_all_customers()
    
    if customers:
        df = pd.DataFrame(customers)
        
        # Display table
        st.dataframe(
            df[['customer_id', 'name', 'email', 'service_plan_id', 'account_status']],
            use_container_width=True
        )
        
        # Customer selector
        selected_customer = st.selectbox(
            "Select Customer for Details",
            options=[c['customer_id'] for c in customers]
        )
        
        if selected_customer:
            # Show detailed view
            customer_info = get_customer_info(selected_customer)
            st.json(customer_info)
    else:
        st.warning("No customers found")
```

**Features**:
- Full customer table
- Customer selection
- Detailed JSON view

### Tab 2: System Analytics

**Purpose**: System-wide statistics

**Implementation**:
```python
def system_analytics_tab():
    """Show system-wide analytics."""
    
    st.header("📊 System Analytics")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        customer_count = len(get_all_customers())
        st.metric("Total Customers", customer_count)
    
    with col2:
        plans = get_all_service_plans()
        st.metric("Active Plans", len(plans))
    
    with col3:
        # Calculate total revenue (example)
        bills = get_all_bills()
        total_revenue = sum(b.get('total_amount', 0) for b in bills)
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    with col4:
        tickets = get_open_support_tickets()
        st.metric("Open Tickets", len(tickets))
    
    # Plan distribution chart
    st.subheader("Customers by Plan")
    plan_distribution = calculate_plan_distribution()
    fig = px.pie(
        plan_distribution,
        values='count',
        names='plan_name',
        title="Customer Distribution by Plan"
    )
    st.plotly_chart(fig, use_container_width=True)
```

**Features**:
- 4 key metrics
- Revenue calculation
- Pie chart for plan distribution

### Tab 3: Database Query

**Purpose**: Raw database access for admins

**Implementation**:
```python
def database_query_tab():
    """Execute custom database queries."""
    
    st.header("🗄️ Database Query")
    st.warning("⚠️ Advanced feature - use caution")
    
    # Query input
    query = st.text_area(
        "SQL Query:",
        height=150,
        placeholder="SELECT * FROM customers LIMIT 10"
    )
    
    if st.button("Execute Query"):
        if query.strip().upper().startswith("SELECT"):
            try:
                results = query_db(query)
                if results:
                    st.success(f"Returned {len(results)} rows")
                    st.dataframe(pd.DataFrame(results))
                else:
                    st.info("Query returned no results")
            except Exception as e:
                st.error(f"Query error: {str(e)}")
        else:
            st.error("Only SELECT queries allowed")
```

**Features**:
- SQL editor
- Read-only (SELECT only)
- Error handling
- Results as DataFrame

---

## Query Processing

### Process Query Function

**File**: `ui/streamlit_app.py` (Lines 94-148)

```python
def process_query(query: str) -> str:
    """
    Process user query through LangGraph workflow.
    
    Args:
        query: User's question
        
    Returns:
        Final response string
    """
    # Get customer context
    customer_id = st.session_state.selected_customer_id
    customer_info = None
    
    if customer_id:
        customer_info = get_customer_info(customer_id)
    
    # Prepare state
    state = {
        "query": query,
        "customer_info": customer_info or {},
        "classification": "",
        "intermediate_responses": {},
        "final_response": "",
        "chat_history": st.session_state.chat_history
    }
    
    # Execute workflow
    workflow = st.session_state.graph
    result = workflow.invoke(state)
    
    # Extract response
    final_response = result.get("final_response", "No response generated")
    
    return final_response
```

**Process**:
1. Fetch customer context (if available)
2. Prepare LangGraph state
3. Invoke workflow
4. Extract final response
5. Return to UI

---

## Styling & Layout

### Page Configuration

**File**: `ui/streamlit_app.py` (Lines 12-17)

```python
st.set_page_config(
    page_title="Telecom Service Assistant",
    page_icon="📱",
    layout="wide",        # Wide layout for dashboards
    initial_sidebar_state="expanded"
)
```

### Custom CSS

```python
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)
```

---

## Performance Optimizations

### Caching

**LangGraph Workflow**:
```python
# Cached in session state (created once)
if "graph" not in st.session_state:
    st.session_state.graph = create_graph()
```

**Database Queries**:
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_customers():
    return query_db("SELECT * FROM customers")
```

### Lazy Loading

- Load data only when tab is active
- Defer chart rendering until needed

---

## Error Handling

### User-Friendly Errors

```python
try:
    response = process_query(query)
    st.success("Response:")
    st.write(response)
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.info("Please try again or contact support")
```

### Validation

```python
if not email or "@" not in email:
    st.error("Please enter a valid email")
    return

if not query.strip():
    st.warning("Please enter a query")
    return
```

---

## Future Enhancements

1. **Real Authentication**: OAuth/SSO integration
2. **User Preferences**: Save dashboard settings
3. **Export Features**: Download reports as PDF/CSV
4. **Real-time Updates**: WebSocket for live data
5. **Mobile Responsive**: Optimize for mobile devices

---

**Last Updated**: December 1, 2025
**File**: `ui/streamlit_app.py`
**Lines of Code**: 443
**Tabs (Customer)**: 4
**Tabs (Admin)**: 3
**Authentication**: Email-based (demo)
