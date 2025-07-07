# translations.py
# ------------------------------------------------------------------
# Centralized bilingual dictionary for web_interface.py
# ------------------------------------------------------------------
TRANSLATE = {
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
    "tab_home": ("🏠 Accueil", "🏠 Home"),
    "tab_guide": ("📖 Tutoriel", "📖 Tutorial"),
    "tab_import": ("📥 Importation", "📥 Import"),
    "tab_clean": ("🧽 Nettoyage", "🧽 Cleaning"),
    "tab_viz": ("📊 Visualisation", "📊 Visualization"),
    "home_md": ("""### 🔍 À propos de ce projet

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

Project by **Timothée ABADJI**, Financial Mathematics and Economics student at the University of Ottawa.

Thank you for your interest. Have a good time!
""",
    ),
    "guide_md": ("""### 📅 Tutoriel StatCan

1. Rendez-vous sur un tableau, ex. : [36-10-0612-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=3610061201)  
2. Cliquez sur **Options de téléchargement**
""",
                 """### 📅 StatCan tutorial

1. Go to any table, e.g. [36-10-0612-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3610061201)  
2. Click **Download options**
"""),
    "g_step3_fr": "3. Sélectionnez **CSV – Télécharger les données sélectionnées (pour le chargement de la base de données).**",
    "g_step3_en": "3. Select **CSV – Download selected data (for database loading).**",
    "g_step4_fr": """4. Importez ce fichier via l’onglet **Importation** (ou collez l’URL directe).

**Notez que tout ceci à été conçu pour fonctionner principalement avec des fichiers et URLs provenant du site officiel de Statistiques Canada. Cependant, il est possible que cette interface fonctionne aussi avec des urls et des fichiers ne provenant pas de Statistiques Canada, mais cela n'est pas toujours garanti.**

---
### 🚀 Démarrer
Vous pouvez maintenant passer à l’onglet **Importation** pour charger vos données.
""",
    "g_step4_en": """4. Import this file via the **Import** tab (or paste the direct URL).

**Note that this interface is mainly designed for files and URLs from the official Statistics Canada website. It may work with other sources, but this is not always guaranteed.**

---
### 🚀 Get started
You can now switch to the **Import** tab to load your data.
""",
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
    "clean_header": ("🧽 Nettoyage automatique du fichier", "🧽 Automatic file cleaning"),
    "warn_import_first": ("⛔ Importez d’abord un fichier.", "⛔ Import a file first."),
    "btn_clean": ("🧹 Lancer le nettoyage", "🧹 Start cleaning"),
    "cleaning": ("Nettoyage en cours…", "Cleaning in progress…"),
    "clean_done": ("✅ Nettoyage terminé :", "✅ Cleaning done:"),
    "download_clean": ("📥 Télécharger le fichier nettoyé", "📥 Download cleaned file"),
    "go_viz": ("ℹ️ Passez à l’onglet **Visualisation**.", "ℹ️ Go to the **Visualization** tab."),
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
