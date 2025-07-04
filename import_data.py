import os, json, re, shutil, requests, chardet
from pathlib import Path
from typing import List, Union

RAW_DIR        = Path("data/raw")
DICT_PATH      = Path("data/dictionary.json")
ML_DIR         = Path("ml_data")
ML_FILE        = ML_DIR / "training_data.csv"
LAST_FILE_PATH = Path("data/last_imported.txt")  # mémorise le dernier import

# ─────────────────────────── utilitaires ────────────────────────────

def ensure_dirs() -> None:
    for d in (RAW_DIR, ML_DIR):
        d.mkdir(parents=True, exist_ok=True)
    if not DICT_PATH.exists():
        DICT_PATH.write_text("{}", encoding="utf-8")

def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")

def detect_encoding(path: Path) -> str:
    with path.open("rb") as f:
        return chardet.detect(f.read(1000)).get("encoding", "utf-8")

def is_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))

# ────────────────────── ajout d’un fichier ──────────────────────────

def add_one_file(source: str, final_name: str | None = None) -> str | None:
    """Télécharge ou copie `source` dans data/raw/ et met à jour le dictionnaire."""
    with DICT_PATH.open("r", encoding="utf-8") as f:
        dico = json.load(f)

    # ─── Gestion du nom unique ──────────────────────
    if final_name:
        final_name = slugify(final_name)
        if final_name in dico:
            print(f"⚠️ Le nom '{final_name}' existe déjà.")
            return None
    else:
        while True:
            name_input = input("📝 Nom pour ce fichier : ").strip()
            final_name = slugify(name_input)
            if final_name in dico:
                print("⚠️ Nom déjà utilisé, choisis-en un autre.")
            elif final_name:
                break

    raw_path = RAW_DIR / f"{final_name}.csv"

    try:
        if is_url(source):
            r = requests.get(source, timeout=30, allow_redirects=True)
            r.raise_for_status()
            with raw_path.open("wb") as f_out:
                f_out.write(r.content)
        else:
            src_path = Path(source)
            if not src_path.exists():
                print("❌ Fichier local introuvable.")
                return None
            shutil.copy2(src_path, raw_path)
        print(f"✅ Fichier sauvegardé : {raw_path}")
    except Exception as e:
        print("❌ Erreur de téléchargement/copie :", e)
        return None

    dico[final_name] = {
        "source": source,
        "path": str(raw_path),
        "encoding": detect_encoding(raw_path),
    }
    DICT_PATH.write_text(json.dumps(dico, indent=4, ensure_ascii=False), encoding="utf-8")

    with ML_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{source},{final_name}\n")

    LAST_FILE_PATH.write_text(final_name, encoding="utf-8")
    return str(raw_path)

# ────────────────────── programme principal (CLI/API) ───────────────

def main(sources: Union[str, List[str], None] = None, *, auto_name: str | None = None) -> str:
    """Importe un ou plusieurs fichiers puis renvoie le chemin du dernier importé."""
    ensure_dirs()

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

    last_path = None
    for i, src in enumerate(sources_list, 1):
        print(f"\n— Import {i}/{len(sources_list)} —")
        last_path = add_one_file(src, final_name=auto_name)

    print("\n🎉 Import terminé.")
    return last_path or ""

if __name__ == "__main__":
    main()
