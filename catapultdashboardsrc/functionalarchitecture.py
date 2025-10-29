import streamlit as st
import os
import pandas as pd
import graphviz
from jsontocsv import json_to_csv

def render(project: dict) -> None:
    folder = project["folder"]
    csv_path = os.path.join(folder, "FunctionalArchitecture.csv")
    json_path = os.path.join(folder, "FunctionalArchitecture.json")

    # Standard file detection / CSV generation
    if not os.path.exists(csv_path) and not os.path.exists(json_path):
        st.info("FunctionalArchitecture.json data is not available – upload it via **🪄 Edit Data**")
        return

    if not os.path.exists(csv_path) and os.path.exists(json_path):
        try:
            json_to_csv(json_input_path=json_path, csv_output_path=csv_path)
        except Exception as e:
            st.error(f"Failed to convert FunctionalArchitecture.json -> CSV: {e}")
            return

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        st.error(f"Failed to read FunctionalArchitecture.csv: {e}")
        return

    # Render table + the functional architecture graph (previous functionalview behavior),
    # using the dataframe we just read instead of a hard-coded reports path.
    st.header("Functional Architecture")

    dot = graphviz.Digraph(comment='Hierarchy', strict=True, graph_attr={"rankdir":"LR"})

    for _, row in df.iterrows():
        # expected columns: SOI, SystemFunction, SubFunction, SubSubFunction
        soi = row.get("SOI")
        sysfunc = row.get("SystemFunction")
        subfunc = row.get("SubFunction")
        subsubfunc = row.get("SubSubFunction")

        if pd.notna(soi):
            dot.node(str(soi))

        if pd.notna(sysfunc):
            if sysfunc not in dot.body:
                dot.node(str(sysfunc))
            if pd.notna(soi):
                dot.edge(str(soi), str(sysfunc), label="has system function")

        if pd.notna(subfunc):
            if subfunc not in dot.body:
                dot.node(str(subfunc))
            if pd.notna(sysfunc):
                dot.edge(str(sysfunc), str(subfunc), label="has sub function")

        if pd.notna(subsubfunc):
            if subsubfunc not in dot.body:
                dot.node(str(subsubfunc))
            if pd.notna(subfunc):
                dot.edge(str(subfunc), str(subsubfunc), label="has sub sub function")

    st.graphviz_chart(dot, use_container_width=True)

def functionalview():

    functionalarch = pd.read_csv("reports/FunctionalArchitecture.csv")
    
    st.write("#### Functional Architecture Diagram")

    dot = graphviz.Digraph(comment='Hierarchy', strict=True, graph_attr={"rankdir":"LR"})

    for index, row in functionalarch.iterrows():
        # colums: SOI,SystemFunction,SubFunction,SubSubFunction

        soi = row["SOI"]
        sysfunc = row["SystemFunction"]
        subfunc = row["SubFunction"]
        subsubfunc = row["SubSubFunction"]


        if pd.notna(soi):
            dot.node(soi)

        if pd.notna(sysfunc):
            if sysfunc not in dot.body:
                dot.node(sysfunc)
            if pd.notna(soi):
                dot.edge(soi, sysfunc, label="has system function")
        
        if pd.notna(subfunc):
            if subfunc not in dot.body:
                dot.node(subfunc)
            if pd.notna(sysfunc):
                dot.edge(sysfunc, subfunc, label="has sub function")
        
        if pd.notna(subsubfunc):
            if subsubfunc not in dot.body:
                dot.node(subsubfunc)
            if pd.notna(subfunc):
                dot.edge(subfunc, subsubfunc, label="has sub sub function")

    st.graphviz_chart(dot, True)