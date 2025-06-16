"""
Data visualization module for kindmesh application.
Contains functions for displaying data and statistics.
"""
import streamlit as st
import pandas as pd
from typing import Any, Optional, Dict, List, Union

def render_data_view(db: Any, is_admin: bool = False) -> None:
    """
    Render data visualization components for the kindmesh application.
    
    This function displays summary statistics and visualizations of interaction data.
    It shows different levels of detail based on the user's role, with administrators
    seeing more detailed information than regular users.
    
    Args:
        db: Database connection object used for retrieving statistics and interaction data
        is_admin: Whether the current user has admin privileges, determines the level of detail shown
    """
    st.subheader("View Data")
    
    # Summary statistics
    stats = db.get_summary_stats()
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Interactions", stats["total_interactions"])
    with col2:
        st.metric("Total Recipients", stats["total_recipients"])
    
    # Interaction types breakdown (admin only)
    if is_admin and stats["interaction_types"]:
        st.subheader("Interaction Types")
        interaction_df = pd.DataFrame(stats["interaction_types"])
        
        # Display as table
        st.dataframe(interaction_df)
        
        # Display as chart
        st.bar_chart(interaction_df.set_index("type")["count"])
    
    # Recent interactions
    st.subheader("Recent Interactions")
    interactions = db.get_interactions(limit=50 if is_admin else 20)
    
    if interactions:
        interactions_df = pd.DataFrame(interactions)
        st.dataframe(interactions_df)
    else:
        st.info("No interactions recorded yet")