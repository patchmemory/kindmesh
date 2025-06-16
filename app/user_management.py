"""
User management module for KindMesh application.
Contains functions for user management (admin only).
"""

import streamlit as st
import pandas as pd

def render_user_management(db, username):
    """Render user management components (admin only)"""
    st.subheader("User Management")

    # Get all users
    users = db.get_all_users()

    # Display users in a table
    if users:
        user_df = pd.DataFrame(users)
        st.dataframe(user_df)

        # User promotion section
        st.subheader("Promote User to Admin")
        non_admin_users = [user["username"] for user in users if user["role"] != "Admin" and user["username"] != username]

        if non_admin_users:
            user_to_promote = st.selectbox("Select user to promote", non_admin_users)
            if st.button("Promote to Admin"):
                success = db.promote_user(user_to_promote, username)
                if success:
                    st.success(f"User {user_to_promote} promoted to Admin")
                    st.rerun()
                else:
                    st.error("Failed to promote user")
        else:
            st.info("No users available for promotion")

        # Admin demotion section
        st.subheader("Demote Admin to Friend")
        admin_users = [user["username"] for user in users if user["role"] == "Admin" and user["username"] != username]

        if admin_users:
            user_to_demote = st.selectbox("Select admin to demote", admin_users)

            # Initialize votes for this user if not already done
            if "admin_demotion_votes" not in st.session_state:
                st.session_state.admin_demotion_votes = {}
            if user_to_demote not in st.session_state.admin_demotion_votes:
                st.session_state.admin_demotion_votes[user_to_demote] = []

            # Check if current user has already voted
            current_user_voted = username in st.session_state.admin_demotion_votes[user_to_demote]

            # Display current votes
            vote_count = len(st.session_state.admin_demotion_votes[user_to_demote])
            st.write(f"Current votes for demotion: {vote_count}/2")

            # Vote button
            vote_button_label = "Remove Vote" if current_user_voted else "Vote to Demote"
            if st.button(vote_button_label):
                if current_user_voted:
                    st.session_state.admin_demotion_votes[user_to_demote].remove(username)
                    st.success(f"Vote removed for demoting {user_to_demote}")
                else:
                    st.session_state.admin_demotion_votes[user_to_demote].append(username)
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
        users_to_delete = [user["username"] for user in users if user["username"] != username]

        if users_to_delete:
            user_to_delete = st.selectbox("Select user to delete", users_to_delete, key="user_to_delete")
            if st.button("Delete User"):
                if user_to_delete == username:
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
                        created_by=username
                    )
                    if success:
                        st.success(f"User {new_username} created successfully with role {new_role}")
                    else:
                        st.error("Failed to create user")
    else:
        st.warning("No users found in the database")