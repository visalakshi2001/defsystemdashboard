import streamlit as st
import os
import json
import pandas as pd
from jsontocsv import json_to_csv
import graphviz

def render(project: dict) -> None:
    folder = project["folder"]
    mission_csv = os.path.join(folder, "MissionArchitecture.csv")
    mission_json = os.path.join(folder, "MissionArchitecture.json")
    env_csv = os.path.join(folder, "EnvEntities.csv")
    env_json = os.path.join(folder, "EnvEntities.json")
    ipt_csv = os.path.join(folder, "IPTStructure.csv")
    ipt_json = os.path.join(folder, "IPTStructure.json")

    # Require at least the main mission architecture file (or its JSON)
    if not any(os.path.exists(p) for p in (mission_csv, mission_json)):
        st.info("MissionArchitecture.json data is not available – upload it via **🪄 Edit Data**")
        return

    # Convert any missing CSVs where JSONs exist
    for csv_path, json_path in ((mission_csv, mission_json), (env_csv, env_json), (ipt_csv, ipt_json)):
        if not os.path.exists(csv_path) and os.path.exists(json_path):
            try:
                json_to_csv(json_input_path=json_path, csv_output_path=csv_path)
            except Exception as e:
                st.warning(f"Could not convert {os.path.basename(json_path)} -> CSV: {e}")

    # Read mission architecture
    try:
        missionarch = pd.read_csv(mission_csv)
    except Exception as e:
        st.error(f"Failed to read MissionArchitecture.csv: {e}")
        return

    st.header("Mission Architecture")
    
    # Build mission graph (previous missionview behavior)
    dot = graphviz.Digraph(comment='Hierarchy', strict=True)
    for _, row in missionarch.iterrows():
        mission = row.get("Mission")
        env = row.get("Env")
        ent = row.get("MissionEntities")

        if pd.notna(mission):
            dot.node(str(mission))

        if pd.notna(env):
            if env not in dot.body:
                dot.node(str(env))
            if pd.notna(mission):
                dot.edge(str(mission), str(env), label="has environment")

        if pd.notna(ent):
            if ent not in dot.body:
                dot.node(str(ent))
            if pd.notna(env):
                dot.edge(str(env), str(ent), label="has mission entity")

    st.graphviz_chart(dot, use_container_width=True)

    # Optional additional panels: IPT Structure and Environment Entities (if present)
    cols = st.columns(2)
    with cols[0]:
        if os.path.exists(ipt_csv):
            try:
                ipts = pd.read_csv(ipt_csv)
                st.write("#### IPT Structure")
                st.dataframe(ipts, hide_index=True, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not read IPTStructure.csv: {e}")
        else:
            st.info("IPTStructure.csv not present (optional)")

    with cols[1]:
        if os.path.exists(env_csv):
            try:
                envdf = pd.read_csv(env_csv)
                st.write("#### Environment Entities")

                dot_env = graphviz.Digraph(comment='Hierarchy', strict=True)
                for _, row in envdf.iterrows():
                    env = row.get("Env")
                    ent = row.get("EnvEntities")
                    quality = row.get("EnvQualities")

                    if pd.notna(env):
                        dot_env.node(str(env))

                    if pd.notna(ent):
                        if ent not in dot_env.body:
                            dot_env.node(str(ent))
                        if pd.notna(env):
                            dot_env.edge(str(env), str(ent), label="has entity")

                    if pd.notna(quality):
                        if quality not in dot_env.body:
                            dot_env.node(str(quality))
                        if pd.notna(ent):
                            dot_env.edge(str(ent), str(quality), label="has quality")

                st.graphviz_chart(dot_env, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not read EnvEntities.csv: {e}")
        else:
            st.info("EnvEntities.csv not present (optional)")

def missionview():

    missionarch = pd.read_csv("reports/MissionArchitecture.csv")

    st.write("#### Mission Architecture Diagram")

    dot = graphviz.Digraph(comment='Hierarchy', strict=True)

    for index, row in missionarch.iterrows():
        mission = row["Mission"]
        env = row["Env"]
        ent = row["MissionEntities"]

        if pd.notna(mission):
            dot.node(mission)

        if pd.notna(env):
            if env not in dot.body:
                dot.node(env)
            if pd.notna(mission):
                dot.edge(mission, env, label="has environment")
        
        if pd.notna(ent):
            if ent not in dot.body:
                dot.node(ent)
            if pd.notna(env):
                dot.edge(env, ent, label="has mission entity")  
    st.graphviz_chart(dot, True)

    cols = st.columns(2)

    with cols[0]:
        ipts = pd.read_csv("reports/IPTStructure.csv")

        st.write("#### IPT Structure")

        st.dataframe(ipts, hide_index=True)

    with cols[1]:
        st.write("#### Environment Entities")

        envdf = pd.read_csv("reports/EnvEntities.csv")

        dot = graphviz.Digraph(comment='Hierarchy', strict=True)

        for index, row in envdf.iterrows():
            env = row["Env"]
            ent = row["EnvEntities"]
            quality = row["EnvQualities"]

            if pd.notna(env):
                dot.node(env)

            if pd.notna(ent):
                if ent not in dot.body:
                    dot.node(ent)
                if pd.notna(env):
                    dot.edge(env, ent, label="has entity")
            
            if pd.notna(quality):
                if quality not in dot.body:
                    dot.node(quality)
                if pd.notna(ent):
                    dot.edge(ent, quality, label="has quality")  
        st.graphviz_chart(dot, True)