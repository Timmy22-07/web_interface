from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl  # <-- ajouté pour rcParams
from matplotlib.ticker import FuncFormatter
from rich import print
from rich.table import Table
from rich.console import Console

# === CONFIGURATION ===
CLEANED_DIR = Path("data/cleaned")
console = Console()


def list_cleaned_files():
    files = list(CLEANED_DIR.glob("*_cleaned.*"))
    return [f for f in files if f.suffix in [".csv", ".xlsx"]]


def load_cleaned_file(filename: str) -> pd.DataFrame:
    filepath = CLEANED_DIR / f"{filename}_cleaned.xlsx"
    if not filepath.exists():
        filepath = CLEANED_DIR / f"{filename}_cleaned.csv"
    if not filepath.exists():
        console.print(f"[bold red]❌ Fichier introuvable : {filepath.name}[/]")
        return None

    df = pd.read_excel(filepath) if filepath.suffix == ".xlsx" else pd.read_csv(filepath)
    console.rule(f"[bold cyan]Chargement du fichier {filepath.name}[/]")
    return df


def preview_data(df: pd.DataFrame):
    console.rule("[bold green]APERÇU DES DONNÉES[/]")
    console.print(df.head(), highlight=True)
    console.print(f"\n[bold blue][{len(df)} rows x {len(df.columns)} columns][/]\n")


def detect_column_types(df: pd.DataFrame):
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    non_numeric_cols = [col for col in df.columns if col not in numeric_cols]
    console.rule("[bold green]COLONNES DÉTECTÉES[/]")
    print(f"[green]Numériques :[/] {numeric_cols}")
    print(f"[yellow]Non numériques :[/] {non_numeric_cols}")
    return numeric_cols, non_numeric_cols


def choose_column(columns, prompt, allow_none=False):
    table = Table(title=prompt)
    table.add_column("n°", style="cyan", justify="right")
    table.add_column("colonne", style="magenta")
    for i, col in enumerate(columns):
        table.add_row(str(i), col)
    console.print(table)
    while True:
        choice = console.input("[bold]➤ Entre le n°[/] (ENTER pour aucune): ")
        if allow_none and choice == "":
            return None
        if choice.isdigit() and int(choice) in range(len(columns)):
            return columns[int(choice)]
        console.print("[red]Entrée invalide.[/]")


def format_thousands(x, pos):
    return f"{int(x):,}".replace(",", " ")


def format_title(x_col, y_col):
    return f"Évolution de {y_col.replace('_', ' ').capitalize()} selon {x_col.replace('_', ' ').capitalize()}"


def plot_data(df: pd.DataFrame):
    preview_data(df)
    numeric_cols, _ = detect_column_types(df)

    x_col = choose_column(df.columns.tolist(), "Choisis la colonne X (catégorie ou valeur)")
    y_col = choose_column(numeric_cols, "Choisis la colonne Y (numérique)")
    z_col = None

    graph_type = console.input("\nSouhaitez-vous un graphique 2D ou 3D ? (2/3) : ")
    while graph_type not in {"2", "3"}:
        console.print("[red]Veuillez entrer 2 ou 3.[/]")
        graph_type = console.input("Souhaitez-vous un graphique 2D ou 3D ? (2/3) : ")

    if graph_type == "3":
        z_col = choose_column(numeric_cols, "Axe Z pour 3D (ENTER pour 2D)", allow_none=True)
        if z_col is None:
            console.print("[yellow]Axe Z non fourni → passage en 2D[/]")
            graph_type = "2"

    # ───── Style global ─────
    mpl.rcParams.update({
        "font.size": 12,
        "axes.labelsize": 13,
        "axes.titlesize": 15,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "axes.grid": True,
        "grid.linestyle": "--",
        "grid.alpha": 0.4,
    })

    # ───── Tracé 2D ─────
    if graph_type == "2":
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(df[x_col], df[y_col], marker="o", linestyle="-", color="navy")
        ax.set_title(format_title(x_col, y_col), pad=15)
        ax.set_xlabel(x_col.replace("_", " ").capitalize())
        ax.set_ylabel(y_col.replace("_", " ").capitalize())
        ax.yaxis.set_major_formatter(FuncFormatter(format_thousands))
        plt.xticks(rotation=45, ha="right")

    # ───── Tracé 3D ─────
    else:
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111, projection="3d")
        # Conversion en numérique avec gestion des NaN
        x = pd.to_numeric(df[x_col], errors="coerce")
        y = pd.to_numeric(df[y_col], errors="coerce")
        z = pd.to_numeric(df[z_col], errors="coerce")
        valid = ~(x.isna() | y.isna() | z.isna())
        ax.scatter(x[valid], y[valid], z[valid], c="#1f77b4", marker="o")
        ax.set_xlabel(x_col.replace("_", " ").capitalize())
        ax.set_ylabel(y_col.replace("_", " ").capitalize())
        ax.set_zlabel(z_col.replace("_", " ").capitalize())
        ax.set_title(f"{z_col.replace('_', ' ').capitalize()} vs {x_col.replace('_', ' ').capitalize()} & {y_col.replace('_', ' ').capitalize()}")

    plt.tight_layout()
    plt.show()


def main():
    files = list_cleaned_files()
    if not files:
        console.print("[red]Aucun fichier nettoyé trouvé dans le dossier 'data/cleaned'.[/]")
        return

    user_input = console.input("Entrez un ou plusieurs noms de fichiers (sans '_cleaned'), séparés par des virgules :\n> ")
    filenames = [f.strip() for f in user_input.split(",") if f.strip()]

    for name in filenames:
        df = load_cleaned_file(name)
        if df is not None:
            plot_data(df)


if __name__ == "__main__":
    main()
