import pandas as pd
import os
import csv
from deepethogram.file_io import VideoReader

def nombre_frames_video(chemin_video):
    reader = VideoReader(chemin_video)
    num_frames = len(reader) - 1
    return num_frames

def nettoyer_csv(filepath, delimiter_csv):
    lignes_brutes = []
    lignes_nettoyees = []
    start_index = end_index = None
    header = None

    with open(filepath, 'r', encoding='utf-8') as f:
        lecteur = csv.reader(f, delimiter=delimiter_csv)
        lignes_brutes = list(lecteur)

    for ligne in lignes_brutes:
        if ligne and ligne[0].strip().lower() == 'time':
            header = ligne
            break

    for i, ligne in enumerate(lignes_brutes):
        contenu = " ".join(cell.lower() for cell in ligne if cell)
        if "start test" in contenu and start_index is None:
            start_index = max(0, i)
        elif "end test" in contenu:
            end_index = i
            break

    if start_index is not None and end_index is not None:
        lignes_nettoyees = lignes_brutes[start_index:end_index + 1]
        if header and lignes_nettoyees and lignes_nettoyees[0] != header:
            lignes_nettoyees.insert(0, header)

    return lignes_nettoyees

def traiter_fichier_csv_unique(filepath, chemin_video, dossier_sortie_csv, shift_fraction, delimiter_csv=",", decimal_csv="."):
    nom_video = os.path.basename(chemin_video)
    frames_totales  = nombre_frames_video(chemin_video)

    if frames_totales is None:
        print(f"❌ Nombre de frames non trouvé pour {nom_video}")
        return

    print(f"📹 Nombre de frames dans {nom_video} : {frames_totales}")

    donnees_nettoyees = nettoyer_csv(filepath, delimiter_csv)
    df = pd.DataFrame(donnees_nettoyees[1:], columns=donnees_nettoyees[0])

    if 'Time' not in df.columns:
        print(f"⚠️ Colonne 'Time' non trouvée dans {filepath}")
        return None

    if decimal_csv != ".":
        df['Time'] = df['Time'].str.replace(decimal_csv, ".", regex=False)
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
    df = df.dropna(subset=['Time']).sort_values(by='Time').reset_index(drop=True)

    lignes_count = len(df)
    if lignes_count == 0:
        print("❌ Aucune ligne exploitable dans le fichier.")
        return

    base_repeats = frames_totales // lignes_count
    reste = frames_totales % lignes_count

    colonnes_comportements = [
        col for col in df.columns
        if col not in ['Time'] and not col.startswith("Unnamed") and col.strip() != ""
    ]

    lignes_expandees = []
    for idx, (_, ligne) in enumerate(df.iterrows()):
        rep = base_repeats + (1 if idx < reste else 0)
        for _ in range(rep):
            nouvelle_ligne = {col: 1 if str(ligne[col]).strip() != "" else 0 for col in colonnes_comportements}
            lignes_expandees.append(nouvelle_ligne)

    resultat = pd.DataFrame(lignes_expandees)
    resultat['background'] = (resultat[colonnes_comportements].sum(axis=1) == 0).astype(int)
    colonnes_finales = ['background'] + colonnes_comportements
    resultat = resultat[colonnes_finales]

    os.makedirs(dossier_sortie_csv, exist_ok=True)
    nom_fichier = os.path.basename(filepath)
    chemin_sortie = os.path.join(dossier_sortie_csv, nom_fichier)

    chemin_sortie = chemin_sortie.replace("-LL", "")
    chemin_sortie = chemin_sortie.replace(" ", "")

    print(f"✔ CSV homogène produit ({len(resultat)} frames) → {chemin_sortie}")

    def normaliser_decalage(df_etiquetas):
        total = len(df_etiquetas)
        max_shift = int(total * shift_fraction)
        if max_shift < 1:
            return df_etiquetas
        new_order = list(range(max_shift, total)) + list(range(max_shift))
        return df_etiquetas.iloc[new_order].reset_index(drop=True)

    if shift_fraction != 0:
        resultat = normaliser_decalage(resultat)

    resultat = resultat.drop(columns=['Transitions', 'Autres', 'Non visible'], errors='ignore')
    resultat.to_csv(chemin_sortie, index=False)

def trouver_video_recursive(base_nom, dossier_parent):
    for racine, _, fichiers in os.walk(dossier_parent):
        for fichier in fichiers:
            if fichier.startswith(base_nom) and os.path.splitext(fichier)[1].lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                return os.path.join(racine, fichier)
    return None

def traiter_lot(dossier_csvs, dossier_videos, dossier_sortie, shift_fraction=0.0005, delimiter_csv=",", decimal_csv="."):
    print("📦 Traitement en lot...")

    fichiers_csv = []
    for racine, _, fichiers in os.walk(dossier_csvs):
        for f in fichiers:
            if f.endswith(".csv"):
                fichiers_csv.append(os.path.join(racine, f))

    for nom_csv in fichiers_csv:
        chemin_csv = nom_csv
        base_nom = os.path.splitext(os.path.basename(nom_csv))[0]

        if "-LL" in base_nom : 
            video_name = base_nom.replace("-LL", "")
            video_name = video_name.replace(" ", "")
        else : 
            video_name = base_nom
            video_name = video_name.replace(" ", "")

            
        chemin_video = trouver_video_recursive(video_name, dossier_videos)

        if not chemin_video:
            print(f"❌ Vidéo non trouvée pour {video_name}, base : {base_nom}")
            continue

        try:
            traiter_fichier_csv_unique(
                filepath=chemin_csv,
                chemin_video=chemin_video,
                dossier_sortie_csv=dossier_sortie,
                shift_fraction=shift_fraction,
                delimiter_csv=delimiter_csv,
                decimal_csv=decimal_csv
            )
        except Exception as e:
            print(f"⚠️ Erreur sur {nom_csv} → {e}")

    print("✅ Traitement terminé.")

# Exemple d'appel
traiter_lot(
    dossier_csvs=r"Z:\Marion\2. Tests - Manuels - Data\6. SIT\4. Preprocessed data\1. VEAVE_LBN-CONT\Cohorte 3\Adulte\SIT LL adult",
    dossier_videos=r"D:\SIT_auto\SIT_deepethogram\DATA",
    dossier_sortie="./LL_annotations/",
    shift_fraction=0.003,
    delimiter_csv=";",        # 👈 adapte ici selon tes fichiers
    decimal_csv=","           # 👈 adapte ici selon tes fichiers
)

# Exemple d'appel
traiter_lot(
    dossier_csvs=r"Z:\Marion\2. Tests - Manuels - Data\6. SIT\4. Preprocessed data\1. VEAVE_LBN-CONT\Cohorte 3\Adulte\SIT JS adult",
    dossier_videos=r"D:\SIT_auto\SIT_deepethogram\DATA",
    dossier_sortie="./JS_annotations/",
    shift_fraction=0.003,
    delimiter_csv=",",        # 👈 adapte ici selon tes fichiers
    decimal_csv="."           # 👈 adapte ici selon tes fichiers
)