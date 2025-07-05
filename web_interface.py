# ───────────────────────── web_interface.py – bilingue FR/EN (v2025-07-05 fix) ─────────────────────────
"""
Data Visualization Tool (.csv & .xlsx) - Import → Clean → Visualize
Version finale entièrement bilingue (FR/EN) avec pipeline complet :
• Accueil, Tutoriel, Importation, Nettoyage, Visualisation
• Sélecteur de langue
• Téléchargement des fichiers (importé / nettoyé / graphique)
"""
from __future__ import annotations

import os, re, tempfile
from io import BytesIO
from pathlib import Path

import streamlit as st

from import_data import add_one_file
from clean_data import main as clean_main
from vizualisation import plot_data, load_cleaned_file

# ───────────────────────── Langues ─────────────────────────
LANGS = {"fr": "Français", "en": "English"}
st.sidebar.selectbox(
    "🌐 Choisissez la langue / Select language",
    list(LANGS.values()),
    index=0,
    key="lang",
)

TRANSLATE = {
    # ── Identité appli ──────────────────────────────────────
    "app_title": (
        "Outil de visualisation de données",
        "Data Visualization Tool",
    ),
    "app_caption": (
        "Importez (.csv / .xlsx), nettoyez et visualisez vos données en quelques clics",
        "Import (.csv / .xlsx), clean and visualize your data in a few clicks",
    ),
    # ── Libellés onglets ───────────────────────────────────
    "home": ("Accueil", "Home"),
    "guide": ("Tutoriel", "Tutorial"),
    "import": ("Importation", "Import"),
    "clean": ("Nettoyage", "Cleaning"),
    "viz": ("Visualisation", "Visualization"),
    # ── Import ─────────────────────────────────────────────
    "src_local": ("Fichier local", "Local file"),
    "src_url": ("Lien URL", "URL link"),
    "upload_file": ("Fichier à importer :", "File to import:"),
    "custom_name": ("Nom personnalisé (facultatif)", "Custom name (optional)"),
    "btn_import": ("🚚 Importer", "🚚 Import"),
    "btn_import_url": ("🌐 Importer depuis le lien", "🌐 Import from URL"),
    "warn_valid_name": ("⚠️ Veuillez saisir un nom valide.", "⚠️ Please enter a valid name."),
    "err_import": ("🚫 Import échoué ou nom déjà utilisé.", "🚫 Import failed or name already used."),
    "file_imported": ("✅ Fichier importé :", "✅ File imported:"),
    "download_raw": ("📥 Télécharger le fichier importé", "📥 Download imported file"),
    "go_clean": ("ℹ️ Passez à l’onglet **Nettoyage**.", "ℹ️ Go to the **Cleaning** tab."),
    # ── Nettoyage ──────────────────────────────────────────
    "btn_clean": ("🧹 Lancer le nettoyage", "🧹 Start cleaning"),
    "cleaning": ("Nettoyage en cours…", "Cleaning in progress…"),
    "clean_done": ("✅ Nettoyage terminé :", "✅ Cleaning done:"),
    "download_clean": ("📥 Télécharger le fichier nettoyé", "📥 Download cleaned file"),
    "go_viz": ("ℹ️ Passez à l’onglet **Visualisation**.", "ℹ️ Go to the **Visualization** tab."),
    # ── Visualisation ──────────────────────────────────────
    "btn_viz_dl": ("📸 Télécharger le graphique", "📸 Download chart"),
    # ── Avertissements / erreurs ───────────────────────────
    "warn_import_first": ("⛔ Importez d’abord un fichier.", "⛔ Import a file first."),
    "warn_clean_first": ("⛔ Nettoyez d’abord un fichier.", "⛔ Clean a file first."),
    "err_load_clean": ("🚫 Impossible de charger le fichier nettoyé.", "🚫 Can't load cleaned file."),
    "err_clean_missing": ("🚫 Fichier nettoyé introuvable.", "🚫 Cleaned file not found."),
    "back_import": (
        "ℹ️ Vous pouvez revenir à l’onglet **Importation** pour analyser un autre fichier.",
        "ℹ️ You can return to the **Import** tab to analyse another file.",
    ),
    # ── Paragraphes longs (nouveaux) ───────────────────────
    "home_md": (
        """### 🔍 À propos de ce projet

Cet outil open-source permet d’**importer**, **nettoyer** et **visualiser** des données (.csv / .xlsx).  
Il vise à simplifier l’accès aux données brutes et leur exploration graphique.

> 💡 Suggestions : abadjiflinmi@gmail.com
""",
        """### 🔍 About this project

This open-source tool lets you **import**, **clean**, and **visualize** data (.csv / .xlsx).  
It makes raw data easier to explore interactively.

> 💡 Feedback : abadjiflinmi@gmail.com
""",
    ),
    "guide_md": (
        """### 📥 Tutoriel StatCan
1. Ouvrez un tableau (ex. 36-10-0612-01)  
2. Cliquez sur **Options de téléchargement**  
3. Choisissez **CSV – Télécharger**  
4. Importez le fichier via l’onglet *Importation*.
""",
        """### 📥 StatCan tutorial
1. Open any table (e.g., 36-10-0612-01)  
2. Click **Download options**  
3. Select **CSV – Download**  
4. Import it via the *Import* tab.
""",
    ),
}

# Helper de traduction
_ = lambda key: TRANSLATE[key][0] if st.session_state.lang == "Français" else TRANSLATE[key][1]

# ────────────────────── Config Streamlit ─────────────────────
st.set_page_config(page_title=_("app_title"), layout="centered")
st.title("📊 " + _("app_title"))
st.caption(_("app_caption"))

# ──────────────────────── États globaux ──────────────────────
st.session_state.setdefault("step", 0)
st.session_state.setdefault("imported_name", "")
st.session_state.setdefault("cleaned_name", "")
step = st.session_state.step

# ─────────────────────────── Tabs ────────────────────────────
TAB_LABELS = [
    "🏠 " + _("home"),
    "📖 " + _("guide"),
    "📥 " + _("import"),
    "🧽 " + _("clean"),
    "📊 " + _("viz"),
]
tab_home, tab_guide, tab_import, tab_clean, tab_viz = st.tabs(TAB_LABELS)

# ──────────────────────────── Accueil ─────────────────────────
with tab_home:
    st.markdown(_("home_md"), unsafe_allow_html=True)

# ─────────────────────────── Tutoriel ─────────────────────────
with tab_guide:
    st.markdown(_("guide_md"))
    st.image(
        "assets/statcan_choose_csv.png",
        caption="Options de téléchargement" if st.session_state.lang == "Français" else "Download options",
        use_container_width=True,
    )
    st.image(
        "assets/statcan_download_button.png",
        caption="Choix du format CSV" if st.session_state.lang == "Français" else "CSV format choice",
        use_container_width=True,
    )

# ───────────────────────── Importation ────────────────────────
with tab_import:
    st.subheader("📥 " + _("import"))
    src_type = st.radio(
        "Source des données / Data source:",
        [_("src_local"), _("src_url")],
        horizontal=True,
    )

    if src_type == _("src_local"):
        uploaded = st.file_uploader(_("upload_file"), type=["csv", "xlsx", "xls"], help="200 Mo max")
        fname = st.text_input(_("custom_name"))
        if uploaded and st.button(_("btn_import")):
            internal = re.sub(r"[^a-z0-9]+", "_", (fname or Path(uploaded.name).stem).lower()).strip("_")
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
        url = st.text_input("URL")
        fname = st.text_input(_("custom_name"))
        if st.button(_("btn_import_url")) and url:
            internal = re.sub(r"[^a-z0-9]+", "_", (fname or Path(url.split("?")[0]).stem).lower()).strip("_")
            saved = add_one_file(url, final_name=internal)
            if saved:
                st.session_state.imported_name = Path(saved).name
                st.session_state.step = 1
                st.rerun()
            else:
                st.error(_("err_import"))

    if st.session_state.imported_name:
        st.success(f"{_('file_imported')} {st.session_state.imported_name}")
        st.download_button(
            _("download_raw"),
            open(f"data/raw/{st.session_state.imported_name}", "rb"),
            file_name=st.session_state.imported_name,
        )
        st.info(_("go_clean"))

# ───────────────────────── Nettoyage ─────────────────────────
with tab_clean:
    st.subheader("🧽 " + _("clean"))
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
            st.download_button(
                _("download_clean"),
                open(f"data/cleaned/{st.session_state.cleaned_name}", "rb"),
                file_name=st.session_state.cleaned_name,
            )
            st.info(_("go_viz"))

# ─────────────────────── Visualisation ───────────────────────
with tab_viz:
    st.subheader("📊 " + _("viz"))
    if step < 2:
        st.warning(_("warn_clean_first"))
    else:
        cleaned_path = Path("data/cleaned") / st.session_state.cleaned_name
        if cleaned_path.exists():
            st.session_state["__in_streamlit"] = True
            df = load_cleaned_file(cleaned_path.stem.replace("_cleaned", ""))
            if df is not None:
                st.sidebar.info("📌 Graph settings / Paramètres du graphique")
                fig = plot_data(df)
                if fig is not None:
                    buf = BytesIO()
                    fig.savefig(buf, format="png", dpi=300)
                    st.download_button(
                        _("btn_viz_dl"),
                        data=buf.getvalue(),
                        file_name="graphique.png",
                        mime="image/png",
                    )
            else:
                st.error(_("err_load_clean"))
        else:
            st.error(_("err_clean_missing"))

        st.info(_("back_import"))
