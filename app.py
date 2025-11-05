import os
import pandas as pd
import streamlit as st
import importlib

from projectdetail import (DATA_TIES, VIEW_OPTIONS, REPORTS_ROOT,
                           project_form, replace_data, error_inspector_form,
                           required_files_for_view, build_oml_form, new_project_from_json_form)
import homepage

from utilities import _run_installation_if_streamlit_env, view_name_to_module_name
import auth



st.set_page_config(page_title="Dashboard", page_icon="🛰️", layout="wide")

def init_session():
    """Ensure all required session_state keys exist."""

    if 'projectlist' not in st.session_state:
        st.session_state['projectlist'] = [
                                            # {'id': 1, 
                                            # 'name': "System Dashboard", 
                                            # 'description': "", 
                                            # 'views': ["Home Page"] + [v for v in VIEW_OPTIONS if v != "Home Page"], 
                                            # 'folder': os.path.join(REPORTS_ROOT, "System Dashboard".lower().replace(" ", "_")),},
                                            # {'id': 2, 
                                            # 'name': "Lego Rover Dashboard", 
                                            # 'description': "", 
                                            # 'views': ["Home Page"] + [v for v in VIEW_OPTIONS if v != "Home Page"], 
                                            # 'folder': os.path.join(REPORTS_ROOT, "Lego Rover Dashboard".lower().replace(" ", "_")),},
                                        ]
    if 'currproject' not in st.session_state:
        st.session_state['currproject'] = None

    # NEW keys for upcoming flows (used later, harmless now)
    st.session_state.setdefault("retained_json_dir", None)      # temp path (str or None)
    st.session_state.setdefault("pending_dashboard_meta", None) # dict or None
    st.session_state.setdefault("create_dashboard_from_retained", False) # bool, True if user clicked "Create Dashboard" in retained JSON flow
    st.session_state.setdefault("create_dashboard_from_uploads", False)
    if 'omluploaded' not in st.session_state:
        st.session_state.omluploaded = False
    if 'build_code' not in st.session_state:
        st.session_state['build_code'] = None
    if 'build_log_path' not in st.session_state:
        st.session_state['build_log_path'] = None
    if 'sparql_present' not in st.session_state:
        st.session_state['sparql_present'] = False
    if 'query_run_exec' not in st.session_state:
        st.session_state['query_run_exec'] = False
    if 'query_code' not in st.session_state:
        st.session_state['query_code'] = None
    if 'query_log_path' not in st.session_state:
        st.session_state['query_log_path'] = None
    if 'query_results' not in st.session_state:
        st.session_state['query_results'] = None
    if 'dir_tree' not in st.session_state:
        st.session_state['dir_tree'] = []
    if 'sparql_selected_nodes' not in st.session_state:
        st.session_state['sparql_selected_nodes'] = []

def rerun_flag_check_function_calls():
    # st.write(st.session_state)
    if st.session_state["create_dashboard_from_retained"]:
        # If the user clicked "Create Dashboard" in retained JSON flow, show the dashboard creation form
        project_form(mode="from_retained")
    if st.session_state["create_dashboard_from_uploads"]:
        project_form(mode="from_uploads")


def panel():

    projectlist = st.session_state.get("projectlist", [])

    # --- Case A: No projects yet → show Welcome page with 2 CTAs and stop ---
    if not projectlist:
        # Display user info and logout at top right
        username = st.session_state.get('username', 'Guest')
        name = st.session_state.get('name', username)

        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            st.title("Welcome 👋")
        with col2:
            st.markdown(f"**👤 {name}**")
            if st.button("Logout", key="logout_no_projects"):
                auth.logout()

        st.caption("<span style='color:rgba(0,0,0,1); font-weight: 600;'>Create your first dashboard here!</span>", unsafe_allow_html=True)


        # Center the CTAs
        left, mid, right = st.columns([1, 2, 1])
        with mid:
            # # ONLY OML FILE --------------
            # if st.button("New project using OML file", icon="🟪", type="primary", use_container_width=True):
            #     build_oml_form()  # defined in projectdetail.py
            # # ----------------------------

            # # Both options ---------------
            c1, c2 = st.columns(2)
            with c1:
                if st.button("New project using OML file", icon="🟪", use_container_width=True):
                    build_oml_form()  # defined in projectdetail.py
            with c2:
                if st.button("New project using JSON files", icon="🔣", use_container_width=True):
                    new_project_from_json_form()
            # # ----------------------------
        
        # Prevent the rest of the app (e.g., main()) from rendering when no projects exist
        st.stop()

    # --- Case B: Projects exist → build Sidebar with selector + 2 creation buttons ---
    with st.sidebar:
        # Display user info and logout at top of sidebar
        username = st.session_state.get('username', 'Guest')
        name = st.session_state.get('name', username)
        project_count = len(projectlist)

        st.markdown(f"### 👤 {name}")
        st.caption(f"@{username} • {project_count} dashboard(s)")

        if st.button("Logout", key="logout_with_projects", use_container_width=True):
            auth.logout()

        st.divider()
        st.header("Dashboards")

        projectnames = [p['name'] for p in projectlist]
        currindex = projectnames.index(st.session_state['currproject']) if st.session_state['currproject'] != None else 0
        currproject = st.radio("Select Current Project", options=projectnames)
        st.session_state['currproject'] = currproject

        st.divider()
        # Replace the single "New Project" button with the two buttons below
        st.caption("<span style='color: rgba(0,0,0,1);'>Dashboard Preferences</span>", unsafe_allow_html=True)
        if st.button("New project", icon="💼", use_container_width=True):
            build_oml_form()
        #### HIDDEN UNTIL NECESSARY
        if st.button("New project using JSON files", icon="🆕", use_container_width=True):
            new_project_from_json_form()
            # st.info("The JSON-based creation flow will be implemented in the next step.")
        if st.button("Edit project", icon="✒️", use_container_width=True):
            project_form(mode="crud_dashboard")
        
        st.divider()
        
        st.subheader("Having problems with OML description?")
        st.caption("Upload your *reasoning.xml* file to easily breakdown your error")
        if st.button("Inspect Error", icon="🔍"):
            error_inspector_form()

def show_tab(tab_name, project):
    """
    Dispatch each tab to its own view module.
    Preference order:
      1) Home Page always uses centralized root homepage.py
      2) If project provides a module_prefix, attempt dynamic import of
         {module_prefix}.{view_module_name} and call its render(project).
      3) Fall back to dynamic import from root-level modules.
      4) Generic CSV preview fallback.
    """
    # ----- 0. Home Page always uses centralized root homepage.py ----------------
    if tab_name == "Home Page":
        homepage.render(project)
        return

    # ----- 1. Try dynamic import from profile-specific package ----------------
    module_prefix = project.get("module_prefix") if isinstance(project, dict) else None
    if module_prefix:
        # Normalize view/tab name to a module-like identifier
        modname = view_name_to_module_name(tab_name)
        candidate = f"{module_prefix}.{modname}"
        try:
            mod = importlib.import_module(candidate)
            if hasattr(mod, "render"):
                mod.render(project)
                return
        except Exception as e:
            # Failed to import profile-specific module — fall through to built-in handlers
            print(f"[debug] dynamic import failed for '{candidate}': {e}")

    else:
        # ---- 2. Try dynamic import from root-level modules  ----------------
        modname = view_name_to_module_name(tab_name)
        try:
            mod = importlib.import_module(modname)
            if hasattr(mod, "render"):
                mod.render(project)
                return
        except Exception as e:
            # Failed to import root-level module — fall through to generic fallback
            print(f"[debug] root-level import failed for '{modname}': {e}")

    # ---- 3. Generic fallback for other tabs  ---------------------------
    folder = project["folder"]
    for base in required_files_for_view(tab_name, project.get("profile")):
        csv_path = os.path.join(folder, f"{base}.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            st.dataframe(df, use_container_width=True)
        else:
            st.info(f"{base}.json data is not available - upload it via **🪄 Edit Data** button")
     
def main():
    projectlist = st.session_state['projectlist']
    currproject = st.session_state['currproject']

    if projectlist != []:
        project = [p for p in projectlist if p['name'] == currproject][0]
    
    if currproject == None:
        st.title("Welcome!")
        st.write("Create your first project to get started.")
    else:
        with st.container():
            # !!! HIDING EDIT DATA BUTTON UNTIL REQUIRED !!!
            # col1, col2 = st.columns([0.9, 0.15])
            # with col1:
            #     st.header(project["name"], divider='violet')
            # with col2:
            #     if st.button("🪄 Edit Data", type='primary'):
            #         replace_data(project) 
            st.header(project["name"], divider='violet')
        
        if project['views'] != []:
            VIEWTABS = st.tabs(project['views'])
            for i, tab in enumerate(VIEWTABS):
                with tab:
                    show_tab(project["views"][i], project)



def main_app():
    """Main application logic - only accessible when authenticated."""
    _run_installation_if_streamlit_env()  # Ensure Java/Gradle are installed
    init_session()
    rerun_flag_check_function_calls()
    panel()
    main()

    st.markdown(
        """
        <style>
        div[data-testid="stDialog"] div[role="dialog"]:has(.big-dialog) {
            width: 80vw;        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    # Check if user is already authenticated
    if auth.is_authenticated():
        # User is already logged in - go directly to main app
        main_app()
    else:
        # User not authenticated - show login/signup page
        name, authentication_status, username = auth.render_auth_page()

        if authentication_status:
            # User just authenticated - store info and run app
            st.session_state['username'] = username
            st.session_state['name'] = name
            st.rerun()  # Rerun to show app without auth page

        elif authentication_status == False:
            st.error('Username is incorrect or not found. Please check your username or sign up.')