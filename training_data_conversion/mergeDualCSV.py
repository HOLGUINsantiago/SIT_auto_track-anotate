import pandas as pd
import os
import csv
from deepethogram.file_io import VideoReader
import numpy as np

# === Utilidades previas sin cambios importantes ===
def nombre_frames_video(chemin_video):
    reader = VideoReader(chemin_video)
    num_frames = len(reader) - 1
    return num_frames

def nettoyer_csv(filepath):
    lignes_brutes = []
    lignes_nettoyees = []
    start_index = end_index = None
    header = None

    with open(filepath, 'r', encoding='utf-8') as f:
        sample = f.read(2048)
        f.seek(0)
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample)
        lecteur = csv.reader(f, dialect)
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


import pandas as pd
import numpy as np

def fusionner_csvs(filepath1, filepath2):
    data1 = nettoyer_csv(filepath1)
    data2 = nettoyer_csv(filepath2)

    df1 = pd.DataFrame(data1[1:], columns=data1[0])
    df2 = pd.DataFrame(data2[1:], columns=data2[0])

    # Nettoyer les noms de colonnes vides
    def nettoyer_colonnes(df):
        nouvelles_colonnes = []
        compteur_vide = 0
        for c in df.columns:
            if c.strip() == "":
                compteur_vide += 1
                nouvelles_colonnes.append(f"Empty_{compteur_vide}")
            else:
                nouvelles_colonnes.append(c.strip())
        df.columns = nouvelles_colonnes
        return df

    df1 = nettoyer_colonnes(df1)
    df2 = nettoyer_colonnes(df2)

    df1['Time'] = df1['Time'].str.replace(',', '.', regex=False)
    df2['Time'] = df2['Time'].str.replace(',', '.', regex=False)

    df1['Time'] = pd.to_numeric(df1['Time'], errors='coerce')
    df2['Time'] = pd.to_numeric(df2['Time'], errors='coerce')

    df1 = df1.dropna(subset=['Time']).sort_values(by='Time').reset_index(drop=True)
    df2 = df2.dropna(subset=['Time']).sort_values(by='Time').reset_index(drop=True)

    merged = pd.merge(df1, df2, on='Time', how='outer', suffixes=('_ann1', '_ann2')).sort_values(by='Time').reset_index(drop=True)

    colonnes = set(c.split('_ann1')[0] for c in merged.columns if '_ann1' in c)
    colonnes.update(c.split('_ann2')[0] for c in merged.columns if '_ann2' in c)
    colonnes.discard('Time')

    fusion = pd.DataFrame()
    fusion['Time'] = merged['Time']

    for col in colonnes:
        col1 = f'{col}_ann1'
        col2 = f'{col}_ann2'

        col_in_1 = col1 in merged.columns
        col_in_2 = col2 in merged.columns

        if col_in_1 and col_in_2:
            def fusionner_ligne(row):
                v1 = row[col1]
                v2 = row[col2]

                is_v1_valid = pd.notna(v1) and str(v1).strip() != ""
                is_v2_valid = pd.notna(v2) and str(v2).strip() != ""

                if is_v1_valid and is_v2_valid:
                    return f"{str(v1).strip()} | {str(v2).strip()}"
                elif is_v1_valid:
                    return str(v1).strip()
                elif is_v2_valid:
                    return str(v2).strip()
                else:
                    return ""

            fusion[col] = merged[[col1, col2]].apply(fusionner_ligne, axis=1)

        elif col_in_1:
            fusion[col] = merged[col1].fillna("").apply(lambda x: str(x).strip() if str(x).strip() != "" else "")
        elif col_in_2:
            fusion[col] = merged[col2].fillna("").apply(lambda x: str(x).strip() if str(x).strip() != "" else "")

    return fusion


def traiter_fichiers_csv_dual(filepath1, filepath2, chemin_video, dossier_sortie_csv, shift_fraction):
    nom_video = os.path.basename(chemin_video)
    frames_totales = nombre_frames_video(chemin_video)

    if frames_totales is None:
        print(f"❌ Nombre de frames non trouvé pour {nom_video}")
        return

    print(f"📹 Nombre de frames dans {nom_video} : {frames_totales}")

    df = fusionner_csvs(filepath1, filepath2)

    lignes_count = len(df)
    if lignes_count == 0:
        print("❌ Aucune ligne exploitable dans les fichiers.")
        return

    base_repeats = frames_totales // lignes_count
    reste = frames_totales % lignes_count

    colonnes_comportements = [col for col in df.columns if col != 'Time']
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
    nom_fichier = os.path.basename(filepath1)
    chemin_sortie = os.path.join(dossier_sortie_csv, nom_fichier)

    def normaliser_decalage(df_etiquetas):
        total = len(df_etiquetas)
        max_shift = int(total * shift_fraction)
        if max_shift < 1:
            return df_etiquetas
        print(f"Normalisation décalage: total={total}, max_shift={max_shift}")
        # Identificar filas sin anotaciones (background == 1)
        filas_sin_anotacion = df_etiquetas[df_etiquetas['background'] == 1]
        filas_con_anotacion = df_etiquetas[df_etiquetas['background'] == 0]

        # Eliminar hasta `max_shift` filas sin anotación al inicio si están disponibles
        sin_anot_inicio = filas_sin_anotacion.head(max_shift).index
        df_shifted = df_etiquetas.drop(index=sin_anot_inicio).reset_index(drop=True)

        # Duplicar `max_shift` filas sin anotación del final (si hay suficientes)
        sin_anot_final = df_shifted[df_shifted['background'] == 1].tail(max_shift)
        df_shifted = pd.concat([df_shifted, sin_anot_final], ignore_index=True)

        return df_shifted

    if shift_fraction != 0:
        resultat = normaliser_decalage(resultat)

    resultat = resultat.drop(columns=['Transitions', 'Autres', 'Non visible', "Test "], errors='ignore')
    orden_columnas = [
        'background',
        'Contact by host',
        'Contact by visitor',
        'Follow by host',
        'Follow by visitor',
        'Paw control (host)',
        'Rearing',
        'Tail rattling',
        'Grooming'
    ]
    resultat = resultat[[col for col in orden_columnas if col in resultat.columns]]

    resultat.to_csv(chemin_sortie, index=False)
    print(f"✔ CSV combiné produit ({len(resultat)} frames) → {chemin_sortie}")

def trouver_video_recursive(base_nom, dossier_parent):
    for racine, _, fichiers in os.walk(dossier_parent):
        for fichier in fichiers:
            if fichier.startswith(base_nom) and os.path.splitext(fichier)[1].lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                return os.path.join(racine, fichier)
    return None

def traiter_lot_dual(dossier_ann1, dossier_ann2, dossier_videos, dossier_sortie, shift_fraction=0.0005):
    print("📦 Traitement en lot pour double annotations...")

    fichiers_ann1 = [os.path.join(racine, f) for racine, _, fichiers in os.walk(dossier_ann1) for f in fichiers if f.endswith(".csv")]
    fichiers_ann2 = [os.path.join(racine, f) for racine, _, fichiers in os.walk(dossier_ann2) for f in fichiers if f.endswith(".csv")]
    fichiers_ann2_dict = {os.path.splitext(os.path.basename(f))[0]: f for f in fichiers_ann2}

    for fichier1 in fichiers_ann1:
        base_nom = os.path.splitext(os.path.basename(fichier1))[0]+ "-LL"
        fichier2 = fichiers_ann2_dict.get(base_nom)

        if not fichier2:
            print(f"⚠️ Pas de fichier correspondant dans annotateur2 pour {base_nom}")
            continue

        base_nom_video = base_nom.split("-LL")[0]

        base_nom_video = base_nom_video.replace(" ", "")

        chemin_video = trouver_video_recursive(base_nom_video, dossier_videos)
        if not chemin_video:
            print(f"❌ Vidéo non trouvée pour {base_nom_video}")
            continue

        try:
            traiter_fichiers_csv_dual(
                filepath1=fichier1,
                filepath2=fichier2,
                chemin_video=chemin_video,
                dossier_sortie_csv=dossier_sortie,
                shift_fraction=shift_fraction
            )
        except Exception as e:
            print(f"⚠️ Erreur sur {base_nom} → {e}")

    print("✅ Traitement terminé.")

# === EXECUTION DIRECTE POUR TON USO ===

traiter_lot_dual(
    dossier_ann1=r"Z:\Marion\2. Tests - Manuels - Data\6. SIT\4. Preprocessed data\1. VEAVE_LBN-CONT\Cohorte 3\Adulte\SIT JS adult",
    dossier_ann2=r"Z:\Marion\2. Tests - Manuels - Data\6. SIT\4. Preprocessed data\1. VEAVE_LBN-CONT\Cohorte 3\Adulte\SIT LL adult",
    dossier_videos=r"D:\SIT_auto\SIT_deepethogram\DATA",
    dossier_sortie="./csv_deg_TS-1_dual/",
    shift_fraction=0.03
)
