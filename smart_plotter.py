#!/usr/bin/env python3
# smart_plotter_v2.py  – version interactive améliorée
# ----------------------------------------------------
# • Montre un aperçu du fichier                                     (HEAD_ROWS)
# • Classe les colonnes par CONTENU (numérique / non numérique)
# • Laisse l’utilisateur choisir librement X, Y, (Z) parmi TOUTES
#   les colonnes détectées
# • Déduit les types de graphiques possibles, les présente clairement
#   et trace celui que l’utilisateur sélectionne
# • Style console lisible (séparateurs, intitulés clairs)
#
#  ── Dépendances ────────────────────────────────────────────────────────────
#     pip install pandas openpyxl matplotlib rich
#
#  ── Usage ─────────────────────────────────────────────────────────────────
#     python smart_plotter_v2.py
#
#  Author: ChatGPT (o3) – 2025-07-02
# ---------------------------------------------------------------------------

import re
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from rich import print
from rich.table import Table
from rich.prompt import Prompt
from rich.console import Console
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (nécessaire pour 3D)

# --------------------------------------------------------------------------- #
# PARAMÈTRES
# --------------------------------------------------------------------------- #
FILE_PATH = r"C:\Users\Timothée ABADJI\OneDrive\Desktop\Pouls_Financier_Canada\data\cleaned\data_20_cleaned.xlsx"
HEAD_ROWS = 5               # Lignes d’aperçu
NUMERIC_THRESHOLD = 0.80    # ≥ 80 % de vrais nombres → numérique
# --------------------------------------------------------------------------- #

console = Console()


# --------------------------------------------------------------------------- #
# UTILITAIRES
# --------------------------------------------------------------------------- #
def is_number(token: str) -> bool:
    """True si `token` est x | x.y | x,y  (pas x.y.z)."""
    token = str(token).strip()
    if len(re.findall(r"[.,]", token)) > 1:  # trop de séparateurs → probable coordonnée
        return False
    try:
        float(token.replace(",", "."))
        return True
    except ValueError:
        return False


def classify_columns(df: pd.DataFrame):
    """Retourne (numeric_cols, categorical_cols) selon le CONTENU."""
    num_cols, cat_cols = [], []
    for col in df.columns:
        serie = df[col].dropna().astype(str)
        if serie.empty:
            cat_cols.append(col)
            continue
        ratio = serie.map(is_number).mean()
        if ratio >= NUMERIC_THRESHOLD:
            df[col] = (
                serie.where(~serie.map(is_number), serie.str.replace(",", "."))
                .astype(float, errors="ignore")
            )
            num_cols.append(col)
        else:
            cat_cols.append(col)
    return num_cols, cat_cols


def choose_column(all_cols: list[str], message: str, allow_blank=False) -> str | None:
    """Affiche un menu Rich et renvoie le nom de la colonne choisie."""
    table = Table(title=message)
    table.add_column("n°", style="bold cyan", justify="right")
    table.add_column("colonne", style="bold")
    for i, col in enumerate(all_cols):
        table.add_row(str(i), col)
    console.print(table)
    while True:
        raw = Prompt.ask("🡆 Entre le n° (ENTER pour aucune)" if allow_blank else "🡆 Entre le n°")
        if allow_blank and raw.strip() == "":
            return None
        if raw.isdigit() and 0 <= int(raw) < len(all_cols):
            return all_cols[int(raw)]
        console.print("[red]Entrée invalide. Essaie encore.[/red]")


# --------------------------------------------------------------------------- #
# LOGIQUE PRINCIPALE
# --------------------------------------------------------------------------- #
def main() -> None:
    path = Path(FILE_PATH)
    if not path.exists():
        console.print(f"[red bold]❌  Fichier non trouvé : {path}[/red bold]")
        sys.exit(1)

    console.rule(f"Chargement du fichier [bold]{path.name}[/bold]")
    df = pd.read_excel(path) if path.suffix.lower().endswith("x") else pd.read_csv(path)

    # APERÇU
    console.rule("[bold]APERÇU DES DONNÉES[/bold]")
    console.print(df.head(HEAD_ROWS))

    # CLASSIFICATION
    num_cols, cat_cols = classify_columns(df)
    console.rule("[bold]COLONNES DÉTECTÉES[/bold]")
    console.print(f"[green]Numériques[/green] : {num_cols or '∅'}")
    console.print(f"[yellow]Non numériques[/yellow] : {cat_cols or '∅'}")

    # CHOIX X / Y / Z
    all_cols = num_cols + cat_cols
    x_col = choose_column(all_cols, "Choisis la colonne [bold]X[/bold] (catégorie ou valeur)")
    y_col = choose_column(num_cols, "Choisis la colonne [bold]Y[/bold] (numérique)", allow_blank=True)
    z_col = None
    if y_col and len(num_cols) >= 2:
        z_col = choose_column(
            [c for c in num_cols if c not in {x_col, y_col}],
            "Axe [bold]Z[/bold] pour 3D (ENTER pour 2D)",
            allow_blank=True,
        )

    # DÉTERMINER LES TYPES DE GRAPHIQUES POSSIBLES
    possibles: dict[str, str] = {}
    if y_col is None:  # un seul axe -> stats de fréquence ou histogramme
        if x_col in num_cols:
            possibles["hist"] = f"Histogramme simple de {x_col}"
        else:
            possibles["bar_count"] = f"Barres : fréquence des valeurs de {x_col}"
            possibles["pie_count"] = f"Secteur : même chose en camembert"
    elif x_col in cat_cols:
        possibles["bar"] = f"Barres : {y_col} moyen par {x_col}"
        possibles["pie"] = f"Secteur : répartition de {y_col} par {x_col}"
    else:  # X et Y numériques
        possibles["scatter"] = f"Nuage de points : {y_col} vs {x_col}"
        possibles["line"] = f"Ligne : {y_col} vs {x_col}"
        if z_col:
            possibles["scatter3d"] = f"Nuage 3D : {z_col} vs {x_col} & {y_col}"

    # MENU DES GRAPHIQUES
    console.rule("[bold]QUEL GRAPHIQUE ?[/bold]")
    gtable = Table(show_header=True, header_style="bold magenta")
    gtable.add_column("n°", justify="right")
    gtable.add_column("Type")
    gtable.add_column("Description")
    for i, (gtype, label) in enumerate(possibles.items()):
        gtable.add_row(str(i), gtype, label)
    console.print(gtable)

    g_choice = Prompt.ask("🡆 Choisis le n° du graphique", choices=[str(i) for i in range(len(possibles))])
    chart_type = list(possibles)[int(g_choice)]
    console.print(f"[bold green]→ Traçage : {possibles[chart_type]}[/bold green]")

    # TRACÉ
    plt.figure()
    if chart_type == "hist":
        df[x_col].plot(kind="hist")
        plt.xlabel(x_col)
        plt.ylabel("Fréquence")
    elif chart_type == "bar_count":
        df[x_col].value_counts().plot(kind="bar")
        plt.ylabel("Fréquence")
    elif chart_type == "pie_count":
        df[x_col].value_counts().plot(kind="pie", autopct="%1.1f%%")
        plt.ylabel("")
    elif chart_type == "bar":
        df.groupby(x_col)[y_col].mean().plot(kind="bar")
        plt.ylabel(y_col)
    elif chart_type == "pie":
        df.groupby(x_col)[y_col].sum().plot(kind="pie", autopct="%1.1f%%")
        plt.ylabel("")
    elif chart_type == "scatter":
        plt.scatter(df[x_col], df[y_col])
        plt.xlabel(x_col)
        plt.ylabel(y_col)
    elif chart_type == "line":
        plt.plot(df[x_col], df[y_col])
        plt.xlabel(x_col)
        plt.ylabel(y_col)
    elif chart_type == "scatter3d":
        ax = plt.axes(projection="3d")
        ax.scatter(df[x_col], df[y_col], df[z_col])
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_zlabel(z_col)

    plt.title(possibles[chart_type])
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
