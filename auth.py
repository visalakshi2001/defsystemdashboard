"""
Authentication module for OML Dashboard application.
Handles username-based authentication (no passwords).
"""

import streamlit as st
import re
from pathlib import Path

# Try to import tomllib (Python 3.11+) or fall back to toml
try:
    import tomllib
except ImportError:
    import toml as tomllib


# Path to user credentials file
USERS_FILE = Path("_auth/users.toml")


def load_credentials():
    """
    Load user credentials from _auth/users.toml (preferred) or Streamlit secrets (fallback).
    Returns credentials dict with usernames.
    """
    credentials = {"usernames": {}}

    # Try loading from _auth/users.toml first
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "rb") as f:
                data = tomllib.load(f)
                if "credentials" in data and "usernames" in data["credentials"]:
                    credentials["usernames"] = dict(data["credentials"]["usernames"])
                    return credentials
        except Exception as e:
            st.warning(f"Could not load credentials from {USERS_FILE}: {e}")

    # Fallback to Streamlit secrets
    try:
        if "credentials" in st.secrets and "usernames" in st.secrets["credentials"]:
            # Convert to regular dict (secrets returns special object)
            credentials["usernames"] = dict(st.secrets["credentials"]["usernames"])
            return credentials
    except Exception as e:
        pass

    return credentials


def render_auth_page():
    """
    Render the login/signup page.
    Returns (name, authentication_status, username) tuple.

    For username-only authentication:
    - Login: User enters username only
    - Signup: User enters username, name, and optional email
    """
    st.title("🔐 OML Dashboard")
    st.markdown("### Welcome to the OML Ontology Modeling Dashboard")

    # Check if already authenticated (from session state)
    if st.session_state.get('authentication_status', False):
        return (
            st.session_state.get('name'),
            st.session_state.get('authentication_status'),
            st.session_state.get('username')
        )

    # Create tabs for Login and Signup
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.markdown("#### Login to your dashboard")
        render_login_form()

    with tab2:
        st.markdown("#### Create a new account")
        render_signup_form()

    # Return current authentication status (will be None until user logs in)
    return (
        st.session_state.get('name'),
        st.session_state.get('authentication_status'),
        st.session_state.get('username')
    )


def render_login_form():
    """
    Render the login form for username-only authentication.
    Returns (name, authentication_status, username) tuple.
    """
    # Custom login form for username-only
    with st.form("login_form"):
        username_input = st.text_input("Username", key="login_username")
        submit = st.form_submit_button("Login", type="primary", use_container_width=True)

        if submit:
            if username_input:
                # Check if username exists in credentials
                credentials = load_credentials()
                usernames = credentials.get("usernames", {})

                if username_input in usernames:
                    # User exists - set session state
                    user_info = usernames[username_input]
                    name = user_info.get("name", username_input)

                    # Set authentication in session state
                    st.session_state['authentication_status'] = True
                    st.session_state['username'] = username_input
                    st.session_state['name'] = name

                    st.toast(f"Welcome back, {name}!", icon="👏")
                    st.rerun()
                else:
                    st.error("Username not found. Please sign up first.")
                    return None, False, None
            else:
                st.error("Please enter a username.")
                return None, None, None

    # Check session state for authentication
    if st.session_state.get('authentication_status', False):
        return (
            st.session_state.get('name'),
            st.session_state.get('authentication_status'),
            st.session_state.get('username')
        )

    return None, None, None


def render_signup_form():
    """
    Render the signup form for new users.
    """
    with st.form("signup_form"):
        new_username = st.text_input("Choose a username", key="signup_username")
        new_name = st.text_input("Your name", key="signup_name")
        new_email = st.text_input("Email (optional)", key="signup_email")

        submit = st.form_submit_button("Sign Up", type="primary", use_container_width=True)

        if submit:
            if new_username and new_name:
                # Validate username
                if not validate_username(new_username):
                    st.error("Username can only contain letters, numbers, underscores, and hyphens.")
                    return

                # Check if username already exists
                credentials = load_credentials()
                usernames = credentials.get("usernames", {})

                if new_username in usernames:
                    st.error("Username already exists. Please choose a different username.")
                    return

                # Save new user
                success, message = save_new_user(new_username, new_name, new_email)

                if success:
                    st.success(message)
                    st.info("You can now login with your username!")
                else:
                    st.error(message)
            else:
                st.error("Please provide both username and name.")


def validate_username(username):
    """
    Validate username format.
    Only allows alphanumeric characters, underscores, and hyphens.
    """
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, username))


def save_new_user(username, name, email=""):
    """
    Save new user to _auth/users.toml file.
    Uses compact TOML format: username = { name = "...", email = "..." }
    """
    # Validate input
    if not username or not name:
        return False, "Username and name are required."

    if not validate_username(username):
        return False, "Invalid username format."

    # Check if user already exists
    credentials = load_credentials()
    if username in credentials.get("usernames", {}):
        return False, "Username already exists."

    try:
        # Ensure _auth directory exists
        USERS_FILE.parent.mkdir(exist_ok=True)

        # Read existing users
        existing_users = {}
        if USERS_FILE.exists():
            with open(USERS_FILE, "rb") as f:
                data = tomllib.load(f)
                if "credentials" in data and "usernames" in data["credentials"]:
                    existing_users = dict(data["credentials"]["usernames"])

        # Add new user
        existing_users[username] = {"name": name, "email": email or ""}

        # Write back to file in compact format
        with open(USERS_FILE, "w") as f:
            f.write("# User credentials for OML Dashboard\n")
            f.write("# Compact format: username = { name = \"Full Name\", email = \"email@example.com\" }\n\n")
            f.write("[credentials.usernames]\n")

            for uname, udata in existing_users.items():
                uemail = udata.get("email", "")
                uname_full = udata.get("name", "")
                f.write(f'{uname} = {{ name = "{uname_full}", email = "{uemail}" }}\n')

        return True, f"User '{username}' registered successfully!"

    except Exception as e:
        return False, f"Error saving user: {e}"


def get_current_user():
    """
    Return currently authenticated username from session state.
    Returns None if not authenticated.
    """
    return st.session_state.get('username', None)


def logout():
    """
    Clear authentication session state and reload the page.
    """
    # Clear all session state to ensure clean logout
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


def is_authenticated():
    """
    Check if user is currently authenticated.
    Returns True if authenticated, False otherwise.
    """
    return st.session_state.get('authentication_status', False)
