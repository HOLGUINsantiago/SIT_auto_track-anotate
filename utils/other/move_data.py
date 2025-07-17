import os
import shutil

def copy_folders_with_labels_csv(source_dir, destination_dir):
    # Vérifie que le dossier source existe
    if not os.path.isdir(source_dir):
        raise ValueError(f"Le dossier source n'existe pas : {source_dir}")

    # Crée le dossier destination s'il n'existe pas
    os.makedirs(destination_dir, exist_ok=True)

    for root, dirs, files in os.walk(source_dir):
        # Vérifie s'il y a un fichier se terminant par "_labels.csv"
        if any(file.endswith("_labels.csv") for file in files):
            # Le dossier qui contient ce fichier
            folder_to_copy = root

            # Nom de base du dossier à copier (ex: juste le nom du sous-dossier)
            folder_name = os.path.basename(folder_to_copy)

            # Chemin de destination complet
            destination_path = os.path.join(destination_dir, folder_name)

            # Évite de copier deux fois le même dossier si déjà existant
            if not os.path.exists(destination_path):
                print(f"Copie de : {folder_to_copy} → {destination_path}")
                shutil.copytree(folder_to_copy, destination_path)
            else:
                print(f"Le dossier existe déjà : {destination_path}, non copié.")

# Exemple d'utilisation
source_dir = r"D:\Copie securite\Maternal_auto_classification_train_deepethogram\DATA"
destination_dir = r"D:\TRY"

copy_folders_with_labels_csv(source_dir, destination_dir)
