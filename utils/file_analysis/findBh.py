import os
import pandas as pd

# Ruta base
base_dir = r'D:\LBN\Maternal_auto_classification_train_deepethogram\DATA'

# Lista para guardar nombres de archivos con background == 1
files_with_background = []

# Recorrer archivos
for root, _, files in os.walk(base_dir):
    for file in files:
        if file.endswith('_labels.csv'):
            file_path = os.path.join(root, file)
            df = pd.read_csv(file_path)

            # Quitar la primera columna si no tiene nombre (índice)
            if df.columns[0] == '':
                df = df.iloc[:, 1:]

            # Verificar si hay algún 1 en la columna 'background'
            if df['background'].sum() > 0 :
                files_with_background.append(file_path)

# Mostrar los archivos encontrados
print("Archivos con al menos un '1' en la columna 'background':")
for path in files_with_background:
    print(path)
