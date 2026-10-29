"""
Google Fit OAuth 2.0 helper functions.

This module encapsulates the Authorization Code flow using google-auth-oauthlib
and stores credentials inside Streamlit's session_state.
"""

from __future__ import annotations

import time
from typing import Optional

import streamlit as st
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from database.db import (
    save_pending_state,
    get_pending_state,
    delete_pending_state,
    save_google_fit_token,
    get_google_fit_token,
)

# OAuth 2.0 settings
CLIENT_ID = "104326270108-mg0atppvnokbfgdt3gp4530off15rm7j.apps.googleusercontent.com"

# NOTE: In a real app, do NOT hard-code the client secret.
# Read it from environment variables or Streamlit secrets instead.
CLIENT_SECRET = st.secrets.get("GOOGLE_FIT_CLIENT_SECRET", "")

# NOTE: Ensure this matches the port Streamlit is running on
REDIRECT_URI = "http://localhost:8505"

# Allow non-HTTPS for local development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/fitness.sleep.read",
]


def _build_flow() -> Flow:
    """Create an OAuth Flow instance for Google Fit."""
    client_config = {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI
    return flow


def _creds_to_dict(creds: Credentials) -> dict:
    """Serialize Credentials to a JSON-serializable dict."""
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "expiry": creds.expiry.timestamp() if creds.expiry else None,
    }


def _creds_from_dict(data: dict) -> Credentials:
    """Rehydrate Credentials from a dict."""
    if not data:
        raise ValueError("Empty credential data")
    if data.get("expiry") is not None:
        # google.oauth2.credentials will parse expiry from seconds since epoch
        data = dict(data)
        data["expiry"] = float(data["expiry"])
    return Credentials(**data)


def get_stored_credentials(user_id: Optional[int] = None) -> Optional[Credentials]:
    """Return valid credentials from session_state, refreshing if needed."""
    raw = st.session_state.get("google_fit_creds")
    
    # If missing from session, check DB
    if not raw and user_id:
        import json
        token_json = get_google_fit_token(user_id)
        if token_json:
            raw = json.loads(token_json)
            st.session_state.google_fit_creds = raw

    if not raw:
        return None
    try:
        creds = _creds_from_dict(raw)
    except Exception:
        return None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            return None
        serialized = _creds_to_dict(creds)
        st.session_state.google_fit_creds = serialized
        if user_id:
            import json
            save_google_fit_token(user_id, json.dumps(serialized))

    return creds


def is_authenticated(user_id: Optional[int] = None) -> bool:
    """Return True if we have usable Google Fit credentials."""
    return get_stored_credentials(user_id) is not None


def get_authorization_url(user_id: int) -> str:
    """
    Build the Google OAuth authorization URL and store the state in session and DB.
    """
    flow = _build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    st.session_state.google_fit_oauth_state = state
    save_pending_state(state, user_id)
    return auth_url


def handle_authorization_response(full_redirect_url: str, query_params: dict) -> tuple[bool, Optional[int]]:
    """
    Exchange the authorization response URL for tokens and store credentials.
    Returns (success, linked_user_id).
    """
    state = st.session_state.get("google_fit_oauth_state")
    if not state:
        # Fallback to DB if session state is lost
        state = query_params.get("state")
        if not state:
            return False, None
    
    linked_user_id = get_pending_state(state)
    if not linked_user_id:
        return False, None

    flow = _build_flow()
    flow.fetch_token(authorization_response=full_redirect_url)
    creds = flow.credentials
    if not creds:
        return False, None

    serialized = _creds_to_dict(creds)
    st.session_state.google_fit_creds = serialized
    st.session_state.google_fit_connected_at = int(time.time())
    
    # Persistent save
    import json
    save_google_fit_token(linked_user_id, json.dumps(serialized))
    delete_pending_state(state)
    
    return True, linked_user_id

