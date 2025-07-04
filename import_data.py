# ────────────── import_data.py  – Version légère et compatible Streamlit ────────────────
import os
import shutil
import requests
from pathlib import Path
from urllib.parse import urlparse

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

def is_url(string: str) -> bool:
    return string.startswith("http://") or string.startswith("https://")

def add_one_file(source: str, *, final_name: str | None = None, interactive: bool = True) -> str | None:
    """Ajoute un fichier dans `data/raw` depuis un chemin local ou une URL.

    - `final_name` (sans extension) est obligatoire en mode non interactif.
    - Si `interactive=True` et `final_name=None`, on demande le nom en CLI.
    - Retourne le chemin enregistré, ou None si l’ajout a échoué.
    """
    if not final_name:
        if interactive:
            final_name = input("📝 Nom interne du fichier (sans extension) : ").strip()
        else:
            print("❌ Erreur : final_name requis en mode non interactif.")
            return None

    # nettoyage du nom
    final_name = final_name.strip().replace(" ", "_").lower()
    if not final_name:
        print("❌ Nom de fichier invalide.")
        return None

    # vérification si le nom est déjà pris
    for ext in [".csv", ".xlsx", ".xls"]:
        candidate = RAW_DIR / f"{final_name}{ext}"
        if candidate.exists():
            print(f"⚠️ Le fichier {candidate.name} existe déjà.")
            return None

    # source URL ou fichier local
    if is_url(source):
        try:
            response = requests.get(source, timeout=15)
            response.raise_for_status()
            ext = Path(urlparse(source).path).suffix or ".csv"
            dest = RAW_DIR / f"{final_name}{ext}"
            with open(dest, "wb") as f:
                f.write(response.content)
            print(f"✅ Fichier téléchargé et enregistré sous {dest}")
            return str(dest)
        except Exception as e:
            print(f"❌ Échec du téléchargement depuis l'URL : {e}")
            return None
    else:
        try:
            ext = Path(source).suffix or ".csv"
            dest = RAW_DIR / f"{final_name}{ext}"
            shutil.copy(source, dest)
            print(f"✅ Copie locale effectuée sous {dest}")
            return str(dest)
        except Exception as e:
            print(f"❌ Échec de la copie locale : {e}")
            return None
