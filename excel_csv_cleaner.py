import csv
import difflib
import sys
from pathlib import Path

import pandas as pd
import janitor  # pip install pyjanitor
from chardet import detect

# ------------------------------------------------------------------
# Paramètres chemins (modifier ici si besoin)
# ------------------------------------------------------------------
SOURCE_PATH = Path(
    "C:/Users/Timothée ABADJI/OneDrive/Desktop/Pouls_Financier_Canada/data/raw/data_18.csv"
).resolve()
OUTPUT_DIR = Path(
    "C:/Users/Timothée ABADJI/OneDrive/Desktop/Pouls_Financier_Canada/data/cleaned"
).resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Dictionnaire de noms de colonnes attendus (à étendre si besoin)
# ------------------------------------------------------------------
CANONICAL_COLS = {
    "année": ["annee", "année", "an", "year"],
    "mois": ["mois", "month"],
    "région": ["region", "région", "reg"],
    "revenu": ["revenu", "income", "revenu_menage"],
}

# ------------------------------------------------------------------
# Helpers encodage & séparateur -------------------------------------------------
# ------------------------------------------------------------------

def detect_encoding(csv_path: Path, n_bytes: int = 10000) -> str:
    """Détecte l’encodage probable d’un CSV."""
    with open(csv_path, "rb") as f:
        rawdata = f.read(n_bytes)
    return detect(rawdata)["encoding"] or "utf-8"

def detect_delimiter(csv_path: Path, encoding: str) -> str:
    """Tente de deviner le délimiteur en ignorant les virgules numériques."""
    with open(csv_path, encoding=encoding) as f:
        sample = f.read(2048)
    delimiter = csv.Sniffer().sniff(sample).delimiter
    return delimiter

# ------------------------------------------------------------------
# Nettoyage --------------------------------------------------------------------
# ------------------------------------------------------------------

def fuzzy_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renomme les colonnes mal orthographiées via fuzzy‑matching."""
    rename_map = {}
    for canon, variants in CANONICAL_COLS.items():
        for col in df.columns:
            if col in variants:
                rename_map[col] = canon
            else:
                best = difflib.get_close_matches(col, variants, n=1, cutoff=0.8)
                if best:
                    rename_map[col] = canon
    return df.rename(columns=rename_map)

def clean_dataframe(df: pd.DataFrame, min_year: int | None = None) -> pd.DataFrame:
    """Pipeline de nettoyage façon Power Query."""
    df = (
        df
        .clean_names()   # snake_case, accents retirés
        .remove_empty()  # lignes/colonnes entièrement vides
        .drop_duplicates()
    )
    df = fuzzy_rename_columns(df)

    # Filtre par année si demandé
    if min_year is not None and "annee" in df.columns:
        df = df[df["annee"] >= min_year]
        if df.empty:
            print(f"⚠️  Aucune donnée après {min_year}.")

    # Remplissage des NA
    num_cols = df.select_dtypes("number").columns
    obj_cols = df.select_dtypes("object").columns
    df[num_cols] = df[num_cols].fillna(0)
    df[obj_cols] = df[obj_cols].ffill()  # <-- plus de FutureWarning
    return df

# ------------------------------------------------------------------
# Main -------------------------------------------------------------------------
# ------------------------------------------------------------------

def main():
    path = SOURCE_PATH
    if not path.exists():
        sys.exit(f"❌ Fichier introuvable : {path}")

    # Chargement
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    elif path.suffix.lower() == ".csv":
        enc = detect_encoding(path)
        delim = detect_delimiter(path, enc)
        df = pd.read_csv(path, encoding=enc, delimiter=delim)
    else:
        sys.exit("❌ Type de fichier non pris en charge (.csv, .xlsx, .xls)")

    print(f"✅ Loaded {len(df):,} rows × {df.shape[1]} cols")

    # Nettoyage
    df = clean_dataframe(df)
    print(f"✅ After cleaning : {len(df):,} rows × {df.shape[1]} cols")

    # Sauvegarde
    output_path = OUTPUT_DIR / f"{path.stem}_cleaned.xlsx"
    df.to_excel(output_path, index=False)
    print(f"🎉 Cleaned file saved to → {output_path}")

if __name__ == "__main__":
    main()