import streamlit as st
from import_data import main as import_main
from clean_data import main as clean_main
from vizualisation import plot_data, load_cleaned_file
from pathlib import Path
import builtins, tempfile, os

# ────────────────────────── CONFIG STREAMLIT ──────────────────────────
st.set_page_config(page_title="Pipeline de données", layout="centered")
st.title("\ud83d\udcca Traitement de données (.csv / .xlsx)")

st.markdown(
    """
    Téléversez un fichier local **ou** collez un lien (Statistique Canada ou autre).
    Le pipeline exécute : **Importation → Nettoyage → Visualisation**.
    """
)

# ──────────────────────────── ÉTAT AVANCEMENT ─────────────────────────
step = st.session_state.get("step", 0)

# ────────────────────────────── ÉTAPE 1 ───────────────────────────────
if step == 0:
    st.subheader("🟢 Étape 1 : Importation")
    input_type = st.radio("Source des données :", ["Fichier local", "Lien URL"], horizontal=True)

    if input_type == "Fichier local":
        uploaded = st.file_uploader("Importez votre fichier", type=["csv", "xlsx", "xls"], help="200 Mo max.")
        custom_name = st.text_input("Nom interne (facultatif)")
        if uploaded:
            if st.button("🚚 Importer le fichier"):
                suffix = Path(uploaded.name).suffix or ".csv"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.read())
                    tmp_path = tmp.name
                old_input = builtins.input
                builtins.input = lambda prompt='': custom_name if 'nom' in prompt.lower() else tmp_path
                try:
                    path = import_main()
                finally:
                    builtins.input = old_input

                if path:
                    st.success("\u2705 Fichier importé !")
                    st.session_state["step"] = 1
                    st.rerun()
                else:
                    st.error("\u274c Importation échouée.")

    else:
        url = st.text_input("Collez le lien direct (.csv/.xlsx ou export StatCan)")
        custom_name = st.text_input("Nom interne (facultatif)")
        if url and st.button("🌐 Importer depuis l'URL"):
            old_input = builtins.input
            builtins.input = lambda prompt='': custom_name if 'nom' in prompt.lower() else url
            try:
                path = import_main()
            finally:
                builtins.input = old_input

            if path:
                st.success("\u2705 Fichier importé !")
                st.session_state["step"] = 1
                st.rerun()
            else:
                st.error("\u274c Importation échouée – vérifie le lien.")

# ────────────────────────────── ÉTAPE 2 ───────────────────────────────
elif step == 1:
    st.subheader("🧹 Étape 2 : Nettoyage des données")
    if st.button("🧼 Nettoyer les données"):
        try:
            with st.spinner("Nettoyage en cours..."):
                cleaned_path = clean_main()
            st.success("\u2705 Nettoyage terminé : " + str(cleaned_path))
            st.session_state["step"] = 2
            st.session_state["cleaned_path"] = str(cleaned_path)
            st.rerun()
        except Exception as e:
            st.error(f"Erreur lors du nettoyage : {e}")

    if st.button("\u2b05\ufe0f Retour à l'importation"):
        st.session_state["step"] = 0
        st.rerun()

# ────────────────────────────── ÉTAPE 3 ───────────────────────────────
elif step == 2:
    st.subheader("📈 Étape 3 : Visualisation")
    cleaned_path = Path(st.session_state.get("cleaned_path", ""))

    if cleaned_path.exists():
        file_key = cleaned_path.stem.replace("_cleaned", "")
        try:
            with st.spinner("Chargement des données pour visualisation..."):
                df = load_cleaned_file(file_key)
            if df is not None:
                st.markdown("**Le système détecte automatiquement les types de colonnes et propose les graphiques appropriés.**")
                plot_data(df)
                st.success("🎉 Visualisation terminée.")
        except Exception as e:
            st.error(f"\u274c Erreur pendant la visualisation : {e}")
    else:
        st.error("\u274c Fichier nettoyé introuvable.")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("\u2b05\ufe0f Retour au nettoyage"):
            st.session_state["step"] = 1
            st.rerun()
    with col2:
        if st.button("🔄 Recommencer depuis le début"):
            st.session_state.clear()
            st.rerun()
