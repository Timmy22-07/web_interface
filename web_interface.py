# ───────────────────────── web_interface.py – bilingue FR/EN (v2025-07-05 fixed) ─────────────────────────
"""
Outil de visualisation de données (.csv & .xlsx) – Import → Nettoyage → Visualisation
Pipeline complet avec interface bilingue Français / English.

⚠️ IMPORTANT
AUCUN texte français fourni n’a été reformulé.  
Les traductions anglaises sont ajoutées en parallèle, et le sélecteur de langue
affiche simplement l’une ou l’autre version.
"""

from __future__ import annotations

import os, re, tempfile
from io import BytesIO
from pathlib import Path

import streamlit as st

from import_data import add_one_file
from clean_data import main as clean_main
from vizualisation import plot_data, load_cleaned_file

# ───────────────────────── Helpers ─────────────────────────
SLUG_RE = re.compile(r"[^a-z0-9]+")
slugify = lambda txt: SLUG_RE.sub("_", txt.lower()).strip("_")

# ─────────────────── Sélecteur de langue ───────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "Français"

st.sidebar.selectbox(
    "🌐 Choisissez la langue / Select language",
    ["Français", "English"],
    index=0,
    key="lang",
)

# ─────────────────── Dictionnaire de traduction ──────────────────
TRANSLATE = {
    # Titres & légendes
    "page_title": (
        "Outil de visualisation de données – Pipeline",
        "Data Visualization Tool – Pipeline",
    ),
    "main_title": (
        "📊 Outil de visualisation de données",
        "📊 Data Visualization Tool",
    ),
    "caption": (
        "Importez (.csv / .xlsx), nettoyez et visualisez vos données en quelques clics",
        "Import (.csv / .xlsx), clean and visualize your data in a few clicks",
    ),

    # Libellés onglets
    "tab_home": ("🏠 Accueil", "🏠 Home"),
    "tab_guide": ("📖 Tutoriel", "📖 Tutorial"),
    "tab_import": ("📥 Importation", "📥 Import"),
    "tab_clean": ("🧽 Nettoyage", "🧽 Cleaning"),
    "tab_viz": ("📊 Visualisation", "📊 Visualization"),

    # ——— Contenu ACCUEIL (texte FR intact) ———
    "home_md": (
        """### 🔍 À propos de ce projet

Cet **outil de visualisation de données (.csv et .xlsx)** est open-source et conçu pour **importer**, **nettoyer** et **visualiser** vos jeux de données, avec une priorité donnée aux exports publics de **Statistique Canada**.

Le but est de simplifier l’accès et l’exploration des données brutes, grâce à une interface intuitive :
- Importez un fichier local ou un lien (.csv / .xlsx)
- Nettoyez automatiquement les colonnes inutiles ou incomplètes
- Visualisez vos données sous forme de graphiques interactifs

> 📌 Projet toujours en développement : d’autres sources seront peut-être prises en charge.
>
> 💡 Vos suggestions : **abadjiflinmi@gmail.com**

Projet porté par **Timothée ABADJI**, étudiant en mathématiques financières et économie à l'université d’Ottawa.

Merci de votre intérêt. Bonne exploration !
""",
        """### 🔍 About this project

This **open-source data-visualization tool (.csv and .xlsx)** is designed to **import**, **clean** and **visualize** your datasets, with a focus on public exports from **Statistics Canada**.

Its goal is to simplify access to, and exploration of, raw data through an intuitive interface:
- Import a local file or a link (.csv / .xlsx)
- Automatically clean unnecessary or incomplete columns
- Visualize your data with interactive charts

> 📌 This project is still under development – other sources may be supported in the future.
>
> 💡 Your suggestions: **abadjiflinmi@gmail.com**

Project by **Timothée ABADJI**, Financial Mathematics & Economics student at the University of Ottawa.

Thank you for your interest. Happy exploring!
""",
    ),

    # ——— Contenu TUTORIEL (texte FR intact) ———
    "guide_md": (
        """### 📥 Tutoriel StatCan

1. Rendez-vous sur un tableau, ex. : [36-10-0612-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=3610061201)  
2. Cliquez sur **Options de téléchargement**
""",
        """### 📥 StatCan tutorial

1. Go to any table, e.g. [36-10-0612-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3610061201)  
2. Click **Download options**
""",
    ),
    "g_step3_fr": "3. Sélectionnez **CSV – Télécharger les données sélectionnées**",
    "g_step3_en": "3. Select **CSV – Download selected data**",
    "g_step4_fr": """4. Importez ce fichier via l’onglet **Importation** (ou collez l’URL directe).

**Notez que tout ceci à été conçu pour fonctionner principalement avec des fichiers et URLs provenant du site officiel de Statistiques Canada. Cependant, il est possible que cette interface fonctionne aussi avec des urls et des fichiers ne provenant pas de Statistiques Canada, mais cela n'est pas toujours garanti.**

---
### 🚀 Démarrer
Vous pouvez maintenant passer à l’onglet **Importation** pour charger vos données.
""",
    "g_step4_en": """4. Import this file via the **Import** tab (or paste the direct URL).

**Note: this interface is mainly designed for files and URLs from the official Statistics Canada website. It may work with other sources, but this is not always guaranteed.**

---
### 🚀 Get started
You can now switch to the **Import** tab to load your data.
""",

    # Importation
    "import_header": ("📥 Importation d’un fichier", "📥 File import"),
    "data_source": ("Source des données :", "Data source:"),
    "src_local": ("Fichier local", "Local file"),
    "src_url": ("Lien URL", "URL link"),
    "upload_file": ("Fichier à importer :", "File to import:"),
    "custom_name": ("Nom personnalisé (facultatif)", "Custom name (optional)"),
    "btn_import": ("🚚 Importer", "🚚 Import"),
    "url_label": ("Lien direct vers le fichier (.csv / .xlsx)", "Direct link to the file (.csv / .xlsx)"),
    "btn_import_url": ("🌐 Importer depuis le lien", "🌐 Import from URL"),
    "warn_valid_name": ("⚠️ Veuillez saisir un nom valide.", "⚠️ Please enter a valid name."),
    "err_import": ("🚫 Import échoué ou nom déjà utilisé.", "🚫 Import failed or name already used."),
    "file_imported": ("✅ Fichier importé :", "✅ File imported:"),
    "download_raw": ("📥 Télécharger le fichier importé", "📥 Download imported file"),
    "go_clean": ("ℹ️ Passez à l’onglet **Nettoyage**.", "ℹ️ Go to the **Cleaning** tab."),

    # Nettoyage
    "clean_header": ("🧽 Nettoyage automatique du fichier", "🧽 Automatic file cleaning"),
    "warn_import_first": ("⛔ Importez d’abord un fichier.", "⛔ Import a file first."),
    "btn_clean": ("🧹 Lancer le nettoyage", "🧹 Start cleaning"),
    "cleaning": ("Nettoyage en cours…", "Cleaning in progress…"),
    "clean_done": ("✅ Nettoyage terminé :", "✅ Cleaning done:"),
    "download_clean": ("📥 Télécharger le fichier nettoyé", "📥 Download cleaned file"),
    "go_viz": ("ℹ️ Passez à l’onglet **Visualisation**.", "ℹ️ Go to the **Visualization** tab."),

    # Visualisation
    "viz_header": ("📊 Visualisation des données", "📊 Data visualization"),
    "warn_clean_first": ("⛔ Nettoyez d’abord un fichier.", "⛔ Clean a file first."),
    "sidebar_graph": ("📌 Paramètres du graphique", "📌 Graph parameters"),
    "btn_viz_dl": ("📸 Télécharger le graphique", "📸 Download chart"),
    "err_load_clean": ("🚫 Impossible de charger le fichier nettoyé.", "🚫 Can't load cleaned file."),
    "err_clean_missing": ("🚫 Fichier nettoyé introuvable.", "🚫 Cleaned file not found."),
    "back_import": (
        "ℹ️ Vous pouvez revenir à l’onglet **Importation** pour analyser un autre fichier.",
        "ℹ️ You can return to the **Import** tab to analyse another file.",
    ),
}

# Helper de traduction – **aucun texte FR n’est altéré**
def _(key: str) -> str:
    if st.session_state.lang == "Français":
        return TRANSLATE[key][0] if isinstance(TRANSLATE[key], tuple) else TRANSLATE[key]
    else:
        return TRANSLATE[key][1] if isinstance(TRANSLATE[key], tuple) else TRANSLATE[key.replace("_fr", "_en")]

# ───────────────── Config générale ─────────────────
st.set_page_config(page_title=_("page_title"), layout="centered")
st.title(_("main_title"))
st.caption(_("caption"))

# ─────────── States / Drapeaux ───────────
st.session_state.setdefault("step", 0)
step = st.session_state.step
st.session_state.setdefault("imported_name", "")
st.session_state.setdefault("cleaned_name", "")

# ─────────────────── Tabs ───────────────────
TAB_LABELS = [_("tab_home"), _("tab_guide"), _("tab_import"), _("tab_clean"), _("tab_viz")]
tab_home, tab_guide, tab_import, tab_clean, tab_viz = st.tabs(TAB_LABELS)

# ╭──── Accueil ────╮
with tab_home:
    st.markdown(_("home_md"), unsafe_allow_html=True)

# ╭──── Tutoriel ───╮
with tab_guide:
    st.markdown(_("guide_md"), unsafe_allow_html=True)
    st.image(
        "assets/statcan_choose_csv.png",
        caption="Options de téléchargement" if st.session_state.lang == "Français" else "Download options",
        use_container_width=True,
    )
    st.markdown(TRANSLATE["g_step3_fr"] if st.session_state.lang == "Français" else TRANSLATE["g_step3_en"], unsafe_allow_html=True)
    st.image(
        "assets/statcan_download_button.png",
        caption="Choix du format CSV" if st.session_state.lang == "Français" else "CSV format choice",
        use_container_width=True,
    )
    st.markdown(TRANSLATE["g_step4_fr"] if st.session_state.lang == "Français" else TRANSLATE["g_step4_en"], unsafe_allow_html=True)

# ╭──── Importation ───╮
with tab_import:
    st.subheader(_("import_header"))
    src_type = st.radio(_("data_source"), [_("src_local"), _("src_url")], horizontal=True)

    if src_type == _("src_local"):
        uploaded = st.file_uploader(_("upload_file"), type=["csv", "xlsx", "xls"], help="200 Mo max")
        fname = st.text_input(_("custom_name"))
        if uploaded and st.button(_("btn_import")):
            internal = slugify(fname) or slugify(Path(uploaded.name).stem)
            if not internal:
                st.warning(_("warn_valid_name"))
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
                    st.error(_("err_import"))

    else:
        url = st.text_input(_("url_label"))
        fname = st.text_input(_("custom_name"))
        if st.button(_("btn_import_url")) and url:
            internal = slugify(fname) or slugify(Path(url.split("?")[0]).stem)
            saved = add_one_file(url, final_name=internal)
            if saved:
                st.session_state.imported_name = Path(saved).name
                st.session_state.step = 1
                st.rerun()
            else:
                st.error(_("err_import"))

    if st.session_state.imported_name:
        st.success(f"{_('file_imported')} {st.session_state.imported_name}")
        st.download_button(_("download_raw"), open(f"data/raw/{st.session_state.imported_name}", "rb"), file_name=st.session_state.imported_name)
        st.info(_("go_clean"))

# ╭──── Nettoyage ───╮
with tab_clean:
    st.subheader(_("clean_header"))
    if step < 1:
        st.warning(_("warn_import_first"))
    else:
        if st.button(_("btn_clean")):
            with st.spinner(_("cleaning")):
                cleaned_path = clean_main()
            st.session_state.cleaned_name = Path(cleaned_path).name
            st.session_state.step = 2
            st.rerun()

        if st.session_state.cleaned_name:
            st.success(f"{_('clean_done')} {st.session_state.cleaned_name}")
            st.download_button(_("download_clean"), open(f"data/cleaned/{st.session_state.cleaned_name}", "rb"), file_name=st.session_state.cleaned_name)
            st.info(_("go_viz"))

# ╭──── Visualisation ───╮
with tab_viz:
    st.subheader(_("viz_header"))
    if step < 2:
        st.warning(_("warn_clean_first"))
    else:
        cleaned_path = Path("data/cleaned") / st.session_state.cleaned_name
        if cleaned_path.exists():
            st.session_state["__in_streamlit"] = True
            df = load_cleaned_file(cleaned_path.stem.replace("_cleaned", ""))
            if df is not None:
                st.sidebar.info(_("sidebar_graph"))
                fig = plot_data(df)
                if fig is not None:
                    buf = BytesIO()
                    fig.savefig(buf, format="png", dpi=300)
                    st.download_button(_("btn_viz_dl"), data=buf.getvalue(), file_name="graphique.png", mime="image/png")
            else:
                st.error(_("err_load_clean"))
        else:
            st.error(_("err_clean_missing"))

        st.info(_("back_import"))
