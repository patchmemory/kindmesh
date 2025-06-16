"""
Interaction module for kindmesh application.
Contains functions for logging resource distributions.
"""
import streamlit as st
from typing import Any

def log_interaction_form(db: Any, username: str) -> None:
    """
    Render and process the interaction logging form for resource distributions.
    
    This function displays a form for logging resource distributions to recipients.
    It allows users to select or create recipients, specify the type of resource,
    and add notes about the interaction. The form handles both existing recipients
    (via dropdown selection) and new recipients (via text input).
    
    Args:
        db: Database connection object used for retrieving recipient data and logging interactions
        username: Username of the currently logged-in user performing the interaction
    """
    st.subheader("Log Resource Distribution")
    
    # Get all recipient keys for dropdown
    recipient_keys = db.get_all_recipient_keys()
    
    with st.form("log_interaction_form"):
        # If there are recipient keys, use a selectbox, otherwise use text input
        if recipient_keys:
            recipient_key = st.selectbox("Recipient Key (required)", options=[""] + recipient_keys)
            
            # Auto-fill pseudonym when recipient key is selected
            recipient_pseudonym = ""
            if recipient_key:
                recipient = db.get_recipient(recipient_key)
                if recipient and recipient.get('pseudonym'):
                    recipient_pseudonym = recipient['pseudonym']
                    
            recipient_pseudonym = st.text_input("Recipient Pseudonym (auto-filled if available)",
                                              value=recipient_pseudonym,
                                              key="recipient_pseudonym_optional")
        else:
            st.warning("No recipients found. Please create recipients in the Recipient panel first.")
            recipient_key = st.text_input("Recipient Key (required)", key="text_input_recipient_key")
            recipient_pseudonym = st.text_input("Recipient Pseudonym (optional)", key="recipient_pseudonym_optional")
            
        interaction_type = st.selectbox("Resource Type", ["Food", "Clothing", "Shelter", "Healthcare", "Education", "Financial", "Other"])
        notes = st.text_area("Notes")
        
        submit_button = st.form_submit_button("Log Interaction")
        
        if submit_button:
            if not recipient_key:
                st.error("Recipient Key is required")
            else:
                success = db.log_interaction(
                    logged_by=username,
                    recipient_key=recipient_key,
                    interaction_type=interaction_type,
                    notes=notes,
                    recipient_pseudonym=recipient_pseudonym if recipient_pseudonym else None
                )
                
                if success:
                    st.success("Interaction logged successfully")
                else:
                    st.error("Failed to log interaction")