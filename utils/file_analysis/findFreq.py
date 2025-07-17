
import os
import csv
import pandas as pd
from datetime import datetime

# Mappage des comportements possibles dans la colonne 'Autres'
excel_behavior_mapping = {
    "On nest" : ["Onnest"],
    "Off nest" : ["Offnest"],
    "Carryingpups": ["Carrying pups"],
    "Selfgrooming": ["Self grooming"],
    "Eat_drink": ["Eat/drink"],
    "Kicking": ["Kicking"],  # ou "Aggression" selon tes fichiers
    "Groomingpups": ["Grooming pups"],
    "Build": ["Build"]
}

def quantifier_comportements_csv(filepath):
    """Quantifie la fréquence de chaque comportement dans un fichier CSV."""
    # Lire le CSV
    donnees_nettoyees = nettoyer_csv(filepath)
    df = pd.DataFrame(donnees_nettoyees[1:], columns=donnees_nettoyees[0])

    if 'Time' not in df.columns:
        print(f"⚠️ Colonne 'Time' non trouvée dans {filepath}")
        return None

    df['Time'] = df['Time'].str.replace(',', '.', regex=False)
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
    df = df.dropna(subset=['Time']).sort_values(by='Time').reset_index(drop=True)

    if len(df) == 0:
        print(f"❌ Aucune ligne exploitable dans {filepath}")
        return None

    # Quantification des comportements
    comportements_freq = {comportement: 0 for comportement in excel_behavior_mapping.keys()}
    
    # Compter les comportements dans chaque ligne
    for _, ligne in df.iterrows():
        for comportement, valeurs in excel_behavior_mapping.items():
            if 'Autres' in ligne:
                if any(valeur.strip() in str(ligne['Autres']) for valeur in valeurs):
                    comportements_freq[comportement] += 1

    return comportements_freq

def nettoyer_csv(filepath):
    """Nettoie un fichier CSV en supprimant les lignes vides et autres erreurs."""
    lignes_nettoyees = []
    entete_trouvee = False

    with open(filepath, 'r', encoding='utf-8') as f:
        lecteur = csv.reader(f, delimiter=";")
        for ligne in lecteur:
            if not ligne or all(cellule.strip() == "" for cellule in ligne):
                if entete_trouvee:
                    break
                continue

            if not entete_trouvee:
                if ligne[0].strip().lower() == 'time':
                    lignes_nettoyees.append(ligne)
                    entete_trouvee = True
                continue

            try:
                float(ligne[0].replace(',', '.'))
                lignes_nettoyees.append(ligne)
            except ValueError:
                continue

    return lignes_nettoyees

def trouver_fichier_csv_recursive(dossier_parent):
    """Trouve tous les fichiers CSV dans un dossier et ses sous-dossiers."""
    fichiers_csv = []
    for racine, _, fichiers in os.walk(dossier_parent):
        for fichier in fichiers:
            if fichier.endswith(".csv"):
                fichiers_csv.append(os.path.join(racine, fichier))
    return fichiers_csv


def est_valide_nuit_apres_seuil(nom_fichier, seuil="06.05.24_12h44"):
    """Vérifie si le fichier est nocturne et postérieur au seuil."""
    try:
        # Extraire la date et l'heure depuis le nom de fichier
        base = os.path.basename(nom_fichier)
        morceaux = base.split("_")
        if len(morceaux) < 3:
            return False  # nom malformé

        date_str = morceaux[-2]  # ex: 06.05.24
        heure_str = morceaux[-1].split(".")[0]  # ex: 23h15

        # Convertir en datetime
        dt_fichier = datetime.strptime(f"{date_str}_{heure_str}", "%d.%m.%y_%Hh%M")
        dt_seuil = datetime.strptime(seuil, "%d.%m.%y_%Hh%M")

        # Filtre : après seuil ET entre 20h et 7h59
        return dt_fichier > dt_seuil or True

    except Exception as e:
        print(f"⚠️ Nom de fichier invalide ou mal formaté: {nom_fichier} → {e}")
        return False


def traiter_lot(dossier_csvs, dossier_sortie):
    """Traite tous les fichiers CSV dans un dossier et enregistre les fréquences des comportements."""
    print("📦 Traitement en lot...")

    fichiers_csv = trouver_fichier_csv_recursive(dossier_csvs)


    # Liste pour stocker les résultats
    resultats = []

    for fichier_csv in fichiers_csv:
        nom_fichier = os.path.basename(fichier_csv)

        # Filtrage sur le nom de fichier (analyses uniquement sur fichiers valides)
        if not any(x in nom_fichier.lower() for x in [
            "metadata", "summary", "properties", "position", "velocity",
            "acceleration", "keypoints", "orientation"
        ]):
            try:
                # Quantifier les comportements dans le CSV
                comportements_freq = quantifier_comportements_csv(fichier_csv)
                if comportements_freq:
                    comportements_freq['Fichier'] = nom_fichier

                    # Créer un DataFrame à partir des résultats
                    df = pd.DataFrame([comportements_freq])

                    # Diviser les valeurs numériques par 5 (sauf la colonne 'Fichier')
                    for col in df.columns:
                        if col != 'Fichier':
                            df[col] = df[col] / 5

                    # Ajouter les résultats normalisés à la liste
                    resultats.append(df.iloc[0].to_dict())
                    
            except Exception as e:
                print(f"⚠️ Erreur sur {fichier_csv} → {e}")

    if resultats:
        # Créer un DataFrame final avec tous les résultats
        df_resultats = pd.DataFrame(resultats)
        
        # Enregistrer le fichier CSV de sortie
        os.makedirs(dossier_sortie, exist_ok=True)
        chemin_sortie = os.path.join(dossier_sortie, "frequencies_comportements.csv")
        df_resultats.to_csv(chemin_sortie, index=False)
        print(f"✔ Fréquences des comportements enregistrées dans {chemin_sortie}")
    else:
        print("❌ Aucun résultat trouvé.")

    print("✅ Traitement terminé.")


# Exemple d'appel
traiter_lot(
    dossier_csvs=r"D:\C0_camuni-D_trainingData\pre-processed-data\1. VEAVE_LBN-CONT",  # Dossier contenant les fichiers CSV
    dossier_sortie="./frequencies_output"  # Dossier de sortie pour le fichier CSV des résultats
)
