"""clean_data.py

Nettoie un fichier CSV ou Excel déjà importé puis place la version nettoyée
 dans `data/cleaned/`. Le script **ne fait plus d'importation** et ne demande
 plus d'année minimale (option supprimée pour éviter toute ambiguïté sur les
 jeux de données non basés sur l'année).

Fonction principale :
    main(file_path: str | Path | None = None) -> Path
        • `file_path` :
            - Chaîne vide ou None  → on prend le **dernier fichier brut importé**
              (référencé dans `data/last_imported.txt`).
            - Nom *simple* sans extension (ex. "data_34")  → on cherche
              automatiquement un `.csv` ou `.xlsx` dans `data/raw/`.
            - Chemin complet (ex. "data/raw/data_34.csv")  → utilisé tel quel.

Retourne le chemin du fichier nettoyé (Path) qui sera ensuite passé à la
visualisation.

Dépendances :
    pip install pandas openpyxl pyjanitor chardet
"""

from __future__ import annotations

import csv
import json
import difflib
import re
from pathlib import Path
from typing import Optional

import chardet
import pandas as pd
import janitor  # <- pyjanitor

# ───────────────────────────── Chemins ──────────────────────────────
RAW_DIR = Path("data/raw")
CLEANED_DIR = Path("data/cleaned")
LAST_FILE_PATH = Path("data/last_imported.txt")  # toujours écrit par import_data

CANONICAL_COLS: dict[str, list[str]] = {
    "annee": ["annee", "année", "an", "year"],
    "mois": ["mois", "month"],
    "region": ["region", "région", "reg"],
    "revenu": ["revenu", "income", "revenu_menage"],
}

# ─────────────────────────── UTILITAIRES ────────────────────────────

def ensure_dirs() -> None:
    for d in (RAW_DIR, CLEANED_DIR):
        d.mkdir(parents=True, exist_ok=True)


def detect_encoding(path: Path) -> str:
    with path.open("rb") as f:
        return chardet.detect(f.read(10000)).get("encoding", "utf-8")


def detect_delimiter(csv_path: Path, encoding: str = "utf-8") -> str:
    with csv_path.open(encoding=encoding) as f:
        sample = f.read(2048)
    return csv.Sniffer().sniff(sample).delimiter


def fuzzy_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map: dict[str, str] = {}
    for canon, variants in CANONICAL_COLS.items():
        for col in df.columns:
            if col in variants:
                rename_map[col] = canon
            else:
                best = difflib.get_close_matches(col, variants, n=1, cutoff=0.8)
                if best:
                    rename_map[col] = canon
    return df.rename(columns=rename_map)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoyage standard : clean_names, remove_empty, etc."""
    df = (
        df.clean_names()
        .remove_empty()
        .drop_duplicates()
    )

    # Renommage flou → colonnes canoniques
    df = fuzzy_rename_columns(df)

    # Valeurs manquantes
    num_cols = df.select_dtypes("number").columns
    obj_cols = df.select_dtypes("object").columns
    df[num_cols] = df[num_cols].fillna(0)
    df[obj_cols] = df[obj_cols].ffill()

    return df.sort_values(by=df.columns.to_list())

# ──────────────────────────── COEUR ────────────────────────────────

def _resolve_input(path_like: str | Path | None) -> Path:
    """Résout l'argument utilisateur vers un Path brut situé dans data/raw."""
    if path_like in (None, ""):
        # On prend le dernier importé
        if not LAST_FILE_PATH.exists():
            raise FileNotFoundError("Aucun fichier importé : exécute import_data.py d’abord.")
        base = LAST_FILE_PATH.read_text(encoding="utf-8").strip()
        # cherche .csv puis .xlsx
        for ext in (".csv", ".xlsx", ".xls"):
            candidate = RAW_DIR / f"{base}{ext}"
            if candidate.exists():
                return candidate
        raise FileNotFoundError(f"Dernier importé introuvable dans {RAW_DIR} : {base}.*")

    p = Path(path_like)
    if p.exists():  # chemin complet fourni
        return p
    # Sinon, l'utilisateur a probablement donné juste "data_34"
    for ext in (".csv", ".xlsx", ".xls"):
        candidate = RAW_DIR / f"{p.stem}{ext}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Fichier non trouvé : {path_like}")


def clean_file(file_path: Path) -> Path:
    if file_path.suffix.lower() == ".csv":
        enc = detect_encoding(file_path)
        delim = detect_delimiter(file_path, enc)
        df = pd.read_csv(file_path, encoding=enc, delimiter=delim)
    elif file_path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Format non pris en charge : {file_path.suffix}")

    print(f"✅ Chargé → {len(df)} lignes, {len(df.columns)} colonnes")
    df = clean_dataframe(df)
    print(f"✅ Nettoyé  → {len(df)} lignes, {len(df.columns)} colonnes")

    cleaned_path = CLEANED_DIR / f"{file_path.stem}_cleaned.xlsx"
    df.to_excel(cleaned_path, index=False)
    print(f"🎉 Exporté  → {cleaned_path}")
    return cleaned_path

# ──────────────────────────── MAIN ──────────────────────────────────

def main(file_path: str | Path | None = None) -> Path:
    """Interface publique pour le pipeline."""
    ensure_dirs()
    raw_file = _resolve_input(file_path)
    return clean_file(raw_file)

# ────────────────────────── EXÉCUTION CLI ───────────────────────────
if __name__ == "__main__":
    user_path = input("Nom ou chemin du fichier brut à nettoyer (ENTER → dernier) : ").strip()
    try:
        out_path = main(user_path or None)
        print("\n✅ Nettoyage terminé →", out_path)
    except Exception as e:
        print("❌", e)
