"""
Recipient management module for KindMesh application.
Contains functions for recipient lookup and creation.
"""

import streamlit as st
import pandas as pd

def render_recipient_management(db, username):
    """Render recipient management components"""
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
            new_recipient_key = st.text_input("Recipient Key (required)", key="new_recipient_key")
            new_recipient_pseudonym = st.text_input("Recipient Pseudonym (optional)", key="new_recipient_pseudonym")
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