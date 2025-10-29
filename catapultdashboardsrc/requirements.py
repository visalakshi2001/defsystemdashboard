import streamlit as st
import os
import json
import pandas as pd
from jsontocsv import json_to_csv


# ########## REQUIREMENTS VIEW FUNCTION
def dashreqs():
    st.subheader("Requirements Table", divider="orange")
    project = st.session_state.get("project", {})
    render(project)


def render(project: dict) -> None:
    folder = project["folder"]
    csv_path = os.path.join(folder, "Requirements.csv")
    json_path = os.path.join(folder, "Requirements.json")

    if not os.path.exists(json_path):
        st.info("Requirements.json data is not available – upload it via **🪄 Edit Data**")
        return

    if not os.path.exists(csv_path):
        try:
            json_to_csv(json_input_path=json_path, csv_output_path=csv_path)
        except Exception as e:
            st.error(f"Failed to convert Requirements.json -> CSV: {e}")
            return

    df = pd.read_csv(csv_path)
    st.subheader("Requirements Table", divider="orange")
    st.dataframe(df, use_container_width=True, hide_index=True)