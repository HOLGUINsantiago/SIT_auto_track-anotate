import os
import h5py
import numpy as np
import pandas as pd
import yaml

# Chemin du projet d'estimation
estimation_path = r"Maternal_auto_classification_TS7_deepethogram\DATA"

# Lister les dossiers vidéos
video_dirs = [d for d in os.listdir(estimation_path) if os.path.isdir(os.path.join(estimation_path, d))]

results = []

for video_dir in video_dirs:
    video_path = os.path.join(estimation_path, video_dir)
    h5_file = os.path.join(video_path, f'{video_dir}_outputs.h5')

    if not os.path.exists(h5_file):
        print(f"❌ Fichier manquant : {h5_file}")
        continue

    # Lire le fichier H5
    with h5py.File(h5_file, 'r') as f:
        probs = f['resnet18']['P'][:]               # Matrice de probabilité (frame, classes)
        thresholds = f['resnet18']['thresholds'][:]  # Seuils pour binarisation
        class_names = f['resnet18']['class_names'][:]  # Noms des comportements (bytes)

    # Transformation des noms de classes
    class_names = [name.decode('utf-8') for name in class_names[1:]]  # On ignore "background"
    frame_probs = probs[:, 1:]  # Supprimer la colonne de numéro de frame
    behavior_thresholds = thresholds[1:]  # Seuils par comportement (sans l’ID)

    # Binarisation
    binary_preds = (frame_probs >= behavior_thresholds).astype(int)

    # Détection de la condition (LBN, CONT, UNKNOWN)
    name_upper = video_dir.upper()
    if 'LBN' in name_upper:
        condition = 'LBN'
    elif 'CONT' in name_upper :
        condition = 'CTRL'
    else:
        condition = 'UNKNOWN'

    # Compter les frames positives par comportement
    for i, behavior in enumerate(class_names):
        count = int(np.sum(binary_preds[:, i]))
        results.append({
            'behavior': behavior,
            'video_name': video_dir,
            'condition': condition,
            'frame_count': count
        })

# Création du DataFrame final
df = pd.DataFrame(results)
df.sort_values(by=["behavior", "frame_count"], ascending=[True, False], inplace=True)

# Cargar los nombres de videos del split
with open('d:/LBN/Maternal_auto_classification_train_deepethogram/SPLITS/split_7.yaml', 'r') as f:
    split = yaml.safe_load(f)

train_videos = set(split.get('train', []))
val_videos = set(split.get('val', []))

def get_split_origin(video_name):
    if video_name in train_videos:
        return "train"
    elif video_name in val_videos:
        return "val"
    else:
        return "none"

df["split_origin"] = df["video_name"].apply(get_split_origin)
df.to_csv("frame_counts_by_behavior.csv", index=False)

print("✅ Fichier CSV généré : frame_counts_by_behavior.csv")


# Charger le CSV existant
df = pd.read_csv("frame_counts_by_behavior.csv")

# Initialiser la liste des vidéos sélectionnées
selected_rows = []

# Récupérer la liste des comportements
behaviors = df['behavior'].unique()

# Filtrer le DataFrame pour exclure ces vidéos
df = df[~df['video_name'].isin(split_videos)]


# Pour chaque comportement, équilibrer par condition
for behavior in behaviors:
    df_behavior = df[df['behavior'] == behavior]
    conditions = df_behavior['condition'].unique()
    
    for condition in conditions:
        df_cond = df_behavior[df_behavior['condition'] == condition]
        
        # Filtre : garder uniquement les vidéos avec au moins 30 frames de ce comportement
        df_cond = df_cond[df_cond['frame_count'] >= 30]
        
        # Si aucune vidéo ne remplit ce critère, on passe cette condition
        if df_cond.empty:
            print(f"⚠️ Pas de vidéos avec >=30 frames pour {behavior} en {condition}")
            continue
        
        # Cas Onnest/Offnest : 5 vidéos ≤ 100 frames + 5 vidéos aléatoires, mais garantir aussi 10 vidéos et 500 frames
        if behavior in ['Onnest', 'Offnest']:
            small_videos = df_cond[df_cond['frame_count'] <= 100].sort_values('frame_count').head(5)
            selected = small_videos.copy()
            
            others = df_cond.drop(small_videos.index)
            if len(others) > 0:
                random_videos = others.sample(n=min(5, len(others)), random_state=42)
                selected = pd.concat([selected, random_videos])
                
            selected = selected.head(10)
            # Si moins de 10 vidéos ou moins de 500 frames, avertir
            if len(selected) < 10 or selected['frame_count'].sum() < 500:
                print(f"⚠️ Moins de 10 vidéos ou moins de 500 frames pour {behavior} en {condition} (Onnest/Offnest)")
        
        else:
            # Pour les autres comportements, garantir au moins 10 vidéos ET 500 frames PAR CONDITION
            df_cond_shuffled = df_cond.sample(frac=1, random_state=42)
            
            total_frames = 0
            selected_indices = []
            
            for idx, row in df_cond_shuffled.iterrows():
                selected_indices.append(idx)
                total_frames += row['frame_count']
                # Stop si on a au moins 10 vidéos ET 500 frames cumulées pour cette condition
                if len(selected_indices) >= 10 and total_frames >= 500:
                    break
            
            selected = df_cond.loc[selected_indices]
            # Si moins de 10 vidéos ou moins de 500 frames, avertir
            if len(selected) < 10 or selected['frame_count'].sum() < 500:
                print(f"⚠️ Moins de 10 vidéos ou moins de 500 frames pour {behavior} en {condition}")
        
        selected_rows.append(selected)

# Concaténer toutes les sélections
df_selected = pd.concat(selected_rows)

# Sauvegarder le CSV final
df_selected.to_csv("selected_videos_balanced_filtered.csv", index=False)

print(f"✅ Sélection équilibrée terminée : {len(df_selected)} vidéos sélectionnées")
print("Fichier sauvegardé sous 'selected_videos_balanced_filtered.csv'")
