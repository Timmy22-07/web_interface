# ───────────────────────── web_interface.py (v2025‑07‑05 renamed) ─────────────────────────
"""
Outil de visualisation de données (.csv & .xlsx) – Import → Nettoyage → Visualisation
+ Accueil enrichi (description du projet)
+ Nouvel onglet : Tutoriel (ancien contenu Accueil)
+ Boutons de téléchargement (fichier importé, nettoyé, graphique PNG)
"""
from __future__ import annotations

import os, re, tempfile
from io import BytesIO
from pathlib import Path

import streamlit as st

from import_data import add_one_file
from clean_data import main as clean_main
from vizualisation import plot_data, load_cleaned_file

# ───────────────────── Helpers ──────────────────────
SLUG_RE = re.compile(r"[^a-z0-9]+")
slugify = lambda txt: SLUG_RE.sub("_", txt.lower()).strip("_")

# ────────────────── Config générale ─────────────────
st.set_page_config(page_title="Outil de visualisation de données – Pipeline", layout="centered")
st.title("📊 Outil de visualisation de données")
st.caption("Importez (.csv / .xlsx), nettoyez et visualisez vos données en quelques clics")

# ──────────────── States / Drapeaux ────────────────
st.session_state.setdefault("step", 0)
step = st.session_state.step
st.session_state.setdefault("imported_name", "")
st.session_state.setdefault("cleaned_name", "")

# ─────────────────── Onglets ────────────────────────
TAB_LABELS = ["🏠 Accueil", "📖 Tutoriel", "📥 Importation", "🧽 Nettoyage", "📊 Visualisation"]
(tab_home, tab_guide, tab_import, tab_clean, tab_viz) = st.tabs(TAB_LABELS)

# ╭────────────────────── Accueil ──────────────────────╮
with tab_home:
    st.markdown("""
### 🔍 À propos de ce projet

Cet **outil de visualisation de données (.csv et .xlsx)** est open‑source et conçu pour **importer**, **nettoyer** et **visualiser** vos jeux de données, avec une priorité donnée aux exports publics de **Statistique Canada**.

Le but est de simplifier l’accès et l’exploration des données brutes, grâce à une interface intuitive :
- Importez un fichier local ou un lien (.csv / .xlsx)
- Nettoyez automatiquement les colonnes inutiles ou incomplètes
- Visualisez vos données sous forme de graphiques interactifs

> 📌 Projet toujours en développement : d’autres sources seront peut‑être prises en charge.
>
> 💡 Vos suggestions : **abadjiflinmi@gmail.com**

Projet porté par **Timothée ABADJI**, étudiant en mathématiques financières et économie à l'université d’Ottawa.

Merci de votre intérêt. Bonne exploration !
""", unsafe_allow_html=True)

# ╭────────────────────── Tutoriel ──────────────────────╮
with tab_guide:
    st.markdown("""
### 📥 Tutoriel StatCan

1. Rendez‑vous sur un tableau, ex. : [36‑10‑0612‑01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=3610061201)
2. Cliquez sur **Options de téléchargement**
""", unsafe_allow_html=True)
    st.image("assets/statcan_choose_csv.png", caption="Options de téléchargement", use_container_width=True)
    st.markdown("""
3. Sélectionnez **CSV – Télécharger les données sélectionnées**
""", unsafe_allow_html=True)
    st.image("assets/statcan_download_button.png", caption="Choix du format CSV", use_container_width=True)
    st.markdown("""
4. Importez ce fichier via l’onglet **Importation** (ou collez l’URL directe).

**Notez que tout ceci à été conçu pour fonctionner principalement avec des fichiers et url provenant du site officiel de Statistiques Canada. Cependant, il est possible que cette interface fonctionne aussi avec des urls et des fichiers ne provenant pas de Statistiques Canada, mais cela n'est pas toujours garanti.

---
### 🚀 Démarrer
Vous pouvez maintenant passer à l’onglet **Importation** pour charger vos données.
""", unsafe_allow_html=True)

# ╭────────────────────── Importation ──────────────────────╮
with tab_import:
    st.subheader("📥 Importation d’un fichier")
    src_type = st.radio("Source des données :", ["Fichier local", "Lien URL"], horizontal=True)

    if src_type == "Fichier local":
        uploaded = st.file_uploader("Fichier à importer :", type=["csv", "xlsx", "xls"], help="200 Mo max")
        fname = st.text_input("Nom personnalisé (facultatif)")
        if uploaded and st.button("🚚 Importer"):
            internal = slugify(fname) or slugify(Path(uploaded.name).stem)
            if not internal:
                st.warning("⚠️ Veuillez saisir un nom valide.")
            else:
                suffix = Path(uploaded.name).suffix or ".csv"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.read())
                    tmp_path = tmp.name
                saved = add_one_file(tmp_path, final_name=internal)
                os.unlink(tmp_path)
                if saved:
                    st.session_state.imported_name = Path(saved).name
                    st.session_state.step = 1
                    st.rerun()
                else:
                    st.error("🚫 Import échoué ou nom déjà utilisé.")

    else:
        url = st.text_input("Lien direct vers le fichier (.csv / .xlsx)")
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

    if st.session_state.imported_name:
        st.success(f"✅ Fichier importé : {st.session_state.imported_name}")
        st.download_button("📥 Télécharger le fichier importé", open(f"data/raw/{st.session_state.imported_name}", "rb"), file_name=st.session_state.imported_name)
        st.info("ℹ️ Passez à l’onglet **Nettoyage**.")

# ╭────────────────────── Nettoyage ──────────────────────╮
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

        if st.session_state.cleaned_name:
            st.success(f"✅ Nettoyage terminé : {st.session_state.cleaned_name}")
            st.download_button("📥 Télécharger le fichier nettoyé", open(f"data/cleaned/{st.session_state.cleaned_name}", "rb"), file_name=st.session_state.cleaned_name)
            st.info("ℹ️ Passez à l’onglet **Visualisation**.")

# ╭────────────────────── Visualisation ──────────────────────╮
with tab_viz:
    st.subheader("📊 Visualisation des données")
    if step < 2:
        st.warning("⛔ Nettoyez d’abord un fichier.")
    else:
        cleaned_path = Path("data/cleaned") / st.session_state.cleaned_name
        if cleaned_path.exists():
            st.session_state["__in_streamlit"] = True
            df = load_cleaned_file(cleaned_path.stem.replace("_cleaned", ""))
            if df is not None:
                st.sidebar.info("📌 Paramètres du graphique")
                fig = plot_data(df)
                if fig is not None:
                    buf = BytesIO()
                    fig.savefig(buf, format="png", dpi=300)
                    st.download_button("📸 Télécharger le graphique", data=buf.getvalue(), file_name="graphique.png", mime="image/png")
            else:
                st.error("🚫 Impossible de charger le fichier nettoyé.")
        else:
            st.error("🚫 Fichier nettoyé introuvable.")

        st.info("ℹ️ Vous pouvez revenir à l’onglet **Importation** pour analyser un autre fichier.")
