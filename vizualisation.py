# vizualisation.py

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter

# Détection facultative de Streamlit
try:
    import streamlit as st
    _IN_STREAMLIT = True
except ImportError:
    _IN_STREAMLIT = False

CLEANED_DIR = Path("data/cleaned")


def list_cleaned_files():
    return sorted(p for p in CLEANED_DIR.glob("*_cleaned.*") if p.suffix in {".csv", ".xlsx"})


def load_cleaned_file(stem: str) -> pd.DataFrame | None:
    for ext in (".xlsx", ".csv"):
        fp = CLEANED_DIR / f"{stem}_cleaned{ext}"
        if fp.exists():
            return pd.read_excel(fp) if ext == ".xlsx" else pd.read_csv(fp)
    if _IN_STREAMLIT:
        st.error(f"Fichier nettoyé introuvable : {stem}")
    else:
        print(f"[red]❌ Fichier introuvable : {stem}[/]")
    return None


def plot_data(df: pd.DataFrame):
    numeric_cols = df.select_dtypes("number").columns.tolist()

    if not numeric_cols:
        if _IN_STREAMLIT:
            st.warning("Aucune colonne numérique à tracer.")
        else:
            print("[red]Aucune colonne numérique trouvée.[/]")
        return

    if _IN_STREAMLIT and st.session_state.get("__in_streamlit", False):
        _plot_streamlit(df, numeric_cols)
    else:
        _plot_console(df, numeric_cols)


# === Helpers ===

def _fmt_thousands(x, _):
    return f"{int(x):,}".replace(",", " ")


def _plot_streamlit(df: pd.DataFrame, numeric_cols):
    st.sidebar.header("🔧 Paramètres du graphe")
    x_col = st.sidebar.selectbox("Colonne X", df.columns, index=0)
    y_col = st.sidebar.selectbox("Colonne Y", numeric_cols, index=0)
    z_choices = ["(aucun)"] + numeric_cols
    z_sel = st.sidebar.selectbox("Colonne Z (3D)", z_choices, index=0)
    z_col = None if z_sel == "(aucun)" else z_sel
    kind = st.sidebar.radio("Type de graphique", ["Ligne", "Nuage de points", "Histogramme", "Barres", "3D"] if z_col else ["Ligne", "Nuage de points", "Histogramme", "Barres"])

    st.sidebar.markdown("### 📊 Aperçu des données")
    st.sidebar.write(df[y_col].describe()[["min", "max", "mean"]])

    fig = _make_plot(df, x_col, y_col, z_col if kind == "3D" else None, kind)
    st.pyplot(fig)

    if st.checkbox("Afficher l'aperçu du tableau"):
        st.dataframe(df.head())


def _plot_console(df: pd.DataFrame, numeric_cols):
    from rich.console import Console
    from rich.table import Table
    console = Console()

    def choose(col_list, prompt):
        table = Table(title=prompt)
        table.add_column("n°", style="cyan", justify="right")
        table.add_column("Nom de colonne", style="magenta")
        for i, col in enumerate(col_list):
            table.add_row(str(i), col)
        console.print(table)
        idx = int(console.input("Choix : "))
        return col_list[idx]

    x_col = choose(df.columns.tolist(), "Colonne X")
    y_col = choose(numeric_cols, "Colonne Y")
    z_col = None
    kind = "Ligne"

    if console.input("Souhaitez-vous un graphique 3D ? (o/n) ").lower().startswith("o"):
        other_nums = [c for c in numeric_cols if c != y_col]
        if other_nums:
            z_col = choose(other_nums, "Colonne Z")
            kind = "3D"

    fig = _make_plot(df, x_col, y_col, z_col, kind)
    plt.show()


def _make_plot(df, x_col, y_col, z_col, kind):
    mpl.rcParams.update({
        "font.size": 11,
        "axes.grid": True,
        "grid.alpha": 0.4,
        "figure.figsize": (9, 5),
    })

    if kind == "3D":
        from mpl_toolkits.mplot3d import Axes3D  # noqa
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.scatter(df[x_col], df[y_col], df[z_col])
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_zlabel(z_col)
        ax.set_title(f"{z_col} vs {x_col} & {y_col}")
        return fig

    fig, ax = plt.subplots()

    if kind == "Ligne":
        ax.plot(df[x_col], df[y_col], marker="o")
    elif kind == "Nuage de points":
        ax.scatter(df[x_col], df[y_col])
    elif kind == "Histogramme":
        ax.hist(df[y_col], bins=20)
    elif kind == "Barres":
        ax.bar(df[x_col].astype(str), df[y_col])
        plt.xticks(rotation=45, ha="right")

    ax.set_title(f"{y_col} vs {x_col}")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.yaxis.set_major_formatter(FuncFormatter(_fmt_thousands))
    plt.tight_layout()
    return fig


# === Lancement manuel ===

if __name__ == "__main__":
    files = list_cleaned_files()
    print("Fichiers disponibles :")
    for i, fp in enumerate(files):
        print(f"{i} : {fp.name}")
    idx = int(input("Choix : "))
    stem = files[idx].stem.replace("_cleaned", "")
    df = load_cleaned_file(stem)
    if df is not None:
        plot_data(df)
