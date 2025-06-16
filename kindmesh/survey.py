"""
Survey module for kindmesh application.
Contains functions for survey creation, editing, and completion.
"""
import streamlit as st
from typing import Any, Dict, List, Optional, Union

def render_survey_management(db: Any, username: str, is_admin: bool = False) -> None:
    """
    Render survey management interface based on user role.
    
    This function serves as a router that directs users to either the admin
    survey management interface or the friend survey completion interface
    based on their role.
    
    Args:
        db: Database connection object used for retrieving and storing survey data
        username: Username of the currently logged-in user
        is_admin: Boolean flag indicating whether the user has admin privileges
    """
    if is_admin:
        render_admin_survey_management(db, username)
    else:
        render_friend_survey_completion(db, username)

def render_admin_survey_management(db: Any, username: str) -> None:
    """
    Render survey management interface for administrators.
    
    This function provides a user interface for administrators to create,
    edit, and delete surveys. It displays existing surveys and allows
    administrators to manage survey sections and questions.
    
    Args:
        db: Database connection object used for retrieving and storing survey data
        username: Username of the administrator performing the survey management
    """
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

    # Save survey button
    if st.button("Save Survey"):
        if not survey_name:
            st.error("Survey name is required")
        else:
            # Validate that all sections have names and all questions have text
            valid = True
            for i, section in enumerate(st.session_state.survey_sections):
                if not section['name']:
                    st.error(f"Section {i+1} must have a name")
                    valid = False
                for j, question in enumerate(section['questions']):
                    if not question['text']:
                        st.error(f"Question {j+1} in Section {i+1} must have text")
                        valid = False
                    if question['type'] in ["radio", "checkbox"] and not question['options']:
                        st.error(f"Question {j+1} in Section {i+1} must have options")
                        valid = False

            if valid:
                # Check if we're editing an existing survey
                if "editing_survey" in st.session_state:
                    success = db.update_survey(
                        survey_id=st.session_state.editing_survey['id'],
                        name=survey_name,
                        description=survey_description,
                        sections=st.session_state.survey_sections,
                        updated_by=username
                    )
                    if success:
                        st.success(f"Survey '{survey_name}' updated successfully")
                        # Clear editing state
                        del st.session_state.editing_survey
                        # Reset survey sections
                        st.session_state.survey_sections = [{"name": "Section 1", "questions": [{"text": "", "type": "text", "options": []}]}]
                        st.rerun()
                    else:
                        st.error(f"Failed to update survey '{survey_name}'")
                else:
                    # Create new survey
                    success = db.create_survey(
                        name=survey_name,
                        description=survey_description,
                        sections=st.session_state.survey_sections,
                        created_by=username
                    )
                    if success:
                        st.success(f"Survey '{survey_name}' created successfully")
                        # Reset survey sections
                        st.session_state.survey_sections = [{"name": "Section 1", "questions": [{"text": "", "type": "text", "options": []}]}]
                        st.rerun()
                    else:
                        st.error(f"Failed to create survey '{survey_name}'")

    # Handle editing existing survey
    if "editing_survey" in st.session_state:
        # Load survey data into form
        survey = st.session_state.editing_survey
        st.session_state.new_survey_name = survey['name']
        st.session_state.new_survey_description = survey['description']
        st.session_state.survey_sections = survey['sections']
        st.rerun()

def render_friend_survey_completion(db: Any, username: str) -> None:
    """
    Render survey completion interface for friends (non-admin users).
    
    This function provides a user interface for friends to complete surveys
    for recipients. It guides users through a multi-step process to select
    a recipient, select a survey, and complete the survey sections.
    
    Args:
        db: Database connection object used for retrieving and storing survey data
        username: Username of the friend completing the survey
    """
    st.subheader("Complete Survey")

    # Initialize session state for survey completion
    if "survey_section" not in st.session_state:
        st.session_state.survey_section = "recipient"
    if "survey_data" not in st.session_state:
        st.session_state.survey_data = {}

    # Helper function to set the current section
    def set_survey_section(section: str) -> None:
        st.session_state.survey_section = section
        st.rerun()

    # Helper function to save section data
    def save_survey_section(section: str, data: Dict) -> None:
        st.session_state.survey_data[section] = data
        st.rerun()

    # Step 1: Select recipient
    if st.session_state.survey_section == "recipient":
        st.write("### Step 1: Select Recipient")
        
        # Get all recipients
        recipients = db.get_all_recipients()
        
        if recipients:
            # Create a list of recipient options
            recipient_options = [f"{r['key']}{' (' + r['pseudonym'] + ')' if r['pseudonym'] else ''}" for r in recipients]
            
            # Select a recipient
            selected_recipient = st.selectbox("Select Recipient", [""] + recipient_options, key="survey_recipient_select")
            
            if selected_recipient:
                # Extract the key from the selection
                recipient_key = selected_recipient.split(" (")[0] if " (" in selected_recipient else selected_recipient
                
                # Save recipient data
                save_survey_section("recipient", {"key": recipient_key})
                
                # Move to survey selection
                set_survey_section("survey")
        else:
            st.error("No recipients found. Please create recipients in the Recipient panel first.")

    # Step 2: Select survey
    elif st.session_state.survey_section == "survey":
        st.write("### Step 2: Select Survey")
        
        # Show selected recipient
        recipient_key = st.session_state.survey_data["recipient"]["key"]
        recipient = db.get_recipient(recipient_key)
        
        if recipient:
            st.write(f"Selected Recipient: **{recipient_key}**")
            if recipient['pseudonym']:
                st.write(f"Pseudonym: **{recipient['pseudonym']}**")
        
        # Get all surveys
        surveys = db.get_all_surveys()
        
        if surveys:
            # Create a list of survey options
            survey_options = [f"{s['name']}" for s in surveys]
            
            # Select a survey
            selected_survey = st.selectbox("Select Survey", [""] + survey_options, key="survey_select")
            
            if selected_survey:
                # Find the selected survey
                survey = next((s for s in surveys if s['name'] == selected_survey), None)
                
                if survey:
                    # Save survey data
                    save_survey_section("survey", {"id": survey['id'], "name": survey['name']})
                    
                    # Initialize section index
                    st.session_state.survey_section_index = 0
                    
                    # Move to first section
                    set_survey_section("section")
                else:
                    st.error("Selected survey not found")
        else:
            st.error("No surveys found. Please ask an administrator to create surveys.")
        
        # Back button
        if st.button("Back to Recipient Selection"):
            set_survey_section("recipient")

    # Step 3: Complete survey sections
    elif st.session_state.survey_section == "section":
        # Get recipient and survey data
        recipient_key = st.session_state.survey_data["recipient"]["key"]
        survey_id = st.session_state.survey_data["survey"]["id"]
        survey_name = st.session_state.survey_data["survey"]["name"]
        
        # Get recipient details
        recipient = db.get_recipient(recipient_key)
        
        # Get survey details
        survey = db.get_survey(survey_id)
        
        if survey and recipient:
            # Display progress
            st.write(f"### Survey: {survey_name}")
            st.write(f"Recipient: **{recipient_key}**")
            if recipient['pseudonym']:
                st.write(f"Pseudonym: **{recipient['pseudonym']}**")
            
            # Get current section index
            section_index = st.session_state.survey_section_index
            
            # Display section progress
            st.progress((section_index + 1) / len(survey['sections']))
            st.write(f"Section {section_index + 1} of {len(survey['sections'])}")
            
            # Get current section
            section = survey['sections'][section_index]
            
            # Display section name
            st.write(f"### {section['name']}")
            
            # Initialize responses for this section
            if f"section_{section_index}" not in st.session_state.survey_data:
                st.session_state.survey_data[f"section_{section_index}"] = {"responses": {}}
            
            # Display questions
            with st.form(f"survey_section_{section_index}_form"):
                for question in section['questions']:
                    question_id = question['text'].lower().replace(' ', '_')
                    
                    # Display question based on type
                    if question['type'] == 'text':
                        response = st.text_area(question['text'], key=f"question_{question_id}")
                    elif question['type'] == 'radio':
                        response = st.radio(question['text'], question['options'], key=f"question_{question_id}")
                    elif question['type'] == 'checkbox':
                        options = st.multiselect(question['text'], question['options'], key=f"question_{question_id}")
                        response = ", ".join(options)
                    elif question['type'] == 'number':
                        response = st.number_input(question['text'], key=f"question_{question_id}")
                    
                    # Save response
                    st.session_state.survey_data[f"section_{section_index}"]["responses"][question_id] = response
                
                # Navigation buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if section_index > 0:
                        back_button = st.form_submit_button("Previous Section")
                        if back_button:
                            st.session_state.survey_section_index -= 1
                            st.rerun()
                
                with col3:
                    if section_index < len(survey['sections']) - 1:
                        next_button = st.form_submit_button("Next Section")
                        if next_button:
                            st.session_state.survey_section_index += 1
                            st.rerun()
                    else:
                        submit_button = st.form_submit_button("Submit Survey")
                        if submit_button:
                            # Prepare data for submission
                            survey_responses = []
                            for i in range(len(survey['sections'])):
                                if f"section_{i}" in st.session_state.survey_data:
                                    section_data = {
                                        "section": survey['sections'][i]['name'],
                                        "responses": st.session_state.survey_data[f"section_{i}"]["responses"]
                                    }
                                    survey_responses.append(section_data)
                            
                            # Submit survey responses
                            success = db.save_questionnaire(
                                recipient_key=recipient_key,
                                survey_id=survey_id,
                                responses=survey_responses,
                                completed_by=username
                            )
                            
                            if success:
                                st.success("Survey completed successfully!")
                                # Reset survey completion state
                                st.session_state.survey_section = "recipient"
                                st.session_state.survey_data = {}
                                st.rerun()
                            else:
                                st.error("Failed to submit survey responses")
                
                with col2:
                    cancel_button = st.form_submit_button("Cancel")
                    if cancel_button:
                        # Reset survey completion state
                        st.session_state.survey_section = "recipient"
                        st.session_state.survey_data = {}
                        st.rerun()
        else:
            if not survey:
                st.error("Selected survey not found")
                # Reset to recipient section
                st.session_state.survey_section = "recipient"
                st.rerun()
            else:
                st.error("Selected recipient not found")
                # Reset to recipient section
                st.session_state.survey_section = "recipient"
                st.rerun()
    else:
        st.error("Invalid survey section")
        # Reset to recipient section
        st.session_state.survey_section = "recipient"
        st.rerun()