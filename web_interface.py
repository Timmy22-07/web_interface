# ─────────────────────────── web_interface.py  (v2025‑07‑04 m) ───────────────────────────
"""
Analytix – pipeline : Import → Nettoyage → Visualisation
Ajouts :
• Bouton de téléchargement du fichier importé
• Bouton de téléchargement du fichier nettoyé
"""
from __future__ import annotations

import re, tempfile, os
from pathlib import Path
import streamlit as st

from import_data import add_one_file
from clean_data import main as clean_main
from vizualisation import plot_data, load_cleaned_file

# ────────────────────── Helpers ──────────────────────
SLUG_RE = re.compile(r"[^a-z0-9]+")
slugify = lambda t: SLUG_RE.sub("_", t.lower()).strip("_")

# ─────────────────── Config page ─────────────────────
st.set_page_config(page_title="Analytix – Analyse de données", layout="centered")
st.title("📊 Analytix")
st.caption("Importez, nettoyez et explorez vos données en trois clics.")

st.markdown(
    """
1. **Importation** d’un fichier .csv ou .xlsx localement ou à partir d'un lien.
2. **Nettoyage** automatique du fichier importé.
3. **Visualisation** sous forme de graphiques interactifs.

*Conseil :* nommer un fichier n’est utile que pour les liens distants. Si vous les importez localement (depuis votre ordinateur), ce n'est pas la peine de les nommer.
    """,
    unsafe_allow_html=True,
)

# ─────────────────── Session state ───────────────────
st.session_state.setdefault("step", 0)           # 0=import,1=nettoyage,2=viz
step = st.session_state.step

# Flags pour messages persistants
st.session_state.setdefault("imported_name", "")
st.session_state.setdefault("cleaned_name", "")

# ─────────────────── Onglets ─────────────────────────
tab_import, tab_clean, tab_viz = st.tabs(["📥 Importation", "🧽 Nettoyage", "📊 Visualisation"])

# ─────────────────── Onglet Importation ──────────────
with tab_import:
    st.subheader("📥 Importation d’un fichier")
    src_type = st.radio("Source des données :", ["Fichier local", "Lien URL"], horizontal=True)

    if src_type == "Fichier local":
        uploaded = st.file_uploader("Fichier à importer :", type=["csv", "xlsx", "xls"], help="200 Mo max")
        fname   = st.text_input("Nom personnalisé (facultatif)")
        if uploaded and st.button("🚚 Importer"):
            internal = slugify(fname) or slugify(Path(uploaded.name).stem)
            if not internal:
                st.warning("⚠️ Merci de saisir un nom valide.")
            else:
                suffix = Path(uploaded.name).suffix or ".csv"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.read()); tmp_path = tmp.name
                saved = add_one_file(tmp_path, final_name=internal)
                os.unlink(tmp_path)
                if saved:
                    st.session_state.imported_name = Path(saved).name
                    st.session_state.step = 1
                    st.rerun()
                else:
                    st.error("🚫 Import échoué ou nom déjà utilisé.")

    else:  # lien URL
        url  = st.text_input("Lien direct vers le fichier")
        fname = st.text_input("Nom personnalisé (facultatif)")
        if st.button("🌐 Importer depuis le lien") and url:
            internal = slugify(fname) or slugify(Path(url.split("?")[0]).stem)
            saved = add_one_file(url, final_name=internal)
            if saved:
                st.session_state.imported_name = Path(saved).name
                st.session_state.step = 1
                st.rerun()
            else:
                st.error("🚫 Import échoué ou nom déjà utilisé.")

    # Message persistant après import
    if st.session_state.imported_name:
        st.success(f"✅ Fichier importé : {st.session_state.imported_name}")
        st.download_button("📥 Télécharger le fichier importé", open(f"data/raw/{st.session_state.imported_name}", "rb"), file_name=st.session_state.imported_name)
        st.info("ℹ️ Passez à l’onglet **Nettoyage**.")

# ─────────────────── Onglet Nettoyage ────────────────
with tab_clean:
    st.subheader("🧽 Nettoyage automatique du fichier")
    if step < 1:
        st.warning("⛔ Importez d’abord un fichier.")
    else:
        if st.button("🧹 Lancer le nettoyage"):
            with st.spinner("Nettoyage en cours…"):
                cleaned_path = clean_main()
            st.session_state.cleaned_name = Path(cleaned_path).name
            st.session_state.step = 2
            st.rerun()

        # message persistant
        if st.session_state.cleaned_name:
            st.success(f"✅ Nettoyage terminé : {st.session_state.cleaned_name}")
            st.download_button("📥 Télécharger le fichier nettoyé", open(f"data/cleaned/{st.session_state.cleaned_name}", "rb"), file_name=st.session_state.cleaned_name)
            st.info("ℹ️ Passez à l’onglet **Visualisation**.")

# ─────────────────── Onglet Visualisation ────────────
with tab_viz:
    st.subheader("📊 Visualisation des données")
    if step < 2:
        st.warning("⛔ Nettoyez d’abord un fichier.")
    else:
        cleaned_path = Path("data/cleaned")/st.session_state.cleaned_name
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

        st.info("ℹ️ Vous pouvez retourner à l’onglet **Importation** pour analyser un autre fichier.")
