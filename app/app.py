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
    # Import here to ensure we get the latest version of the class
    from utils.graph import GraphDatabase
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
        password = st.text_input("Password", type="password", key="_username___________password___st_text_input__password_")
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
        new_password = st.text_input("Password", type="password", key="_username___________new_password___st_text_input__password_")
        confirm_password = st.text_input("Confirm Password", type="password", key="_confirm_password_")
        submit_button = st.form_submit_button("Create User")

        if submit_button:
            if not new_username or not new_password:
                st.error("Username and password are required")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                success = db.create_user(
                    username=new_username,
                    password=new_password,
                    created_by=st.session_state.username
                )
                if success:
                    st.success(f"User {new_username} created successfully")
                else:
                    st.error("Failed to create user")

def render_admin_page():
    """Render the page for users with the Admin role"""
    st.title("KindMesh Admin Dashboard")
    st.write(f"Logged in as: {st.session_state.username} (Role: {st.session_state.role})")

    # Create tabs for different admin functions
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["User Management", "Log Interaction", "View Data", "Export Data", "Survey Management"])

    with tab1:
        st.subheader("User Management")

        # Get all users
        users = db.get_all_users()

        # Display users in a table
        if users:
            user_df = pd.DataFrame(users)
            st.dataframe(user_df)

            # User promotion section
            st.subheader("Promote User to Admin")
            non_admin_users = [user["username"] for user in users if user["role"] != "Admin" and user["username"] != st.session_state.username]

            if non_admin_users:
                user_to_promote = st.selectbox("Select user to promote", non_admin_users)
                if st.button("Promote to Admin"):
                    success = db.promote_user(user_to_promote, st.session_state.username)
                    if success:
                        st.success(f"User {user_to_promote} promoted to Admin")
                        st.rerun()
                    else:
                        st.error("Failed to promote user")
            else:
                st.info("No users available for promotion")

            # Admin demotion section
            st.subheader("Demote Admin to Friend")
            admin_users = [user["username"] for user in users if user["role"] == "Admin" and user["username"] != st.session_state.username]

            if admin_users:
                user_to_demote = st.selectbox("Select admin to demote", admin_users)

                # Initialize votes for this user if not already done
                if user_to_demote not in st.session_state.admin_demotion_votes:
                    st.session_state.admin_demotion_votes[user_to_demote] = []

                # Check if current user has already voted
                current_user_voted = st.session_state.username in st.session_state.admin_demotion_votes[user_to_demote]

                # Display current votes
                vote_count = len(st.session_state.admin_demotion_votes[user_to_demote])
                st.write(f"Current votes for demotion: {vote_count}/2")

                # Vote button
                vote_button_label = "Remove Vote" if current_user_voted else "Vote to Demote"
                if st.button(vote_button_label):
                    if current_user_voted:
                        st.session_state.admin_demotion_votes[user_to_demote].remove(st.session_state.username)
                        st.success(f"Vote removed for demoting {user_to_demote}")
                    else:
                        st.session_state.admin_demotion_votes[user_to_demote].append(st.session_state.username)
                        st.success(f"Vote added for demoting {user_to_demote}")

                    # Check if we have enough votes to demote
                    if len(st.session_state.admin_demotion_votes[user_to_demote]) >= 2:
                        success = db.demote_admin(
                            user_to_demote, 
                            st.session_state.admin_demotion_votes[user_to_demote]
                        )
                        if success:
                            st.success(f"Admin {user_to_demote} demoted to Friend")
                            # Reset votes for this user
                            st.session_state.admin_demotion_votes[user_to_demote] = []
                            st.rerun()
                        else:
                            st.error("Failed to demote admin")
            else:
                st.info("No admins available for demotion")

            # Delete user section
            st.subheader("Delete User")
            users_to_delete = [user["username"] for user in users if user["username"] != st.session_state.username]

            if users_to_delete:
                user_to_delete = st.selectbox("Select user to delete", users_to_delete, key="user_to_delete")
                if st.button("Delete User"):
                    if user_to_delete == st.session_state.username:
                        st.error("You cannot delete yourself")
                    else:
                        success = db.delete_user(user_to_delete)
                        if success:
                            st.success(f"User {user_to_delete} deleted successfully")
                            st.rerun()
                        else:
                            st.error("Failed to delete user")
            else:
                st.info("No users available for deletion")

            # Create new user section
            st.subheader("Create New User")
            with st.form("admin_create_user_form"):
                new_username = st.text_input("Username", key="admin_new_username")
                new_password = st.text_input("Password", type="password", key="_username___________________new_password___st_text_input__password_")
                confirm_password = st.text_input("Confirm Password", type="password", key="_confirm_password_")
                new_role = st.selectbox("Role", ["Friend", "Admin"])
                submit_button = st.form_submit_button("Create User")

                if submit_button:
                    if not new_username or not new_password:
                        st.error("Username and password are required")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success = db.create_user(
                            username=new_username,
                            password=new_password,
                            role=new_role,
                            created_by=st.session_state.username
                        )
                        if success:
                            st.success(f"User {new_username} created successfully with role {new_role}")
                        else:
                            st.error("Failed to create user")
        else:
            st.warning("No users found in the database")

    with tab2:
        st.subheader("Log Resource Distribution")

        # Get all recipient keys for dropdown
        recipient_keys = db.get_all_recipient_keys()

        with st.form("log_interaction_form"):
            # If there are recipient keys, use a selectbox, otherwise use text input
            if recipient_keys:
                recipient_key = st.selectbox("Recipient Key (required)", options=[""] + recipient_keys, key="admin_recipient_key_dropdown")

                # Auto-fill pseudonym when recipient key is selected
                recipient_pseudonym = ""
                if recipient_key:
                    recipient = db.get_recipient(recipient_key)
                    if recipient and recipient.get('pseudonym'):
                        recipient_pseudonym = recipient['pseudonym']

                recipient_pseudonym = st.text_input("Recipient Pseudonym (auto-filled if available)", 
                                                  value=recipient_pseudonym,
                                                  key="recipient_pseudonym_optional_1")
            else:
                st.warning("No recipients found. Please create recipients in the Recipient panel first.")
                recipient_key = st.text_input("Recipient Key (required)", key="text_input_3908")
                recipient_pseudonym = st.text_input("Recipient Pseudonym (optional)", key="recipient_pseudonym_optional_1")

            interaction_type = st.selectbox("Resource Type", ["Food", "Clothing", "Shelter", "Healthcare", "Education", "Financial", "Other"], key="_recipient_key__required________________recipient_pseudonym___st_text_input__recipient_pseudonym__optional________________interaction_type___st_selectbox__resource_type_")
            notes = st.text_area("Notes")
            submit_button = st.form_submit_button("Log Interaction")

            if submit_button:
                if not recipient_key:
                    st.error("Recipient Key is required")
                else:
                    success = db.log_interaction(
                        logged_by=st.session_state.username,
                        recipient_key=recipient_key,
                        interaction_type=interaction_type,
                        notes=notes,
                        recipient_pseudonym=recipient_pseudonym if recipient_pseudonym else None
                    )
                    if success:
                        st.success("Interaction logged successfully")
                    else:
                        st.error("Failed to log interaction")

    with tab3:
        st.subheader("View Data")

        # Summary statistics
        stats = db.get_summary_stats()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Interactions", stats["total_interactions"])
        with col2:
            st.metric("Total Recipients", stats["total_recipients"])

        # Interaction types breakdown
        if stats["interaction_types"]:
            st.subheader("Interaction Types")
            interaction_df = pd.DataFrame(stats["interaction_types"])

            # Display as table
            st.dataframe(interaction_df)

            # Display as chart
            st.bar_chart(interaction_df.set_index("type")["count"])

        # Recent interactions
        st.subheader("Recent Interactions")
        interactions = db.get_interactions(limit=50)

        if interactions:
            interactions_df = pd.DataFrame(interactions)
            st.dataframe(interactions_df)
        else:
            st.info("No interactions recorded yet")

    with tab4:
        st.subheader("Export Data")

        # Get all interaction data
        all_interactions = db.export_interactions_data()

        if all_interactions:
            interactions_df = pd.DataFrame(all_interactions)

            # Export options
            export_format = st.radio("Export Format", ["CSV", "JSON"])

            if export_format == "CSV":
                csv = interactions_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"kindmesh_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:  # JSON
                json_data = interactions_df.to_json(orient="records")
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"kindmesh_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        else:
            st.info("No data available for export")

    with tab5:
        st.subheader("Survey Management")

        # Get all existing surveys
        surveys = db.get_all_surveys()

        # Display existing surveys
        if surveys:
            st.write("### Existing Surveys")
            for survey in surveys:
                with st.expander(f"{survey['name']} - {len(survey['sections'])} sections"):
                    st.write(f"**Description:** {survey['description']}")
                    st.write(f"**Created by:** {survey['created_by']}")
                    st.write(f"**Created at:** {survey['created_at']}")

                    # Display sections and questions
                    for i, section in enumerate(survey['sections']):
                        st.write(f"**Section {i+1}:** {section['name']}")
                        for j, question in enumerate(section['questions']):
                            st.write(f"  - Question {j+1}: {question['text']} ({question['type']})")
                            if 'options' in question and question['options']:
                                st.write(f"    Options: {', '.join(question['options'])}")

                    # Edit and delete buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Edit Survey", key=f"edit_{survey['id']}"):
                            st.session_state.editing_survey = survey
                            st.rerun()
                    with col2:
                        if st.button(f"Delete Survey", key=f"delete_{survey['id']}"):
                            success = db.delete_survey(survey['id'])
                            if success:
                                st.success(f"Survey '{survey['name']}' deleted successfully")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete survey '{survey['name']}'")
        else:
            st.info("No surveys created yet")

        # Create new survey form
        st.write("### Create New Survey")

        # Initialize state for survey creation
        if "survey_sections" not in st.session_state:
            st.session_state.survey_sections = [{"name": "Section 1", "questions": [{"text": "", "type": "text", "options": []}]}]

        # Survey basic info
        survey_name = st.text_input("Survey Name", key="new_survey_name")
        survey_description = st.text_area("Survey Description", key="new_survey_description")

        # Section management
        st.write("### Survey Sections")

        # Display and edit sections
        for i, section in enumerate(st.session_state.survey_sections):
            with st.expander(f"Section {i+1}: {section['name']}", expanded=True):
                # Section name
                section_name = st.text_input("Section Name", value=section['name'], key=f"section_name_{i}")
                st.session_state.survey_sections[i]['name'] = section_name

                # Questions
                st.write("#### Questions")
                for j, question in enumerate(section['questions']):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        question_text = st.text_input("Question Text", value=question['text'], key=f"question_text_{i}_{j}")
                        st.session_state.survey_sections[i]['questions'][j]['text'] = question_text
                    with col2:
                        question_type = st.selectbox("Type", ["text", "radio", "checkbox", "number"], 
                                                   index=["text", "radio", "checkbox", "number"].index(question['type']) if question['type'] in ["text", "radio", "checkbox", "number"] else 0,
                                                   key=f"question_type_{i}_{j}")
                        st.session_state.survey_sections[i]['questions'][j]['type'] = question_type

                    # Options for radio and checkbox questions
                    if question_type in ["radio", "checkbox"]:
                        options_str = st.text_input("Options (comma-separated)", 
                                                  value=",".join(question['options']) if 'options' in question and question['options'] else "",
                                                  key=f"question_options_{i}_{j}")
                        st.session_state.survey_sections[i]['questions'][j]['options'] = [opt.strip() for opt in options_str.split(",") if opt.strip()]

                    # Delete question button
                    if len(section['questions']) > 1:
                        if st.button("Delete Question", key=f"delete_question_{i}_{j}"):
                            st.session_state.survey_sections[i]['questions'].pop(j)
                            st.rerun()

                    st.divider()

                # Add question button
                if st.button("Add Question", key=f"add_question_{i}"):
                    st.session_state.survey_sections[i]['questions'].append({"text": "", "type": "text", "options": []})
                    st.rerun()

                # Delete section button
                if len(st.session_state.survey_sections) > 1:
                    if st.button("Delete Section", key=f"delete_section_{i}"):
                        st.session_state.survey_sections.pop(i)
                        st.rerun()

        # Add section button
        if st.button("Add Section"):
            st.session_state.survey_sections.append({"name": f"Section {len(st.session_state.survey_sections) + 1}", "questions": [{"text": "", "type": "text", "options": []}]})
            st.rerun()

        # Create survey button
        if st.button("Create Survey"):
            if not survey_name:
                st.error("Survey name is required")
            elif not survey_description:
                st.error("Survey description is required")
            else:
                # Validate sections and questions
                valid = True
                for i, section in enumerate(st.session_state.survey_sections):
                    if not section['name']:
                        st.error(f"Section {i+1} name is required")
                        valid = False
                        break

                    for j, question in enumerate(section['questions']):
                        if not question['text']:
                            st.error(f"Question text is required in section {i+1}, question {j+1}")
                            valid = False
                            break

                        if question['type'] in ["radio", "checkbox"] and (not 'options' in question or not question['options']):
                            st.error(f"Options are required for radio/checkbox questions in section {i+1}, question {j+1}")
                            valid = False
                            break

                if valid:
                    # Create the survey
                    survey_id = db.create_survey(
                        name=survey_name,
                        description=survey_description,
                        sections=st.session_state.survey_sections,
                        created_by=st.session_state.username
                    )

                    if survey_id:
                        st.success(f"Survey '{survey_name}' created successfully")
                        # Reset the form
                        st.session_state.survey_sections = [{"name": "Section 1", "questions": [{"text": "", "type": "text", "options": []}]}]
                        st.rerun()
                    else:
                        st.error("Failed to create survey")

def render_friend_page():
    """Render the page for users with the Friend role"""
    st.title("KindMesh Dashboard")
    st.write(f"Logged in as: {st.session_state.username} (Role: {st.session_state.role})")

    # Initialize questionnaire section if not set
    if "questionnaire_section" not in st.session_state:
        st.session_state.questionnaire_section = "recipient"

    # Initialize questionnaire data if not set
    if "questionnaire_data" not in st.session_state:
        st.session_state.questionnaire_data = {}

    # Function to navigate between questionnaire sections
    def set_questionnaire_section(section):
        st.session_state.questionnaire_section = section

    # Function to save questionnaire data
    def save_questionnaire_section(section, data):
        if "questionnaire_data" not in st.session_state:
            st.session_state.questionnaire_data = {}
        st.session_state.questionnaire_data[section] = data

    # Create tabs for different functions
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Interaction", "View Data", "Batch Entry", "Survey", "Recipient"])

    with tab1:
        st.subheader("Details")

        # Get all recipient keys for dropdown
        recipient_keys = db.get_all_recipient_keys()

        with st.form("friend_log_interaction_form"):
            # If there are recipient keys, use a selectbox, otherwise use text input
            if recipient_keys:
                recipient_key = st.selectbox("Recipient Key (required)", options=[""] + recipient_keys)
            else:
                recipient_key = st.text_input("Recipient Key (required)", key="text_input_3908")

            recipient_pseudonym = st.text_input("Recipient Pseudonym (optional)", key="recipient_pseudonym_optional_2")
            interaction_type = st.selectbox("Resource Type", ["Food", "Clothing", "Shelter", "Healthcare", "Education", "Financial", "Other"], key="_recipient_key__required_________________recipient_pseudonym___st_text_input__recipient_pseudonym__optional________________interaction_type___st_selectbox__resource_type_")
            notes = st.text_area("Notes")
            submit_button = st.form_submit_button("Log Interaction")

            if submit_button:
                if not recipient_key:
                    st.error("Recipient Key is required")
                else:
                    success = db.log_interaction(
                        logged_by=st.session_state.username,
                        recipient_key=recipient_key,
                        interaction_type=interaction_type,
                        notes=notes,
                        recipient_pseudonym=recipient_pseudonym if recipient_pseudonym else None
                    )
                    if success:
                        st.success("Interaction logged successfully")
                    else:
                        st.error("Failed to log interaction")

    with tab2:
        st.subheader("View Data")

        # Summary statistics
        stats = db.get_summary_stats()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Interactions", stats["total_interactions"])
        with col2:
            st.metric("Total Recipients", stats["total_recipients"])

        # Recent interactions
        st.subheader("Recent Interactions")
        interactions = db.get_interactions(limit=20)

        if interactions:
            interactions_df = pd.DataFrame(interactions)
            st.dataframe(interactions_df)
        else:
            st.info("No interactions recorded yet")

    with tab3:
        st.subheader("Batch Entry from Spreadsheet")

        # File upload
        uploaded_file = st.file_uploader("Upload spreadsheet", type=["xlsx", "xls", "csv"])

    with tab4:
        st.subheader("Survey")

        # Initialize survey state if not exists
        if "survey_section" not in st.session_state:
            st.session_state.survey_section = "recipient"
        if "survey_data" not in st.session_state:
            st.session_state.survey_data = {}
        if "recipient_key" not in st.session_state:
            st.session_state.recipient_key = ""
        if "selected_survey_id" not in st.session_state:
            st.session_state.selected_survey_id = None

        # Function to navigate between survey sections
        def set_survey_section(section):
            st.session_state.survey_section = section

        # Function to save survey data
        def save_survey_section(section, data):
            if "survey_data" not in st.session_state:
                st.session_state.survey_data = {}
            st.session_state.survey_data[section] = data

        # Recipient selection/creation
        if st.session_state.survey_section == "recipient":
            st.write("### Recipient Information")
            st.write("Please select the recipient's key identifier. This will be used to link all survey responses.")

            # Get all recipient keys for dropdown
            recipient_keys = db.get_all_recipient_keys()

            if recipient_keys:
                recipient_key = st.selectbox("Recipient Key (required)", 
                                           options=[""] + recipient_keys, 
                                           index=recipient_keys.index(st.session_state.recipient_key) + 1 if "recipient_key" in st.session_state and st.session_state.recipient_key in recipient_keys else 0,
                                           key="recipient_key_dropdown")

                # Auto-fill pseudonym when recipient key is selected
                recipient_pseudonym = ""
                if recipient_key:
                    recipient = db.get_recipient(recipient_key)
                    if recipient and recipient.get('pseudonym'):
                        recipient_pseudonym = recipient['pseudonym']

                recipient_pseudonym = st.text_input("Recipient Pseudonym (auto-filled if available)", 
                                                  value=recipient_pseudonym,
                                                  key="recipient_pseudonym_optional_3")
            else:
                st.warning("No recipients found. Please create recipients in the Recipient panel first.")
                recipient_key = st.text_input("Recipient Key (required)", 
                                            value=st.session_state.recipient_key if "recipient_key" in st.session_state else "", 
                                            key="recipient_key_required_1")
                recipient_pseudonym = st.text_input("Recipient Pseudonym (optional)", key="recipient_pseudonym_optional_3")

            # Get all available surveys
            surveys = db.get_all_surveys()

            if surveys:
                # Create a list of survey names with their IDs
                survey_options = [f"{survey['name']}" for survey in surveys]

                # Select a survey
                selected_survey_name = st.selectbox("Select Survey", [""] + survey_options, key="survey_selector")

                if selected_survey_name:
                    # Find the selected survey
                    selected_survey = next((survey for survey in surveys if survey['name'] == selected_survey_name), None)

                    if selected_survey:
                        st.session_state.selected_survey_id = selected_survey['id']

                        # Display survey description
                        st.write(f"**Description:** {selected_survey['description']}")

                        # Display survey sections
                        st.write(f"**Sections:** {', '.join([section['name'] for section in selected_survey['sections']])}")

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Continue to Survey"):
                                if not recipient_key:
                                    st.error("Recipient Key is required")
                                else:
                                    st.session_state.recipient_key = recipient_key
                                    # Set the first section from the survey
                                    if selected_survey['sections']:
                                        st.session_state.survey_section = selected_survey['sections'][0]['name'].lower()
                                    else:
                                        st.session_state.survey_section = "survey"
                                    st.rerun()
                    else:
                        st.error("Selected survey not found")
                else:
                    st.info("Please select a survey to continue")
            else:
                st.warning("No surveys available. Please ask an administrator to create a survey.")

            # Check if there are existing survey responses for this recipient
            if recipient_key:
                existing_responses = db.get_questionnaire(recipient_key)
                if existing_responses:
                    st.write("### Existing Survey Responses")
                    for response in existing_responses:
                        st.write(f"**Section:** {response['section']}")
                        if response['updated_at']:
                            st.write(f"**Last Updated:** {response['updated_at']}")
                        elif response['created_at']:
                            st.write(f"**Created:** {response['created_at']}")
                        if 'survey_id' in response and response['survey_id']:
                            # Find the survey name
                            survey = next((s for s in surveys if s['id'] == response['survey_id']), None)
                            if survey:
                                st.write(f"**Survey:** {survey['name']}")

                    if st.button("View/Edit Existing Responses", key="view_edit_survey_responses"):
                        # Load existing responses into session state
                        for response in existing_responses:
                            if "responses" in response and response["responses"]:
                                st.session_state.survey_data[response["section"]] = response["responses"]
                                if 'survey_id' in response and response['survey_id']:
                                    st.session_state.selected_survey_id = response['survey_id']

                        # Set the section to the first one with data
                        if st.session_state.survey_data:
                            st.session_state.survey_section = next(iter(st.session_state.survey_data))
                        else:
                            st.session_state.survey_section = "survey"
                        st.rerun()

        # Dynamic survey section based on selected survey
        elif st.session_state.survey_section != "recipient":
            # Get the selected survey
            if st.session_state.selected_survey_id:
                survey = db.get_survey(st.session_state.selected_survey_id)

                if survey:
                    # Find the current section in the survey
                    current_section = None
                    for section in survey['sections']:
                        if section['name'].lower() == st.session_state.survey_section:
                            current_section = section
                            break

                    if current_section:
                        st.write(f"### {current_section['name']}")

                        with st.form(f"survey_form_{current_section['name'].lower()}"):
                            # Load existing data if available
                            existing_data = st.session_state.survey_data.get(current_section['name'].lower(), {})

                            # Dictionary to store responses
                            responses = {}

                            # Generate form fields based on questions
                            for question in current_section['questions']:
                                question_id = question['text'].lower().replace(" ", "_")

                                if question['type'] == 'text':
                                    responses[question_id] = st.text_input(
                                        question['text'],
                                        value=existing_data.get(question_id, ""),
                                        key=f"survey_{question_id}"
                                    )
                                elif question['type'] == 'radio':
                                    options = question.get('options', [])
                                    if options:
                                        default_index = 0
                                        if question_id in existing_data and existing_data[question_id] in options:
                                            default_index = options.index(existing_data[question_id])
                                        responses[question_id] = st.radio(
                                            question['text'],
                                            options,
                                            index=default_index,
                                            key=f"survey_{question_id}"
                                        )
                                elif question['type'] == 'checkbox':
                                    options = question.get('options', [])
                                    if options:
                                        default = []
                                        if question_id in existing_data:
                                            default = existing_data[question_id]
                                        responses[question_id] = st.multiselect(
                                            question['text'],
                                            options,
                                            default=default,
                                            key=f"survey_{question_id}"
                                        )
                                elif question['type'] == 'number':
                                    responses[question_id] = st.number_input(
                                        question['text'],
                                        value=float(existing_data.get(question_id, 0)),
                                        key=f"survey_{question_id}"
                                    )

                            # Form submission buttons
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                # If this is the first section, go back to recipient
                                if survey['sections'][0]['name'].lower() == current_section['name'].lower():
                                    back_button = st.form_submit_button("Back to Recipient")
                                else:
                                    # Find the previous section
                                    current_index = next((i for i, s in enumerate(survey['sections']) if s['name'].lower() == current_section['name'].lower()), 0)
                                    if current_index > 0:
                                        prev_section = survey['sections'][current_index - 1]['name'].lower()
                                        back_button = st.form_submit_button(f"Back to {survey['sections'][current_index - 1]['name']}")
                                    else:
                                        back_button = st.form_submit_button("Back to Recipient")
                            with col2:
                                # If this is the last section, show "Complete Survey"
                                if survey['sections'][-1]['name'].lower() == current_section['name'].lower():
                                    submit_button = st.form_submit_button("Complete Survey")
                                else:
                                    # Find the next section
                                    current_index = next((i for i, s in enumerate(survey['sections']) if s['name'].lower() == current_section['name'].lower()), 0)
                                    if current_index < len(survey['sections']) - 1:
                                        next_section = survey['sections'][current_index + 1]['name'].lower()
                                        submit_button = st.form_submit_button(f"Continue to {survey['sections'][current_index + 1]['name']}")
                                    else:
                                        submit_button = st.form_submit_button("Complete Survey")
                            with col3:
                                save_button = st.form_submit_button("Save Only")

                            if back_button:
                                # If this is the first section, go back to recipient
                                if survey['sections'][0]['name'].lower() == current_section['name'].lower():
                                    st.session_state.survey_section = "recipient"
                                else:
                                    # Find the previous section
                                    current_index = next((i for i, s in enumerate(survey['sections']) if s['name'].lower() == current_section['name'].lower()), 0)
                                    if current_index > 0:
                                        st.session_state.survey_section = survey['sections'][current_index - 1]['name'].lower()
                                    else:
                                        st.session_state.survey_section = "recipient"
                                st.rerun()

                            if submit_button or save_button:
                                # Save the data
                                save_survey_section(current_section['name'].lower(), responses)

                                # Save to database
                                success = db.save_questionnaire(
                                    st.session_state.recipient_key,
                                    current_section['name'].lower(),
                                    responses,
                                    survey_id=st.session_state.selected_survey_id,
                                    username=st.session_state.username
                                )

                                if success:
                                    st.success(f"{current_section['name']} saved successfully")
                                    if submit_button:
                                        # If this is the last section, go back to recipient
                                        if survey['sections'][-1]['name'].lower() == current_section['name'].lower():
                                            st.session_state.survey_section = "recipient"
                                            st.success("Survey completed successfully!")
                                        else:
                                            # Find the next section
                                            current_index = next((i for i, s in enumerate(survey['sections']) if s['name'].lower() == current_section['name'].lower()), 0)
                                            if current_index < len(survey['sections']) - 1:
                                                st.session_state.survey_section = survey['sections'][current_index + 1]['name'].lower()
                                        st.rerun()
                                else:
                                    st.error(f"Failed to save {current_section['name']}")
                    else:
                        st.error(f"Section '{st.session_state.survey_section}' not found in the selected survey")
                        # Reset to recipient section
                        st.session_state.survey_section = "recipient"
                        st.rerun()
                else:
                    st.error("Selected survey not found")
                    # Reset to recipient section
                    st.session_state.survey_section = "recipient"
                    st.rerun()
            else:
                st.error("No survey selected")
                # Reset to recipient section
                st.session_state.survey_section = "recipient"
                st.rerun()

    with tab5:
        st.subheader("Recipient Management")

        # Create tabs for lookup and creation
        lookup_tab, create_tab = st.tabs(["Lookup Recipient", "Create Recipient"])

        with lookup_tab:
            st.write("### Find Recipient")

            # Get all recipients
            recipients = db.get_all_recipients()

            if recipients:
                # Create a list of recipient options
                recipient_options = [f"{r['key']}{' (' + r['pseudonym'] + ')' if r['pseudonym'] else ''}" for r in recipients]

                # Select a recipient
                selected_recipient = st.selectbox("Select Recipient", [""] + recipient_options, key="recipient_lookup")

                if selected_recipient:
                    # Extract the key from the selection
                    recipient_key = selected_recipient.split(" (")[0] if " (" in selected_recipient else selected_recipient

                    # Get recipient details
                    recipient = db.get_recipient(recipient_key)

                    if recipient:
                        st.write(f"**Key:** {recipient['key']}")
                        if recipient['pseudonym']:
                            st.write(f"**Pseudonym:** {recipient['pseudonym']}")
                        st.write(f"**Created:** {recipient['created_at']}")

                        # Get survey responses for this recipient
                        responses = db.get_questionnaire(recipient_key)

                        if responses:
                            st.write("### Survey Responses")

                            # Group responses by survey
                            survey_responses = {}
                            for response in responses:
                                survey_id = response.get('survey_id', 'Unknown')
                                if survey_id not in survey_responses:
                                    survey_responses[survey_id] = []
                                survey_responses[survey_id].append(response)

                            # Display responses by survey
                            for survey_id, survey_responses_list in survey_responses.items():
                                # Get survey name if available
                                survey_name = "Unknown Survey"
                                if survey_id != 'Unknown':
                                    survey = db.get_survey(survey_id)
                                    if survey:
                                        survey_name = survey['name']

                                with st.expander(f"Survey: {survey_name}"):
                                    for response in survey_responses_list:
                                        st.write(f"**Section:** {response['section']}")
                                        if response['responses']:
                                            for question, answer in response['responses'].items():
                                                st.write(f"- **{question.replace('_', ' ').title()}:** {answer}")
                                        if response['updated_at']:
                                            st.write(f"**Last Updated:** {response['updated_at']}")
                                        elif response['created_at']:
                                            st.write(f"**Created:** {response['created_at']}")
                                        st.divider()
                        else:
                            st.info("No survey responses found for this recipient")

                        # Get interactions for this recipient
                        interactions = db.get_interactions(recipient_key=recipient_key)

                        if interactions:
                            st.write("### Interactions")
                            for interaction in interactions:
                                with st.expander(f"{interaction['type']} - {interaction['timestamp']}"):
                                    st.write(f"**Logged by:** {interaction['logged_by']}")
                                    if interaction['notes']:
                                        st.write(f"**Notes:** {interaction['notes']}")
                        else:
                            st.info("No interactions found for this recipient")
                    else:
                        st.error("Recipient not found")
            else:
                st.info("No recipients found in the database")

        with create_tab:
            st.write("### Create New Recipient")

            with st.form("create_recipient_form"):
                new_recipient_key = st.text_input("Recipient Key (required)", key="text_input_3908")
                new_recipient_pseudonym = st.text_input("Recipient Pseudonym (optional)", key="recipient_pseudonym_optional_4")
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

        # Recipient selection/creation
        if st.session_state.questionnaire_section == "recipient":
            # Automatically redirect to financial section
            st.session_state.questionnaire_section = "financial"
            st.rerun()

        # Financial section
        elif st.session_state.questionnaire_section == "financial":
            st.write("### Financial Assessment")

            with st.form("financial_form_tab5"):
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

                    # Check if recipient key is set
                    if not st.session_state.recipient_key:
                        st.error("Recipient Key is required. Please go back to the Recipient section and enter a key.")
                    else:
                        # Save to database
                        success = db.save_questionnaire(
                            st.session_state.recipient_key,
                            "financial",
                            data,
                            username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
                        data,
                        username=st.session_state.username
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
