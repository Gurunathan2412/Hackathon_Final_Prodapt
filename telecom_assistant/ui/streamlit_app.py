# Streamlit UI code
import streamlit as st
import pandas as pd
import json
from orchestration.graph import create_graph  # type: ignore
from utils.database import list_customers, get_customer, get_customer_usage, get_service_plan, list_active_incidents


def init_session_state():
    if "user_type" not in st.session_state:
        # Default can be switched between "Customer" and "Admin"
        st.session_state.user_type = "Customer"


def customer_dashboard(customer_info=None, customer_usage=None, service_plan=None):
    st.title("Telecom Service Assistant")
    st.caption("Customer Portal")

    # Create tabs (adding a placeholder Overview tab since snippet started at tab2)
    tab1, tab2, tab3 = st.tabs(["Overview", "My Account Information", "Network Status"])

    with tab1:
        st.header("Overview")
        if customer_info:
            st.write(f"Welcome, **{customer_info.get('name', 'Customer')}**!")
            st.write(f"Account Status: **{customer_info.get('account_status', 'Unknown')}**")
        else:
            st.write("Welcome to your telecom service dashboard. Use the other tabs to view details.")
            st.info("👈 Please select a customer from the sidebar to view personalized data.")

    # Snippet: Account Information (originally shown under tab2)
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

    # Snippet: Network Status (originally shown under tab3)
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
                st.success(f"Processed {file.name} and added to knowledge base")
        st.subheader("Existing Documents")
        doc_df = pd.DataFrame({
            "Document Name": [
                "Service Plans Guide.md",
                "Network Troubleshooting Guide.md",
                "Billing FAQs.md",
                "Technical Support Guide.md",
            ],
            "Type": ["Markdown", "Markdown", "Markdown", "Markdown"],
            "Last Updated": ["2023-06-20", "2023-06-18", "2023-06-15", "2023-06-10"],
        })
        st.dataframe(doc_df, width='stretch')

    # Customer Support Dashboard
    with tab2:
        st.header("Customer Support Dashboard")
        st.subheader("Active Support Tickets")
        ticket_df = pd.DataFrame({
            "Ticket ID": ["TKT004", "TKT005"],
            "Customer": ["Ananya Singh", "Vikram Reddy"],
            "Issue": ["Account reactivation", "Slow internet speeds"],
            "Status": ["In Progress", "Assigned"],
            "Priority": ["Medium", "Medium"],
            "Created": ["2023-06-15", "2023-06-17"],
        })
        st.dataframe(ticket_df, width='stretch')
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Open Tickets", "2", "-3")
        with col2:
            st.metric("Avg. Resolution Time", "4.3 hours", "-0.5")
        with col3:
            st.metric("Customer Satisfaction", "92%", "+3%")

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
    st.sidebar.header("User Mode")
    mode = st.sidebar.selectbox("Select mode", ["Customer", "Admin"], index=0)
    st.session_state.user_type = mode

    customer_options = list_customers()
    cust_map = {f"{c['name']} ({c['customer_id']})": c['customer_id'] for c in customer_options}
    selected_customer = st.sidebar.selectbox("Customer", list(cust_map.keys()) or ["None"])
    customer_id = cust_map.get(selected_customer)
    
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

    st.divider()
    st.header("Ask a Question")
    query = st.text_area("Enter your telecom question", height=120)
    if st.button("Submit Query") and query.strip():
        workflow = create_graph()
        state = {
            "query": query,
            "customer_info": customer_info or {},
            "classification": "",
            "intermediate_responses": {},
            "final_response": "",
            "chat_history": [],
        }
        result = workflow.invoke(state)  # type: ignore
        # Safely handle missing result
        resp = result if isinstance(result, dict) else {}
        st.caption(f"Workflow status: {resp.get('status','')} ")
        st.markdown(f"**Classification:** `{resp.get('classification','')}`")
        st.subheader("Final Response")
        st.write(resp.get("final_response","(none)"))
        with st.expander("Intermediate Responses JSON"):
            st.json(resp.get("intermediate_responses", {}))
        with st.expander("Full State Dump"):
            import json as _json
            st.code(_json.dumps(resp, indent=2))
        status_val = next(iter(result.get('intermediate_responses', {}).values()), {}).get('status') if result.get('intermediate_responses') else None
        if status_val == 'error':
            st.error("Processing failed")
        elif status_val == 'ok':
            st.success("Processed successfully")


if __name__ == "__main__":
    main()
