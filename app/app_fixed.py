"""
KindMesh - A lightweight, secure, browser-based app for resource distribution tracking

This Streamlit application provides a user interface for:
- User authentication and management
- Tracking resource distributions
- Visualizing and exporting data
"""

import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime
import tracemalloc

# Enable tracemalloc to track object allocation
tracemalloc.start()

# Import the graph database module
from utils.graph import GraphDatabase

# Page configuration
st.set_page_config(
    page_title="KindMesh",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "admin_demotion_votes" not in st.session_state:
    st.session_state.admin_demotion_votes = {}

# Connect to the Neo4j database
@st.cache_resource(ttl=3600)  # Cache for 1 hour
def get_database_connection():
    """Create and cache the database connection"""
    return GraphDatabase(
        uri=os.environ.get("NEO4J_URI", "bolt://neo4j:7687"),
        user=os.environ.get("NEO4J_USER", "neo4j"),
        password=os.environ.get("NEO4J_PASSWORD", "kindmesh")
    )

db = get_database_connection()

# Authentication functions
def login(username, password):
    """Authenticate user and set session state"""
    success, user_data = db.authenticate_user(username, password)
    if success:
        st.session_state.authenticated = True
        st.session_state.username = user_data["username"]
        st.session_state.role = user_data["role"]
        return True
    return False

def logout():
    """Clear session state and log out user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.admin_demotion_votes = {}

# Page rendering functions
def render_login_page():
    """Render the login page"""
    st.title("KindMesh - Login")

    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            if login(username, password):
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

def render_greeter_page():
    """Render the page for users with the Greeter role"""
    st.title("Welcome to KindMesh")
    st.write(f"Logged in as: {st.session_state.username} (Role: {st.session_state.role})")

    st.write("As a Greeter, you can create new users for the system.")

    with st.form("create_user_form"):
        st.subheader("Create New User")
        new_username = st.text_input("Username", key="greeter_new_username")
        new_password = st.text_input("Password", type="password", key="greeter_new_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="greeter_confirm_password")
        submit_button = st.form_submit_button("Create User")

        if submit_button:
            if not new_username or not new_password:
                st.error("Username and password are required")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                success = db.create_user(new_username, new_password, "Friend")
                if success:
                    st.success(f"User {new_username} created successfully")
                else:
                    st.error("Failed to create user. Username may already exist.")

def render_admin_page():
    """Render the page for users with the Admin role"""
    st.title("KindMesh Admin Dashboard")
    st.write(f"Logged in as: {st.session_state.username} (Role: {st.session_state.role})")

    # Tabs for different admin functions
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["User Management", "Data Export", "System Stats", "Create User", "Create Recipient"])

    with tab1:
        st.header("User Management")
        
        # Get all users
        users = db.get_all_users()
        
        if users:
            # Create a DataFrame for display
            user_df = pd.DataFrame(users)
            user_df = user_df[["username", "role", "created_at"]]
            
            # Display users
            st.dataframe(user_df)
            
            # User actions
            st.subheader("User Actions")
            
            # Select a user
            selected_user = st.selectbox("Select User", [user["username"] for user in users], key="admin_select_user")
            
            # Get the selected user's role
            selected_user_role = next((user["role"] for user in users if user["username"] == selected_user), None)
            
            # Actions based on role
            if selected_user_role:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Change role
                    new_role = st.selectbox("New Role", ["Friend", "Greeter", "Admin"], 
                                           index=["Friend", "Greeter", "Admin"].index(selected_user_role),
                                           key="admin_new_role")
                    
                    if st.button("Change Role"):
                        if selected_user == st.session_state.username and new_role != "Admin":
                            st.error("You cannot demote yourself from Admin")
                        else:
                            success = db.update_user_role(selected_user, new_role)
                            if success:
                                st.success(f"Changed {selected_user}'s role to {new_role}")
                            else:
                                st.error("Failed to change role")
                
                with col2:
                    # Delete user
                    if st.button("Delete User"):
                        if selected_user == st.session_state.username:
                            st.error("You cannot delete yourself")
                        else:
                            success = db.delete_user(selected_user)
                            if success:
                                st.success(f"Deleted user {selected_user}")
                            else:
                                st.error("Failed to delete user")
        else:
            st.write("No users found")

    with tab2:
        st.header("Data Export")
        
        # Export options
        export_type = st.selectbox("Export Type", ["All Interactions", "User Activity", "Recipient Data"], key="admin_export_type")
        
        if export_type == "All Interactions":
            # Get all interactions
            interactions = db.get_all_interactions()
            
            if interactions:
                # Create a DataFrame for display and export
                interaction_df = pd.DataFrame(interactions)
                
                # Display preview
                st.subheader("Preview")
                st.dataframe(interaction_df.head(10))
                
                # Export button
                csv = interaction_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="kindmesh_interactions.csv",
                    mime="text/csv"
                )
            else:
                st.write("No interactions found")
                
        elif export_type == "User Activity":
            # Get all users
            users = db.get_all_users()
            
            if users:
                # Select a user
                selected_user = st.selectbox("Select User", [user["username"] for user in users], key="admin_export_user")
                
                # Get user activity
                user_activity = db.get_user_activity(selected_user)
                
                if user_activity:
                    # Create a DataFrame for display and export
                    activity_df = pd.DataFrame(user_activity)
                    
                    # Display preview
                    st.subheader("Preview")
                    st.dataframe(activity_df.head(10))
                    
                    # Export button
                    csv = activity_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"kindmesh_{selected_user}_activity.csv",
                        mime="text/csv"
                    )
                else:
                    st.write("No activity found for this user")
            else:
                st.write("No users found")
                
        elif export_type == "Recipient Data":
            # Get all recipients
            recipients = db.get_all_recipients()
            
            if recipients:
                # Select a recipient
                selected_recipient = st.selectbox("Select Recipient", 
                                                 [f"{r['key']} ({r['pseudonym']})" if r['pseudonym'] else r['key'] for r in recipients],
                                                 key="admin_export_recipient")
                
                # Extract the key from the selection
                recipient_key = selected_recipient.split(" (")[0] if " (" in selected_recipient else selected_recipient
                
                # Get recipient data
                recipient_data = db.get_recipient_data(recipient_key)
                
                if recipient_data:
                    # Create a DataFrame for display and export
                    data_df = pd.DataFrame(recipient_data)
                    
                    # Display preview
                    st.subheader("Preview")
                    st.dataframe(data_df.head(10))
                    
                    # Export button
                    csv = data_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"kindmesh_{recipient_key}_data.csv",
                        mime="text/csv"
                    )
                else:
                    st.write("No data found for this recipient")
            else:
                st.write("No recipients found")

    with tab3:
        st.header("System Statistics")
        
        # Get system stats
        stats = db.get_system_stats()
        
        if stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Users", stats.get("total_users", 0))
                st.metric("Total Recipients", stats.get("total_recipients", 0))
                
            with col2:
                st.metric("Total Interactions", stats.get("total_interactions", 0))
                st.metric("Active Users (Last 7 Days)", stats.get("active_users_7d", 0))
                
            with col3:
                st.metric("New Recipients (Last 30 Days)", stats.get("new_recipients_30d", 0))
                st.metric("New Interactions (Last 24 Hours)", stats.get("new_interactions_24h", 0))
                
            # Activity over time
            if "activity_over_time" in stats and stats["activity_over_time"]:
                st.subheader("Activity Over Time")
                activity_df = pd.DataFrame(stats["activity_over_time"])
                st.line_chart(activity_df.set_index("date")["count"])
        else:
            st.write("No statistics available")

    with tab4:
        st.header("Create New User")
        
        with st.form("admin_create_user_form"):
            new_username = st.text_input("Username", key="admin_new_username")
            new_password = st.text_input("Password", type="password", key="admin_new_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="admin_confirm_password")
            new_role = st.selectbox("Role", ["Friend", "Greeter", "Admin"], key="admin_create_role")
            
            submit_button = st.form_submit_button("Create User")
            
            if submit_button:
                if not new_username or not new_password:
                    st.error("Username and password are required")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success = db.create_user(new_username, new_password, new_role)
                    if success:
                        st.success(f"User {new_username} created successfully with role {new_role}")
                    else:
                        st.error("Failed to create user. Username may already exist.")

    with tab5:
        st.header("Create New Recipient")
        
        with st.form("admin_create_recipient_form"):
            new_recipient_key = st.text_input("Recipient Key (required)", key="admin_new_recipient_key")
            new_recipient_pseudonym = st.text_input("Recipient Pseudonym (optional)", key="admin_new_recipient_pseudonym")
            
            submit_button = st.form_submit_button("Create Recipient")
            
            if submit_button:
                if not new_recipient_key:
                    st.error("Recipient Key is required")
                else:
                    success = db.create_recipient(
                        key=new_recipient_key,
                        pseudonym=new_recipient_pseudonym if new_recipient_pseudonym else None
                    )
                    if success:
                        st.success(f"Recipient {new_recipient_key} created successfully")
                    else:
                        st.error("Failed to create recipient")

def render_friend_page():
    """Render the page for users with the Friend role"""
    st.title("KindMesh Friend Dashboard")
    st.write(f"Logged in as: {st.session_state.username} (Role: {st.session_state.role})")

    # Initialize questionnaire section if not set
    if "questionnaire_section" not in st.session_state:
        st.session_state.questionnaire_section = "recipient"
    
    # Initialize questionnaire data if not set
    if "questionnaire_data" not in st.session_state:
        st.session_state.questionnaire_data = {}

    # Tabs for different friend functions
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Log Interaction", "View History", "Search Recipients", "Upload Data", "Questionnaire"])

    with tab1:
        st.header("Log New Interaction")
        
        with st.form("log_interaction_form"):
            recipient_key = st.text_input("Recipient Key (required)", key="log_recipient_key")
            recipient_pseudonym = st.text_input("Recipient Pseudonym (optional)", key="log_recipient_pseudonym")
            
            interaction_type = st.selectbox(
                "Interaction Type",
                ["Food", "Clothing", "Furniture", "Financial Assistance", "Housing", "Medical", "Transportation", "Other"],
                key="log_interaction_type"
            )
            
            if interaction_type == "Other":
                other_type = st.text_input("Specify Other Type", key="log_other_type")
            
            notes = st.text_area("Notes", key="log_notes")
            
            submit_button = st.form_submit_button("Log Interaction")
            
            if submit_button:
                if not recipient_key:
                    st.error("Recipient Key is required")
                else:
                    # Use the "Other" type if specified
                    final_type = other_type if interaction_type == "Other" and other_type else interaction_type
                    
                    success = db.log_interaction(
                        logged_by=st.session_state.username,
                        recipient_key=recipient_key,
                        interaction_type=final_type,
                        notes=notes,
                        recipient_pseudonym=recipient_pseudonym
                    )
                    
                    if success:
                        st.success("Interaction logged successfully")
                    else:
                        st.error("Failed to log interaction")

    with tab2:
        st.header("View Interaction History")
        
        # Get recent interactions for this user
        interactions = db.get_user_interactions(st.session_state.username)
        
        if interactions:
            # Create a DataFrame for display
            interaction_df = pd.DataFrame(interactions)
            
            # Format the DataFrame for display
            if "created_at" in interaction_df.columns:
                interaction_df["created_at"] = pd.to_datetime(interaction_df["created_at"])
                interaction_df = interaction_df.sort_values("created_at", ascending=False)
            
            # Display interactions
            st.dataframe(interaction_df)
            
            # Export button
            csv = interaction_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="my_interactions.csv",
                mime="text/csv"
            )
        else:
            st.write("No interactions found")

    with tab3:
        st.header("Search Recipients")
        
        search_term = st.text_input("Search by Key or Pseudonym", key="search_recipient")
        
        if search_term:
            # Search for recipients
            recipients = db.search_recipients(search_term)
            
            if recipients:
                # Create a DataFrame for display
                recipient_df = pd.DataFrame(recipients)
                
                # Display recipients
                st.dataframe(recipient_df)
                
                # Select a recipient to view details
                selected_recipient = st.selectbox(
                    "Select Recipient to View Details",
                    [f"{r['key']} ({r['pseudonym']})" if r['pseudonym'] else r['key'] for r in recipients],
                    key="search_select_recipient"
                )
                
                # Extract the key from the selection
                recipient_key = selected_recipient.split(" (")[0] if " (" in selected_recipient else selected_recipient
                
                # Get recipient details
                recipient_details = db.get_recipient_details(recipient_key)
                
                if recipient_details:
                    st.subheader(f"Details for {recipient_key}")
                    
                    # Display recipient information
                    st.write(f"**Key:** {recipient_details['key']}")
                    if recipient_details.get('pseudonym'):
                        st.write(f"**Pseudonym:** {recipient_details['pseudonym']}")
                    st.write(f"**Created:** {recipient_details.get('created_at', 'Unknown')}")
                    
                    # Display interaction history
                    if "interactions" in recipient_details and recipient_details["interactions"]:
                        st.write("### Interaction History")
                        interaction_df = pd.DataFrame(recipient_details["interactions"])
                        st.dataframe(interaction_df)
                    else:
                        st.write("No interactions recorded for this recipient")
            else:
                st.write("No recipients found matching your search")

    with tab4:
        st.header("Upload Interaction Data")
        
        uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])
        
        st.write("""
        ### File Format Instructions
        Your file should contain columns for:
        - Recipient Key (required)
        - Interaction Type (optional)
        - Notes (optional)
        - Recipient Pseudonym (optional)
        
        You'll be able to map these columns after uploading.
        """)

    with tab5:
        st.header("Questionnaire")
        
        # Function to navigate between questionnaire sections
        def set_questionnaire_section(section):
            st.session_state.questionnaire_section = section
        
        # Function to save questionnaire data
        def save_questionnaire_section(section, data):
            if "questionnaire_data" not in st.session_state:
                st.session_state.questionnaire_data = {}
            st.session_state.questionnaire_data[section] = data
        
        # Recipient selection/creation
        if st.session_state.questionnaire_section == "recipient":
            st.write("### Recipient Information")
            st.write("Please enter the recipient's key identifier. This will be used to link all questionnaire responses.")
            
            recipient_key = st.text_input("Recipient Key (required)", value=st.session_state.recipient_key if "recipient_key" in st.session_state else "", key="recipient_key_required")
            recipient_pseudonym = st.text_input("Recipient Pseudonym (optional)", key="recipient_pseudonym_optional")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Continue to Questionnaire"):
                    if not recipient_key:
                        st.error("Recipient Key is required")
                    else:
                        st.session_state.recipient_key = recipient_key
                        st.session_state.questionnaire_section = "financial"
                        st.rerun()
            
            # Check if there are existing questionnaire responses for this recipient
            if recipient_key:
                existing_responses = db.get_questionnaire(recipient_key)
                if existing_responses:
                    st.write("### Existing Questionnaire Responses")
                    for response in existing_responses:
                        st.write(f"**Section:** {response['section']}")
                        if response['updated_at']:
                            st.write(f"**Last Updated:** {response['updated_at']}")
                        elif response['created_at']:
                            st.write(f"**Created:** {response['created_at']}")
                    
                    if st.button("View/Edit Existing Responses"):
                        # Load existing responses into session state
                        for response in existing_responses:
                            if "responses" in response and response["responses"]:
                                st.session_state.questionnaire_data[response["section"]] = response["responses"]
                        st.session_state.questionnaire_section = "financial"
                        st.rerun()
        
        # Financial section
        elif st.session_state.questionnaire_section == "financial":
            st.write("### Financial Assessment")
            
            with st.form("financial_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("financial", {})
                
                # Financial questions from the grant proposal
                financial_q1 = st.radio(
                    "How often does this describe you? I don't have enough money to pay my bills:",
                    ["Never", "Rarely", "Sometimes", "Often", "Always"],
                    index=["Never", "Rarely", "Sometimes", "Often", "Always"].index(existing_data.get("financial_q1", "Never")) if "financial_q1" in existing_data else 0
                )
                
                financial_q2 = st.radio(
                    "In the past 12 months has the electric, gas, oil, or water company threatened to shut off services in your home?",
                    ["Yes", "No", "Already shut off"],
                    index=["Yes", "No", "Already shut off"].index(existing_data.get("financial_q2", "No")) if "financial_q2" in existing_data else 1
                )
                
                # Only show this if they selected "Already shut off" or "Yes"
                if financial_q2 in ["Already shut off", "Yes"]:
                    financial_q2_1 = st.radio(
                        "How long ago: If Shut Off, or Notified of a Shut Off",
                        ["1 - 3 Weeks", "1 - 3 Months"],
                        index=["1 - 3 Weeks", "1 - 3 Months"].index(existing_data.get("financial_q2_1", "1 - 3 Weeks")) if "financial_q2_1" in existing_data else 0
                    )
                else:
                    financial_q2_1 = None
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Recipient")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "recipient"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "financial_q1": financial_q1,
                        "financial_q2": financial_q2
                    }
                    if financial_q2_1:
                        data["financial_q2_1"] = financial_q2_1
                    
                    save_questionnaire_section("financial", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "financial",
                        data
                    )
                    
                    if success:
                        st.success("Financial assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "employment"
                            st.rerun()
                    else:
                        st.error("Failed to save financial assessment")
        
        # Employment section
        elif st.session_state.questionnaire_section == "employment":
            st.write("### Employment Assessment")
            
            with st.form("employment_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("employment", {})
                
                # Employment questions from the grant proposal
                employment_q1 = st.radio(
                    "Are you currently employed?",
                    ["Full time", "Part time", "Occasionally", "Not employed"],
                    index=["Full time", "Part time", "Occasionally", "Not employed"].index(existing_data.get("employment_q1", "Not employed")) if "employment_q1" in existing_data else 3
                )
                
                employment_q2 = st.radio(
                    "Do you have a high school degree or GED?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("employment_q2", "No")) if "employment_q2" in existing_data else 1
                )
                
                employment_q3 = st.radio(
                    "Do you have a college degree?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("employment_q3", "No")) if "employment_q3" in existing_data else 1
                )
                
                # Only show this if they selected "Yes" to college degree
                if employment_q3 == "Yes":
                    employment_q3_1 = st.text_input(
                        "If Yes, what is your highest degree level",
                        value=existing_data.get("employment_q3_1", ""),
                        key="employment_q3_1"
                    )
                else:
                    employment_q3_1 = None
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Financial")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "financial"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "employment_q1": employment_q1,
                        "employment_q2": employment_q2,
                        "employment_q3": employment_q3
                    }
                    if employment_q3_1:
                        data["employment_q3_1"] = employment_q3_1
                    
                    save_questionnaire_section("employment", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "employment",
                        data
                    )
                    
                    if success:
                        st.success("Employment assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "transportation"
                            st.rerun()
                    else:
                        st.error("Failed to save employment assessment")
        
        # Transportation section
        elif st.session_state.questionnaire_section == "transportation":
            st.write("### Transportation Assessment")
            
            with st.form("transportation_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("transportation", {})
                
                # Transportation questions from the grant proposal
                transportation_q1 = st.radio(
                    "Do you put off or neglect going to the doctor because of distance or transportation?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("transportation_q1", "No")) if "transportation_q1" in existing_data else 1
                )
                
                transportation_q2 = st.radio(
                    "In the last 3 months, has the lack of transportation kept you from work, medical appointments, getting medication, or getting food?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("transportation_q2", "No")) if "transportation_q2" in existing_data else 1
                )
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Employment")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "employment"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "transportation_q1": transportation_q1,
                        "transportation_q2": transportation_q2
                    }
                    
                    save_questionnaire_section("transportation", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "transportation",
                        data
                    )
                    
                    if success:
                        st.success("Transportation assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "food"
                            st.rerun()
                    else:
                        st.error("Failed to save transportation assessment")
        
        # Food section
        elif st.session_state.questionnaire_section == "food":
            st.write("### Food, Clothing, and Furniture Assessment")
            
            with st.form("food_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("food", {})
                
                # Food questions from the grant proposal
                food_q1 = st.radio(
                    "Within the past 12 months, have you worried that your food would run out before you would have the money to buy more?",
                    ["Often true", "Sometimes true", "Never true"],
                    index=["Often true", "Sometimes true", "Never true"].index(existing_data.get("food_q1", "Never true")) if "food_q1" in existing_data else 2
                )
                
                food_q2 = st.radio(
                    "Within the past 12 months, the food you bought didn't last and you didn't have money to buy more?",
                    ["Often true", "Sometimes true", "Never true"],
                    index=["Often true", "Sometimes true", "Never true"].index(existing_data.get("food_q2", "Never true")) if "food_q2" in existing_data else 2
                )
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Transportation")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "transportation"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "food_q1": food_q1,
                        "food_q2": food_q2
                    }
                    
                    save_questionnaire_section("food", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "food",
                        data
                    )
                    
                    if success:
                        st.success("Food assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "care"
                            st.rerun()
                    else:
                        st.error("Failed to save food assessment")
        
        # Care section
        elif st.session_state.questionnaire_section == "care":
            st.write("### Child Care, Elder Care, Sick Spouse or Partner Assessment")
            
            with st.form("care_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("care", {})
                
                # Care questions from the grant proposal
                care_q1 = st.radio(
                    "Do problems finding regular, affordable, and dependable care for children, elderly family members, or sick family members make it difficult to work, go to school, or care for yourself or family?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("care_q1", "No")) if "care_q1" in existing_data else 1
                )
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Food")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "food"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "care_q1": care_q1
                    }
                    
                    save_questionnaire_section("care", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "care",
                        data
                    )
                    
                    if success:
                        st.success("Care assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "medical"
                            st.rerun()
                    else:
                        st.error("Failed to save care assessment")
        
        # Medical section
        elif st.session_state.questionnaire_section == "medical":
            st.write("### Medical and Dental Care Assessment")
            
            with st.form("medical_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("medical", {})
                
                # Medical questions from the grant proposal
                medical_q1 = st.radio(
                    "Are you, or have you over the last 3 months experienced persistent pain or physical illness that you thought needed medical attention?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("medical_q1", "No")) if "medical_q1" in existing_data else 1
                )
                
                # Only show this if they selected "Yes"
                if medical_q1 == "Yes":
                    medical_q1_1 = st.radio(
                        "If Yes, How long have you experienced this?",
                        ["Less than 1 month", "1 - 3 months"],
                        index=["Less than 1 month", "1 - 3 months"].index(existing_data.get("medical_q1_1", "Less than 1 month")) if "medical_q1_1" in existing_data else 0
                    )
                else:
                    medical_q1_1 = None
                
                medical_q2 = st.radio(
                    "In the last 3 months, did you skip buying medications or going to the doctor to save money?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("medical_q2", "No")) if "medical_q2" in existing_data else 1
                )
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Care")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "care"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "medical_q1": medical_q1,
                        "medical_q2": medical_q2
                    }
                    if medical_q1_1:
                        data["medical_q1_1"] = medical_q1_1
                    
                    save_questionnaire_section("medical", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "medical",
                        data
                    )
                    
                    if success:
                        st.success("Medical assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "benefits"
                            st.rerun()
                    else:
                        st.error("Failed to save medical assessment")
        
        # Benefits section
        elif st.session_state.questionnaire_section == "benefits":
            st.write("### Federal and State Benefits Assessment")
            
            with st.form("benefits_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("benefits", {})
                
                # Benefits questions from the grant proposal
                benefits_q1 = st.radio(
                    "Are you a veteran?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("benefits_q1", "No")) if "benefits_q1" in existing_data else 1
                )
                
                benefits_q2_options = ["Medicare/Medicaid", "Social Security", "Housing/Rental assistance"]
                benefits_q2_default = existing_data.get("benefits_q2", []) if "benefits_q2" in existing_data else []
                benefits_q2 = st.multiselect(
                    "Have you filed, or received help in filing, for Federal or State assistance to receive:",
                    options=benefits_q2_options,
                    default=benefits_q2_default
                )
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Medical")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "medical"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "benefits_q1": benefits_q1,
                        "benefits_q2": benefits_q2
                    }
                    
                    save_questionnaire_section("benefits", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "benefits",
                        data
                    )
                    
                    if success:
                        st.success("Benefits assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "mental_health"
                            st.rerun()
                    else:
                        st.error("Failed to save benefits assessment")
        
        # Mental Health section
        elif st.session_state.questionnaire_section == "mental_health":
            st.write("### Mental Health Assessment")
            
            with st.form("mental_health_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("mental_health", {})
                
                # Mental Health questions from the grant proposal
                mental_health_options = [
                    "Little interest or pleasure in doing things",
                    "Feeling down, depressed, hopeless",
                    "Trouble falling asleep, staying asleep, or sleeping too much",
                    "Feeling tired or having little energy",
                    "Little appetite or Overeating",
                    "Feeling bad about yourself, feeling you are a failure, feeling you have let yourself or family down",
                    "Trouble concentrating on things, reading, watching TV, listening to others",
                    "Moving or speaking so slowly that others have noticed",
                    "Moving or speaking so quickly, being fidgety, restless, can't stop moving more than usual",
                    "Thoughts that you would be better off dead or feelings of hurting yourself"
                ]
                mental_health_default = existing_data.get("mental_health_q1", []) if "mental_health_q1" in existing_data else []
                mental_health_q1 = st.multiselect(
                    "Over the past 4 weeks, have you experienced any of the following;",
                    options=mental_health_options,
                    default=mental_health_default
                )
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Benefits")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "benefits"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "mental_health_q1": mental_health_q1
                    }
                    
                    save_questionnaire_section("mental_health", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "mental_health",
                        data
                    )
                    
                    if success:
                        st.success("Mental Health assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "housing"
                            st.rerun()
                    else:
                        st.error("Failed to save mental health assessment")
        
        # Housing section
        elif st.session_state.questionnaire_section == "housing":
            st.write("### Housing/Safe Shelter Assessment")
            
            with st.form("housing_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("housing", {})
                
                # Housing questions from the grant proposal
                housing_q1 = st.radio(
                    "Are you worried or concerned that within the next 2 months you may not have consistent housing that you own, rent, or stay in as part of a household?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("housing_q1", "No")) if "housing_q1" in existing_data else 1
                )
                
                housing_problems_options = [
                    "Bug infestation",
                    "Mold",
                    "Lead paint or pipes",
                    "Inadequate heat or cold air",
                    "Oven or stove not working properly",
                    "No smoke detectors, not working smoke detectors",
                    "Water leaks"
                ]
                housing_problems_default = existing_data.get("housing_q2", []) if "housing_q2" in existing_data else []
                housing_q2 = st.multiselect(
                    "Think about the place you live. Do you have problems with;",
                    options=housing_problems_options,
                    default=housing_problems_default
                )
                
                housing_q3 = st.radio(
                    "In the last 12 months has there been a safety concern with electric, water, sewer, gas, oil services or related appliances where you are living?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("housing_q3", "No")) if "housing_q3" in existing_data else 1
                )
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Mental Health")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "mental_health"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "housing_q1": housing_q1,
                        "housing_q2": housing_q2,
                        "housing_q3": housing_q3
                    }
                    
                    save_questionnaire_section("housing", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "housing",
                        data
                    )
                    
                    if success:
                        st.success("Housing assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "legal"
                            st.rerun()
                    else:
                        st.error("Failed to save housing assessment")
        
        # Legal section
        elif st.session_state.questionnaire_section == "legal":
            st.write("### Legal Services Assessment")
            
            with st.form("legal_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("legal", {})
                
                # Legal questions from the grant proposal
                legal_options = ["Child/Family", "Immigration", "Housing/rental", "Discrimination", "Domestic issues"]
                legal_default = existing_data.get("legal_q1", []) if "legal_q1" in existing_data else []
                legal_q1 = st.multiselect(
                    "Do you need legal services for:",
                    options=legal_options,
                    default=legal_default
                )
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Housing")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "housing"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "legal_q1": legal_q1
                    }
                    
                    save_questionnaire_section("legal", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "legal",
                        data
                    )
                    
                    if success:
                        st.success("Legal assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "relationships"
                            st.rerun()
                    else:
                        st.error("Failed to save legal assessment")
        
        # Relationships section
        elif st.session_state.questionnaire_section == "relationships":
            st.write("### Relationships Assessment")
            
            with st.form("relationships_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("relationships", {})
                
                # Relationships questions from the grant proposal
                relationships_q1 = st.radio(
                    "Are you finding it hard to get along with a spouse, partner, or family member(s) that is causing stress?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("relationships_q1", "No")) if "relationships_q1" in existing_data else 1
                )
                
                relationships_q2 = st.radio(
                    "Does anyone, including family, physically hurt you?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("relationships_q2", "No")) if "relationships_q2" in existing_data else 1
                )
                
                relationships_q3 = st.radio(
                    "Does anyone, including family, insult or talk down to you?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("relationships_q3", "No")) if "relationships_q3" in existing_data else 1
                )
                
                relationships_q4 = st.radio(
                    "Does anyone, including family, threaten to harm you?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("relationships_q4", "No")) if "relationships_q4" in existing_data else 1
                )
                
                relationships_q5 = st.radio(
                    "Does anyone, including family, scream or curse at you?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("relationships_q5", "No")) if "relationships_q5" in existing_data else 1
                )
                
                relationships_q6 = st.radio(
                    "Does anyone, including family, frighten you, hurt you, or make you feel unsafe?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("relationships_q6", "No")) if "relationships_q6" in existing_data else 1
                )
                
                relationships_q7 = st.radio(
                    "Experiencing those items listed above, do they cause you not to do things daily you want to do?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("relationships_q7", "No")) if "relationships_q7" in existing_data else 1
                )
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Legal")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "legal"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "relationships_q1": relationships_q1,
                        "relationships_q2": relationships_q2,
                        "relationships_q3": relationships_q3,
                        "relationships_q4": relationships_q4,
                        "relationships_q5": relationships_q5,
                        "relationships_q6": relationships_q6,
                        "relationships_q7": relationships_q7
                    }
                    
                    save_questionnaire_section("relationships", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "relationships",
                        data
                    )
                    
                    if success:
                        st.success("Relationships assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "community"
                            st.rerun()
                    else:
                        st.error("Failed to save relationships assessment")
        
        # Community section
        elif st.session_state.questionnaire_section == "community":
            st.write("### Community Involvement Assessment")
            
            with st.form("community_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("community", {})
                
                # Community questions from the grant proposal
                community_q1 = st.radio(
                    "Do you visit your local park, the library, church, or are you involved in a club or sport?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("community_q1", "No")) if "community_q1" in existing_data else 1
                )
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Relationships")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "relationships"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "community_q1": community_q1
                    }
                    
                    save_questionnaire_section("community", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "community",
                        data
                    )
                    
                    if success:
                        st.success("Community assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "mentor"
                            st.rerun()
                    else:
                        st.error("Failed to save community assessment")
        
        # Mentor section
        elif st.session_state.questionnaire_section == "mentor":
            st.write("### Mentor Assessment")
            
            with st.form("mentor_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("mentor", {})
                
                # Mentor questions from the grant proposal
                mentor_q1 = st.radio(
                    "Do you have anyone you trust and can count on to ask important personal questions?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("mentor_q1", "No")) if "mentor_q1" in existing_data else 1
                )
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Community")
                with col2:
                    submit_button = st.form_submit_button("Save and Continue")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "community"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "mentor_q1": mentor_q1
                    }
                    
                    save_questionnaire_section("mentor", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "mentor",
                        data
                    )
                    
                    if success:
                        st.success("Mentor assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "spiritual"
                            st.rerun()
                    else:
                        st.error("Failed to save mentor assessment")
        
        # Spiritual section
        elif st.session_state.questionnaire_section == "spiritual":
            st.write("### Spiritual Focused Care Assessment")
            
            with st.form("spiritual_form"):
                # Load existing data if available
                existing_data = st.session_state.questionnaire_data.get("spiritual", {})
                
                # Spiritual questions from the grant proposal
                spiritual_q1 = st.radio(
                    "Do you have someone you can turn to for questions concerning faith, spiritual matters, prayer, or questions about God?",
                    ["Yes", "No"],
                    index=["Yes", "No"].index(existing_data.get("spiritual_q1", "No")) if "spiritual_q1" in existing_data else 1
                )
                
                # Form submission buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    back_button = st.form_submit_button("Back to Mentor")
                with col2:
                    submit_button = st.form_submit_button("Save and Complete")
                with col3:
                    save_button = st.form_submit_button("Save Only")
                
                if back_button:
                    st.session_state.questionnaire_section = "mentor"
                    st.rerun()
                
                if submit_button or save_button:
                    # Save the data
                    data = {
                        "spiritual_q1": spiritual_q1
                    }
                    
                    save_questionnaire_section("spiritual", data)
                    
                    # Save to database
                    success = db.save_questionnaire(
                        st.session_state.recipient_key,
                        "spiritual",
                        data
                    )
                    
                    if success:
                        st.success("Spiritual assessment saved successfully")
                        if submit_button:
                            st.session_state.questionnaire_section = "summary"
                            st.rerun()
                    else:
                        st.error("Failed to save spiritual assessment")
        
        # Summary section
        elif st.session_state.questionnaire_section == "summary":
            st.write("### Questionnaire Summary")
            st.write(f"Thank you for completing the questionnaire for recipient: **{st.session_state.recipient_key}**")
            
            # Display summary of all sections
            st.write("#### Completed Sections:")
            
            # Get all questionnaire data for this recipient
            all_responses = db.get_questionnaire(st.session_state.recipient_key)
            
            if all_responses:
                for response in all_responses:
                    section = response["section"]
                    st.write(f"- **{section.capitalize()}** section completed")
                    if response["updated_at"]:
                        st.write(f"  Last updated: {response['updated_at']}")
                    elif response["created_at"]:
                        st.write(f"  Created: {response['created_at']}")
            
            # Button to start a new questionnaire
            if st.button("Start New Questionnaire"):
                st.session_state.questionnaire_section = "recipient"
                st.session_state.recipient_key = ""
                st.session_state.questionnaire_data = {}
                st.rerun()
            
            # Button to edit current questionnaire
            if st.button("Edit Current Questionnaire"):
                st.session_state.questionnaire_section = "financial"
                st.rerun()
        
        if uploaded_file is not None:
            try:
                # Determine file type and read accordingly
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success(f"File uploaded successfully: {uploaded_file.name}")
                
                # Display the first few rows of the spreadsheet
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                # Scan for sections in the spreadsheet
                sections = []
                current_section = "Main"
                section_start_rows = {current_section: 0}
                section_end_rows = {}
                
                for i, row in df.iterrows():
                    # Check if this row might be a section header
                    # Look for rows where first column has text but second column is empty
                    # or rows that have specific section indicators
                    first_col_value = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else ""
                    
                    # Check if this might be a section header
                    if (first_col_value and 
                        (pd.isna(row.iloc[1]) if len(row) > 1 else True) and
                        any(keyword in first_col_value for keyword in ["Follow-Up", "Pledge", "Notes", "Referred", "Update"])):
                        
                        # End the previous section
                        section_end_rows[current_section] = i - 1
                        
                        # Start a new section
                        current_section = first_col_value
                        sections.append(current_section)
                        section_start_rows[current_section] = i
                
                # End the last section
                section_end_rows[current_section] = len(df) - 1
                
                # If no sections were found, use the entire spreadsheet as one section
                if len(sections) == 0:
                    sections = ["Main"]
                    section_start_rows["Main"] = 0
                    section_end_rows["Main"] = len(df) - 1
                
                # Let user select which sections to import
                st.write("### Select sections to import")
                selected_sections = {}
                
                for section in sections:
                    selected_sections[section] = st.checkbox(f"Import {section}", value=True)
                
                # For each selected section, let user map columns
                if any(selected_sections.values()):
                    st.write("### Map columns for each section")
                    
                    # Process each selected section
                    for section in sections:
                        if selected_sections[section]:
                            st.write(f"#### Section: {section}")
                            
                            # Get the section data
                            section_df = df.iloc[section_start_rows[section]:section_end_rows[section]+1].copy()
                            
                            # Display section preview
                            st.write(f"Preview of section '{section}':")
                            st.dataframe(section_df.head())
                            
                            # Get column names for mapping
                            column_options = [""] + list(section_df.columns)
                            
                            # Create column mapping
                            st.write("Map columns to required fields:")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                recipient_key_col = st.selectbox(
                                    "Recipient Key (required)", 
                                    column_options,
                                    key=f"{section}_recipient_key"
                                )
                                
                                interaction_type_col = st.selectbox(
                                    "Interaction Type", 
                                    column_options,
                                    key=f"{section}_interaction_type"
                                )
                            
                            with col2:
                                recipient_pseudonym_col = st.selectbox(
                                    "Recipient Pseudonym (optional)", 
                                    column_options,
                                    key=f"{section}_recipient_pseudonym"
                                )
                                
                                notes_col = st.selectbox(
                                    "Notes (optional)", 
                                    column_options,
                                    key=f"{section}_notes"
                                )
                            
                            # Default interaction type if not mapped
                            default_interaction_type = st.text_input(
                                "Default Interaction Type (if not mapped)", 
                                "Other",
                                key=f"{section}_default_type"
                            )
                    
                    # Process button
                    if st.button("Process and Import Data"):
                        total_imported = 0
                        total_errors = 0
                        
                        for section in sections:
                            if selected_sections[section]:
                                # Get the section data
                                section_df = df.iloc[section_start_rows[section]:section_end_rows[section]+1].copy()
                                
                                # Get the column mappings for this section
                                recipient_key_col = st.session_state[f"{section}_recipient_key"]
                                interaction_type_col = st.session_state[f"{section}_interaction_type"]
                                recipient_pseudonym_col = st.session_state[f"{section}_recipient_pseudonym"]
                                notes_col = st.session_state[f"{section}_notes"]
                                default_interaction_type = st.session_state[f"{section}_default_type"]
                                
                                # Validate required fields
                                if not recipient_key_col:
                                    st.error(f"Recipient Key column must be selected for section '{section}'")
                                    continue
                                
                                # Process each row in the section
                                for i, row in section_df.iterrows():
                                    try:
                                        # Skip rows with empty recipient key
                                        if pd.isna(row[recipient_key_col]):
                                            continue
                                        
                                        # Get values from the row
                                        recipient_key = str(row[recipient_key_col])
                                        
                                        # Get interaction type (use default if not mapped or empty)
                                        interaction_type = default_interaction_type
                                        if interaction_type_col and not pd.isna(row[interaction_type_col]):
                                            interaction_type = str(row[interaction_type_col])
                                        
                                        # Get optional fields
                                        recipient_pseudonym = None
                                        if recipient_pseudonym_col and not pd.isna(row[recipient_pseudonym_col]):
                                            recipient_pseudonym = str(row[recipient_pseudonym_col])
                                        
                                        notes = None
                                        if notes_col and not pd.isna(row[notes_col]):
                                            notes = str(row[notes_col])
                                        
                                        # Log the interaction
                                        success = db.log_interaction(
                                            logged_by=st.session_state.username,
                                            recipient_key=recipient_key,
                                            interaction_type=interaction_type,
                                            notes=notes,
                                            recipient_pseudonym=recipient_pseudonym
                                        )
                                        
                                        if success:
                                            total_imported += 1
                                        else:
                                            total_errors += 1
                                    
                                    except Exception as e:
                                        st.error(f"Error processing row {i}: {str(e)}")
                                        total_errors += 1
                        
                        # Show results
                        st.success(f"Import completed: {total_imported} interactions imported successfully.")
                        if total_errors > 0:
                            st.warning(f"{total_errors} errors occurred during import.")
            
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.info("Please make sure your file is properly formatted and try again.")

# Main app logic
def main():
    # Add a sidebar with logout button if authenticated
    if st.session_state.authenticated:
        with st.sidebar:
            st.write(f"Logged in as: {st.session_state.username}")
            st.write(f"Role: {st.session_state.role}")
            if st.button("Logout"):
                logout()
                st.rerun()
    
    # Render the appropriate page based on authentication status and role
    if not st.session_state.authenticated:
        render_login_page()
    else:
        if st.session_state.role == "Greeter":
            render_greeter_page()
        elif st.session_state.role == "Admin":
            render_admin_page()
        else:  # Friend role
            render_friend_page()

if __name__ == "__main__":
    main()