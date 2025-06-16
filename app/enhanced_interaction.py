"""
Enhanced interaction module for kindmesh application.
Contains functions for logging resource distributions with batch entry integration.
"""

import streamlit as st
from interaction import log_interaction_form
from batch_entry import render_batch_entry

def enhanced_log_interaction_form(db, username):
    """Render enhanced interaction logging form with batch entry option"""
    
    # Create tabs for single entry and batch entry
    single_tab, batch_tab = st.tabs(["Single Entry", "Batch Entry"])
    
    with single_tab:
        log_interaction_form(db, username)
        
    with batch_tab:
        render_batch_entry(db, username)