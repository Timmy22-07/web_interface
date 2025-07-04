import streamlit as st
from import_data import add_one_file              # ⬅️ appel direct, sans input mock
from clean_data import main as clean_main
from vizualisation import plot_data, load_cleaned_file
from pathlib import Path
import tempfile, os, re

# ───────────────────────── CONFIG STREAMLIT ─────────────────────────
st.set_page_config(page_title="Pipeline de données", layout="centered")
st.title("📊 Traitement de données (.csv / .xlsx)")

st.markdown(
    """
Téléversez un fichier local **ou** collez un lien (Statistique Canada ou autre).  
Le pipeline exécute : **Importation → Nettoyage → Visualisation**.
    """
)

# ────────────────────────── ÉTAT GLOBAL ────────────────────────────
if "step" not in st.session_state:
    st.session_state.step = 0
if "cleaned_path" not in st.session_state:
    st.session_state.cleaned_path = ""

# utilitaire
slugify = lambda t: re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")

step = st.session_state.step

# ───────────────────────────── ÉTAPE 1 ──────────────────────────────
if step == 0:
    st.subheader("🟢 Étape 1 : Importation")
    src_type = st.radio("Source des données :", ["Fichier local", "Lien URL"], horizontal=True)

    # ‣ fichier local ───────────────────────────────────────────────
    if src_type == "Fichier local":
        uploaded = st.file_uploader("Importez votre fichier", type=["csv", "xlsx", "xls"], help="200 Mo max.")
        fname = st.text_input("Nom interne (facultatif)")
        if uploaded and st.button("🚚 Importer"):
            suffix = Path(uploaded.name).suffix or ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            final = slugify(fname) if fname else slugify(Path(uploaded.name).stem)
            path = add_one_file(tmp_path, final_name=final)
            os.unlink(tmp_path)
            if path:
                st.success(f"✅ Importé : {path}")
                st.session_state.step = 1
                st.experimental_rerun()
            else:
                st.error("❌ Importation échouée.")

    # ‣ lien URL ────────────────────────────────────────────────────
    else:
        url = st.text_input("Collez le lien direct (.csv/.xlsx ou export StatCan)")
        fname = st.text_input("Nom interne (facultatif)")
        if st.button("🌐 Importer depuis l'URL") and url:
            final = slugify(fname) if fname else None
            try:
                path = add_one_file(url, final_name=final)
            except Exception as e:
                st.error(f"❌ Erreur réseau : {e}")
                path = None
            if path:
                st.success(f"✅ Importé : {path}")
                st.session_state.step = 1
                st.experimental_rerun()
            else:
                st.error("❌ Importation échouée – le lien ne renvoie pas un fichier valide.")

# ───────────────────────────── ÉTAPE 2 ──────────────────────────────
elif step == 1:
    st.subheader("🧹 Étape 2 : Nettoyage")
    if st.button("🧼 Lancer le nettoyage"):
        with st.spinner("Nettoyage en cours…"):
            cleaned = clean_main()
        st.success(f"✅ Nettoyé : {cleaned}")
        st.session_state.cleaned_path = str(cleaned)
        st.session_state.step = 2
        st.experimental_rerun()

    if st.button("⬅️ Retour"):
        st.session_state.step = 0
        st.experimental_rerun()

# ───────────────────────────── ÉTAPE 3 ──────────────────────────────
elif step == 2:
    st.subheader("📈 Étape 3 : Visualisation")
    cleaned_path = Path(st.session_state.cleaned_path)
    if cleaned_path.exists():
        df = load_cleaned_file(cleaned_path.stem.replace("_cleaned", ""))
        if df is not None:
            st.info("Sélectionnez les colonnes et le type de graphique dans la console interactive qui s'ouvre.")
            plot_data(df)
    else:
        st.error("❌ Fichier nettoyé introuvable.")

    col1, col2 = st.columns(2)
    if col1.button("⬅️ Retour"):
        st.session_state.step = 1
        st.experimental_rerun()
    if col2.button("🔄 Recommencer"):
        st.session_state.clear()
        st.experimental_rerun()
