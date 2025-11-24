# app_service/pages/5_Public_Feed.py

from pathlib import Path
import sys

# Ajouter la racine du projet au sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="SAV Free - Fil public",
    page_icon="🌐",
    layout="wide",
)

st.title("🌐 Plateforme publique – Fil des tweets SAV Free")

st.markdown(
    """
Cette page propose une **vue publique** du flux Twitter autour de Free / Freebox :

- Timeline des **tweets originaux**, des **retweets** et des **citations**,
- **Barre de recherche** (texte + auteur),
- **Pagination**,
- Affichage des **commentaires d’un post** lorsqu’on clique sur 💬.
"""
)

# ----------------- Chargement des données (fichier original) -----------------
RAW_PATH = Path("data/raw/tweets.csv")

if not RAW_PATH.exists():
    alt_path = Path("tweets.csv")
    if alt_path.exists():
        RAW_PATH = alt_path

if not RAW_PATH.exists():
    st.error(
        "Le fichier original `tweets.csv` est introuvable.\n\n"
        "Merci de le placer dans `data/raw/tweets.csv` ou à la racine du projet."
    )
    st.stop()

df = pd.read_csv(RAW_PATH, dtype=str)

if df.empty:
    st.info("Le fichier `tweets.csv` est vide.")
    st.stop()

st.caption(f"Source de données : `{RAW_PATH}`")

# ----------------- Normalisation des colonnes -----------------
for col in [
    "id",
    "created_at",
    "full_text",
    "screen_name",
    "name",
    "profile_image_url",
    "user_id",
    "in_reply_to",
    "retweeted_status",
    "quoted_status",
    "favorite_count",
    "retweet_count",
    "reply_count",
    "views_count",
]:
    if col not in df.columns:
        df[col] = None

if df["id"].isna().all():
    df["id"] = df.index.astype(str)

# Texte affiché
def get_display_text(row):
    txt = row.get("full_text")
    if isinstance(txt, str):
        return txt.strip()
    return ""

# Détection du type de tweet
def detect_tweet_type(row):
    full_text = str(row.get("full_text", "") or "")
    rs = str(row.get("retweeted_status", "") or "").strip().lower()
    qs = str(row.get("quoted_status", "") or "").strip().lower()
    ir = str(row.get("in_reply_to", "") or "").strip().lower()

    if rs not in ("", "nan"):
        return "retweet"
    if qs not in ("", "nan"):
        return "quote"
    if ir not in ("", "nan"):
        return "reply"
    if full_text.startswith("RT "):
        # sécurité : certains exports marquent seulement "RT ..."
        return "retweet"
    return "original"

df["tweet_type"] = df.apply(detect_tweet_type, axis=1)

# Séparation posts / commentaires
posts_df = df[df["tweet_type"].isin(["original", "retweet", "quote"])].copy()
replies_df = df[df["tweet_type"] == "reply"].copy()

# Parse des dates pour trier
df["created_at_parsed"] = pd.to_datetime(df["created_at"], errors="coerce")
posts_df["created_at_parsed"] = pd.to_datetime(
    posts_df["created_at"], errors="coerce"
)

# ----------------- Filtres / recherche / pagination -----------------
st.sidebar.header("🔎 Recherche / Filtres")

search_text = st.sidebar.text_input("Recherche texte ou auteur (@pseudo)")

type_options = ["Tous", "Originaux", "Retweets", "Citations"]
selected_type = st.sidebar.selectbox("Type de tweet", type_options)

page_size = st.sidebar.slider(
    "Tweets par page",
    min_value=10,
    max_value=50,
    value=20,
    step=10,
)

# Tri par date décroissante si possible
if posts_df["created_at_parsed"].notna().any():
    posts_df = posts_df.sort_values("created_at_parsed", ascending=False)
else:
    posts_df = posts_df.sort_values("id", ascending=False)

# Filtre par type
filtered = posts_df.copy()

if selected_type == "Originaux":
    filtered = filtered[filtered["tweet_type"] == "original"]
elif selected_type == "Retweets":
    filtered = filtered[filtered["tweet_type"] == "retweet"]
elif selected_type == "Citations":
    filtered = filtered[filtered["tweet_type"] == "quote"]
# "Tous" -> rien

# Recherche
if search_text:
    q = search_text.lower().strip()
    mask_text = filtered["full_text"].astype(str).str.lower().str.contains(q)
    mask_user = filtered["screen_name"].astype(str).str.lower().str.contains(q)
    filtered = filtered[mask_text | mask_user]

total_posts = len(filtered)

if total_posts == 0:
    st.info("Aucun tweet ne correspond à la recherche / aux filtres.")
    st.stop()

# Pagination
total_pages = (total_posts - 1) // page_size + 1

st.sidebar.markdown("---")
page_number = st.sidebar.number_input(
    "Page",
    min_value=1,
    max_value=total_pages,
    value=1,
    step=1,
    help=f"{total_posts} tweets au total, {total_pages} page(s).",
)

start_idx = (page_number - 1) * page_size
end_idx = start_idx + page_size
page_df = filtered.iloc[start_idx:end_idx]

st.markdown(f"### 🧵 Page {page_number}/{total_pages} – {len(page_df)} tweets affichés")

# ----------------- Fonctions utilitaires -----------------
def format_count(val):
    try:
        v = int(val)
    except (ValueError, TypeError):
        return "0"
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.1f}K"
    return str(v)

def find_tweet_by_id(tweet_id: str):
    if not tweet_id:
        return None
    tid = str(tweet_id).strip()
    if tid == "" or tid.lower() == "nan":
        return None
    sub = df[df["id"].astype(str) == tid]
    if sub.empty:
        return None
    return sub.iloc[0]

def render_comment(row):
    """Affichage d'un commentaire (reply)."""
    with st.container():
        col_avatar, col_content = st.columns([1, 8])

        with col_avatar:
            img_url = row.get("profile_image_url", None)
            if isinstance(img_url, str) and img_url.strip():
                try:
                    st.image(img_url, width=32)
                except Exception:
                    st.write("👤")
            else:
                st.write("👤")

        with col_content:
            name = row.get("name") or ""
            screen_name = row.get("screen_name") or ""
            created_at = row.get("created_at") or ""

            st.markdown(f"**{name}**  @{screen_name} · {created_at}")
            st.write(get_display_text(row))

def render_embedded_tweet(row):
    """Affichage compact d'un tweet cité ou original (dans un bloc)."""
    if row is None:
        return
    with st.container():
        st.markdown(
            "<div style='border:1px solid #444; border-radius:8px; padding:8px;'>",
            unsafe_allow_html=True,
        )
        name = row.get("name") or ""
        screen_name = row.get("screen_name") or ""
        created_at = row.get("created_at") or ""
        text = get_display_text(row)

        st.markdown(f"**{name}**  @{screen_name} · {created_at}")
        st.write(text)
        fav = format_count(row.get("favorite_count"))
        rt = format_count(row.get("retweet_count"))
        rep = format_count(row.get("reply_count"))
        views = format_count(row.get("views_count"))
        c1, c2, c3, c4 = st.columns(4)
        c1.caption(f"💬 {rep}")
        c2.caption(f"🔁 {rt}")
        c3.caption(f"❤️ {fav}")
        c4.caption(f"👁️ {views}")
        st.markdown("</div>", unsafe_allow_html=True)

def render_post(row):
    """Affichage d'un post (original / retweet / citation) dans la timeline."""
    post_id = str(row.get("id", ""))
    ttype = row.get("tweet_type", "original")
    screen_name = row.get("screen_name") or ""
    name = row.get("name") or ""
    created_at = row.get("created_at") or ""

    # Commentaires associés
    post_replies = replies_df[replies_df["in_reply_to"].astype(str) == post_id]
    nb_comments = len(post_replies)

    # Pour les compteurs, on part de la ligne courante
    base_row = row

    with st.container():
        col_avatar, col_content = st.columns([1, 8])

        with col_avatar:
            img_url = row.get("profile_image_url", None)
            if isinstance(img_url, str) and img_url.strip():
                try:
                    st.image(img_url, width=48)
                except Exception:
                    st.write("👤")
            else:
                st.write("👤")

        with col_content:
            # HEADER
            st.markdown(f"**{name}**  @{screen_name} · {created_at}")

            # Type de tweet + éventuel original/quoted
            if ttype == "retweet":
                # On essaye de récupérer le tweet original
                orig = find_tweet_by_id(row.get("retweeted_status"))
                st.caption(f"🔁 @{screen_name} a retweeté")
                # Si on trouve le tweet original, on l'affiche comme sur Twitter
                if orig is not None:
                    base_row = orig  # pour les compteurs
                    render_embedded_tweet(orig)
                else:
                    # fallback : on affiche juste le texte "RT ..."
                    st.write(get_display_text(row))

            elif ttype == "quote":
                st.caption("💬 Citation d'un tweet")
                # D'abord le commentaire
                st.write(get_display_text(row))
                # Ensuite, si possible, le tweet cité
                orig = find_tweet_by_id(row.get("quoted_status"))
                if orig is not None:
                    st.caption("Tweet cité :")
                    render_embedded_tweet(orig)

            else:  # original
                st.caption("🧷 Tweet original")
                st.write(get_display_text(row))

            # Barre d'engagements (sur le tweet de référence : base_row)
            fav = format_count(base_row.get("favorite_count"))
            rt = format_count(base_row.get("retweet_count"))
            rep = format_count(base_row.get("reply_count"))
            views = format_count(base_row.get("views_count"))

            c1, c2, c3, c4 = st.columns(4)

            show_comments = c1.button(
                f"💬 {nb_comments}",
                key=f"comments_{post_id}_{screen_name}",
                help="Afficher les commentaires de ce post",
            )
            c2.caption(f"🔁 {rt}")
            c3.caption(f"❤️ {fav}")
            c4.caption(f"👁️ {views}")

            if show_comments:
                st.markdown("**Commentaires sur ce post :**")
                if nb_comments == 0:
                    st.write("Aucun commentaire pour ce post.")
                else:
                    pr = post_replies.copy()
                    pr["created_at_parsed"] = pd.to_datetime(
                        pr["created_at"], errors="coerce"
                    )
                    if pr["created_at_parsed"].notna().any():
                        pr = pr.sort_values("created_at_parsed", ascending=True)

                    for _, reply_row in pr.iterrows():
                        render_comment(reply_row)

        st.markdown("---")


# ----------------- Rendu de la timeline (page courante) -----------------
for _, tweet_row in page_df.iterrows():
    render_post(tweet_row)
