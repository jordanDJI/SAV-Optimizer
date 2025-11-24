# app_service/pages/1_Agent.py

from pathlib import Path
import sys

# === Ajouter la racine du projet au sys.path ===
# 1_Agent.py est dans app_service/pages -> parents[2] = solution_Sav_Free/
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import streamlit as st

from backend.auth.session_utils import require_auth
from backend.data_pipeline.storage import load_enriched_tweets

# ----------------- Config page -----------------
st.set_page_config(page_title="SAV Free - Agent", page_icon="📞")

# ----------------- Authentification -----------------
require_auth(["agent", "admin"])

st.title("📞 Espace Agent SAV")

st.markdown(
    """
Cette interface permet aux agents de **traiter les problèmes clients** détectés dans les tweets :

- Filtrer les plaintes par **priorité**, **type de plainte**, **sarcasme**, **risque de résiliation**.
- Voir le **détail d'un tweet** (texte, classification, contexte).
- Gérer un **statut de traitement** et une **note interne** (démonstration).
"""
)

# ----------------- Etat local pour les notes agent -----------------
if "agent_notes" not in st.session_state:
    st.session_state["agent_notes"] = {}  # {row_id: note}

if "agent_status" not in st.session_state:
    st.session_state["agent_status"] = {}  # {row_id: "Nouveau"/"En cours"/"Résolu"}

# ----------------- Chargement des tweets enrichis -----------------
try:
    df = load_enriched_tweets()  # par défaut: data/processed/tweets_enriched.csv
except FileNotFoundError:
    st.error(
        "Le fichier `data/processed/tweets_enriched.csv` est introuvable.\n\n"
        "Va d'abord sur la page **Admin** pour lancer le pipeline."
    )
    st.stop()

# On ne garde que les plaintes pour l'agent
if "final_intent" in df.columns:
    df = df[df["final_intent"] == "complaint"].copy()

if df.empty:
    st.info("Aucune plainte à afficher pour le moment.")
    st.stop()

# ----------------- Identification d'un ID de tweet pour la clé agent -----------------
ID_COL = None
for cand in ["id", "tweet_id", "status_id"]:
    if cand in df.columns:
        ID_COL = cand
        break

if ID_COL is None:
    # fallback: on crée un identifiant basé sur l'index
    ID_COL = "_agent_row_id"
    df[ID_COL] = df.index.astype(str)

# ----------------- Colonne 'est_commentaire' -----------------
# Un commentaire = une réponse à un autre tweet
if "tweet_type" in df.columns:
    df["is_comment"] = df["tweet_type"].astype(str).str.lower().eq("reply")
elif "in_reply_to" in df.columns:
    df["is_comment"] = df["in_reply_to"].astype(str).str.strip().ne("").fillna(False)
else:
    df["is_comment"] = False

# ----------------- Filtres dans la sidebar -----------------
st.sidebar.header("🧰 Filtres")

# Priorité
if "final_priority" in df.columns:
    priorities = df["final_priority"].dropna().unique().tolist()
    # on ordonne un peu si possible
    order = ["critical", "high", "medium", "low", "none"]
    priorities = [p for p in order if p in priorities] + [
        p for p in priorities if p not in order
    ]
    selected_priorities = st.sidebar.multiselect(
        "Priorités", priorities, default=[p for p in priorities if p not in ("none")]
    )
else:
    selected_priorities = []

# Types de plainte
if "final_complaint_type" in df.columns:
    types_plainte = df["final_complaint_type"].dropna().unique().tolist()
    selected_types = st.sidebar.multiselect(
        "Types de plainte", types_plainte, default=types_plainte
    )
else:
    selected_types = []

# Sarcasme
only_sarcasm = False
if "final_sarcasm" in df.columns:
    only_sarcasm = st.sidebar.checkbox("Uniquement les tweets sarcastiques")

# Risque de résiliation
only_resiliation_risk = False
if "nlp_has_resiliation_risk" in df.columns:
    only_resiliation_risk = st.sidebar.checkbox("Risque de résiliation détecté")

# Commentaire / original
filter_comments = st.sidebar.selectbox(
    "Type de message",
    ["Tous", "Commentaires (réponses)", "Tweets originaux"],
)

# Recherche texte
search_text = st.sidebar.text_input("Recherche dans le texte (mot-clé)")

# ----------------- Application des filtres -----------------
filtered = df.copy()

if selected_priorities:
    if "final_priority" in filtered.columns:
        filtered = filtered[filtered["final_priority"].isin(selected_priorities)]

if selected_types:
    if "final_complaint_type" in filtered.columns:
        filtered = filtered[filtered["final_complaint_type"].isin(selected_types)]

if only_sarcasm and "final_sarcasm" in filtered.columns:
    filtered = filtered[filtered["final_sarcasm"].astype(str).str.lower() == "true"]

if only_resiliation_risk and "nlp_has_resiliation_risk" in filtered.columns:
    filtered = filtered[
        filtered["nlp_has_resiliation_risk"].astype(str).str.lower().isin(["true", "1"])
    ]

if filter_comments == "Commentaires (réponses)":
    filtered = filtered[filtered["is_comment"] == True]
elif filter_comments == "Tweets originaux":
    filtered = filtered[filtered["is_comment"] == False]

if search_text:
    search_lower = search_text.lower()
    if "text_clean" in filtered.columns:
        filtered = filtered[
            filtered["text_clean"].astype(str).str.lower().str.contains(search_lower)
        ]

if filtered.empty:
    st.warning("Aucun tweet ne correspond aux filtres sélectionnés.")
    st.stop()

# ----------------- Tri par priorité + date si dispo -----------------
if "final_priority" in filtered.columns:
    # on mappe la priorité sur un score pour trier correctement
    priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "none": 0}
    filtered["_priority_score"] = filtered["final_priority"].map(
        priority_order
    ).fillna(0)
    if "created_at" in filtered.columns:
        filtered = filtered.sort_values(
            by=["_priority_score", "created_at"], ascending=[False, True]
        )
    else:
        filtered = filtered.sort_values(by="_priority_score", ascending=False)
else:
    if "created_at" in filtered.columns:
        filtered = filtered.sort_values("created_at", ascending=True)

# ----------------- Tableau principal -----------------
st.subheader("📋 Liste des plaintes à traiter")

display_cols = []

if "created_at" in filtered.columns:
    display_cols.append("created_at")
if "screen_name" in filtered.columns:
    display_cols.append("screen_name")

display_cols.append("text_clean")

for c in ["final_complaint_type", "final_priority", "final_sentiment", "final_sarcasm"]:
    if c in filtered.columns:
        display_cols.append(c)

if "is_comment" in filtered.columns:
    display_cols.append("is_comment")

st.dataframe(filtered[display_cols], use_container_width=True)

# ----------------- Sélection d'un tweet pour traitement -----------------
st.subheader("🛠️ Détail et traitement d'un tweet")

# Liste des lignes pour sélection
options = []
for idx, row in filtered.iterrows():
    label_parts = []
    if "created_at" in row:
        label_parts.append(str(row["created_at"]))
    if "screen_name" in row:
        label_parts.append(f"@{row['screen_name']}")
    if "final_complaint_type" in row:
        label_parts.append(f"[{row['final_complaint_type']}]")
    # résumé du texte
    txt = str(row.get("text_clean", ""))[:80].replace("\n", " ")
    label_parts.append(f"« {txt}… »")
    label = " - ".join(label_parts)
    options.append((label, idx))

# Selectbox
labels = [opt[0] for opt in options]
indices = [opt[1] for opt in options]

selected_label = st.selectbox("Sélectionner un tweet à traiter", labels)
selected_idx = indices[labels.index(selected_label)]

row = filtered.loc[selected_idx]
row_id = str(row[ID_COL])

# ----------------- Affichage des détails du tweet -----------------
st.markdown("### 🧾 Détails du tweet")

col_left, col_right = st.columns(2)

with col_left:
    st.write("**Utilisateur** :", f"@{row['screen_name']}" if "screen_name" in row else "N/A")
    st.write("**Date** :", row.get("created_at", "N/A"))
    st.write("**Type de message** :", row.get("tweet_type", "N/A"))
    st.write("**Commentaire d'un post ?** :", "Oui" if row.get("is_comment", False) else "Non")

with col_right:
    st.write("**Type de plainte (final)** :", row.get("final_complaint_type", "N/A"))
    st.write("**Priorité (finale)** :", row.get("final_priority", "N/A"))
    st.write("**Sentiment (final)** :", row.get("final_sentiment", "N/A"))
    st.write("**Sarcasme (final)** :", "Oui" if str(row.get("final_sarcasm", "False")).lower() == "true" else "Non")
    st.write(
        "**Risque de résiliation** :",
        "Oui" if str(row.get("nlp_has_resiliation_risk", "False")).lower() in ["true", "1"] else "Non",
    )

st.markdown("**Texte du tweet (nettoyé)** :")
st.write(row.get("text_clean", ""))

if "llm_explanation" in row:
    st.markdown("**Explication de la classification** :")
    st.info(row["llm_explanation"])

# ----------------- Gestion du statut + note interne -----------------
st.markdown("### 🧩 Suivi du traitement")

current_status = st.session_state["agent_status"].get(row_id, "Nouveau")
current_note = st.session_state["agent_notes"].get(row_id, "")

new_status = st.selectbox(
    "Statut du ticket",
    ["Nouveau", "En cours", "Résolu"],
    index=["Nouveau", "En cours", "Résolu"].index(current_status),
)

new_note = st.text_area("Note interne (non visible par le client)", value=current_note, height=120)

if st.button("💾 Enregistrer le statut et la note pour ce tweet"):
    st.session_state["agent_status"][row_id] = new_status
    st.session_state["agent_notes"][row_id] = new_note
    st.success("Statut et note mis à jour (en mémoire pour la démo).")
