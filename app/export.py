"""
Export module for KindMesh application.
Contains functions for exporting data.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

def render_export_data(db):
    """Render data export components (admin only)"""
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