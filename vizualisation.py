# ───────────────────────── vizualisation.py (v2025-07-05 bilingue) ─────────────────────────
"""
Visualisation interactive – version améliorée 🎨
------------------------------------------------
• Interface Streamlit plus riche (style "Tableau")
• Choix dynamique du type de graphique
• Palette de couleurs ou thème prédéfini
• Statistiques descriptives complètes
• Téléchargement du graphique (géré par web_interface)
• Stockage de la dernière figure via get_last_figure()

⚠️  Tous les textes français d’origine sont conservés à l’identique.
"""

from pathlib import Path
from typing import Optional

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter

# Style par défaut inspiré de Tableau
plt.style.use("seaborn-v0_8-darkgrid")

# ───────────────────── Détection Streamlit ─────────────────────
try:
    import streamlit as st

    _IN_STREAMLIT = True
except ImportError:
    _IN_STREAMLIT = False

# ─────────────── Dictionnaire de traduction ────────────────
# ! Les chaînes FR d’origine sont reprises mot pour mot
T = {
    "sidebar_header": ("🔧 Paramètres du graphe", "🔧 Graph parameters"),
    "x_col": ("Colonne X", "X column"),
    "y_col": ("Colonne Y", "Y column"),
    "z_col": ("Colonne Z (3D)", "Z column (3D)"),
    "none": ("(aucun)", "(none)"),
    "kind_line": "Ligne",
    "kind_scatter": "Nuage de points",
    "kind_hist": "Histogramme",
    "kind_bar": "Barres",
    "kind_3d": "3D",
    "main_colour": ("Couleur principale", "Main colour"),
    "stats_header": ("### 📊 Statistiques descriptives", "### 📊 Descriptive statistics"),
    "warn_no_numeric": ("Aucune colonne numérique à tracer.", "No numeric column to plot."),
    "show_df": ("Afficher un aperçu du tableau", "Show a preview of the dataframe"),
}

def _t(key):
    """Renvoie la version FR ou EN selon st.session_state.lang (par défaut FR)."""
    if not _IN_STREAMLIT or st.session_state.get("lang", "Français") == "Français":
        return T[key][0] if isinstance(T[key], tuple) else T[key]
    return T[key][1] if isinstance(T[key], tuple) else T[key]

# ─────────────────────── Constantes ────────────────────────
CLEANED_DIR = Path("data/cleaned")
_last_fig = None  # pour export PNG via web_interface

# ──────────────────────────── API ────────────────────────────
def get_last_figure():
    """Retourne la dernière figure matplotlib générée."""
    return _last_fig


def list_cleaned_files():
    return sorted(p for p in CLEANED_DIR.glob("*_cleaned.*") if p.suffix in {".csv", ".xlsx"})


def load_cleaned_file(stem: str) -> Optional[pd.DataFrame]:
    for ext in (".xlsx", ".csv"):
        fp = CLEANED_DIR / f"{stem}_cleaned{ext}"
        if fp.exists():
            return pd.read_excel(fp) if ext == ".xlsx" else pd.read_csv(fp)
    if _IN_STREAMLIT:
        st.error(f"Fichier nettoyé introuvable : {stem}")
    return None


def plot_data(df: pd.DataFrame):
    """Affiche un graphique (Streamlit ou console)."""
    numeric_cols = df.select_dtypes("number").columns.tolist()
    if not numeric_cols:
        if _IN_STREAMLIT:
            st.warning(_t("warn_no_numeric"))
        return None

    if _IN_STREAMLIT and st.session_state.get("__in_streamlit", False):
        return _plot_streamlit(df, numeric_cols)

    _plot_console(df, numeric_cols)
    return None

# ────────────────────────── Helpers ──────────────────────────
def _fmt_thousands(x, _):
    return f"{int(x):,}".replace(",", " ")

# ------------------------- Streamlit -------------------------
def _plot_streamlit(df: pd.DataFrame, numeric_cols):
    global _last_fig

    st.sidebar.header(_t("sidebar_header"))

    x_col = st.sidebar.selectbox(_t("x_col"), df.columns, index=0)
    y_col = st.sidebar.selectbox(_t("y_col"), numeric_cols, index=0)

    z_choices = [_t("none")] + [c for c in numeric_cols if c not in {x_col, y_col}]
    z_sel = st.sidebar.selectbox(_t("z_col"), z_choices, index=0)
    z_col = None if z_sel == _t("none") else z_sel

    kinds_fr = ["Ligne", "Nuage de points", "Histogramme", "Barres", "3D"]
    kinds_en = ["Line", "Scatter", "Histogram", "Bar", "3D"]
    kinds = kinds_fr if st.session_state.lang == "Français" else kinds_en

    kind = st.sidebar.radio(
        "Type de graphique",
        kinds if z_col else kinds[:-1],  # sans 3D si pas de Z
    )

    # Palette
    default_color = "#1f77b4"
    color_pick = st.sidebar.color_picker(_t("main_colour"), default_color)

    # Statistiques descriptives
    st.sidebar.markdown(_t("stats_header"))
    stats_fr = {
        "count": "n",
        "mean": "moyenne",
        "median": "médiane",
        "std": "écart-type",
        "var": "variance",
        "min": "min",
        "max": "max",
    }
    stats_en = {
        "count": "count",
        "mean": "mean",
        "median": "median",
        "std": "std-dev",
        "var": "variance",
        "min": "min",
        "max": "max",
    }
    mapper = stats_fr if st.session_state.lang == "Français" else stats_en

    stats = (
        df[y_col]
        .agg(list(mapper.keys()))
        .round(3)
        .rename(index=mapper)
    )
    st.sidebar.table(stats.to_frame(name=y_col))

    # Construction du graphe
    kind_key = kinds_fr[kinds.index(kind)] if st.session_state.lang != "Français" else kind
    fig = _make_plot(df, x_col, y_col, z_col if kind_key == "3D" else None, kind_key, color_pick)
    _last_fig = fig
    st.pyplot(fig, use_container_width=True)

    if st.checkbox(_t("show_df")):
        st.dataframe(df.head())

    return fig

# --------------------------- Console ---------------------------
def _plot_console(df: pd.DataFrame, numeric_cols):
    import rich
    from rich.table import Table
    from rich.console import Console

    console = Console()

    def choose(col_list, prompt):
        table = Table(title=prompt)
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Nom de colonne" if prompt.endswith("X") else "Colonne", style="magenta")
        for i, col in enumerate(col_list):
            table.add_row(str(i), col)
        console.print(table)
        idx = int(console.input("Choix : "))
        return col_list[idx]

    x_col = choose(df.columns.tolist(), "Colonne X")
    y_col = choose(numeric_cols, "Colonne Y")
    fig = _make_plot(df, x_col, y_col, None, "Ligne", "#1f77b4")
    plt.show()

# ------------------------- Plot builder ------------------------
def _make_plot(df, x_col, y_col, z_col, kind, color):
    mpl.rcParams.update({"font.size": 11, "axes.grid": True, "grid.alpha": 0.4, "figure.figsize": (9, 5)})

    if kind == "3D" and z_col:
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.scatter(df[x_col], df[y_col], df[z_col], color=color)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_zlabel(z_col)
        ax.set_title(f"{z_col} vs {x_col} & {y_col}")
        return fig

    fig, ax = plt.subplots()

    if kind == "Ligne":
        ax.plot(df[x_col], df[y_col], marker="o", color=color)
    elif kind == "Nuage de points":
        ax.scatter(df[x_col], df[y_col], color=color)
    elif kind == "Histogramme":
        ax.hist(df[y_col], bins=20, color=color)
    elif kind == "Barres":
        ax.bar(df[x_col].astype(str), df[y_col], color=color)
        plt.xticks(rotation=45, ha="right")

    ax.set_title(f"{y_col} vs {x_col}")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.yaxis.set_major_formatter(FuncFormatter(_fmt_thousands))
    plt.tight_layout()
    return fig

# ─────────────────────────── CLI ────────────────────────────
if __name__ == "__main__":
    files = list_cleaned_files()
    if not files:
        print("Aucun fichier nettoyé trouvé dans data/cleaned")
    else:
        df = load_cleaned_file(files[0].stem.replace("_cleaned", ""))
        plot_data(df)
