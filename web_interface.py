import streamlit as st
import pandas as pd
import requests
from pathlib import Path
from io import BytesIO

st.set_page_config(page_title="📊 Pipeline Excel - Données", layout="wide")
st.markdown("""
    <h1 style='text-align: center; color: #4A90E2;'>📈 Pipeline de Traitement Excel</h1>
    <p style='text-align: center;'>Importation ➜ Nettoyage ➜ Visualisation</p>
""", unsafe_allow_html=True)

# --- Session state ---
if "step" not in st.session_state:
    st.session_state.step = 0

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

# --- Sidebar ---
st.sidebar.title("Navigation")
if st.sidebar.button("🔄 Recommencer depuis le début"):
    st.session_state.step = 0
    st.session_state.uploaded_file = None
    st.experimental_rerun()

steps = ["Importation", "Nettoyage", "Visualisation"]
st.sidebar.markdown("## Étapes")
for i, label in enumerate(steps):
    st.sidebar.markdown(f"{'✅' if st.session_state.step > i else '⬜'} {label}")

# --- Étape 1 : Importation ---
if st.session_state.step == 0:
    st.subheader("📥 Étape 1 - Importation")
    source_type = st.radio("Importer un fichier Excel :", ["📁 Fichier local", "🌐 Depuis une URL"], horizontal=True)

    if source_type == "📁 Fichier local":
        uploaded_file = st.file_uploader("Déposez un fichier Excel ici", type=["xlsx", "xls", "csv"])
        if uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            st.success("Fichier importé avec succès ✅")

    elif source_type == "🌐 Depuis une URL":
        url = st.text_input("Entrez l'URL du fichier :")
        if url:
            try:
                response = requests.get(url)
                response.raise_for_status()

                if ".csv" in url or "csv" in response.headers.get("Content-Type", ""):
                    df = pd.read_csv(BytesIO(response.content))
                else:
                    df = pd.read_excel(BytesIO(response.content), engine="openpyxl")

                st.session_state.uploaded_file = BytesIO(df.to_csv(index=False).encode())
                st.success("Fichier importé depuis l'URL ✅")
            except Exception as e:
                st.error(f"Erreur de chargement : {e}")

    if st.session_state.uploaded_file:
        if st.button("➡️ Passer au nettoyage"):
            st.session_state.step = 1
            st.experimental_rerun()

# --- Étape 2 : Nettoyage ---
elif st.session_state.step == 1:
    st.subheader("🧹 Étape 2 - Nettoyage")
    st.info("Nettoyage automatique en cours...")

    try:
        df = pd.read_csv(st.session_state.uploaded_file)
    except:
        st.session_state.uploaded_file.seek(0)
        df = pd.read_excel(st.session_state.uploaded_file)

    df.dropna(axis=1, how="all", inplace=True)
    df.dropna(axis=0, how="all", inplace=True)

    st.session_state.cleaned_df = df
    st.success("Nettoyage terminé ✅")

    if st.button("➡️ Passer à la visualisation"):
        st.session_state.step = 2
        st.experimental_rerun()

# --- Étape 3 : Visualisation ---
elif st.session_state.step == 2:
    st.subheader("📊 Étape 3 - Visualisation")
    df = st.session_state.cleaned_df

    st.markdown("### 🧾 Aperçu des données nettoyées")
    st.dataframe(df.head(10))

    from matplotlib import pyplot as plt
    import seaborn as sns

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if len(numeric_cols) >= 2:
        x_col = st.selectbox("🟦 Axe X", numeric_cols)
        y_col = st.selectbox("🟥 Axe Y", numeric_cols, index=1)

        max_val = df[y_col].max()
        min_val = df[y_col].min()
        avg_val = df[y_col].mean()

        fig, ax = plt.subplots()
        sns.lineplot(data=df, x=x_col, y=y_col, ax=ax, marker="o", linewidth=2.5)
        ax.set_title(f"Évolution de {y_col} en fonction de {x_col}", fontsize=14)
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel(y_col, fontsize=12)
        ax.grid(True)

        st.pyplot(fig)

        with st.expander("📌 Statistiques clés"):
            st.write(f"**Valeur minimale de {y_col}** : {min_val:.2f}")
            st.write(f"**Valeur maximale de {y_col}** : {max_val:.2f}")
            st.write(f"**Moyenne de {y_col}** : {avg_val:.2f}")
    else:
        st.warning("Pas assez de colonnes numériques pour générer un graphique.")

    st.success("🎉 Visualisation complétée !")
