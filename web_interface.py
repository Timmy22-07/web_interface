# ─────────────────────────── web_interface.py  (v2025‑07‑04 g) ──────────────────────────
"""
Analytix : Importez → Nettoyez → Visualisez
--------------------------------------------------
Interface Streamlit minimaliste pour explorer rapidement des fichiers CSV ou Excel.

Nouveautés de la version **g**
• Branding complet "Analytix" (titre + accroche)                         
• Libellés simplifiés et cohérents (nom de fichier, lien direct)          
• Bloc d’explications clair + expander "Aide"                            
• Messages harmonisés (icônes ✅ 🚫 ⚠️)                                    
• Code encore basé sur le système `step` (plus rapide à intégrer).        

NB : l’amélioration des statistiques (écart‑type, variance) sera faite dans
`vizualisation.py` lors du prochain commit, pour ne pas mélanger les rôles.
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
    """Nettoie un texte pour servir de slug/nom de fichier."""
    return SLUG_RE.sub("_", txt.lower()).strip("_")

# ─────────────────────────── CONFIG STREAMLIT ─────────────────────────────────
st.set_page_config(page_title="Analytix – Analyse de données", layout="centered")
st.title("📊 Analytix – Analysez vos données intelligemment")

st.markdown(
    """
**Analytix** est un outil web qui transforme vos fichiers `.csv` ou `.xlsx` en graphiques interactifs en trois étapes :

1. **Importer** un fichier local ou coller un **lien direct** vers un fichier.
2. **Nettoyer** les données automatiquement (types, valeurs manquantes…).
3. **Visualiser** vos variables grâce à un graphique dynamique.

*Astuce :* si vous importez depuis un lien, vous pouvez donner un **nom personnalisé** à votre fichier (facultatif).
""",
    unsafe_allow_html=True,
)

with st.expander("ℹ️ Formats acceptés / limites"):
    st.markdown(
        """
        - Fichiers **`.csv`**, **`.xlsx`** ou **`.xls`**  
        - Taille maximale recommandée : **200 Mo**  
        - Fonctionne avec les exports **Statistique Canada**, Banque mondiale, etc.
        """
    )

# ────────────────────────────── STATE ─────────────────────────────────────────
st.session_state.setdefault("step", 0)
st.session_state.setdefault("cleaned_path", "")

step = st.session_state.step

# ──────────────────────────── ÉTAPE 1 : IMPORTATION ───────────────────────────
if step == 0:
    st.subheader("🟢 Étape 1 : Importation")
    src_type = st.radio("Source de vos données :", ["Fichier local", "Lien URL"], horizontal=True)

    # ——— Import local ————————————————————————————————————————————————
    if src_type == "Fichier local":
        uploaded = st.file_uploader("Glissez‑déposez ou sélectionnez un fichier :", type=["csv", "xlsx", "xls"], help="Limite 200 Mo")
        fname = st.text_input("Nom de votre fichier analysé (facultatif)")

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
                    st.session_state.step = 1
                    st.rerun()
                else:
                    st.error(f"🚫 Le nom ‘{internal}’ est déjà utilisé ou l’import a échoué.")

    # ——— Import par URL ————————————————————————————————————————————————
    else:
        url = st.text_input("Lien vers un fichier .csv ou .xlsx")
        fname = st.text_input("Nom de votre fichier analysé (facultatif)")

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
                st.session_state.step = 1
                st.rerun()
            else:
                st.error(f"🚫 Le nom ‘{internal}’ est déjà utilisé ou l’import a échoué.")

# ──────────────────────────── ÉTAPE 2 : NETTOYAGE ─────────────────────────────
elif step == 1:
    st.subheader("🧹 Étape 2 : Nettoyage automatique")
    if st.button("🧼 Lancer le nettoyage"):
        with st.spinner("Nettoyage en cours…"):
            cleaned_path = clean_main()
        st.success(f"✅ Nettoyage terminé : {cleaned_path}")
        st.session_state.cleaned_path = str(cleaned_path)
        st.session_state.step = 2
        st.rerun()

    if st.button("⬅️ Retour à l’importation"):
        st.session_state.step = 0
        st.rerun()

# ──────────────────────────── ÉTAPE 3 : VISUALISATION ─────────────────────────
elif step == 2:
    st.subheader("📈 Étape 3 : Visualisation interactive")
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

    col1, col2 = st.columns(2)
    if col1.button("⬅️ Retour au nettoyage"):
        st.session_state.step = 1
        st.rerun()
    if col2.button("🔄 Recommencer depuis le début"):
        st.session_state.clear()
        st.rerun()
