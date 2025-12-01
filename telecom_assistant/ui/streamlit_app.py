# Streamlit UI code
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from orchestration.graph import create_graph  # type: ignore
from utils.database import (
    list_customers, get_customer, get_customer_usage, get_service_plan, 
    list_active_incidents, get_all_support_tickets, create_support_ticket, 
    update_ticket_status
)

# Set page configuration
st.set_page_config(
    page_title="Telecom Service Assistant",
    page_icon="📱",
    layout="wide"
)

def init_session_state():
    """Initialize all session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_type" not in st.session_state:
        st.session_state.user_type = None
    if "email" not in st.session_state:
        st.session_state.email = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "graph" not in st.session_state:
        # Initialize the LangGraph workflow once and cache it
        st.session_state.graph = create_graph()
    if "selected_customer_id" not in st.session_state:
        st.session_state.selected_customer_id = None


def process_query(query: str, customer_info: dict = None) -> str:
    """Process a user query through the LangGraph workflow"""
    # Use cached graph from session state
    workflow = st.session_state.graph
    
    # Create state with customer context
    state = {
        "query": query,
        "customer_info": customer_info or {},
        "classification": "",
        "intermediate_responses": {},
        "final_response": "",
        "chat_history": st.session_state.chat_history,
    }
    
    try:
        # Process through the graph
        result = workflow.invoke(state)
        return result.get("final_response", "No response generated.")
    except Exception as e:
        return f"Error processing query: {str(e)}"


def customer_dashboard(customer_info=None, customer_usage=None, service_plan=None):
    st.title("Welcome to Telecom Service Assistant")
    st.caption("Customer Portal")

    # Create tabs with Chat Assistant as first tab
    tab1, tab2, tab3, tab4 = st.tabs(["Chat Assistant", "My Account Information", "Network Status", "Quick Query"])

    # Tab 1: Chat Assistant (NEW)
    with tab1:
        st.header("Chat with our AI Assistant")
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("How can I help you today?"):
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Process user query through LangGraph
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = process_query(prompt, customer_info)
                    st.write(response)
            
            # Add assistant response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            # Force rerun to update chat display
            st.rerun()

    # Tab 2: Account Information (EXISTING - preserved)
    with tab2:
        st.header("My Account Information")
        
        if not customer_info:
            st.warning("Please select a customer from the sidebar to view account information.")
            return
        
        st.subheader("Current Plan")
        plan_name = service_plan.get('name', 'Unknown Plan') if service_plan else customer_info.get('service_plan_id', 'Unknown')
        st.write(f"**{plan_name}** ({customer_info.get('service_plan_id', 'N/A')})")
        
        # Get latest usage data
        latest_usage = customer_usage[0] if customer_usage else {}
        
        col1, col2, col3 = st.columns(3)
        with col1:
            data_used = latest_usage.get('data_used_gb', 0) if latest_usage else 0
            data_limit = service_plan.get('data_limit_gb', 0) if service_plan else 0
            unlimited_data = service_plan.get('unlimited_data', 0) if service_plan else 0
            
            if unlimited_data:
                st.metric("Data Used", f"{data_used} GB", "Unlimited")
            elif data_limit > 0:
                remaining = round(max(0, data_limit - data_used), 2)
                st.metric("Data Used", f"{data_used} GB", f"{remaining} GB remaining")
            else:
                st.metric("Data Used", f"{data_used} GB", "No data plan")
                
        with col2:
            voice_used = latest_usage.get('voice_minutes_used', 0) if latest_usage else 0
            voice_limit = service_plan.get('voice_minutes', 0) if service_plan else 0
            unlimited_voice = service_plan.get('unlimited_voice', 0) if service_plan else 0
            
            if unlimited_voice:
                st.metric("Voice Minutes", f"{voice_used} mins", "Unlimited")
            elif voice_limit > 0:
                remaining = int(max(0, voice_limit - voice_used))
                st.metric("Voice Minutes", f"{voice_used} mins", f"{remaining} remaining")
            else:
                st.metric("Voice Minutes", f"{voice_used} mins", "No voice plan")
                
        with col3:
            sms_used = latest_usage.get('sms_count_used', 0) if latest_usage else 0
            sms_limit = service_plan.get('sms_count', 0) if service_plan else 0
            unlimited_sms = service_plan.get('unlimited_sms', 0) if service_plan else 0
            
            if unlimited_sms:
                st.metric("SMS Used", str(sms_used), "Unlimited")
            elif sms_limit > 0:
                remaining = int(max(0, sms_limit - sms_used))
                st.metric("SMS Used", str(sms_used), f"{remaining} remaining")
            else:
                st.metric("SMS Used", str(sms_used), "No SMS plan")
        
        st.subheader("Billing Information")
        last_bill_date = customer_info.get('last_billing_date', 'N/A')
        st.write(f"Last Bill Date: **{last_bill_date}**")
        
        monthly_cost = service_plan.get('monthly_cost', 0) if service_plan else 0
        st.write(f"Monthly Charge: **₹{monthly_cost:.2f}**")
        
        if latest_usage:
            total_bill = latest_usage.get('total_bill_amount', monthly_cost)
            additional_charges = latest_usage.get('additional_charges', 0)
            st.write(f"Last Bill Amount: **₹{total_bill:.2f}**")
            if additional_charges > 0:
                st.write(f"Additional Charges: **₹{additional_charges:.2f}**")

    # Tab 3: Network Status (EXISTING - preserved)
    with tab3:
        st.header("Network Status")
        
        # Fetch real network incidents
        incidents = list_active_incidents()
        
        if incidents:
            # Group incidents by region for status overview
            regions_status = {}
            for inc in incidents:
                region = inc['location']
                severity = inc['severity']
                service = inc['affected_services']
                
                if region not in regions_status:
                    regions_status[region] = {'4G': 'Normal', '5G': 'Normal'}
                
                # Update status based on affected service
                if '4G' in service:
                    if severity == 'Critical':
                        regions_status[region]['4G'] = 'Outage'
                    elif severity == 'High':
                        regions_status[region]['4G'] = 'Degraded'
                    else:
                        regions_status[region]['4G'] = 'Issues'
                        
                if '5G' in service:
                    if severity == 'Critical':
                        regions_status[region]['5G'] = 'Outage'
                    elif severity == 'High':
                        regions_status[region]['5G'] = 'Degraded'
                    else:
                        regions_status[region]['5G'] = 'Issues'
            
            # Create status dataframe
            status_data = []
            all_regions = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad"]
            for region in all_regions:
                if region in regions_status:
                    status_data.append({
                        "Region": region,
                        "4G Status": regions_status[region]['4G'],
                        "5G Status": regions_status[region]['5G']
                    })
                else:
                    status_data.append({
                        "Region": region,
                        "4G Status": "Normal",
                        "5G Status": "Normal"
                    })
            
            status_df = pd.DataFrame(status_data)
            st.dataframe(status_df, width='stretch')
            
            st.subheader("Known Issues")
            for inc in incidents[:5]:  # Show top 5 incidents
                severity_icon = "🔴" if inc['severity'] == 'Critical' else "🟡" if inc['severity'] == 'High' else "🟢"
                st.warning(f"{severity_icon} **{inc['incident_type']}** in {inc['location']} - {inc['affected_services']} ({inc['status']})")
        else:
            # Fallback to normal status if no incidents
            status_df = pd.DataFrame({
                "Region": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad"],
                "4G Status": ["Normal", "Normal", "Normal", "Normal", "Normal"],
                "5G Status": ["Normal", "Normal", "Normal", "Normal", "Normal"],
            })
            st.dataframe(status_df, width='stretch')
            st.success("✓ All networks operating normally")

    # Tab 4: Quick Query (EXISTING functionality preserved in separate tab)
    with tab4:
        st.header("Quick Query (Detailed View)")
        st.info("Use this tab to see detailed workflow information and intermediate responses.")
        
        query = st.text_area("Enter your telecom question", height=120)
        if st.button("Submit Query") and query.strip():
            workflow = st.session_state.graph
            state = {
                "query": query,
                "customer_info": customer_info or {},
                "classification": "",
                "intermediate_responses": {},
                "final_response": "",
                "chat_history": st.session_state.chat_history,
            }
            result = workflow.invoke(state)
            resp = result if isinstance(result, dict) else {}
            st.caption(f"Workflow status: {resp.get('status','')} ")
            st.markdown(f"**Classification:** `{resp.get('classification','')}`")
            st.subheader("Final Response")
            st.write(resp.get("final_response","(none)"))
            with st.expander("Intermediate Responses JSON"):
                import json as _json
                st.json(resp.get("intermediate_responses", {}))
            with st.expander("Full State Dump"):
                st.code(_json.dumps(resp, indent=2))
            status_val = next(iter(result.get('intermediate_responses', {}).values()), {}).get('status') if result.get('intermediate_responses') else None
            if status_val == 'error':
                st.error("Processing failed")
            elif status_val == 'ok':
                st.success("Processed successfully")


def admin_dashboard():
    st.title("Admin Dashboard")
    tab1, tab2, tab3 = st.tabs(["Knowledge Base Management", "Customer Support", "Network Monitoring"])

    # Knowledge Base Management
    with tab1:
        st.header("Knowledge Base Management")
        st.subheader("Upload Documents to Knowledge Base")
        uploaded_files = st.file_uploader(
            "Upload PDF, Markdown, or Text files",
            type=["pdf", "md", "txt"],
            accept_multiple_files=True,
        )
        if uploaded_files:
            for file in uploaded_files:
                try:
                    # Save file to data/documents/
                    save_path = Path(__file__).parent.parent / "data" / "documents" / file.name
                    
                    # Check for duplicate
                    if save_path.exists():
                        st.warning(f"⚠️ {file.name} already exists, overwriting...")
                    
                    # Save file
                    with open(save_path, "wb") as f:
                        f.write(file.getbuffer())
                    
                    # Clear LlamaIndex cache to force rebuild
                    import agents.knowledge_agents as ka
                    ka._ENGINE_CACHE = None
                    
                    st.success(f"✅ {file.name} uploaded successfully!")
                    st.info("📚 Document will be indexed on next knowledge query (~10-30 seconds)")
                    
                except Exception as e:
                    st.error(f"❌ Failed to upload {file.name}: {str(e)}")
            
            # Refresh document list
            st.rerun()
        
        st.subheader("Existing Documents")
        # Read real documents from the active data/documents directory
        # Use absolute path relative to project root
        docs_path = Path(__file__).parent.parent / "data" / "documents"
        if docs_path.exists():
            docs = [f for f in docs_path.iterdir() if f.is_file() and f.suffix in ['.txt', '.md', '.pdf']]
            if docs:
                doc_data = []
                for doc in docs:
                    file_stat = doc.stat()
                    doc_data.append({
                        "Document Name": doc.name,
                        "Type": doc.suffix.upper().replace('.', ''),
                        "Size (KB)": f"{file_stat.st_size / 1024:.1f}",
                        "Last Updated": datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    })
                doc_df = pd.DataFrame(doc_data)
                st.dataframe(doc_df, width='stretch')
                st.info(f"📚 Total documents in knowledge base: {len(docs)}")
            else:
                st.warning("No documents found in knowledge base")
        else:
            st.error("Knowledge base directory not found")

    # Customer Support Dashboard
    with tab2:
        st.header("Customer Support Dashboard")
        
        # CREATE NEW TICKET FORM
        with st.expander("➕ Create New Ticket", expanded=False):
            with st.form("create_ticket_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Customer dropdown
                    customers = list_customers()
                    customer_options = {f"{c['name']} ({c['customer_id']})": c['customer_id'] for c in customers}
                    selected_customer = st.selectbox("Customer", list(customer_options.keys()))
                    
                    # Category dropdown
                    category = st.selectbox("Issue Category", [
                        "Billing Inquiry",
                        "Connectivity Issue",
                        "Service Request",
                        "Technical Support"
                    ])
                
                with col2:
                    # Priority dropdown
                    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                
                # Description
                description = st.text_area("Issue Description", height=100)
                
                # Submit button
                submitted = st.form_submit_button("Create Ticket")
                
                if submitted:
                    if description.strip():
                        customer_id = customer_options[selected_customer]
                        ticket_id = create_support_ticket(customer_id, category, description, priority)
                        st.success(f"✅ Ticket {ticket_id} created successfully!")
                        st.rerun()
                    else:
                        st.error("Please provide an issue description")
        
        st.divider()
        
        # FILTER AND DISPLAY TICKETS
        col1, col2 = st.columns([2, 8])
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Open", "In Progress", "Assigned", "Resolved"]
            )
        
        st.subheader("Support Tickets")
        
        # Fetch tickets with filter
        if status_filter == "All":
            all_tickets = get_all_support_tickets()
        else:
            all_tickets = get_all_support_tickets(status=status_filter)
        
        if all_tickets:
            # Display tickets with update functionality
            displayed_tickets = all_tickets if status_filter == "All" else [t for t in all_tickets if t['status'] == status_filter]
            
            if displayed_tickets:
                st.write(f"**Found {len(displayed_tickets)} ticket(s)**")
                
                # Display each ticket with update controls
                for idx, ticket in enumerate(displayed_tickets):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                        
                        with col1:
                            st.markdown(f"**{ticket['ticket_id']}** - {ticket['customer_name']}")
                            st.caption(f"📋 {ticket['issue_category']}")
                            with st.expander("View Description"):
                                st.write(ticket['issue_description'])
                        
                        with col2:
                            current_status = ticket['status']
                            status_options = ["Open", "In Progress", "Assigned", "Resolved"]
                            current_index = status_options.index(current_status) if current_status in status_options else 0
                            
                            new_status = st.selectbox(
                                "Status",
                                status_options,
                                index=current_index,
                                key=f"status_{ticket['ticket_id']}"
                            )
                        
                        with col3:
                            st.write(f"**Priority:** {ticket['priority']}")
                            st.caption(f"Created: {ticket['creation_time']}")
                        
                        with col4:
                            # Show resolution notes input if status is Resolved
                            if new_status == "Resolved":
                                st.write("")  # Spacing
                            
                            if st.button("💾 Update", key=f"update_{ticket['ticket_id']}"):
                                if new_status != current_status:
                                    # If changing to Resolved, prompt for notes
                                    if new_status == "Resolved":
                                        st.session_state[f"show_notes_{ticket['ticket_id']}"] = True
                                    else:
                                        update_ticket_status(ticket['ticket_id'], new_status)
                                        st.success(f"✅ Updated {ticket['ticket_id']} to {new_status}")
                                        st.rerun()
                                else:
                                    st.info("No change in status")
                        
                        # Show resolution notes dialog if needed
                        if st.session_state.get(f"show_notes_{ticket['ticket_id']}", False):
                            with st.form(key=f"resolve_form_{ticket['ticket_id']}"):
                                notes = st.text_area("Resolution Notes", height=100)
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    if st.form_submit_button("✅ Resolve"):
                                        update_ticket_status(ticket['ticket_id'], "Resolved", notes)
                                        st.session_state[f"show_notes_{ticket['ticket_id']}"] = False
                                        st.success(f"✅ Ticket {ticket['ticket_id']} resolved")
                                        st.rerun()
                                with col_b:
                                    if st.form_submit_button("Cancel"):
                                        st.session_state[f"show_notes_{ticket['ticket_id']}"] = False
                                        st.rerun()
                        
                        st.divider()
            else:
                st.success("✓ No tickets found for this filter!")
            
            st.divider()
            
            # Calculate real metrics from ALL tickets (not just displayed ones)
            open_tickets = len([t for t in all_tickets if t['status'] == 'Open'])
            in_progress_tickets = len([t for t in all_tickets if t['status'] == 'In Progress'])
            resolved_tickets = [t for t in all_tickets if t['status'] == 'Resolved' and t['resolution_time']]
            
            # Calculate average resolution time
            avg_resolution_hours = 0
            if resolved_tickets:
                total_hours = 0
                for ticket in resolved_tickets:
                    try:
                        created = datetime.strptime(ticket['creation_time'], "%Y-%m-%d %H:%M:%S")
                        resolved = datetime.strptime(ticket['resolution_time'], "%Y-%m-%d %H:%M:%S")
                        hours = (resolved - created).total_seconds() / 3600
                        total_hours += hours
                    except Exception:
                        pass
                if total_hours > 0:
                    avg_resolution_hours = total_hours / len(resolved_tickets)
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Open Tickets", open_tickets)
            with col2:
                st.metric("In Progress", in_progress_tickets)
            with col3:
                st.metric("Avg. Resolution Time", f"{avg_resolution_hours:.1f}h" if avg_resolution_hours > 0 else "N/A")
            with col4:
                total_tickets = len(all_tickets)
                resolved_count = len(resolved_tickets)
                satisfaction = int((resolved_count / total_tickets * 100)) if total_tickets > 0 else 0
                st.metric("Resolution Rate", f"{satisfaction}%")
        else:
            st.info("No support tickets found in database")

    # Network Monitoring
    with tab3:
        st.header("Network Monitoring")
        st.subheader("Active Network Incidents")
        
        # Fetch real incidents from database
        incidents = list_active_incidents()
        
        if incidents:
            incident_data = []
            for inc in incidents:
                incident_data.append({
                    "Incident ID": inc['incident_id'],
                    "Type": inc['incident_type'],
                    "Location": inc['location'],
                    "Affected Services": inc['affected_services'],
                    "Started": inc['start_time'],
                    "Status": inc['status'],
                    "Severity": inc['severity'],
                })
            incident_df = pd.DataFrame(incident_data)
            st.dataframe(incident_df, width='stretch')
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Active Incidents", len(incidents))
            with col2:
                critical_count = sum(1 for inc in incidents if inc['severity'] == 'Critical')
                st.metric("Critical", critical_count)
            with col3:
                high_count = sum(1 for inc in incidents if inc['severity'] == 'High')
                st.metric("High Priority", high_count)
        else:
            st.success("✓ No active incidents reported")
            st.info("All network services are operating normally.")


# Function to run the app

def main():
    init_session_state()
    
    # Sidebar for authentication
    with st.sidebar:
        st.title("📱 Telecom Assistant")
        
        if not st.session_state.authenticated:
            # Login form
            st.subheader("Login")
            email = st.text_input("Email Address")
            user_type = st.selectbox("User Type", ["Customer", "Admin"])
            
            if st.button("Login"):
                if email and "@" in email:
                    st.session_state.authenticated = True
                    st.session_state.user_type = user_type
                    st.session_state.email = email
                    st.session_state.chat_history = []  # Clear chat history on login
                    st.success(f"Logged in as {user_type}")
                    st.rerun()
                else:
                    st.error("Please enter a valid email address")
        else:
            # Logged in state
            st.success(f"Logged in as {st.session_state.user_type}")
            st.text(f"Email: {st.session_state.email}")
            
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.user_type = None
                st.session_state.email = None
                st.session_state.chat_history = []
                st.session_state.selected_customer_id = None
                st.rerun()
            
            st.divider()
            
            # Customer selector (for both Customer and Admin views)
            st.subheader("Select Customer")
            customer_options = list_customers()
            cust_map = {f"{c['name']} ({c['customer_id']})": c['customer_id'] for c in customer_options}
            
            if cust_map:
                selected_customer = st.selectbox("Customer", list(cust_map.keys()))
                st.session_state.selected_customer_id = cust_map.get(selected_customer)
            else:
                st.warning("No customers found in database")
                st.session_state.selected_customer_id = None
    
    # Main content - only show if authenticated
    if st.session_state.authenticated:
        customer_id = st.session_state.selected_customer_id
        
        # Fetch all required customer data
        customer_info = get_customer(customer_id) if customer_id else None
        customer_usage = get_customer_usage(customer_id) if customer_id else []
        service_plan = None
        if customer_info and customer_info.get('service_plan_id'):
            service_plan = get_service_plan(customer_info['service_plan_id'])

        if st.session_state.user_type == "Admin":
            admin_dashboard()
        else:
            customer_dashboard(customer_info, customer_usage, service_plan)
    else:
        # Welcome screen for non-authenticated users
        st.title("Welcome to Telecom Service Assistant")
        st.markdown("""
        ### 📱 Your AI-Powered Telecom Support
        
        Please login using the sidebar to access:
        - 💬 **Chat Assistant** - Conversational AI support
        - 📊 **Account Information** - View your usage and billing
        - 🌐 **Network Status** - Real-time network monitoring
        - 🔧 **Admin Dashboard** - Manage customers and incidents
        
        ---
        **Features:**
        - Multi-framework AI (CrewAI, AutoGen, LangChain, LlamaIndex)
        - Intelligent query routing with LangGraph
        - Real-time database integration
        - Comprehensive troubleshooting
        """)
        
        st.info("👈 Please login with your email address to get started")


if __name__ == "__main__":
    main()
