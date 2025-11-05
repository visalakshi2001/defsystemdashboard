import os
import pandas as pd
import streamlit as st
from projectdetail import required_files_for_view


def render(project: dict) -> None:
    """
    Profile-aware Home Page view.
    • Shows triple‑count if TripleCount.csv exists
    • Shows a table of which JSON feeds which tab (using profile-specific ties)
    """
    folder   = project["folder"]
    csv_path = os.path.join(folder, "TripleCount.csv")

    if not os.path.exists(csv_path):
        st.info("TripleCount.json data is not available – upload it via **🪄 Edit Data**")
        # return
    else:
        tc_df = pd.read_csv(csv_path)
        if "tripleCount" in tc_df.columns:
            cnt = tc_df["tripleCount"].iloc[0]
            st.markdown(f"#### RDF Triple Count: :blue[{cnt}]", unsafe_allow_html=True)

    # Tab‑to‑file reference table (profile-aware)
    profile_name = project.get("profile")
    views = project.get("views", [])

    data = []
    for view in views:
        required_files = required_files_for_view(view, profile_name)
        for fname in required_files:
            data.append({"Tab Name": view, "Files Utilized": f"{fname}.json"})

    if data:
        map_df = pd.DataFrame(data)
        st.markdown("#### Files used in each tab")
        st.dataframe(map_df, hide_index=True, width=550)
