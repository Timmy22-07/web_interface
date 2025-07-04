# ─────────────────────────── web_interface.py  (v2025-07-04 b) ──────────────────────────
"""
Interface Streamlit en 3 étapes :
1️⃣ Importation (local / URL)  → `data/raw/`
2️⃣ Nettoyage (clean_data.main) → `data/cleaned/`
3️⃣ Visualisation (vizualisation.plot_data)

⚙️ Modifications demandées :
• L’utilisateur choisit **toujours** le nom interne ; plus d’auto‑génération incrémentale.
• Si le champ « Nom interne » est vide → on **utilise le nom de fichier** / la partie finale de l’URL (slugifiée).
• S’il existe déjà dans `dictionary.json`, on lève une erreur explicite et on affiche un message.
• Suppression de tout appel superflu à `st.experimental_rerun()`.
• Aucune boucle d’incrémentation automatique (_foo_2, _foo_3_) : le contrôle reste à l’utilisateur.
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
    """Minimal : garde lettres/ chiffres, remplace le reste par _ et strip."""
    return SLUG_RE.sub("_", txt.lower()).strip("_")


# ─────────────────────────── CONFIG STREAMLIT ─────────────────────────────────
st.set_page_config(page_title="Pipeline de données", layout="centered")
st.title("📊 Traitement de données (.csv / .xlsx)")

st.markdown(
    """
Téléversez un fichier local **ou** collez un lien (Statistique Canada ou autre).<br>
Le pipeline exécute : **Importation → Nettoyage → Visualisation**.
""",
    unsafe_allow_html=True,
)

# ────────────────────────────── STATE ─────────────────────────────────────────
st.session_state.setdefault("step", 0)
st.session_state.setdefault("cleaned_path", "")

step = st.session_state.step

# ──────────────────────────── ÉTAPE 1 : IMPORTATION ───────────────────────────
if step == 0:
    st.subheader("🟢 Étape 1 : Importation")
    src_type = st.radio("Source des données :", ["Fichier local", "Lien URL"], horizontal=True)

    # ——— Import local ————————————————————————————————————————————————
    if src_type == "Fichier local":
        uploaded = st.file_uploader("Importez votre fichier", type=["csv", "xlsx", "xls"], help="200 Mo max.")
        fname = st.text_input("Nom interne (obligatoire si différent du nom du fichier)")

        if uploaded and st.button("🚚 Importer"):
            # Détermination du nom interne
            internal = slugify(fname) if fname else slugify(Path(uploaded.name).stem)
            if not internal:
                st.error("❌ Impossible de déduire un nom interne — renseignez le champ.")
            else:
                # Stockage temporaire pour passer un Path à add_one_file()
                suffix = Path(uploaded.name).suffix or ".csv"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.read())
                    tmp_path = tmp.name
                try:
                    saved = add_one_file(tmp_path, final_name=internal, interactive=False)
                finally:
                    os.unlink(tmp_path)

                if saved:
                    st.success(f"✅ Importé : {saved}")
                    st.session_state.step = 1
                    st.rerun()
                else:
                    st.error(f"❌ Le nom interne ‘{internal}’ est déjà utilisé ou l’import a échoué.")

    # ——— Import par URL ————————————————————————————————————————————————
    else:
        url = st.text_input("Lien direct (.csv/.xlsx ou export StatCan)")
        fname = st.text_input("Nom interne (obligatoire si vous souhaitez un nom précis)")

        if st.button("🌐 Importer depuis l’URL") and url:
            base = Path(url.split("?")[0]).stem  # enlève la querystring éventuelle
            internal = slugify(fname) if fname else slugify(base)
            if not internal:
                st.error("❌ Impossible de déduire un nom interne — renseignez le champ.")
            else:
                saved = add_one_file(url, final_name=internal, interactive=False)
                if saved:
                    st.success(f"✅ Importé : {saved}")
                    st.session_state.step = 1
                    st.rerun()
                else:
                    st.error(f"❌ Le nom interne ‘{internal}’ est déjà utilisé ou l’import a échoué.")

# ──────────────────────────── ÉTAPE 2 : NETTOYAGE ─────────────────────────────
elif step == 1:
    st.subheader("🧹 Étape 2 : Nettoyage des données")
    if st.button("🧼 Lancer le nettoyage"):
        with st.spinner("Nettoyage en cours…"):
            cleaned_path = clean_main()  # dépile le dernier importé
        st.success(f"✅ Nettoyage terminé : {cleaned_path}")
        st.session_state.cleaned_path = str(cleaned_path)
        st.session_state.step = 2
        st.rerun()

    if st.button("⬅️ Retour à l’importation"):
        st.session_state.step = 0
        st.rerun()

# ──────────────────────────── ÉTAPE 3 : VISUALISATION ─────────────────────────
elif step == 2:
    st.subheader("📈 Étape 3 : Visualisation")
    cleaned_path = Path(st.session_state.cleaned_path)

    if cleaned_path.exists():
        st.session_state["__in_streamlit"] = True  # informe vizualisation.py
        df = load_cleaned_file(cleaned_path.stem.replace("_cleaned", ""))
        if df is not None:
            st.sidebar.info("📌 Sélectionnez les paramètres du graphique dans la barre latérale.")
            plot_data(df)
        else:
            st.error("❌ Impossible de charger le fichier nettoyé.")
    else:
        st.error("❌ Fichier nettoyé introuvable.")

    col1, col2 = st.columns(2)
    if col1.button("⬅️ Retour au nettoyage"):
        st.session_state.step = 1
        st.rerun()
    if col2.button("🔄 Recommencer depuis le début"):
        st.session_state.clear()
        st.rerun()
