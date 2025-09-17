import streamlit as st

def check_auth():
    """
    Simple username/password authentication gate for a Streamlit app.

    This function:
      - Retrieves valid credentials from Streamlit secrets
      - Checks if the user is already authenticated via `st.session_state`
      - If not authenticated, displays a login form asking for username and password
      - If credentials match, sets `authenticated=True` in session_state and reloads the app
      - If credentials are incorrect, shows an error message
      - If user is not authenticated, execution stops after showing the login form

    Secrets required (in .streamlit/secrets.toml):
        [auth]
        username = "your_username"
        password = "your_password"
    """

    # Retrieve stored credentials from secrets
    USERNAME = st.secrets["auth"]["username"]
    PASSWORD = st.secrets["auth"]["password"]

    # Initialize the authenticated flag in session state if not set
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # If user is not yet authenticated, display login form
    if not st.session_state["authenticated"]:
        with st.form("Login"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            # When form is submitted, verify credentials
            if submitted:
                if user == USERNAME and pwd == PASSWORD:
                    # If valid, set authenticated to True and rerun the app
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    # If invalid, show error message
                    st.error("Invalid username or password")
        # Stop further script execution until user logs in successfully
        st.stop()
