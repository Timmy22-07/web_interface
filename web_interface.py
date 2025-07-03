import streamlit as st
from import_data import main as import_main
from clean_data import main as clean_main
from vizualisation import plot_data, load_cleaned_file
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="📊 Pipeline Excel - Données", layout="wide")
st.markdown("""
    <h1 style='text-align: center; color: #4A90E2;'>📈 Pipeline de Traitement Excel</h1>
    <p style='text-align: center;'>Importation ➜ Nettoyage ➜ Visualisation</p>
""", unsafe_allow_html=True)

# --- Session state ---
if "step" not in st.session_state:
    st.session_state.step = 0

if "last_file" not in st.session_state:
    st.session_state.last_file = ""

# --- Sidebar ---
st.sidebar.title("Navigation")
if st.sidebar.button("🔄 Recommencer depuis le début"):
    st.session_state.step = 0
    st.session_state.last_file = ""
    st.experimental_rerun()

steps = ["Importation", "Nettoyage", "Visualisation"]
st.sidebar.markdown("## Étapes")
for i, label in enumerate(steps):
    st.sidebar.markdown(f"{'✅' if st.session_state.step > i else '⬜'} {label}")

# --- Étape 1 : Importation ---
if st.session_state.step == 0:
    st.subheader("📥 Étape 1 - Importation")
    source_type = st.radio("Importer un fichier Excel :", ["📁 Fichier local", "🌐 Depuis une URL"], horizontal=True)

    st.markdown("""
    <div style='background-color:#f0f8ff;padding:10px;border-radius:10px;'>
        ⚠️ Pour cette démonstration, l'import se fait encore en ligne de commande.<br>
        Veuillez exécuter le script `import_data.py` manuellement pour ajouter un fichier.
    </div>
    """, unsafe_allow_html=True)

    if st.button("✅ J'ai terminé l'importation"):
        try:
            last_file = import_main()
            if last_file:
                st.session_state.last_file = last_file
                st.session_state.step = 1
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Erreur d'importation : {e}")

# --- Étape 2 : Nettoyage ---
elif st.session_state.step == 1:
    st.subheader("🧹 Étape 2 - Nettoyage")
    st.info("Cliquez ci-dessous pour lancer le nettoyage de votre fichier importé.")

    if st.button("🧼 Nettoyer les données maintenant"):
        try:
            cleaned_path = clean_main()
            if cleaned_path:
                st.success("Nettoyage terminé avec succès !")
                st.session_state.cleaned_path = cleaned_path
                st.session_state.step = 2
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Erreur lors du nettoyage : {e}")

# --- Étape 3 : Visualisation ---
elif st.session_state.step == 2:
    st.subheader("📊 Étape 3 - Visualisation")
    filename = Path(st.session_state.cleaned_path).stem.replace("_cleaned", "")
    df = load_cleaned_file(filename)

    if df is not None:
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
