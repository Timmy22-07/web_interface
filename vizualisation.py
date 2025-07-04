# ───────────────────────── vizualisation.py (v2025‑07‑05) ─────────────────────────
"""
Visualisation interactive – version améliorée 🎨
------------------------------------------------
- Interface Streamlit plus riche (style "Tableau")
- Choix dynamique du **type de graphique** (Ligne, Nuage de points, Histogramme, Barres, 3D)
- **Palette de couleurs** ou thème prédéfini
- Statistiques descriptives complètes : min, max, moyenne, médiane, écart‑type, variance
- Téléchargement du graphique (géré par web_interface)
- Stockage de la dernière figure via `get_last_figure()`

⚠️  Reste compatible avec la logique existante de `web_interface.py`
"""

from pathlib import Path
from typing import Optional

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter

# Style par défaut inspiré de Tableau
plt.style.use("seaborn-v0_8-darkgrid")

try:
    import streamlit as st

    _IN_STREAMLIT = True
except ImportError:
    _IN_STREAMLIT = False

CLEANED_DIR = Path("data/cleaned")
_last_fig = None  # pour export PNG dans web_interface

# ──────────────────────────── API ────────────────────────────

def get_last_figure():
    """Retourne la dernière figure générée (matplotlib)."""
    return _last_fig


def list_cleaned_files():
    return sorted(
        p for p in CLEANED_DIR.glob("*_cleaned.*") if p.suffix in {".csv", ".xlsx"}
    )


def load_cleaned_file(stem: str) -> Optional[pd.DataFrame]:
    for ext in (".xlsx", ".csv"):
        fp = CLEANED_DIR / f"{stem}_cleaned{ext}"
        if fp.exists():
            return pd.read_excel(fp) if ext == ".xlsx" else pd.read_csv(fp)
    if _IN_STREAMLIT:
        st.error(f"Fichier nettoyé introuvable : {stem}")
    return None


def plot_data(df: pd.DataFrame):
    """Affiche un graphique et renvoie la figure (si Streamlit)"""
    numeric_cols = df.select_dtypes("number").columns.tolist()
    if not numeric_cols:
        if _IN_STREAMLIT:
            st.warning("Aucune colonne numérique à tracer.")
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

    st.sidebar.header("🔧 Paramètres du graphe")

    x_col = st.sidebar.selectbox("Colonne X", df.columns, index=0)
    y_col = st.sidebar.selectbox("Colonne Y", numeric_cols, index=0)

    # Z si souhaité
    z_choices = ["(aucun)"] + [c for c in numeric_cols if c not in {x_col, y_col}]
    z_sel = st.sidebar.selectbox("Colonne Z (3D)", z_choices, index=0)
    z_col = None if z_sel == "(aucun)" else z_sel

    kind = st.sidebar.radio(
        "Type de graphique",
        [
            "Ligne",
            "Nuage de points",
            "Histogramme",
            "Barres",
            "3D",
        ]
        if z_col
        else ["Ligne", "Nuage de points", "Histogramme", "Barres"],
    )

    # Palette / couleur principale
    default_color = "#1f77b4"
    color_pick = st.sidebar.color_picker("Couleur principale", default_color)

    # Stats descriptives complètes
    st.sidebar.markdown("### 📊 Statistiques descriptives")
    stats = (
        df[y_col]
        .agg(["count", "mean", "median", "std", "var", "min", "max"])
        .round(3)
        .rename(index={
            "count": "n",
            "mean": "moyenne",
            "median": "médiane",
            "std": "écart‑type",
            "var": "variance",
            "min": "min",
            "max": "max",
        })
    )
    st.sidebar.table(stats.to_frame(name=y_col))

    fig = _make_plot(df, x_col, y_col, z_col if kind == "3D" else None, kind, color_pick)
    _last_fig = fig
    st.pyplot(fig, use_container_width=True)

    if st.checkbox("Afficher un aperçu du tableau"):
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
        table.add_column("Nom de colonne", style="magenta")
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
    mpl.rcParams.update({
        "font.size": 11,
        "axes.grid": True,
        "grid.alpha": 0.4,
        "figure.figsize": (9, 5),
    })

    if kind == "3D" and z_col:
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (nécessaire pour 3D)
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
