# ─────────────────────────── web_interface.py  (refactor 2025‑07‑04) ──────────────────────────
"""
Interface Streamlit en 3 étapes :
1. Importation (local ou URL)  → data/raw/
2. Nettoyage (clean_data.main) → data/cleaned/
3. Visualisation (vizualisation.plot_data)

Correctifs :
• plus d'appel isolé à st.experimental_rerun   → on utilise st.rerun() **uniquement** après action utilisateur
• import du même fichier N fois                → auto‑incrémente le nom interne ‹foo›, ‹foo_2›, ‹foo_3› …
• forçage non‐interactif de add_one_file()     → interactive=False (plus de prompt bloquant)
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import streamlit as st
from import_data import add_one_file
from clean_data import main as clean_main
from vizualisation import plot_data, load_cleaned_file

# ────────────────────────────── CONSTANTES / OUTILS ──────────────────────────────
DATA_RAW        = Path("data/raw")
SLUG_PATTERN    = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Transforme « Nom de Fichier.csv » → "nom_de_fichier"."""
    return SLUG_PATTERN.sub("_", text.lower()).strip("_")


def auto_name(base: str) -> str:
    """Retourne un nom interne unique basé sur *base* (foo, foo_2, foo_3…)."""
    stem = slugify(base)
    suffix = 1
    candidate = stem
    with (Path("data/dictionary.json").open("r", encoding="utf-8")) as f:
        used = f.read()
    # boucle jusqu'à trouver un slug libre
    while stem and stem in used:
        suffix += 1
        stem = f"{candidate}_{suffix}"
    return stem or "file"


def safe_add_file(src: str | Path, desired_name: str | None) -> str | None:
    """Tente d'ajouter le fichier en auto‑incrémentant le nom interne si collision."""
    base_name = desired_name or Path(src).stem
    slug = slugify(base_name)
    attempt = 1
    while attempt <= 20:  # évite boucle infinie
        final = slug if attempt == 1 else f"{slug}_{attempt}"
        saved = add_one_file(str(src), final_name=final, interactive=False)  # ← non‑bloquant
        if saved:
            return saved
        attempt += 1
    return None  # échec après 20 tentatives


# ──────────────────────────── CONFIG STREAMLIT ───────────────────────────────────
st.set_page_config(page_title="Pipeline de données", layout="centered")
st.title("📊 Traitement de données (.csv / .xlsx)")

st.markdown(
    """
Téléversez un fichier local **ou** collez un lien (Statistique Canada ou autre).  
Le pipeline exécute : **Importation → Nettoyage → Visualisation**.
"""
)

# ───────────────────────────── ÉTAT GLOBAL ───────────────────────────────────────
st.session_state.setdefault("step", 0)
st.session_state.setdefault("cleaned_path", "")

step = st.session_state.step

# ──────────────────────────── ÉTAPE 1 : IMPORTATION ─────────────────────────────
if step == 0:
    st.subheader("🟢 Étape 1 : Importation")
    src_type = st.radio("Source des données :", ["Fichier local", "Lien URL"], horizontal=True)

    # ——— Import local ———————————————————————————————————————————————
    if src_type == "Fichier local":
        uploaded = st.file_uploader("Importez votre fichier", type=["csv", "xlsx", "xls"], help="200 Mo max.")
        fname = st.text_input("Nom interne (facultatif)")
        if uploaded and st.button("🚚 Importer"):
            suffix = Path(uploaded.name).suffix or ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            try:
                internal = slugify(fname) if fname else auto_name(Path(uploaded.name).stem)
                saved_path = safe_add_file(tmp_path, internal)
            finally:
                os.unlink(tmp_path)
            if saved_path:
                st.success(f"✅ Importé : {saved_path}")
                st.session_state.step = 1
                st.rerun()
            else:
                st.error("❌ Importation échouée après plusieurs tentatives.")

    # ——— Import par URL ————————————————————————————————————————————————
    else:
        url = st.text_input("Collez le lien direct (.csv/.xlsx ou export StatCan)")
        fname = st.text_input("Nom interne (facultatif)")
        if st.button("🌐 Importer depuis l'URL") and url:
            internal = slugify(fname) if fname else auto_name(Path(url).stem)
            saved_path = safe_add_file(url, internal)
            if saved_path:
                st.success(f"✅ Importé : {saved_path}")
                st.session_state.step = 1
                st.rerun()
            else:
                st.error("❌ Importation échouée – lien invalide ou réseau hors service.")

# ──────────────────────────── ÉTAPE 2 : NETTOYAGE ───────────────────────────────
elif step == 1:
    st.subheader("🧹 Étape 2 : Nettoyage des données")
    if st.button("🧼 Lancer le nettoyage"):
        with st.spinner("Nettoyage en cours…"):
            cleaned_path = clean_main()
        st.success(f"✅ Nettoyage terminé : {cleaned_path}")
        st.session_state.cleaned_path = str(cleaned_path)
        st.session_state.step = 2
        st.rerun()

    if st.button("⬅️ Retour à l’importation"):
        st.session_state.step = 0
        st.rerun()

# ──────────────────────────── ÉTAPE 3 : VISUALISATION ───────────────────────────
elif step == 2:
    st.subheader("📈 Étape 3 : Visualisation")
    cleaned_path = Path(st.session_state.cleaned_path)

    if cleaned_path.exists():
        # Indique à vizualisation.py que nous sommes en mode Streamlit
        st.session_state["__in_streamlit"] = True

        df = load_cleaned_file(cleaned_path.stem.replace("_cleaned", ""))
        if df is not None:
            st.sidebar.info("📌 Choisissez les paramètres du graphique dans la barre latérale.")
            plot_data(df)
        else:
            st.error("❌ Impossible de charger le fichier nettoyé.")
    else:
        st.error("❌ Fichier nettoyé introuvable.")

    col1, col2 = st.columns(2)
    if col1.button("⬅️ Retour au nettoyage"):
        st.session_state.step = 1
        st.rerun()
    if col2.button("🔄 Recommencer depuis le début"):
        st.session_state.clear()
        st.rerun()
