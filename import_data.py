# import_data.py
import os, json, re, shutil, requests, chardet
from pathlib import Path
from typing import List, Union

RAW_DIR        = Path("data/raw")
DICT_PATH      = Path("data/dictionary.json")
ML_DIR         = Path("ml_data")
ML_FILE        = ML_DIR / "training_data.csv"
LAST_FILE_PATH = Path("data/last_imported.txt")

# ───────────────────────── utilitaires ──────────────────────────
def ensure_dirs() -> None:
    for d in (RAW_DIR, ML_DIR):
        d.mkdir(parents=True, exist_ok=True)
    DICT_PATH.write_text("{}", encoding="utf-8") if not DICT_PATH.exists() else None

slugify   = lambda txt: re.sub(r"[^a-z0-9]+", "_", txt.lower()).strip("_")
is_url    = lambda p: p.startswith(("http://", "https://"))
detect_encoding = lambda p: chardet.detect(p.read_bytes()[:1_000]).get("encoding", "utf-8")

# ─────────────────────── cœur : import d’un fichier ───────────────────────
def add_one_file(source: str, *, final_name: str | None = None) -> str | None:
    """Copie/télécharge *source* dans `data/raw` et met à jour le dictionnaire."""

    dico: dict = json.loads(DICT_PATH.read_text(encoding="utf-8"))

    # nom automatique si absent
    if not final_name:
        stem = Path(source).stem or source.split("/")[-1][:50]
        final_name = slugify(stem)
        if final_name in dico:
            idx = 1
            while f"{final_name}_{idx}" in dico:
                idx += 1
            final_name = f"{final_name}_{idx}"
    elif final_name in dico:
        print(f"⚠️ Le nom « {final_name} » existe déjà.")
        return None

    raw_path = RAW_DIR / f"{final_name}.csv"

    try:
        if is_url(source):
            r = requests.get(source, timeout=30, allow_redirects=True)
            r.raise_for_status()
            # petite vérif : si c’est HTML on prévient
            if "text/html" in r.headers.get("Content-Type", ""):
                print("⚠️ L’URL ne renvoie pas un fichier direct (contenu HTML détecté).")
                return None
            raw_path.write_bytes(r.content)
        else:
            src = Path(source)
            if not src.exists():
                print("❌ Fichier local introuvable.")
                return None
            shutil.copy2(src, raw_path)

        print(f"✅ Fichier enregistré : {raw_path}")
    except Exception as e:
        print("❌ Échec du téléchargement/de la copie :", e)
        return None

    # mise à jour du dictionnaire
    dico[final_name] = {
        "source": source,
        "path"  : str(raw_path),
        "encoding": detect_encoding(raw_path),
    }
    DICT_PATH.write_text(json.dumps(dico, indent=4, ensure_ascii=False), encoding="utf-8")
    ML_FILE.write_text(f"{source},{final_name}\n", encoding="utf-8", errors="ignore", append=True)
    LAST_FILE_PATH.write_text(final_name, encoding="utf-8")

    return str(raw_path)

# ───────────────────── fonction publique main() ────────────────────
def main(
    sources: Union[str, List[str], None] = None,
    *,
    auto_name: str | None = None,
) -> str:
    """
    Importe un ou plusieurs fichiers, retourne le chemin du dernier.

    - `sources` :
        * None  → invite utilisateur (une seule fois).
        * str   → ‘a.csv, https://…b.xlsx’
        * list  → ['a.csv', 'b.xlsx']
    - `auto_name` : nom imposé (utile pour appels programmatiques).
    """
    ensure_dirs()

    # prépare la liste de sources
    if sources is None:
        raw = input("Lien(s) ou chemin(s) (séparés par virgule) :\n> ")
        sources_list = [s.strip() for s in raw.split(",") if s.strip()]
    elif isinstance(sources, str):
        sources_list = [s.strip() for s in sources.split(",") if s.strip()]
    else:
        sources_list = [str(s).strip() for s in sources]

    if not sources_list:
        print("❌ Aucune source fournie.")
        return ""

    last_path = ""
    for i, src in enumerate(sources_list, 1):
        print(f"─ Import {i}/{len(sources_list)} ─")
        last_path = add_one_file(src, final_name=auto_name) or last_path

    print("🎉 Import terminé.")
    return last_path

# ───────────────────────── exécution directe ───────────────────────
if __name__ == "__main__":
    main()
