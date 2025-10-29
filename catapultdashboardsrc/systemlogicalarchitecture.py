import streamlit as st
import os
import pandas as pd
from jsontocsv import json_to_csv
import graphviz

def systemview():

    st.write("#### System Architecture Diagram")
    # systemarch = pd.read_csv("reports/SystemArchitecture.csv")
    # st.write("SOI: catapultSystem")


    # subsystem = st.selectbox("Select Subsystem to view the architecture", systemarch["Subsystem"].unique())

    # subsetsystem = systemarch[systemarch["Subsystem"] == subsystem]

    subsystemdf = pd.read_csv("reports/Subsystems.csv")
    assembliesdf = pd.read_csv("reports/Assemblies.csv")
    componentsdf = pd.read_csv("reports/Components.csv")

    dot = graphviz.Digraph(
                comment='Hierarchy',  
                graph_attr={"height":"1000", "width":"1000", "rankdir":"LR"},
                strict=True
            )


    for index, row in subsystemdf.iterrows():
        soi = row["SOI"]
        subsystem = row["Subsystem"]

        if pd.notna(soi) and soi not in dot.body:
            dot.node(soi)

        if pd.notna(subsystem):
            if subsystem not in dot.body:
                dot.node(subsystem)
            if pd.notna(soi):
                dot.edge(soi, subsystem, label="has subsystem") 

        
    for index, row in assembliesdf.iterrows():
        soi = row["SOI"]
        subsystem = row["Subsystem"]
        assembly = row["Assembly"]

        if pd.notna(soi) and soi not in dot.body:
            dot.node(soi)

        if pd.notna(subsystem):
            if subsystem not in dot.body:
                dot.node(subsystem)
            if pd.notna(soi):
                dot.edge(soi, subsystem, label="has subsystem") 

        if pd.notna(assembly):
            if assembly not in dot.body:
                dot.node(assembly)
            if pd.notna(subsystem):
                dot.edge(subsystem, assembly, label="has assembly")

    for index, row in componentsdf.iterrows():
        soi = row["SOI"]
        subsystem = row["Subsystem"]
        assembly = row["Assembly"]
        component = row["Component"]

        if pd.notna(soi) and soi not in dot.body:
            dot.node(soi)

        if pd.notna(subsystem):
            if subsystem not in dot.body:
                dot.node(subsystem)
            if pd.notna(soi):
                dot.edge(soi, subsystem, label="has subsystem") 

        if pd.notna(assembly):
            if assembly not in dot.body:
                dot.node(assembly)
            if pd.notna(subsystem):
                dot.edge(subsystem, assembly, label="has assembly")

        if pd.notna(component):
            if component not in dot.body:
                dot.node(component)
            if pd.notna(assembly):
                dot.edge(assembly, component, label="has component")

    # st.graphviz_chart(dot)

    systemdot = graphviz.Digraph(
                comment='Hierarchy',  
                graph_attr={"height":"1000", "width":"1000", "rankdir":"LR"},
                strict=True
            )
    

    completesystemsdf = pd.concat([subsystemdf, assembliesdf, componentsdf])


    for index, row in completesystemsdf.iterrows():
        soi = row["SOI"]
        subsystem = row["Subsystem"]
        
        

        if pd.notna(soi) and soi not in dot.body:
            systemdot.node(soi)

        if pd.notna(subsystem):
            if subsystem not in dot.body:
                systemdot.node(subsystem)
            if pd.notna(soi):
                systemdot.edge(soi, subsystem, label="has subsystem") 
        

    subsystemopts = st.multiselect(label="Select one/multiple subsystem(s) to expand and  display", 
                                   options=completesystemsdf["Subsystem"].unique(),
                                   placeholder="Choose one/more subsystems")

    if subsystemopts != []:
        subsetdf = completesystemsdf[completesystemsdf["Subsystem"].isin(subsystemopts)]

        for index, row in subsetdf.iterrows():
            soi = row["SOI"]
            subsystem = row["Subsystem"]
            assembly = row["Assembly"]
            component = row["Component"]


            if pd.notna(soi) and soi not in systemdot.body:
                systemdot.node(soi)

            if pd.notna(subsystem):
                if subsystem not in systemdot.body:
                    systemdot.node(subsystem)
                if pd.notna(soi):
                    systemdot.edge(soi, subsystem, label="has subsystem")
            
            if pd.notna(assembly):
                if assembly not in systemdot.body:
                    systemdot.node(assembly)
                if pd.notna(subsystem):
                    systemdot.edge(subsystem, assembly, label="has assembly")

            if pd.notna(component):
                if component not in systemdot.body:
                    systemdot.node(component)
                if pd.notna(assembly):
                    systemdot.edge(assembly, component, label="has component")

    cols = st.columns(2)

    st.graphviz_chart(systemdot)

def render(project: dict) -> None:
    folder = project["folder"]
    subsystems_csv = os.path.join(folder, "Subsystems.csv")
    assemblies_csv = os.path.join(folder, "Assemblies.csv")
    components_csv = os.path.join(folder, "Components.csv")
    subsystems_json = os.path.join(folder, "Subsystems.json")
    assemblies_json = os.path.join(folder, "Assemblies.json")
    components_json = os.path.join(folder, "Components.json")

    # Need at least one of the key CSVs (prefer subsystems)
    if not any(os.path.exists(p) for p in (subsystems_csv, assemblies_csv, components_csv,
                                           subsystems_json, assemblies_json, components_json)):
        st.info("System architecture data (Subsystems/Assemblies/Components) is not available – upload via **🪄 Edit Data**")
        return

    # Convert available JSONs to CSVs if needed
    for csv_path, json_path in ((subsystems_csv, subsystems_json), (assemblies_csv, assemblies_json), (components_csv, components_json)):
        if not os.path.exists(csv_path) and os.path.exists(json_path):
            try:
                json_to_csv(json_input_path=json_path, csv_output_path=csv_path)
            except Exception as e:
                st.warning(f"Could not convert {os.path.basename(json_path)} -> CSV: {e}")

    # Read dataframes where possible (use empty frames if missing)
    def _safe_read(p):
        try:
            return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    subsystemdf = _safe_read(subsystems_csv)
    assembliesdf = _safe_read(assemblies_csv)
    componentsdf = _safe_read(components_csv)

    # Compose the complete table for options
    completesystemsdf = pd.concat([df for df in (subsystemdf, assembliesdf, componentsdf) if not df.empty], ignore_index=True) if not all(df.empty for df in (subsystemdf, assembliesdf, componentsdf)) else pd.DataFrame()

    st.header("System Logical Architecture")

    # Build a full graph (like previous systemview)
    systemdot = graphviz.Digraph(
        comment='Hierarchy',
        graph_attr={"height":"1000", "width":"1000", "rankdir":"LR"},
        strict=True
    )

    for _, row in completesystemsdf.iterrows():
        soi = row.get("SOI")
        subsystem = row.get("Subsystem")
        assembly = row.get("Assembly")
        component = row.get("Component")

        if pd.notna(soi):
            systemdot.node(str(soi))
        if pd.notna(subsystem):
            if subsystem not in systemdot.body:
                systemdot.node(str(subsystem))
            if pd.notna(soi):
                systemdot.edge(str(soi), str(subsystem), label="has subsystem")
        if pd.notna(assembly):
            if assembly not in systemdot.body:
                systemdot.node(str(assembly))
            if pd.notna(subsystem):
                systemdot.edge(str(subsystem), str(assembly), label="has assembly")
        if pd.notna(component):
            if component not in systemdot.body:
                systemdot.node(str(component))
            if pd.notna(assembly):
                systemdot.edge(str(assembly), str(component), label="has component")

    # Multi-select to filter subsystem(s) and display subgraph
    subsystem_opts = completesystemsdf["Subsystem"].dropna().unique().tolist() if not completesystemsdf.empty else []
    subsystemopts = st.multiselect(
        label="Select one/multiple subsystem(s) to expand and display",
        options=subsystem_opts,
        placeholder="Choose one/more subsystems"
    )

    if subsystemopts:
        subsetdf = completesystemsdf[completesystemsdf["Subsystem"].isin(subsystemopts)]
        subsetdot = graphviz.Digraph(
            comment='Subset Hierarchy',
            graph_attr={"height":"1000", "width":"1000", "rankdir":"LR"},
            strict=True
        )
        for _, row in subsetdf.iterrows():
            soi = row.get("SOI")
            subsystem = row.get("Subsystem")
            assembly = row.get("Assembly")
            component = row.get("Component")

            if pd.notna(soi):
                subsetdot.node(str(soi))
            if pd.notna(subsystem):
                if subsystem not in subsetdot.body:
                    subsetdot.node(str(subsystem))
                if pd.notna(soi):
                    subsetdot.edge(str(soi), str(subsystem), label="has subsystem")
            if pd.notna(assembly):
                if assembly not in subsetdot.body:
                    subsetdot.node(str(assembly))
                if pd.notna(subsystem):
                    subsetdot.edge(str(subsystem), str(assembly), label="has assembly")
            if pd.notna(component):
                if component not in subsetdot.body:
                    subsetdot.node(str(component))
                if pd.notna(assembly):
                    subsetdot.edge(str(assembly), str(component), label="has component")

        st.graphviz_chart(subsetdot, use_container_width=True)
    else:
        # show the full system graph if nothing selected
        st.graphviz_chart(systemdot, use_container_width=True)