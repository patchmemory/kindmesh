"""
Data management module for KindMesh application.
Contains functions for viewing and exporting data.
"""

import streamlit as st
from data_view import render_data_view
from export import render_export_data

def render_manage_data(db):
    """Render data management components with export functionality"""
    st.subheader("Manage Data")
    
    # Create tabs for viewing and exporting
    view_tab, export_tab = st.tabs(["View Statistics", "Export Data"])
    
    with view_tab:
        render_data_view(db, is_admin=True)
        
    with export_tab:
        render_export_data(db)