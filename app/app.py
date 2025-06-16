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

# Import application modules
from auth import login, logout, render_login_page
from interaction import log_interaction_form
from data_view import render_data_view
from export import render_export_data
from user_management import render_user_management
from recipient import render_recipient_management
from batch_entry import render_batch_entry
from survey import render_survey_management
from enhanced_interaction import enhanced_log_interaction_form
from manage_data import render_manage_data

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

# Page rendering functions

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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Log Survey", 
        "Log Interaction", 
        "Manage Data", 
        "Manage Users", 
        "Manage Recipients", 
        "Manage Surveys", 
        "View Data"
    ])

    with tab1:  # Log Survey
        render_survey_management(db, st.session_state.username, is_admin=False)  # Use Friend's survey completion

    with tab2:  # Log Interaction
        log_interaction_form(db, st.session_state.username)

    with tab3:  # Manage Data
        render_manage_data(db)

    with tab4:  # Manage Users
        render_user_management(db, st.session_state.username)

    with tab5:  # Manage Recipients
        render_recipient_management(db, st.session_state.username)

    with tab6:  # Manage Surveys
        render_survey_management(db, st.session_state.username, is_admin=True)

    with tab7:  # View Data
        render_data_view(db, is_admin=True)

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

    # Create tabs for different functions
    tab1, tab2, tab3, tab4 = st.tabs([
        "Log Survey", 
        "Log Interaction", 
        "View Data", 
        "Manage Recipients"
    ])

    with tab1:  # Log Survey
        render_survey_management(db, st.session_state.username, is_admin=False)

    with tab2:  # Log Interaction (with integrated batch entry)
        enhanced_log_interaction_form(db, st.session_state.username)

    with tab3:  # View Data
        render_data_view(db, is_admin=False)

    with tab4:  # Manage Recipients
        render_recipient_management(db, st.session_state.username)

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
        render_login_page(db)
    else:
        if st.session_state.role == "Greeter":
            render_greeter_page()
        elif st.session_state.role == "Admin":
            render_admin_page()
        else:  # Friend role
            render_friend_page()

if __name__ == "__main__":
    main()
