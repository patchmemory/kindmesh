"""
Authentication module for kindmesh application.
Contains functions for user login, logout, and rendering the login page.
"""

import streamlit as st
from typing import Any, Optional

def login(username: str, password: str, db: Any) -> bool:
    """
    Authenticate user and set session state

    Args:
        username: User's username
        password: User's password
        db: Database connection object

    Returns:
        bool: True if authentication successful, False otherwise
    """
    success, user_data = db.authenticate_user(username, password)
    if success:
        st.session_state.authenticated = True
        st.session_state.username = user_data["username"]
        st.session_state.role = user_data["role"]
        return True
    return False

def logout() -> None:
    """
    Clear session state and log out user

    Resets all authentication-related session state variables to their default values.
    """
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.admin_demotion_votes = {}

def render_login_page(db: Any) -> None:
    """
    Render the login page with username and password input fields

    Args:
        db: Database connection object used for authentication
    """
    st.title("kindmesh - Login")

    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="_username___________password___st_text_input__password_")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            if login(username, password, db):
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")
