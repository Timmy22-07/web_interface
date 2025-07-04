# ────────────────────────── import_data.py ──────────────────────────
import os, re, json, shutil, requests, chardet
from pathlib import Path
from typing import List, Union

RAW_DIR        = Path("data/raw")
DICT_PATH      = Path("data/dictionary.json")
ML_DIR         = Path("ml_data")
ML_FILE        = ML_DIR / "training_data.csv"
LAST_FILE_PATH = Path("data/last_imported.txt")     # mémorise le dernier import

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
def add_one_file(source: str, *, final_name: str | None = None) -> str | None:
    """Télécharge ou copie `source` dans data/raw/ et met à jour le dictionnaire."""

    with DICT_PATH.open("r", encoding="utf-8") as f:
        dico: dict = json.load(f)

    # ─── Choix / validation du nom interne ───────────────────────────
    if final_name:
        final_name = slugify(final_name)
        if final_name in dico:
            print(f"⚠️  Le nom « {final_name} » existe déjà.")
            return None
    else:
        while True:
            name_input = input("📝 Nom interne pour ce fichier : ").strip()
            final_name = slugify(name_input)
            if final_name in dico:
                print("⚠️  Nom déjà utilisé, choisis-en un autre.")
            elif final_name:
                break

    raw_path = RAW_DIR / f"{final_name}.csv"        # extension neutre (on ne la touche plus)

    # ─── Téléchargement / copie ──────────────────────────────────────
    try:
        if is_url(source):
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/csv, application/vnd.ms-excel, */*"
            }
            r = requests.get(source, timeout=30, headers=headers, allow_redirects=True)
            r.raise_for_status()

            ctype = r.headers.get("Content-Type", "").lower()
            if "html" in ctype:
                print("⚠️  Le lien renvoie du HTML. Vérifie qu’il s’agit bien d’un export CSV/XLSX.")
                # on continue quand même – certains exports StatCan renvoient text/html mais contiennent le fichier
            with raw_path.open("wb") as f_out:
                f_out.write(r.content)

        else:                                       # fichier local
            src_path = Path(source)
            if not src_path.exists():
                print("❌ Fichier local introuvable.")
                return None
            shutil.copy2(src_path, raw_path)

        print(f"✅  Fichier sauvegardé → {raw_path}")

    except Exception as e:
        print("❌  Erreur de transfert :", e)
        return None

    # ─── Mise à jour du dictionnaire + logs ──────────────────────────
    dico[final_name] = {
        "source"  : source,
        "path"    : str(raw_path),
        "encoding": detect_encoding(raw_path),
    }
    DICT_PATH.write_text(json.dumps(dico, indent=4, ensure_ascii=False), encoding="utf-8")

    with ML_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{source},{final_name}\n")

    LAST_FILE_PATH.write_text(final_name, encoding="utf-8")
    return str(raw_path)

# ──────────────────────── programme principal ───────────────────────
def main(
    source: Union[str, List[str], None] = None,
    *,
    final_name: str | None = None,
) -> str:
    """
    Appel CLI : lance le prompt si `source` vaut None.
    Appel API : passe une URL ou un chemin dans `source` (str ou liste) + `final_name` optionnel.
    Retourne le **chemin** du dernier fichier importé ou "" si échec.
    """
    ensure_dirs()

    if source is None:                         # ⇒ utilisation interactive
        raw = input("🟩 Lien(s) ou chemin(s) (.csv/.xlsx) séparés par virgule :\n> ")
        sources = [s.strip() for s in raw.split(",") if s.strip()]
    elif isinstance(source, str):
        sources = [source.strip()]
    else:                                      # liste déjà fournie
        sources = [str(s).strip() for s in source]

    if not sources:
        print("❌  Aucune source fournie.")
        return ""

    last_path = None
    for i, src in enumerate(sources, 1):
        print(f"\n— Import {i}/{len(sources)} —")
        last_path = add_one_file(src, final_name=final_name)

    print("\n🎉  Import terminé.")
    return last_path or ""

# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
