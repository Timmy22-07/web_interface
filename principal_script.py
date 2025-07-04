from import_data import main as import_main
from clean_data import main as clean_main
from vizualisation import plot_data, load_cleaned_file
from rich.console import Console
from pathlib import Path
import builtins

console = Console()

def confirm_step(message):
    response = input(f"{message} [o/n] : ").strip().lower()
    return response in ["o", "oui", "y", "yes"]

def run_pipeline():
    console.rule("[bold blue]Étape 1 - Importation[/]")
    source_type = input("Importer un [1] fichier local ou [2] depuis une URL ? [1/2] (1): ").strip()
    source_type = source_type if source_type in ["1", "2"] else "1"

    if source_type == "1":
        sources = input("Chemin complet ou relatif du fichier (.csv|.xlsx): ").strip()
    else:
        sources = input("Lien vers le fichier (.csv|.xlsx): ").strip()

    # Substitution du input temporaire
    old_input = builtins.input
    builtins.input = lambda prompt='': sources if "Lien(s)" in prompt or "Chemin" in prompt else old_input(prompt)

    try:
        last_import_path = import_main()
    finally:
        builtins.input = old_input

    if not last_import_path:
        print("❌ Importation échouée. Arrêt du script.")
        return

    if not confirm_step("Souhaitez-vous passer à l'étape de nettoyage ?"):
        print("⛔ Fin du processus après l'importation.")
        return

    console.rule("[bold green]Étape 2 - Nettoyage[/]")
    try:
        cleaned_path = clean_main()
    except Exception as e:
        print("❌ Erreur lors du nettoyage :", e)
        return

    if not confirm_step("Souhaitez-vous passer à l'étape de visualisation ?"):
        print("📦 Fin du processus après le nettoyage.")
        return

    console.rule("[bold magenta]Étape 3 - Visualisation[/]")
    try:
        filename = Path(cleaned_path).stem.replace("_cleaned", "")
        df = load_cleaned_file(filename)
        if df is not None:
            plot_data(df)
            print("✅ Visualisation terminée.")
    except Exception as e:
        print("❌ Erreur lors de la visualisation :", e)

if __name__ == "__main__":
    run_pipeline()
