import os

carpeta_x = r"Training-5"

for filename in os.listdir(carpeta_x):
    if " " in filename:
        old_path = os.path.join(carpeta_x, filename)
        new_filename = filename.replace(" ", "")
        new_path = os.path.join(carpeta_x, new_filename)
        os.rename(old_path, new_path)
        print(f"Renombrado: {filename} → {new_filename}")
