import os, re, json, shutil, requests, chardet
from urllib.parse import urlparse

RAW_DIR  = "data/raw"
DICT_PATH = "data/dictionary.json"
ML_DIR  = "ml_data"
ML_FILE = os.path.join(ML_DIR, "training_data.csv")
LAST_FILE_PATH = "data/last_imported.txt"  # ✅ fichier mémoire

# ---------- utilitaires ----------
def ensure_dirs():
    for d in (RAW_DIR, ML_DIR):
        os.makedirs(d, exist_ok=True)
    if not os.path.exists(DICT_PATH):
        with open(DICT_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return "_".join(text.split())

def detect_encoding(path: str) -> str:
    with open(path, "rb") as f:
        return chardet.detect(f.read(10000)).get("encoding", "utf-8")

def is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")

# ---------- ajout d'un fichier ----------
def add_one_file(source: str) -> str | None:
    with open(DICT_PATH, "r", encoding="utf-8") as f:
        dico = json.load(f)

    while True:
        name_input = input(f"\nEntrez un nom pour ce fichier : ").strip()
        final_name = slugify(name_input)
        if final_name in dico:
            print("⚠️ Ce nom existe déjà. Choisissez-en un autre.")
        else:
            break

    raw_path = os.path.join(RAW_DIR, f"{final_name}.csv")

    try:
        if is_url(source):
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/csv,application/vnd.ms-excel"
            }
            r = requests.get(source, timeout=30, allow_redirects=True, headers=headers)
            r.raise_for_status()

            content_type = r.headers.get("Content-Type", "")
            if "text" not in content_type and "application" not in content_type:
                print("❌ Le lien ne semble pas pointer vers un fichier téléchargeable.")
                print(f"🔎 Content-Type détecté : {content_type}")
                return None

            with open(raw_path, "wb") as f_out:
                f_out.write(r.content)
        else:
            if not os.path.exists(source):
                print("❌ Fichier local introuvable.")
                return None
            shutil.copy(source, raw_path)

        print(f"✅ Sauvegardé sous {raw_path}")
    except Exception as e:
        print("❌ Erreur de transfert :", e)
        return None

    enc = detect_encoding(raw_path)

    dico[final_name] = {"source": source, "path": raw_path, "encoding": enc}
    with open(DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(dico, f, indent=4, ensure_ascii=False)

    with open(ML_FILE, "a", encoding="utf-8") as f:
        f.write(f"{source},{final_name}\n")

    with open(LAST_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(final_name)

    print(f"🗂️ Nom '{final_name}' ajouté au dictionnaire.")
    return raw_path

# ---------- pour appel depuis main_pipeline ----------
def main() -> str:
    ensure_dirs()
    sources = input("Entrez un ou plusieurs liens/fichiers séparés par virgule :\n> ").strip().split(",")
    sources = [s.strip() for s in sources if s.strip()]
    last_path = None
    for src in sources:
        last_path = add_one_file(src)
    print("\n🎉 Import terminé.")
    return last_path if last_path else ""

# ---------- mode exécution directe ----------
if __name__ == "__main__":
    main()
