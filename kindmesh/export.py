"""
Export module for kindmesh application.
Contains functions for exporting data to various formats.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Any

def render_export_data(db: Any) -> None:
    """
    Render data export components for administrators.
    
    This function provides a user interface for exporting interaction data
    in various formats (CSV, JSON). It retrieves all interaction data from
    the database and allows the user to download it in the selected format.
    
    Args:
        db: Database connection object used for retrieving interaction data
    """
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