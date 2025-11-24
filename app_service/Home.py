# app_service/Home.py

from pathlib import Path
import sys

# Ajouter la racine du projet au sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.auth.users_store import authenticate
from backend.auth.session_utils import init_session_state, login_user, logout_user

import streamlit as st

st.set_page_config(page_title="SAV Free - Plateforme Service", page_icon="🛰️")
init_session_state()

st.title("🛰️ Plateforme SAV Free - Connexion")

if st.session_state["authenticated"]:
    st.success(f"Connecté en tant que {st.session_state['username']} ({st.session_state['role']})")
    if st.button("Se déconnecter"):
        logout_user()
        st.experimental_rerun()
else:
    username = st.text_input("Identifiant")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        user = authenticate(username, password)
        if not user:
            st.error("Identifiants incorrects")
        else:
            login_user(user["username"], user["role"])
            st.success(f"Connexion réussie ({user['role']})")

            role = user["role"]
            if role == "agent":
                st.switch_page("pages/1_Agent.py")
            elif role == "manager":
                st.switch_page("pages/2_Manager.py")
            elif role == "analyst":
                st.switch_page("pages/3_Analyst.py")
            elif role == "admin":
                st.switch_page("pages/4_Admin_Upload_CSV.py")
            else:
                st.info("Aucune page définie pour ce rôle.")
