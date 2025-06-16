"""
Batch entry module for kindmesh application.
Contains functions for batch entry from spreadsheets.
"""

import streamlit as st
import pandas as pd

def render_batch_entry(db, username):
    """Render batch entry components"""
    st.subheader("Batch Entry from Spreadsheet")

    # File upload
    uploaded_file = st.file_uploader("Upload spreadsheet", type=["xlsx", "xls", "csv"])

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
                                        logged_by=username,
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