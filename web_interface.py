import streamlit as st
from import_data import main as import_main
from clean_data import main as clean_main
from vizualisation import plot_data, load_cleaned_file
from pathlib import Path
import builtins

st.set_page_config(page_title="Interface Pipeline", layout="centered")
st.title("📊 Traitement de données (.csv/.xlsx)")

st.markdown("""
Bienvenue sur votre interface de traitement de données.
Téléversez un fichier local **ou** fournissez un lien direct Statistique Canada / autre pour démarrer.
""")

step = st.session_state.get("step", 0)

if step == 0:
    st.subheader("Étape 1 : Importation")
    input_type = st.radio("Choisissez la source de vos données :", ["Fichier local", "Lien URL"])

    if input_type == "Fichier local":
        uploaded_file = st.file_uploader("Importez votre fichier (.csv ou .xlsx)", type=["csv", "xlsx"])
        if uploaded_file and st.button("Importer le fichier"):
            with open("temp_user_file.csv", "wb") as f:
                f.write(uploaded_file.read())
            builtins.input = lambda prompt='': "temp_user_file.csv"
            path = import_main()
            builtins.input = input
            if path:
                st.session_state["step"] = 1
                st.experimental_rerun()
    else:
        url_input = st.text_input("Entrez le lien vers le fichier (.csv ou .xlsx)")
        if st.button("Importer depuis l'URL") and url_input:
            builtins.input = lambda prompt='': url_input
            path = import_main()
            builtins.input = input
            if path:
                st.session_state["step"] = 1
                st.experimental_rerun()

elif step == 1:
    st.subheader("Étape 2 : Nettoyage des données")
    if st.button("Nettoyer les données"):
        try:
            path = clean_main()
            if path:
                st.session_state["step"] = 2
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Erreur lors du nettoyage : {e}")

elif step == 2:
    st.subheader("Étape 3 : Visualisation")
    try:
        last_file = Path(clean_main()).stem.replace("_cleaned", "")
        df = load_cleaned_file(last_file)
        if df is not None:
            plot_data(df)
            st.success("✅ Visualisation terminée.")
    except Exception as e:
        st.error(f"Erreur lors de la visualisation : {e}")

    if st.button("Recommencer depuis le début"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()
