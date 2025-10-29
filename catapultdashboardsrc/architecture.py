import streamlit as st
import os
import pandas as pd
import graphviz
from jsontocsv import json_to_csv


def render(project: dict) -> None:
    """
    Consolidated Architecture view for Catapult Dashboard.
    Provides a dropdown to select between Mission, Functional, and System Logical architectures.
    """
    folder = project["folder"]

    # Dropdown selector for architecture type
    arch_type = st.selectbox(
        "Select Architecture View",
        options=["Mission", "Functional Architecture", "System Logical Architecture"],
        key="catapult_arch_selector"
    )

    # Route to appropriate rendering based on selection
    if arch_type == "Mission":
        _render_mission(folder)
    elif arch_type == "Functional Architecture":
        _render_functional(folder)
    elif arch_type == "System Logical Architecture":
        _render_system_logical(folder)


def _render_mission(folder: str) -> None:
    """Render Mission Architecture view with environment entities and IPT structure."""
    mission_csv = os.path.join(folder, "MissionArchitecture.csv")
    mission_json = os.path.join(folder, "MissionArchitecture.json")
    env_csv = os.path.join(folder, "EnvEntities.csv")
    env_json = os.path.join(folder, "EnvEntities.json")
    ipt_csv = os.path.join(folder, "IPTStructure.csv")
    ipt_json = os.path.join(folder, "IPTStructure.json")

    # Require at least the main mission architecture file (or its JSON)
    if not any(os.path.exists(p) for p in (mission_csv, mission_json)):
        st.info("MissionArchitecture.json data is not available – upload it via **🪄 Edit Data**")
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

    # Build mission graph
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


def _render_functional(folder: str) -> None:
    """Render Functional Architecture view."""
    csv_path = os.path.join(folder, "FunctionalArchitecture.csv")
    json_path = os.path.join(folder, "FunctionalArchitecture.json")

    # Standard file detection / CSV generation
    if not os.path.exists(csv_path) and not os.path.exists(json_path):
        st.info("FunctionalArchitecture.json data is not available – upload it via **🪄 Edit Data**")
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

    # Render the functional architecture graph
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


def _render_system_logical(folder: str) -> None:
    """Render System Logical Architecture view with subsystem filtering."""
    subsystems_csv = os.path.join(folder, "Subsystems.csv")
    assemblies_csv = os.path.join(folder, "Assemblies.csv")
    components_csv = os.path.join(folder, "Components.csv")
    subsystems_json = os.path.join(folder, "Subsystems.json")
    assemblies_json = os.path.join(folder, "Assemblies.json")
    components_json = os.path.join(folder, "Components.json")

    # Need at least one of the key CSVs (prefer subsystems)
    if not any(os.path.exists(p) for p in (subsystems_csv, assemblies_csv, components_csv,
                                           subsystems_json, assemblies_json, components_json)):
        st.info("System architecture data (Subsystems/Assemblies/Components) is not available – upload via **🪄 Edit Data**")
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

    # Build a full graph
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
