# ─────────────────────────── web_interface.py  (v2025‑07‑04 i) ──────────────────────────
"""
Analytix : Analysez vos données facilement
--------------------------------------------------
Interface Streamlit modernisée pour importer, nettoyer et explorer vos données CSV ou Excel.

Nouveautés de la version **i**
• Nouveau texte d’explication plus clair pour les utilisateurs
• Retrait de la mention « Compatible : Statistique Canada… »
• Ajout d’un bouton pour passer à l’onglet suivant après chaque étape
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import streamlit as st
from import_data import add_one_file
from clean_data import main as clean_main
from vizualisation import plot_data, load_cleaned_file

# ────────────────────────────── OUTILS ─────────────────────────────────────────
SLUG_RE = re.compile(r"[^a-z0-9]+")

def slugify(txt: str) -> str:
    return SLUG_RE.sub("_", txt.lower()).strip("_")

# ─────────────────────────── CONFIG STREAMLIT ─────────────────────────────────
st.set_page_config(page_title="Analytix – Analyse de données", layout="centered")
st.title("📊 Analytix")
st.caption("Analysez vos données rapidement et efficacement")

st.markdown(
    """
Bienvenue sur **Analytix**, une interface rapide pour explorer vos fichiers de données.

1. Importation d’un fichier depuis votre ordinateur ou un lien (ce lien doit mener à un fichier .csv, .xlsx).
2. Nettoyage automatique du fichier importé.
3. Visualisation des données sous forme de graphiques clairs et interactifs.

*Conseil :* vous pouvez nommer vos fichiers pour les retrouver facilement. Si vous les importez localement (depuos votre ordinateur), ce n'est pas la peine de les nommer.
    """,
    unsafe_allow_html=True,
)

with st.expander("ℹ️ Aide / Formats acceptés"):
    st.markdown(
        """
        - Formats supportés : `.csv`, `.xlsx`, `.xls`
        - Limite recommandée : **200 Mo**
        """
    )

# ──────────────────────────── ONGLET PRINCIPAL ───────────────────────────────
tab1, tab2, tab3 = st.tabs(["1️⃣ Importation", "2️⃣ Nettoyage", "3️⃣ Visualisation"])

# ──────────────────────────── ÉTAPE 1 : IMPORTATION ───────────────────────────
with tab1:
    st.subheader("🟢 Importer un fichier")
    src_type = st.radio("Source des données :", ["Fichier local", "Lien URL"], horizontal=True)

    if src_type == "Fichier local":
        uploaded = st.file_uploader("Sélectionnez un fichier à importer :", type=["csv", "xlsx", "xls"], help="Max 200 Mo")
        fname = st.text_input("Nom personnalisé pour ce fichier (facultatif)")

        if uploaded and st.button("🚚 Importer le fichier"):
            internal = slugify(fname) if fname else slugify(Path(uploaded.name).stem)
            if not internal:
                st.warning("⚠️ Veuillez renseigner un nom correct.")
            else:
                suffix = Path(uploaded.name).suffix or ".csv"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.read())
                    tmp_path = tmp.name
                try:
                    saved = add_one_file(tmp_path, final_name=internal)
                except Exception as e:
                    saved = None
                    st.error("🚫 Erreur lors de l'import local.")
                    st.exception(e)
                finally:
                    os.unlink(tmp_path)

                if saved:
                    st.success(f"✅ Fichier importé : {saved}")
                    if st.button("➡️ Passer au nettoyage"):
                        st.experimental_set_query_params(tab="2")
                else:
                    st.error(f"🚫 Le nom ‘{internal}’ est déjà utilisé ou l’import a échoué.")

    else:
        url = st.text_input("Veuillez entrer un lien vers un fichier (.csv, .xlsx, .xls)")
        fname = st.text_input("Veuillez choisir un nom pour votre fichier (facultatif)")

        if st.button("🌐 Importer depuis le lien") and url:
            try:
                base = Path(url.split("?")[0]).stem
                internal = slugify(fname) if fname else slugify(base)
                if not internal:
                    st.warning("⚠️ Veuillez choisir un nom valide.")
                else:
                    saved = add_one_file(url, final_name=internal)
            except Exception as e:
                saved = None
                st.error("🚫 Échec du téléchargement ou de l’enregistrement.")
                st.exception(e)

            if saved:
                st.success(f"✅ Fichier importé : {saved}")
                if st.button("➡️ Passer au nettoyage"):
                    st.experimental_set_query_params(tab="2")
            else:
                st.error(f"🚫 Le nom ‘{internal}’ est déjà utilisé ou l’import a échoué.")

# ──────────────────────────── ÉTAPE 2 : NETTOYAGE ─────────────────────────────
with tab2:
    st.subheader("🧹 Nettoyage automatique du fichier")
    if st.button("🧼 Lancer le nettoyage"):
        with st.spinner("Nettoyage en cours…"):
            cleaned_path = clean_main()
        st.success(f"✅ Nettoyage terminé : {cleaned_path}")
        st.session_state.cleaned_path = str(cleaned_path)
        if st.button("➡️ Passer à la visualisation"):
            st.experimental_set_query_params(tab="3")

# ──────────────────────────── ÉTAPE 3 : VISUALISATION ─────────────────────────
with tab3:
    st.subheader("📈 Exploration graphique des données")
    if "cleaned_path" not in st.session_state:
        st.warning("⚠️ Veuillez d’abord importer et nettoyer un fichier.")
    else:
        cleaned_path = Path(st.session_state.cleaned_path)
        if cleaned_path.exists():
            st.session_state["__in_streamlit"] = True
            df = load_cleaned_file(cleaned_path.stem.replace("_cleaned", ""))
            if df is not None:
                st.sidebar.info("📌 Paramètres du graphique")
                plot_data(df)
            else:
                st.error("🚫 Impossible de charger le fichier nettoyé.")
        else:
            st.error("🚫 Fichier nettoyé introuvable.")
