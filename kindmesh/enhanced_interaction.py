"""
Enhanced interaction module for kindmesh application.
Contains functions for logging resource distributions with batch entry integration.
"""
import streamlit as st
from typing import Any

from kindmesh.interaction import log_interaction_form
from kindmesh.batch_entry import render_batch_entry

def enhanced_log_interaction_form(db: Any, username: str) -> None:
    """
    Render enhanced interaction logging form with batch entry option.
    
    This function provides a tabbed interface that allows users to choose between
    single interaction entry and batch entry from spreadsheets.
    
    Args:
        db: Database connection object used for logging interactions
        username: Username of the current user performing the interaction logging
    """
    # Create tabs for single entry and batch entry
    single_tab, batch_tab = st.tabs(["Single Entry", "Batch Entry"])

    with single_tab:
        log_interaction_form(db, username)

    with batch_tab:
        render_batch_entry(db, username)