## Project Overview

This is a Streamlit-based dashboard application for visualizing and analyzing OML (Ontology Modeling Language) data. The application processes OML files through a Gradle-based build system, runs SPARQL queries against the resulting ontology, and presents the data through configurable dashboard views.

**Key workflow:**
1. User uploads an OML file (generated from Violet or similar tools)
2. System builds the OML using Gradle (via `omltemplateproject/`)
3. System runs SPARQL queries to extract data (stored as JSON)
4. JSON results are converted to CSV
5. Dashboard views render the data using Streamlit components

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py
```

**Prerequisites:**
- Java 21 (automatically installed on Streamlit Cloud; must be installed locally)
- Gradle (bundled as gradlew in `omltemplateproject/`)
- Python 3.9+

## Authentication System

The application uses a custom username-based authentication system. Users must sign in to access the dashboard.

### Overview
- **Authentication Type**: Username-only (no passwords currently)
- **User Storage**: Credentials stored in `_auth/users.toml` with fallback to `.streamlit/secrets.toml`
- **User Isolation**: Each user has their own folder structure at `reports/<username>/`
- **Session Management**: Session state tracks authenticated user and loads only their dashboards

### User Management

**Credentials File** (`_auth/users.toml`):
```toml
# User credentials for OML Dashboard
# Compact format: username = { name = "Full Name", email = "email@example.com" }

[credentials.usernames]
testuser = { name = "Test User", email = "test@example.com" }
johndoe = { name = "John Doe", email = "johndoe@example.com" }
```

**Automatic User Registration**:
- Users can sign up with a unique username, name, and optional email
- New users are automatically added to `_auth/users.toml`
- Username validation: only alphanumeric characters, underscores, and hyphens allowed

### Folder Structure

Projects are isolated per user:
```
reports/
├── .tmp/                    # Universal temp directory (session-scoped)
├── testuser/                # User-specific folder
│   ├── catapult_dashboard/
│   ├── lego_rover/
│   └── ...
├── johndoe/                 # Another user's folder
│   ├── test_optimization/
│   └── ...
```

**Key functions** (in `utilities.py`):
- `get_reports_root(username)`: Returns `Path("reports") / username`
- `session_tmp_dir()`: Universal temp dir (`.tmp/`) - session-isolated via UUIDs

### Authentication Module

**auth.py** provides:
- `load_credentials()`: Loads credentials from `_auth/users.toml` or `.streamlit/secrets.toml`
- `render_auth_page()`: Displays login/signup interface
- `save_new_user(username, name, email)`: Registers new user to `_auth/users.toml`
- `get_current_user()`: Returns current username from session state
- `logout()`: Clears session state and reruns app
- `is_authenticated()`: Checks if user is logged in

### Session Initialization

**app.py:init_session(username)**:
When a user logs in, `init_session(username)` is called to:
1. Scan `reports/<username>/` for existing project folders
2. For each folder, detect available CSV files
3. Match against `DASHBOARD_PROFILES` to identify dashboard type
4. Load project metadata with appropriate views and module prefix
5. Populate `projectlist` with only the user's dashboards

This ensures complete isolation: users see only their own projects.

### Development Notes

**Testing with multiple users:**
1. Create test users in `_auth/users.toml`
2. Login as different users in separate browsers/incognito tabs
3. Verify dashboard isolation (no cross-user data leakage)

**Security considerations:**
- ⚠️ No password protection currently (suitable for internal tools)
- Session cookies manage authentication state
- User folders provide isolation at filesystem level
- Consider adding password hashing for production deployments

**Migration from single-user setup:**
If you have existing projects in `reports/<project_name>/`, move them to `reports/<username>/<project_name>/` for proper user isolation. See `MIGRATION.md` for details.

## Architecture

### Entry Point & Session Management
- **app.py**: Main entry point. Initializes session state, manages dashboard selection sidebar, and routes to appropriate views via `show_tab()`.
- Session state tracks: project list, current project, OML upload status, build/query execution status, SPARQL file presence, and query results.

### Core Module Responsibilities

**projectdetail.py** (~860 lines)
- Manages dashboard CRUD operations via dialog forms
- Handles OML build workflow (upload → build → SPARQL query → dashboard creation)
- Contains `DASHBOARD_PROFILES` dict mapping profile names to required data files, views, and module prefixes
- Implements the JSON-to-dashboard creation flow
- Error inspector for OML reasoning failures (`error_inspector_form()`)

**omlbuilder.py**
- `buildoml()`: Saves uploaded OML file to `omltemplateproject/src/oml/`, runs Gradle build (`gradlew clean downloadDependencies build`)
- `sparql_query()`: Executes `startFuseki`, `owlQuery`, `stopFuseki` to generate JSON results in `omltemplateproject/build/results/`

**utilities.py**
- Temp directory management for session-scoped file staging
- Profile matching: `match_profile_from_basenames()` scores dashboard profiles by coverage of available JSON files
- Result consolidation: `consolidate_result_aliases()` merges duplicate JSON files (e.g., `Requirements_main.json` + `Requirements_testopt.json` → `Requirements.json`)
- Build tool installation for Streamlit Cloud (JDK 21 download/setup)

**jsontocsv.py**
- Converts SPARQL JSON results to CSV format for tabular display

### View Modules
Each view module has a `render(project: dict)` function:
- **homepage.py**: Displays triple count and basic project info
- **architecture.py**: Graphviz visualization of System/Mission Architecture
- **requirements.py**: Requirements table
- **testfacility.py**: Test facilities, equipment, personnel tables
- **teststrategy.py**: Test strategy overview
- **testresults.py**: Test results table
- **issueswarnings.py**: Warnings and issues extracted from data

### Profile-Specific Views
The app supports multiple dashboard profiles with specialized views in separate packages:
- **testoptimizationsrc/**: Views for Test Optimization profile (test strategy with cost analysis, scenarios)
- **catapultdashboardsrc/**: Views for Catapult profile (mission, functional architecture, system logical architecture)

Profile modules are dynamically imported based on `project["module_prefix"]` in `app.py:show_tab()`.

### Dashboard Profiles System
Defined in `projectdetail.py:DASHBOARD_PROFILES`:
- Each profile specifies: `data` (required JSON basenames), `views` (tab names), `module_prefix` (Python package for custom views), `view_data_ties` (per-view data requirements)
- Current profiles: "Lego Rover", "Test Optimization", "Catapult"
- When creating dashboards from results, the system auto-detects the best-matching profile by comparing available JSONs against profile requirements

## OML Build System

Located in `omltemplateproject/`:
- **build.gradle**: Defines OML dependencies, build tasks (omlToOwl, owlReason, owlLoad, owlQuery), Fuseki server management
- **src/oml/**: Stores uploaded OML file (as `uaomlfile.oml`)
- **src/sparql/**: SPARQL query files (`.sparql`) copied here by user or provided by default
- **build/results/**: Output directory for SPARQL JSON results
- **build/logs/**: Build and query logs

The Gradle build process:
1. Downloads OML dependencies (UA_Foundation, UA_Core, UA_Domain, UA_Libraries, Scenarios)
2. Converts OML to OWL
3. Runs Openllet reasoner
4. Starts Fuseki server, loads ontology, executes SPARQL queries, stops server

## Data Flow

```
OML file → buildoml() → Gradle build → SPARQL queries → JSON results
    → consolidate_result_aliases() → CSV conversion → Dashboard views
```

## Key Data Structures

**Project object:**
```python
{
    "id": int,
    "name": str,
    "description": str,
    "views": list[str],  # e.g., ["Home Page", "Architecture", "Requirements"]
    "folder": str,       # path to reports/project_name/
    "profile": str,      # optional, e.g., "Lego Rover"
    "module_prefix": str # optional, e.g., "catapultdashboardsrc"
}
```

**DATA_TIES mapping (in projectdetail.py):**
Maps view names to required JSON file basenames. Example:
```python
"Architecture": ["SystemArchitecture", "MissionArchitecture"]
```

## Session State Flags

Important session state keys that control workflow:
- `omluploaded`: True after OML file is uploaded
- `build_code`: Exit code from Gradle build (0 = success)
- `sparql_present`: True if SPARQL files exist in `omltemplateproject/src/sparql/`
- `query_run_exec`: True after SPARQL queries have been executed
- `query_code`: Exit code from SPARQL execution
- `retained_json_dir`: Path to temp directory with JSON results for dashboard creation
- `create_dashboard_from_retained`: Flag to trigger dashboard creation dialog after OML build
- `create_dashboard_from_uploads`: Flag to trigger dashboard creation dialog after JSON upload

## Common Tasks

**Add a new dashboard profile:**
1. Edit `projectdetail.py:DASHBOARD_PROFILES` to add new profile entry
2. Create a new package directory (e.g., `newprofilesrc/`)
3. Implement view modules with `render(project)` functions
4. Add corresponding SPARQL queries to `omltemplateproject/src/sparql/`

**Add a new view to existing profile:**
1. Create `viewname.py` with `render(project)` function in appropriate package
2. Update profile's `views` and `view_data_ties` in `DASHBOARD_PROFILES`
3. Ensure required JSON files are produced by SPARQL queries

**Debug build failures:**
- Check `omltemplateproject/build/logs/buildlogs_code*.log`
- Use Error Inspector dialog to analyze `omltemplateproject/build/reports/reasoning.xml`

**Debug SPARQL query issues:**
- Check `omltemplateproject/build/logs/querylogs_code*.log`
- Verify SPARQL files exist in `omltemplateproject/src/sparql/`
- Ensure Fuseki server starts/stops correctly (check port 3030 availability)

## Code Style

**Code Comements:**  
Do NOT delete the comments that are already made by the developer. You can add new comments if necessary for better documentation and edit/replace the comments of the code lines you are replacing/editing.

**Variables:**  
Make the variable names succinct, logical, and easy to write. The variable names should be lowercase and should represent what they store.

**Function:**  
The function nomenclature should be in par with the current style. 

## Logging

The application uses Python's `logging` module (configured in `utilities.py`). Debug-level logging is enabled throughout. Check console output or implement file logging if needed.

## Git Workflow

Recent commits show active development on:
- OML builder state management (flag resets after dashboard creation)
- Dashboard profile configuration plots
- SPARQL file consolidation for different profiles

When committing, include descriptive messages focusing on the feature/fix implemented.
