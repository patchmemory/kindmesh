"""
Data management module for kindmesh application.
Contains functions for viewing and exporting data.
"""
import streamlit as st
from typing import Any

from kindmesh.data_view import render_data_view
from kindmesh.export import render_export_data

def render_manage_data(db: Any) -> None:
    """
    Render data management components with viewing and export functionality.
    
    This function provides a tabbed interface that allows administrators to
    view statistics about interactions and export data in various formats.
    
    Args:
        db: Database connection object used for retrieving and exporting data
    """
    st.subheader("Manage Data")

    # Create tabs for viewing and exporting
    view_tab, export_tab = st.tabs(["View Statistics", "Export Data"])

    with view_tab:
        render_data_view(db, is_admin=True)

    with export_tab:
        render_export_data(db)