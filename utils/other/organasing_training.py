import os
import shutil
import pandas as pd

# Ruta base
base_dir = r'D:\LBN\Maternal_auto_classification_train_deepethogram\DATA'
trash_dir = r"D:\LBN\trash"

# Comportamientos válidos
allowed_behaviors = {'Onnest', 'Offnest', 'background','Unnamed: 0' , 'Eat_drink'}

# Recorrer las subcarpetas directamente bajo DATA
for folder_name in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder_name)

    # Saltar si no es carpeta o es la carpeta trash
    if not os.path.isdir(folder_path) or folder_name == 'trash':
        continue

    # Buscar archivo *_labels.csv en esta carpeta
    label_file = None
    for f in os.listdir(folder_path):
        if f.endswith('_labels.csv') and "CONT" in f and "Cage6" not in f:
            label_file = os.path.join(folder_path, f)
            break

    if label_file:
        df = pd.read_csv(label_file)
        if df.columns[0] == '':
            df = df.iloc[:, 1:]

        active_behaviors = set(df.columns[df.sum() > 0])

        if active_behaviors.issubset(allowed_behaviors):
            print(f"Moviendo carpeta: {folder_path}")
            shutil.move(folder_path, os.path.join(trash_dir, folder_name))
