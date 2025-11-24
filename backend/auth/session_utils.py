# backend/auth/session_utils.py

from __future__ import annotations

from typing import List
import streamlit as st


def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "role" not in st.session_state:
        st.session_state["role"] = None


def login_user(username: str, role: str):
    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["role"] = role


def logout_user():
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["role"] = None


def require_auth(allowed_roles: List[str]):
    if not st.session_state.get("authenticated", False):
        st.error("Vous devez être connecté(e).")
        st.stop()
    role = st.session_state.get("role")
    if role not in allowed_roles:
        st.error("Accès refusé pour ce rôle.")
        st.stop()
