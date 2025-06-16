"""
Survey module for kindmesh application.
Contains functions for survey creation, editing, and completion.
"""

import streamlit as st

def render_survey_management(db, username, is_admin=False):
    """Render survey management for admins or survey completion for friends"""
    if is_admin:
        render_admin_survey_management(db, username)
    else:
        render_friend_survey_completion(db, username)

def render_admin_survey_management(db, username):
    """Render survey management for admins"""
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
                    created_by=username
                )

                if survey_id:
                    st.success(f"Survey '{survey_name}' created successfully")
                    # Reset the form
                    st.session_state.survey_sections = [{"name": "Section 1", "questions": [{"text": "", "type": "text", "options": []}]}]
                    st.rerun()
                else:
                    st.error("Failed to create survey")

def render_friend_survey_completion(db, username):
    """Render survey completion for friends"""
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
                                username=username
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