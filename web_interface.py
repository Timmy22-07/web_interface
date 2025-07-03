import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from pathlib import Path
import tempfile

# 🚀 Modules « pipeline » déjà finalisés ------------------------------
from import_data import add_one_file  # pour importer
from clean_data import main as clean_main      # pour nettoyer → renvoie Path nettoyé
from vizualisation import plot_data, load_cleaned_file  # pour tracer
# -------------------------------------------------------------------

st.set_page_config(page_title="📊 Pipeline Excel - Données", layout="wide")

st.markdown(
    """
    <h1 style='text-align: center; color: #4A90E2;'>📈 Pipeline de Traitement Excel</h1>
    <p style='text-align: center;'>Importation ➜ Nettoyage ➜ Visualisation</p>
    """,
    unsafe_allow_html=True,
)

# ╭──────────────────────── Session State ─────────────────────────╮
if "step" not in st.session_state:
    st.session_state.step = 0  # 0→import, 1→clean, 2→viz
if "last_name" not in st.session_state:
    st.session_state.last_name = ""  # nom interne du fichier sans _cleaned
# ╰────────────────────────────────────────────────────────────────╯

# ╭──── Sidebar navigation ────╮
st.sidebar.title("Navigation")
if st.sidebar.button("🔄 Recommencer"):
    st.session_state.step = 0
    st.session_state.last_name = ""
    st.experimental_rerun()

steps = ["Importation", "Nettoyage", "Visualisation"]
for i, lbl in enumerate(steps):
    st.sidebar.markdown(f"{'✅' if st.session_state.step > i else '⬜'} {lbl}")
# ╰────────────────────────────╯

# ╭──────────────────────────── ÉTAPE 1 : IMPORT ─╮
if st.session_state.step == 0:
    st.subheader("📥 Étape 1 – Importation")
    source = st.radio("Source du fichier :", ["📁 Local", "🌐 URL"], horizontal=True)

    chosen_path: str | None = None

    if source == "📁 Local":
        up = st.file_uploader("Déposez un fichier Excel ou CSV", type=["xlsx", "xls", "csv"], key="upload")
        if up is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(up.name).suffix) as tmp:
                tmp.write(up.getbuffer())
                tmp_path = tmp.name
            chosen_path = tmp_path
            st.success("Fichier uploadé ✔️ – cliquez sur *Importer* pour continuer.")

    else:  # URL
        url = st.text_input("Copiez l'URL directe du fichier (.xlsx ou .csv)")
        if url:
            chosen_path = url
            st.info("URL prête – cliquez sur *Importer* pour continuer.")

    if chosen_path and st.button("🚚 Importer vers le pipeline"):
        st.info("⏳ Tentative d'importation avec timeout 10 s…")
        with st.spinner("Importation en cours…"):
            try:
                raw_path = add_one_file(chosen_path)  # écrit last_imported.txt
                st.success(f"✅ Importation réussie → {raw_path}")
                st.session_state.last_name = Path(raw_path).stem
                st.session_state.step = 1
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erreur d'importation : {e}")
# ╰──────────────────────────────────────────────────────────────────╯

# ╭──────────────────────────── ÉTAPE 2 : NETTOYAGE ─╮
elif st.session_state.step == 1:
    st.subheader("🧹 Étape 2 – Nettoyage")
    st.write("Fichier brut : **", st.session_state.last_name, "**")

    if st.button("🧼 Lancer le nettoyage"):
        with st.spinner("Nettoyage en cours…"):
            try:
                cleaned_path = clean_main(st.session_state.last_name)
                st.session_state.cleaned_path = cleaned_path
                st.success("Nettoyage terminé ✅")
                st.code(str(cleaned_path))
                st.session_state.step = 2
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erreur nettoyage : {e}")
# ╰──────────────────────────────────────────────────────────────────╯

# ╭──────────────────────────── ÉTAPE 3 : VISUALISATION ─╮
elif st.session_state.step == 2:
    st.subheader("📊 Étape 3 – Visualisation")

    df = load_cleaned_file(st.session_state.last_name)
    if df is None:
        st.error("Impossible de charger le fichier nettoyé.")
    else:
        st.write("### Aperçu des données (premières lignes)")
        st.dataframe(df.head(), use_container_width=True)

        st.write("### Choix des axes et graphique")
        numeric_cols = df.select_dtypes("number").columns
        if numeric_cols.empty:
            st.error("Aucune colonne numérique à tracer.")
        else:
            xcol = st.selectbox("Colonne X", df.columns, key="xcol")
            ycol = st.selectbox("Colonne Y (numérique)", numeric_cols, key="ycol")
            if st.button("📈 Tracer le graphique"):
                with st.spinner("Génération du graphique…"):
                    plot_data(df[[xcol, ycol]])
                    st.pyplot()

        st.success("🎉 Pipeline complet ! Vous pouvez recommencer ou fermer l'application.")
# ╰──────────────────────────────────────────────────────────────────╯
